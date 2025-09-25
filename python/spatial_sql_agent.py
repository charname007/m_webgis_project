import logging
from typing import List, Tuple, Optional, Dict, Any
from langchain.chains import create_sql_query_chain
from base_llm import BaseLLM
from sql_connector import SQLConnector
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

# 空间查询系统提示词
SPATIAL_SYSTEM_PROMPT = """
你是一个专门处理空间数据库查询的AI助手。你精通PostGIS、PgRouting和PostGIS拓扑扩展。

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

class SpatialSQLQueryAgent:
    """空间SQL查询代理类，专门处理空间数据库查询"""
    
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
        
        # 创建包含空间知识的系统提示词
        custom_prompt = ChatPromptTemplate.from_messages([
            ("system", final_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # 重新配置LLM的提示词
        self.llm.prompt = custom_prompt
        
        # 创建SQL代理
        self.agent = create_sql_agent(
            self.llm.llm, 
            db=self.connector.db, 
            verbose=True, 
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
            handle_parsing_errors=True,
        )
        
        # 确保输出解析为字符串
        self.chain = self.agent | StrOutputParser()
        
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
    
    def run(self, query: str) -> str:
        """
        执行SQL查询，支持空间查询
        
        Args:
            query: 自然语言查询字符串
            
        Returns:
            SQL查询结果字符串
        """
        try:
            if not isinstance(query, str):
                query = str(query)
            
            # 增强查询以包含空间提示
            enhanced_query = self._enhance_spatial_query(query)
            
            self.logger.info(f"处理空间查询: {enhanced_query}")
            
            # SQL agent expects input as a dictionary with 'input' key
            result = self.agent.invoke({"input": enhanced_query})
            
            if not isinstance(result, str):
                # Extract the output from the agent result
                if hasattr(result, 'get') and callable(result.get):
                    result = result.get('output', str(result))
                else:
                    result = str(result)
            
            # 后处理结果，确保包含空间信息
            result = self._postprocess_result(result, query)
            
            return result
        except Exception as e:
            self.logger.error(f"空间查询处理失败: {e}")
            return f"抱歉，处理您的空间查询时出现了问题：{str(e)}"
    
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
        has_spatial_keyword = any(keyword in query.lower() for keyword in spatial_keywords)
        
        if has_spatial_keyword and self.enable_spatial_functions:
            enhanced_query = f"""
{query}

请使用PostGIS空间函数来回答这个问题。确保：
1. 包含几何列（通常是geom）
2. 使用ST_AsGeoJSON将几何数据转换为GeoJSON格式
3. 使用适当的空间索引优化查询
4. 如果涉及路径规划，请使用PgRouting函数

