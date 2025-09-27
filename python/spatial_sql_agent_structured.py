"""
使用StructuredOutputParser的空间SQL查询代理
真正使用LangChain的StructuredOutputParser来控制AI代理输出格式
"""

import logging
from typing import List, Tuple, Optional, Dict, Any
from langchain.chains import create_sql_query_chain
from base_llm import BaseLLM
from sql_connector import SQLConnector
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser,StructuredOutputParser,ResponseSchema
from langchain.output_parsers.retry import RetryOutputParser
from langchain_core.prompts import PromptTemplate
import re
import json

# 使用兼容的Pydantic导入方式
try:
    from pydantic import BaseModel, Field
    PYDANTIC_V2 = True
except ImportError:
    try:
        from pydantic.v1 import BaseModel, Field
        PYDANTIC_V2 = True
    except ImportError:
        from langchain_core.pydantic_v1 import BaseModel, Field
        PYDANTIC_V2 = False

class SpatialQueryResponse(BaseModel):
    """空间查询响应格式"""
    answer: str = Field(description="自然语言回答，解释查询结果和发现")
    geojson: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="GeoJSON格式的空间数据，如果查询不涉及空间数据可以省略"
    )

# 创建Pydantic输出解析器
output_parser = PydanticOutputParser(pydantic_object=SpatialQueryResponse)
format_instructions = output_parser.get_format_instructions()

# 空间查询系统提示词（使用真正的StructuredOutputParser）
SPATIAL_SYSTEM_PROMPT_STRUCTURED = f"""
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
2. 每次查询空间表要获得要素时，必须使用ST_AsGeoJSON(ST_Transform(geom, 4326))来将geom属性转换为WGS84坐标系的GeoJSON格式
3. 包含适当的空间索引优化
4. 避免危险操作（DROP, DELETE等）

## 响应格式要求
你必须严格按照以下JSON格式返回最终答案：

{format_instructions}

## 示例响应格式
```json
{{
  "answer": "查询成功返回了whupoi表的前2条记录，以GeoJSON FeatureCollection格式呈现。结果包含以下信息：第一条记录：- gid: 1 - osm_id: 845686557 - highway: traffic_signals - 几何类型: Point - 坐标: [114.3699588, 30.5309076] 第二条记录：- gid: 2 - osm_id: 1148740588 - barrier: gate - 几何类型: Point - 坐标: [114.3465494, 30.5240617]",
  "geojson": {{
    "type": "FeatureCollection",
    "features": [
      {{
        "type": "Feature",
        "geometry": {{
          "type": "Point",
          "coordinates": [114.3699588, 30.5309076]
        }},
        "properties": {{
          "gid": 1,
          "osm_id": "845686557",
          "highway": "traffic_signals"
        }}
      }},
      {{
        "type": "Feature",
        "geometry": {{
          "type": "Point",
          "coordinates": [114.3465494, 30.5240617]
        }},
        "properties": {{
          "gid": 2,
          "osm_id": "1148740588",
          "barrier": "gate"
        }}
      }}
    ]
  }}
}}
```

如果查询不涉及空间数据或不需要返回GeoJSON，可以省略geojson字段。

请确保你的响应是有效的JSON格式，可以直接被解析。

重要规则：当查询包含几何数据的表时，如果是空间查询且要求返回结果，默认将查询结果以完整的GeoJSON FeatureCollection形式返回。

强制要求：对于任何涉及空间表的查询，如果要求返回完整的结果集，必须使用以下格式返回GeoJSON FeatureCollection：
例如：
SELECT jsonb_build_object(
    'type', 'FeatureCollection',
    'features', jsonb_agg(
        jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::jsonb,
            'properties', to_jsonb(sub) - 'geom'
        )
    )
) AS geojson
FROM (
    SELECT * 
    FROM ${{tableName}}
    ${{whereClause}}
    ${{limitClause}}
) AS sub

示例正确的查询格式：
- 简单查询：SELECT gid, name, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry FROM whupoi LIMIT 3
- 完整GeoJSON查询：SELECT jsonb_build_object('type', 'FeatureCollection', 'features', jsonb_agg(jsonb_build_object('type', 'Feature', 'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::jsonb, 'properties', to_jsonb(sub) - 'geom'))) AS geojson FROM (SELECT * FROM whupoi LIMIT 3) AS sub

错误的查询格式（缺少坐标转换）：
SELECT gid, name, geom FROM whupoi LIMIT 3

如果查询涉及空间分析，请优先使用空间函数而不是普通SQL操作。

输出格式示例：
Thought: 我需要先查看数据库中有哪些表
Action: sql_db_list_tables
Action Input: ""

或者：
Thought: 我已经获得了所有需要的信息
Final Answer: {{
  "answer": "查询成功返回了2条记录",
  "geojson": {{
    "type": "FeatureCollection",
    "features": [...]
  }}
}}

重要：最终答案必须使用上述JSON格式，确保可以直接被解析。
"""


