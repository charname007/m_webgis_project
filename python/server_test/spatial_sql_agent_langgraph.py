import logging
from typing import List, Tuple, Optional, Dict, Any
from base_llm import BaseLLM
from sql_connector import SQLConnector
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers.retry import RetryOutputParser
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, create_react_agent
import re
import json

# 空间查询系统提示词
SPATIAL_SYSTEM_PROMPT = """
你是一个专门处理空间数据库查询的AI助手。你精通PostGIS、PgRouting和PostGIS拓扑扩展。

IMPORTANT: 你必须严格遵守以下输出格式要求：
- 每个"Thought:"后面必须跟着"Action:"和"Action Input:"或者"Final Answer:"
- 不要跳过任何步骤，确保格式完全正确
- 使用明确的标记来区分思考、行动和最终答案

重要提示：
1. 当用户询问空间相关问题时，优先使用PostGIS函数
2. 对于路径规划问题，使用PgRouting函数
3. 对于拓扑关系问题，使用PostGIS拓扑函数

PostGIS常用函数：
- 空间关系：ST_Intersects, ST_Contains, ST_Within, ST_Distance, ST_Buffer
- 几何操作：ST_Union, ST_Intersection, ST_Difference, ST_Simplify
- 测量函数：ST_Length, ST_Area, ST_Perimeter
- 坐标转换：ST_Transform, ST_SetSRID
- 几何创建：ST_MakePoint, ST_MakeLine, ST_MakePolygon
- 几何分析：ST_Centroid, ST_Envelope, ST_ConvexHull

PgRouting常用函数：
- 最短路径：pgr_dijkstra, pgr_aStar, pgr_bdDijkstra
- 路径规划：pgr_trsp, pgr_turnRestrictedPath
- 网络分析：pgr_connectedComponents, pgr_strongComponents

PostGIS拓扑函数：
- 拓扑创建：TopoGeo_CreateTopology
- 拓扑编辑：TopoGeo_AddLineString, TopoGeo_AddPolygon
- 拓扑查询：GetTopoGeomElements, GetTopoGeomElementArray

查询示例：
- "查找距离某个点5公里内的所有建筑" → 使用ST_DWithin
- "计算两条路线的最短路径" → 使用pgr_dijkstra
- "分析两个多边形的拓扑关系" → 使用ST_Touches, ST_Overlaps

请确保生成的SQL查询：
1. 包含必要的几何列（通常是geom）
2. 使用ST_AsGeoJSON将几何数据转换为GeoJSON格式
3. 包含适当的空间索引优化
4. 避免危险操作（DROP, DELETE等）

如果查询涉及空间分析，请优先使用空间函数而不是普通SQL操作。
"""