请直接返回有效的SQL查询语句。
"""
            return enhanced_query
        else:
            return query
    
    def _postprocess_result(self, result: str, original_query: str) -> str:
        """
        后处理查询结果，确保空间查询的完整性
        
        Args:
            result: 原始结果
            original_query: 原始查询
            
        Returns:
            处理后的结果
        """
        # 检查结果是否包含有效的SQL
        if "SELECT" in result.upper() and "FROM" in result.upper():
            # 确保空间查询包含几何列
            if any(keyword in original_query.lower() for keyword in ['距离', '附近', '相交', '包含']):
                if "geom" not in result.upper() and "ST_" not in result.upper():
                    self.logger.warning("空间查询可能缺少几何列，尝试增强")
                    # 这里可以添加逻辑来增强查询以包含几何列
                    pass
            
            # 确保包含GeoJSON转换
            if "ST_AsGeoJSON" not in result.upper() and "GeoJSON" in original_query:
                self.logger.info("建议在查询中添加ST_AsGeoJSON以生成GeoJSON格式")
        
        return result
    
    def execute_spatial_query(self, query: str, return_geojson: bool = True) -> Dict[str, Any]:
        """
        执行空间查询并返回结构化结果
        
        Args:
            query: SQL查询语句
            return_geojson: 是否返回GeoJSON格式
            
        Returns:
            结构化查询结果
        """
        try:
            # 执行查询
            result = self.connector.execute_query(query)
            
            # 如果要求返回GeoJSON，但查询中没有包含ST_AsGeoJSON
            if return_geojson and "ST_AsGeoJSON" not in query.upper():
                self.logger.warning("查询可能未包含GeoJSON转换，建议使用ST_AsGeoJSON")
            
            return {
                "status": "success",
                "query": query,
                "result": result,
                "geojson_available": "ST_AsGeoJSON" in query.upper()
            }
        except Exception as e:
            self.logger.error(f"执行空间查询失败: {e}")
            return {
                "status": "error",
                "query": query,
                "error": str(e)
            }
    
    def get_spatial_tables_info(self) -> Dict[str, Any]:
        """
        获取空间表信息
        
        Returns:
            空间表信息字典
        """
        try:
            # 查询包含几何列的表
            spatial_tables_query = """
            SELECT 
                f_table_name as table_name,
                f_geometry_column as geometry_column,
                type as geometry_type,
                srid,
                coord_dimension
            FROM geometry_columns
            WHERE f_table_schema = 'public'
            ORDER BY f_table_name;
            """
            
            result = self.connector.execute_query(spatial_tables_query)
            
            return {
                "status": "success",
                "spatial_tables": result,
                "count": len(result) if isinstance(result, list) else 0
            }
        except Exception as e:
            self.logger.error(f"获取空间表信息失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def analyze_spatial_query(self, query: str) -> Dict[str, Any]:
        """
        分析空间查询的优化建议
        
        Args:
            query: SQL查询语句
            
        Returns:
            分析结果
        """
        analysis = {
            "has_spatial_functions": False,
            "spatial_functions_used": [],
            "suggestions": [],
            "optimization_tips": []
        }
        
        # 检查使用的空间函数
        spatial_functions = [
            "ST_", "pgr_", "TopoGeo_", "ST_AsGeoJSON", "ST_Transform",
            "ST_Intersects", "ST_Contains", "ST_Within", "ST_Distance",
            "ST_Buffer", "ST_Union", "ST_Intersection"
        ]
        
        for func in spatial_functions:
            if func in query.upper():
                analysis["has_spatial_functions"] = True
                analysis["spatial_functions_used"].append(func)
        
        # 提供优化建议
        if analysis["has_spatial_functions"]:
            if "ST_DWithin" not in query.upper() and ("ST_Distance" in query.upper() or "距离" in query):
                analysis["suggestions"].append("考虑使用ST_DWithin替代ST_Distance进行距离过滤，性能更好")
            
            if "geom" in query.upper() and "INDEX" not in query.upper():
                analysis["optimization_tips"].append("确保几何列上有空间索引（GIST索引）")
            
            if "ST_Transform" in query.upper():
                analysis["optimization_tips"].append("考虑在应用层进行坐标转换，而不是在数据库层")
        
        return analysis
    
    def close(self):
        """清理资源"""
        if hasattr(self, 'connector'):
            self.connector.close()


# 使用示例
if __name__ == "__main__":
    # 创建空间查询代理
    spatial_agent = SpatialSQLQueryAgent()
    
    try:
        # 获取空间表信息
        tables_info = spatial_agent.get_spatial_tables_info()
        print("空间表信息:", tables_info)
        
        # 示例空间查询
        test_queries = [
            "查找距离某个点5公里内的所有建筑",
            "计算从A点到B点的最短路径",
            "查找与某个多边形相交的所有道路"
        ]
        
        for query in test_queries:
            print(f"\n查询: {query}")
            result = spatial_agent.run(query)
            print(f"结果: {result}")
            
            # 分析查询
            analysis = spatial_agent.analyze_spatial_query(result)
            print(f"分析: {analysis}")
    
    finally:
        spatial_agent.close()