class StructuredSpatialSQLQueryAgent:
    """使用StructuredOutputParser的空间SQL查询代理类"""

    def __init__(self, system_prompt: Optional[str] = None, enable_spatial_functions: bool = True):
        """
        初始化结构化空间SQL查询代理

        Args:
            system_prompt: 自定义系统提示词，如果为None则使用默认结构化提示词
            enable_spatial_functions: 是否启用空间函数支持
        """
        self.connector = SQLConnector()
        self.enable_spatial_functions = enable_spatial_functions
        self.output_parser = output_parser

        # 创建LLM实例
        self.llm = BaseLLM()

        # 使用结构化系统提示词或自定义提示词
        final_prompt = system_prompt or SPATIAL_SYSTEM_PROMPT_STRUCTURED

        # 创建包含结构化输出要求的系统提示词
        self.prompt_template = PromptTemplate(
            template="""
{system_prompt}

用户查询：{query}

请严格按照指定的JSON格式返回最终答案。
""",
            input_variables=["system_prompt", "query"],
            partial_variables={"format_instructions": format_instructions}
        )

        # 创建SQL代理
        self.agent = create_sql_agent(
            self.llm.llm,
            db=self.connector.db,
            verbose=True,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            handle_parsing_errors=True,
            output_parser=RetryOutputParser.from_llm(
                llm=self.llm.llm, parser=StrOutputParser()),
            agent_executor_kwargs={"return_intermediate_steps": True}
        )

        # 确保输出解析为字符串
        self.chain = self.agent | StrOutputParser()

        self.logger = self._setup_logger()

        # 初始化思维链捕获相关变量
        self.thought_chain_log = []

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

    def run_with_structured_output(self, query: str) -> Dict[str, Any]:
        """
        执行SQL查询并返回结构化输出

        Args:
            query: 自然语言查询字符串

        Returns:
            结构化查询结果
        """
        try:
            if not isinstance(query, str):
                query = str(query)

            # 启用查询增强功能
            enhanced_query = self._enhance_spatial_query(query)
            self.logger.info(f"处理空间查询: {query}")
            self.logger.info(f"增强后的查询: {enhanced_query}")

            # 生成结构化提示词
            formatted_prompt = self.prompt_template.format(
                system_prompt=SPATIAL_SYSTEM_PROMPT_STRUCTURED,
                query=enhanced_query
            )

            # SQL agent expects input as a dictionary with 'input' key
            result = self.agent.invoke({"input": enhanced_query})

            if not isinstance(result, str):
                # Extract the output from the agent result
                if hasattr(result, 'get') and callable(result.get):
                    result = result.get('output', str(result))
                else:
                    result = str(result)

            # 尝试使用结构化解析器解析结果
            try:
                parsed_result = self.output_parser.parse(result)
                self.logger.info("✅ 成功使用StructuredOutputParser解析结果")
                return {
                    "status": "success",
                    "answer": parsed_result.get("answer", ""),
                    "geojson": parsed_result.get("geojson"),
                    "original_response": result,
                    "parser_used": "StructuredOutputParser"
                }
            except Exception as parse_error:
                self.logger.warning(f"StructuredOutputParser解析失败，使用备用解析器: {parse_error}")
                
                # 使用备用解析器
                from simple_structured_solution import parse_structured_response
                backup_result = parse_structured_response(result)
                
                return {
                    "status": "partial_success",
                    "answer": backup_result.get("answer", ""),
                    "geojson": backup_result.get("geojson"),
                    "original_response": result,
                    "parser_used": "BackupParser",
                    "parse_warning": f"StructuredOutputParser失败: {str(parse_error)}"
                }

        except Exception as e:
            self.logger.error(f"空间查询处理失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "parser_used": "None"
            }

    def run(self, query: str) -> str:
        """
        兼容现有接口，返回字符串格式的结果

        Args:
            query: 自然语言查询字符串

        Returns:
            字符串格式的查询结果
        """
        structured_result = self.run_with_structured_output(query)
        
        if structured_result["status"] == "success":
            # 返回格式化的JSON字符串
            return json.dumps({
                "answer": structured_result["answer"],
                "geojson": structured_result["geojson"]
            }, ensure_ascii=False, indent=2)
        else:
            # 返回错误信息
            return f"查询失败: {structured_result.get('error', '未知错误')}"

    def _enhance_spatial_query(self, query: str) -> str:
        """
        增强查询以包含空间提示

        Args:
            query: 原始查询

        Returns:
            增强后的查询
        """
        spatial_keywords = [
            '距离', '附近', '周围', '范围内', '路径', '路线', '最短', '最近',
            '相交', '包含', '在内', '边界', '面积', '长度', '周长',
            '点', '线', '面', '多边形', '几何', '空间', '地理',
            'buffer', 'intersect', 'contain', 'within', 'distance',
            'route', 'path', 'shortest', 'nearest', 'proximity'
        ]

        # 检查是否包含空间关键词
        has_spatial_keyword = any(keyword in query.lower()
                                  for keyword in spatial_keywords)

        # 检查是否涉及空间表查询（包含表名如whupoi等）
        spatial_tables = ['whupoi', 'map_elements', 'edges', 'faces', 'place', 'county', 'state']
        has_spatial_table = any(table in query.lower() for table in spatial_tables)

        if (has_spatial_keyword or has_spatial_table) and self.enable_spatial_functions:
            enhanced_query = f"""
{query}

请使用PostGIS空间函数来回答这个问题。确保：
1. 包含几何列（通常是geom）
2. 必须使用ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry来将geom属性转换为WGS84坐标系的GeoJSON格式
3. 使用适当的空间索引优化查询
4. 如果涉及路径规划，请使用PgRouting函数

强制要求：对于任何涉及空间表的查询，如果是空间查询且要求返回结果，默认将查询结果以完整的GeoJSON FeatureCollection形式返回。

推荐使用以下格式返回完整的GeoJSON FeatureCollection：

SELECT jsonb_build_object(
    'type', 'FeatureCollection',
    'features', jsonb_agg(
        jsonb_build_object(
            'type', 'Feature',
            'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::jsonb,
            'properties', to_jsonb(sub) - 'geom'
        )
    )
) AS geojson
FROM (
    SELECT * 
    FROM 表名
    WHERE 条件
    LIMIT 数量
) AS sub

示例正确的查询格式：
- 简单查询：SELECT gid, name, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry FROM whupoi LIMIT 3
- 完整GeoJSON查询：SELECT jsonb_build_object('type', 'FeatureCollection', 'features', jsonb_agg(jsonb_build_object('type', 'Feature', 'geometry', ST_AsGeoJSON(ST_Transform(geom, 4326))::jsonb, 'properties', to_jsonb(sub) - 'geom'))) AS geojson FROM (SELECT * FROM whupoi LIMIT 3) AS sub

错误的查询格式（缺少坐标转换）：
SELECT gid, name, geom FROM whupoi LIMIT 3

请直接返回有效的SQL查询语句。
"""
            return enhanced_query
        else:
            return query

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

            # 启用查询增强功能
            enhanced_query = self._enhance_spatial_query(query)
            self.logger.info(f"处理空间查询: {query}")
            self.logger.info(f"增强后的查询: {enhanced_query}")

            # 执行查询并获取中间步骤
            result = self.agent.invoke({"input": enhanced_query})
            
            # 提取中间步骤（即使有输出解析错误，中间步骤仍然可用）
            intermediate_steps = result.get('intermediate_steps', [])
            
            # 构建思维链
            thought_chain = []
            sql_queries_with_results = []
            
            for step_num, (action, observation) in enumerate(intermediate_steps, 1):
                # 构建动作步骤
                action_step = {
                    "step": step_num,
                    "type": "action",
                    "action": action.tool,
                    "action_input": action.tool_input,
                    "log": action.log,
                    "timestamp": str(hash(str(action))),
                    "observation": str(observation) if observation else "No output",
                    "status": "completed"
                }
                thought_chain.append(action_step)
                
                # 如果是SQL查询，记录详细信息
                if action.tool == 'sql_db_query':
                    sql_queries_with_results.append({
                        "sql": action.tool_input,
                        "result": observation,
                        "step": step_num,
                        "status": "completed"
                    })
            
            # 尝试提取最终结果，即使有错误也继续处理
            final_result = ""
            try:
                if hasattr(result, 'get'):
                    final_result = result.get('output', '')
                else:
                    final_result = str(result)
            except:
                final_result = "无法提取最终结果（可能存在输出解析错误）"
            
            # 添加最终答案步骤
            if final_result:
                final_step = {
                    "step": len(thought_chain) + 1,
                    "type": "final_answer",
                    "content": final_result,
                    "log": final_result,
                    "timestamp": str(hash(final_result)),
                    "status": "completed"
                }
                thought_chain.append(final_step)

            self.logger.info(f"捕获到{len(sql_queries_with_results)}个SQL查询及其执行结果")

            return {
                "status": "success" if intermediate_steps else "partial_success",
                "final_answer": final_result,
                "thought_chain": thought_chain,
                "step_count": len(thought_chain),
                "sql_queries_with_results": sql_queries_with_results,
                "intermediate_steps": intermediate_steps  # 保留原始中间步骤数据
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

    def close(self):
        """清理资源"""
        if hasattr(self, 'connector'):
            self.connector.close()


# 使用示例
if __name__ == "__main__":
    # 创建结构化空间查询代理
    structured_agent = StructuredSpatialSQLQueryAgent()

    try:
        # 测试结构化输出功能
        test_queries = [
            "查询whupoi表的前2条记录",
            "查找距离某个点5公里内的所有建筑",
            "计算从A点到B点的最短路径"
        ]

        for query in test_queries:
            print(f"\n=== 测试查询: {query} ===")
            result = structured_agent.run_with_structured_output(query)
            print(f"状态: {result['status']}")
            print(f"使用的解析器: {result['parser_used']}")
            print(f"Answer长度: {len(result.get('answer', ''))}")
            print(f"GeoJSON要素数: {len(result.get('geojson', {}).get('features', [])) if result.get('geojson') else 0}")
            
            if result.get('parse_warning'):
                print(f"解析警告: {result['parse_warning']}")

    finally:
        structured_agent.close()