class SpatialSQLQueryAgentLangGraph:
    """使用LangGraph的空间SQL查询代理类，专门处理空间数据库查询"""
    
    def __init__(self, system_prompt: Optional[str] = None, enable_spatial_functions: bool = True):
        """
        初始化空间SQL查询代理
        
        Args:
            system_prompt: 自定义系统提示词，如果为None则使用默认空间提示词
            enable_spatial_functions: 是否启用空间函数支持
        """
        self.connector = SQLConnector()
        self.enable_spatial_functions = enable_spatial_functions
        
        # 创建LLM实例
        self.llm = BaseLLM()
        
        # 使用空间系统提示词或自定义提示词
        final_prompt = system_prompt or SPATIAL_SYSTEM_PROMPT
        
        # 获取SQL工具包
        toolkit = SQLDatabaseToolkit(db=self.connector.db, llm=self.llm.llm)
        tools = toolkit.get_tools()
        
        # 创建LangGraph React Agent
        self.agent = create_react_agent(
            self.llm.llm,
            tools,
            prompt=final_prompt,
        )
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def run_with_thought_chain(self, query: str) -> Dict[str, Any]:
        """
        执行SQL查询并返回完整的思维链，包括SQL查询的执行结果
        
        Args:
            query: 自然语言查询字符串
            
        Returns:
            包含思维链和最终结果的字典
        """
        try:
            if not isinstance(query, str):
                query = str(query)
            
            self.logger.info(f"处理空间查询: {query}")
            
            # 使用LangGraph的stream模式捕获中间步骤
            thought_chain = []
            sql_queries_with_results = []
            final_answer = ""
            
            # 执行查询并捕获每个步骤
            for step in self.agent.stream(
                {"messages": [{"role": "user", "content": query}]},
                stream_mode="values",
            ):
                messages = step["messages"]
                last_message = messages[-1]
                
                # 记录每个步骤
                step_info = {
                    "step": len(thought_chain) + 1,
                    "messages": [msg.model_dump() for msg in messages],
                    "timestamp": str(hash(str(messages)))  # 简单的时间戳
                }
                
                # 检查是否是工具调用
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    for tool_call in last_message.tool_calls:
                        tool_step = {
                            "step": len(thought_chain) + 1,
                            "type": "action",
                            "action": tool_call.get('name', 'unknown'),
                            "action_input": tool_call.get('args', {}),
                            "log": str(last_message.content) if last_message.content else "",
                            "timestamp": step_info["timestamp"],
                            "status": "started"
                        }
                        thought_chain.append(tool_step)
                        
                        # 如果是SQL查询，执行并记录结果
                        if tool_call.get('name') == 'sql_db_query':
                            sql_query = tool_call.get('args', {}).get('query', '')
                            if sql_query:
                                try:
                                    # 直接执行SQL查询获取结果
                                    result = self.connector.execute_query(sql_query)
                                    tool_step["observation"] = result
                                    tool_step["status"] = "completed"
                                    
                                    # 记录SQL查询和结果
                                    sql_queries_with_results.append({
                                        "sql": sql_query,
                                        "result": result,
                                        "step": tool_step["step"],
                                        "status": "completed"
                                    })
                                except Exception as e:
                                    tool_step["observation"] = f"Error: {str(e)}"
                                    tool_step["status"] = "failed"
                                    sql_queries_with_results.append({
                                        "sql": sql_query,
                                        "result": f"Error: {str(e)}",
                                        "step": tool_step["step"],
                                        "status": "failed"
                                    })
                
                # 检查是否是最终答案
                if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
                    if last_message.content:
                        final_step = {
                            "step": len(thought_chain) + 1,
                            "type": "final_answer",
                            "content": last_message.content,
                            "log": str(last_message.content),
                            "timestamp": step_info["timestamp"],
                            "status": "completed"
                        }
                        thought_chain.append(final_step)
                        final_answer = last_message.content
            
            self.logger.info(f"捕获到{len(sql_queries_with_results)}个SQL查询及其执行结果")
            
            return {
                "status": "success",
                "final_answer": final_answer,
                "thought_chain": thought_chain,
                "step_count": len(thought_chain),
                "sql_queries_with_results": sql_queries_with_results
            }
            
        except Exception as e:
            self.logger.error(f"Error in run_with_thought_chain function: {e}")
            return {
                "status": "error",
                "error": f"处理您的请求时出现了问题：{str(e)}",
                "thought_chain": [],
                "step_count": 0,
                "sql_queries_with_results": []
            }
    
    def run(self, query: str) -> str:
        """
        执行SQL查询，支持空间查询
        
        Args:
            query: 自然语言查询字符串
            
        Returns:
            SQL查询结果字符串
        """
        try:
            result = self.agent.invoke({"messages": [{"role": "user", "content": query}]})
            
            # 提取最终答案
            if hasattr(result, 'messages'):
                messages = result.messages
                for msg in reversed(messages):
                    if hasattr(msg, 'content') and msg.content:
                        return str(msg.content)
            
            return str(result)
            
        except Exception as e:
            self.logger.error(f"空间查询处理失败: {e}")
            return f"抱歉，处理您的空间查询时出现了问题：{str(e)}"
    
    def close(self):
        """清理资源"""
        if hasattr(self, 'connector'):
            self.connector.close()


# 测试函数
def test_langgraph_agent():
    """测试LangGraph实现的SQL Agent"""
    print("=== 测试LangGraph SQL Agent ===")
    
    # 创建LangGraph代理
    agent = SpatialSQLQueryAgentLangGraph()
    
    try:
        # 测试查询
        test_query = "查询whupoi表的前5条记录"
        print(f"测试查询: {test_query}")
        
        # 使用思维链模式获取详细结果
        result = agent.run_with_thought_chain(test_query)
        
        print(f"执行状态: {result['status']}")
        print(f"最终答案: {result['final_answer']}")
        print(f"步骤数量: {result['step_count']}")
        
        # 显示思维链
        print("\n=== 思维链 ===")
        for step in result['thought_chain']:
            print(f"步骤 {step['step']}: {step['type']}")
            if step['type'] == 'action':
                print(f"  动作: {step['action']}")
                print(f"  输入: {step['action_input']}")
                print(f"  状态: {step['status']}")
                if 'observation' in step:
                    print(f"  观察结果: {step['observation'][:200]}...")
            elif step['type'] == 'final_answer':
                print(f"  内容: {step['content'][:200]}...")
            print()
        
        # 显示SQL查询和结果
        print("\n=== SQL查询和结果 ===")
        for sql_info in result['sql_queries_with_results']:
            print(f"步骤 {sql_info['step']}:")
            print(f"  SQL: {sql_info['sql']}")
            print(f"  状态: {sql_info['status']}")
            if sql_info['status'] == 'completed':
                print(f"  结果: {str(sql_info['result'])[:200]}...")
            print()
        
    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        agent.close()


if __name__ == "__main__":
    test_langgraph_agent()
