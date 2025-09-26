import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
import fastapi
import uvicorn
from sql_query_agent import SQLQueryAgent  # pyright: ignore[reportMissingImports]
from spatial_sql_prompt import SQL_AGENT_SPATIAL_PROMPT, SPATIAL_SYSTEM_PROMPT_SIMPLE, SpatialSQLQueryAgent
from spatial_sql_agent import SpatialSQLQueryAgent as EnhancedSpatialSQLQueryAgent
from geojson_utils import GeoJSONGenerator
from sql_connector import SQLConnector  # pyright: ignore[reportMissingImports]
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量
sql_query_agent: Optional[EnhancedSpatialSQLQueryAgent] = None
agent_initialized = False

@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    """
    应用生命周期管理
    """
    # 启动时初始化
    logger.info("Starting SQL Query API")
    initialize_agent()
    
    yield
    
    # 关闭时清理资源
    logger.info("Shutting down SQL Query API")
    if sql_query_agent is not None:
        sql_query_agent.close()

# 创建FastAPI应用
app = fastapi.FastAPI(
    title="SQL Query API",
    description="自然语言SQL查询API服务",
    version="1.0.0",
    lifespan=lifespan
)

# 常量定义
MAX_QUERY_LENGTH = 500
ALLOWED_SPECIAL_CHARS = " .,?!@#$%^&*()-_=+[]{}|;:'\"<>/\\"

def initialize_agent() -> bool:
    """
    初始化SQL查询代理
    
    Returns:
        bool: 初始化是否成功
    """
    global sql_query_agent, agent_initialized
    
    if agent_initialized:
        return sql_query_agent is not None
    
    try:
        logger.info("Initializing Enhanced Spatial SQL Query Agent...")
        
        # 直接使用EnhancedSpatialSQLQueryAgent
        sql_query_agent = EnhancedSpatialSQLQueryAgent()
        logger.info("使用EnhancedSpatialSQLQueryAgent初始化SQL查询代理")
        
        agent_initialized = True
        logger.info("Enhanced Spatial SQL Query Agent initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Enhanced Spatial SQL Query Agent: {str(e)}")
        sql_query_agent = None
        agent_initialized = False
        return False

@app.get("/", summary="健康检查")
async def health_check() -> Dict[str, str]:
    """
    健康检查端点，用于验证服务是否正常运行
    """
    agent_status = "initialized" if agent_initialized and sql_query_agent else "not_initialized"
    return {
        "status": "healthy", 
        "message": "SQL Query API is running",
        "agent_status": agent_status
    }

@app.get("/query/{query_text}", summary="执行SQL查询")
async def execute_query(query_text: str) -> Dict[str, Any]:
    """
    执行自然语言SQL查询
    
    Args:
        query_text: 自然语言查询文本
        
    Returns:
        查询结果或错误信息
    """
    # 输入验证
    validation_error = validate_query_input(query_text)
    if validation_error:
        logger.warning(f"Invalid query input: {query_text}")
        return {"error": validation_error, "status": "error"}
    
    # 检查并初始化代理
    if not agent_initialized or sql_query_agent is None:
        if not initialize_agent():
            logger.error("SQL Query Agent is not available")
            return {
                "error": "SQL查询代理未初始化，请检查API密钥配置",
                "status": "error"
            }
    
    try:
        logger.info(f"Processing query: {query_text}")
        result = sql_query_agent.run(query_text)
        
        # 确保返回格式一致
        if isinstance(result, str):
            return {"result": result, "status": "success"}
        else:
            return {"result": str(result), "status": "success"}
            
    except Exception as e:
        logger.error(f"Error processing query '{query_text}': {str(e)}")
        return {
            "error": "处理查询时发生错误", 
            "details": str(e),
            "status": "error"
        }

def validate_query_input(query: str) -> str:
    """
    验证查询输入
    
    Args:
        query: 查询字符串
        
    Returns:
        错误消息，如果验证通过则返回空字符串
    """
    if not query or not query.strip():
        return "查询不能为空"
    
    if len(query) > MAX_QUERY_LENGTH:
        return f"查询长度不能超过{MAX_QUERY_LENGTH}个字符"
    
    # 检查是否包含危险字符（基本的安全检查）
    dangerous_patterns = [";", "--", "/*", "*/", "xp_", "sp_"]
    for pattern in dangerous_patterns:
        if pattern in query.lower():
            return "查询包含潜在危险字符"
    
    # 允许字母、数字、空格和常见标点符号
    cleaned_query = ''.join(c for c in query if c.isalnum() or c in ALLOWED_SPECIAL_CHARS)
    if len(cleaned_query) < len(query) * 0.8:  # 如果过滤掉太多字符，可能有问题
        return "查询包含过多无效字符"
    
    return ""

def natural_language_to_geojson(query_text: str, limit: int = 1000) -> Dict[str, Any]:
    """
    将自然语言查询转换为GeoJSON结果
    
    Args:
        query_text: 自然语言查询文本
        limit: 限制返回的记录数
        
    Returns:
        GeoJSON格式的查询结果
    """
    try:
        # 检查并初始化代理
        if not agent_initialized or sql_query_agent is None:
            if not initialize_agent():
                raise Exception("SQL查询代理未初始化")
        
        logger.info(f"处理自然语言查询: {query_text}")
        
        # 构建包含几何查询提示的自然语言查询
        enhanced_query = f"""{query_text}。请生成一个SQL查询，该查询应该：
1. 包含几何列(geom)
2. 使用ST_AsGeoJSON(ST_Transform(geom, 4326))将几何数据转换为WGS84坐标系并转换为GeoJSON格式
3. 返回的结果应该可以直接用于生成GeoJSON FeatureCollection

请直接返回SQL查询语句，不要添加解释。"""
        
        # 使用SQL查询代理生成SQL
        sql_result = sql_query_agent.run(enhanced_query)
        
        # 提取SQL查询语句（假设代理返回包含SQL的字符串）
        sql_query = extract_sql_from_result(sql_result)
        
        if not sql_query:
            raise Exception("无法从代理响应中提取有效的SQL查询")
        
        logger.info(f"生成的SQL查询: {sql_query}")
        
        # 使用SQL连接器执行查询
        connector = SQLConnector()
        
        # 检查查询是否包含几何列
        if "geom" not in sql_query.lower():
            # 如果查询不包含几何列，尝试修改查询以包含几何数据
            sql_query = enhance_sql_with_geometry(sql_query)
        
        # 使用GeoJSON生成器转换结果
        connection_string = "postgresql://sagasama:cznb6666@localhost:5432/WGP_db"
        generator = GeoJSONGenerator(connection_string)
        
        # 直接返回所有几何类型的GeoJSON数据
        geojson_data = generator.query_to_geojson(sql_query)
        
        return {
            "status": "success",
            "original_query": query_text,
            "generated_sql": sql_query,
            "feature_count": len(geojson_data.get("features", [])),
            "geojson": geojson_data
        }
        
    except Exception as e:
        logger.error(f"自然语言到GeoJSON转换失败: {str(e)}")
        return {
            "status": "error",
            "error": f"处理查询失败: {str(e)}",
            "original_query": query_text
        }

def extract_sql_from_result(result: str) -> List[str]:
    """
    从SQL查询代理的结果中提取SQL查询语句
    
    Args:
        result: 代理返回的结果字符串
        
    Returns:
        提取的SQL查询语句列表（包含所有执行过的SQL）
    """
    logger.info(f"开始提取SQL查询，响应长度: {len(result)}")
    
    sql_queries = []
    
    # 1. 提取所有Action Input中的SQL查询（包括中间查询）
    if "Action Input:" in result:
        # 查找所有Action Input
        action_inputs = []
        start_index = 0
        while True:
            action_start = result.find("Action Input:", start_index)
            if action_start == -1:
                break
            action_start += len("Action Input:")
            # 查找下一个Action或Final Answer或结束
            next_action = result.find("Action:", action_start)
            final_answer = result.find("Final Answer:", action_start)
            end_index = min(next_action, final_answer) if next_action > 0 and final_answer > 0 else max(next_action, final_answer)
            if end_index == -1:
                end_index = len(result)
            
            action_input = result[action_start:end_index].strip()
            action_inputs.append(action_input)
            start_index = end_index
        
        # 检查每个Action Input是否是有效的SQL
        for action_input in action_inputs:
            # 清理可能的引号和换行符
            cleaned_input = action_input.strip().strip('"').strip("'").strip()
            if is_valid_sql(cleaned_input):
                logger.info(f"从Action Input中提取到SQL: {cleaned_input[:100]}...")
                sql_queries.append(cleaned_input)
    
    # 2. 提取所有SQL代码块（包括中间查询）
    if "```sql" in result:
        start_index = result.find("```sql") + 6
        while start_index > 5:  # 可能有多个代码块
            end_index = result.find("```", start_index)
            if end_index > start_index:
                sql_content = result[start_index:end_index].strip()
                if is_valid_sql(sql_content):
                    logger.info(f"从代码块中提取到SQL: {sql_content[:100]}...")
                    sql_queries.append(sql_content)
                # 查找下一个代码块
                start_index = result.find("```sql", end_index)
                if start_index == -1:
                    break
                start_index += 6
            else:
                break
    
    # 3. 提取所有直接的SQL查询模式（包括中间查询）
    sql_patterns = [
        r"SELECT\s+.*?\s+FROM\s+.*?(?:\s+WHERE\s+.*?)?(?:\s+LIMIT\s+\d+)?",
        r"SELECT\s+.*?\s+FROM\s+.*",
        r"CREATE\s+TABLE\s+.*",
        r"INSERT\s+INTO\s+.*",
        r"UPDATE\s+.*",
        r"DELETE\s+FROM\s+.*"
    ]
    
    import re
    for pattern in sql_patterns:
        matches = re.findall(pattern, result, re.IGNORECASE | re.DOTALL)
        for match in matches:
            if is_valid_sql(match):
                logger.info(f"从正则匹配中提取到SQL: {match[:100]}...")
                sql_queries.append(match.strip())
    
    # 4. 提取所有执行的SQL查询（从日志中）
    # 查找类似 "Action: sql_db_query" 后面的查询
    sql_query_pattern = r"Action:\s+sql_db_query\s+Action Input:\s+([^\n]+)"
    matches = re.findall(sql_query_pattern, result, re.IGNORECASE | re.DOTALL)
    for match in matches:
        cleaned_match = match.strip().strip('"').strip("'").strip()
        if is_valid_sql(cleaned_match):
            logger.info(f"从sql_db_query中提取到SQL: {cleaned_match[:100]}...")
            sql_queries.append(cleaned_match)
    
    # 5. 提取所有schema查询
    schema_pattern = r"Action:\s+sql_db_schema\s+Action Input:\s+([^\n]+)"
    matches = re.findall(schema_pattern, result, re.IGNORECASE | re.DOTALL)
    for match in matches:
        table_name = match.strip().strip('"').strip("'").strip()
        if table_name:
            schema_query = f"SELECT * FROM {table_name} LIMIT 1"
            logger.info(f"从schema查询生成SQL: {schema_query}")
            sql_queries.append(schema_query)
    
    # 6. 提取所有list tables查询
    list_tables_pattern = r"Action:\s+sql_db_list_tables\s+Action Input:\s*([^\n]*)"
    matches = re.findall(list_tables_pattern, result, re.IGNORECASE | re.DOTALL)
    if matches:
        list_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        logger.info(f"添加list tables查询: {list_query}")
        sql_queries.append(list_query)
    
    # 7. 过滤和清理SQL查询，只返回完整的查询
    if sql_queries:
        # 过滤掉不完整的查询
        complete_queries = []
        for query in sql_queries:
            # 检查查询是否完整（包含SELECT和FROM）
            if "SELECT" in query.upper() and "FROM" in query.upper():
                # 检查查询是否以分号结尾或包含完整的语句
                if not query.strip().endswith(';'):
                    query = query.strip() + ';'
                complete_queries.append(query)
        
        # 去重但保持顺序
        unique_queries = []
        seen = set()
        for query in complete_queries:
            # 标准化查询以便去重
            normalized_query = re.sub(r'\s+', ' ', query.strip().upper())
            if normalized_query not in seen and len(query.strip()) > 20:  # 确保查询有足够长度
                seen.add(normalized_query)
                unique_queries.append(query)
        
        logger.info(f"提取到{len(unique_queries)}个完整的SQL查询")
        return unique_queries
    
    # 8. 如果所有方法都失败，根据查询意图生成一个默认查询
    logger.warning(f"无法从代理响应中提取有效的SQL查询，将根据查询意图生成默认查询")
    
    # 分析查询意图并生成相应的SQL
    if "交通" in result or "transport" in result.lower():
        return ["SELECT gid, osm_id, name, highway, barrier, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry FROM whupoi WHERE highway IS NOT NULL OR barrier IS NOT NULL LIMIT 10"]
    elif "点" in result or "point" in result.lower():
        return ["SELECT gid, osm_id, name, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry FROM whupoi WHERE geom IS NOT NULL LIMIT 10"]
    else:
        return ["SELECT gid, osm_id, name, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry FROM whupoi LIMIT 10"]

def extract_thought_chain(result: str) -> List[Dict[str, str]]:
    """
    从代理结果中提取思维链（Thought Chain）
    
    Args:
        result: 代理返回的结果字符串
        
    Returns:
        思维链列表，包含thought、action、action_input等信息
    """
    # 首先尝试使用新的解析器
    try:
        from parsing_fix import LLMResponseParser
        parser = LLMResponseParser()
        parsed_result = parser.parse_llm_response(result)
        
        if parsed_result["status"] == "success" and "thought_chain" in parsed_result:
            logger.info(f"使用新解析器提取到{len(parsed_result['thought_chain'])}个思维链步骤")
            return parsed_result["thought_chain"]
    except Exception as e:
        logger.warning(f"使用新解析器失败，回退到原有逻辑: {e}")
    
    # 如果新解析器失败，回退到原来的逻辑
    thought_chain = []
    
    # 使用正则表达式提取Thought、Action、Action Input、Final Answer等
    thought_pattern = r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)"
    action_pattern = r"Action:\s*(\w+)(?:\s+Action Input:\s*(.*?))?(?=Thought:|Final Answer:|$)"
    final_answer_pattern = r"Final Answer:\s*(.*?)(?=Thought:|Action:|$)"
    
    import re
    
    # 提取Thoughts
    thought_matches = re.findall(thought_pattern, result, re.DOTALL)
    for i, thought in enumerate(thought_matches):
        thought_chain.append({
            "step": i + 1,
            "type": "thought",
            "content": thought.strip(),
            "timestamp": f"step_{i+1}"
        })
    
    # 提取Actions
    action_matches = re.findall(action_pattern, result, re.DOTALL)
    for i, (action, action_input) in enumerate(action_matches):
        thought_chain.append({
            "step": len(thought_chain) + 1,
            "type": "action",
            "action": action.strip(),
            "action_input": action_input.strip() if action_input else "",
            "timestamp": f"step_{len(thought_chain)+1}"
        })
    
    # 提取Final Answer
    final_answer_matches = re.findall(final_answer_pattern, result, re.DOTALL)
    if final_answer_matches:
        thought_chain.append({
            "step": len(thought_chain) + 1,
            "type": "final_answer",
            "content": final_answer_matches[0].strip(),
            "timestamp": "final"
        })
    
    # 如果没有找到标准的思维链格式，尝试从整个结果中提取关键信息
    if not thought_chain:
        # 查找所有包含"Thought"、"Action"、"Final Answer"的行
        lines = result.split('\n')
        current_step = 1
        for line in lines:
            line = line.strip()
            if line.startswith('Thought:'):
                thought_chain.append({
                    "step": current_step,
                    "type": "thought",
                    "content": line.replace('Thought:', '').strip(),
                    "timestamp": f"step_{current_step}"
                })
                current_step += 1
            elif line.startswith('Action:'):
                action_parts = line.replace('Action:', '').strip().split('Action Input:')
                action = action_parts[0].strip()
                action_input = action_parts[1].strip() if len(action_parts) > 1 else ""
                thought_chain.append({
                    "step": current_step,
                    "type": "action",
                    "action": action,
                    "action_input": action_input,
                    "timestamp": f"step_{current_step}"
                })
                current_step += 1
            elif line.startswith('Final Answer:'):
                thought_chain.append({
                    "step": current_step,
                    "type": "final_answer",
                    "content": line.replace('Final Answer:', '').strip(),
                    "timestamp": "final"
                })
                current_step += 1
    
    # 如果仍然没有找到思维链，返回整个结果作为单个thought
    if not thought_chain:
        thought_chain.append({
            "step": 1,
            "type": "thought",
            "content": result[:500] + "..." if len(result) > 500 else result,
            "timestamp": "single_step"
        })
    
    logger.info(f"使用原有逻辑提取到{len(thought_chain)}个思维链步骤")
    return thought_chain

def is_valid_sql(sql: str) -> bool:
    """
    简单验证SQL语句的有效性
    
    Args:
        sql: SQL语句
        
    Returns:
        是否是有效的SQL
    """
    # 基本验证：包含SELECT关键字
    if "SELECT" not in sql.upper() and "select" not in sql:
        return False
    
    # 检查是否包含危险操作
    dangerous_operations = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER"]
    for operation in dangerous_operations:
        if operation in sql.upper():
            return False
    
    return True

def enhance_sql_with_geometry(sql_query: str) -> str:
    """
    增强SQL查询以包含几何数据
    
    Args:
        sql_query: 原始SQL查询
        
    Returns:
        增强后的SQL查询
    """
    # 简单的增强逻辑：在SELECT子句中添加geom列
    # 这需要更复杂的逻辑来识别正确的表和几何列
    # 暂时返回原始查询
    
    # 如果查询不包含FROM子句，无法增强
    if "FROM" not in sql_query.upper():
        return sql_query
    
    # 尝试在SELECT子句后添加geom
    select_index = sql_query.upper().find("SELECT")
    if select_index >= 0:
        # 找到SELECT后的第一个空格
        space_after_select = sql_query.find(" ", select_index + 6)
        if space_after_select > 0:
            # 在SELECT后插入geom
            enhanced_sql = (sql_query[:space_after_select + 1] + 
                           "geom, " + 
                           sql_query[space_after_select + 1:])
            return enhanced_sql
    
    return sql_query

# GeoJSON相关端点
@app.get("/geojson/tables", summary="获取空间表列表")
async def get_spatial_tables() -> Dict[str, Any]:
    """
    获取数据库中包含空间数据的表列表
    """
    try:
        connection_string = "postgresql://sagasama:cznb6666@localhost:5432/WGP_db"
        generator = GeoJSONGenerator(connection_string)
        tables = generator.get_spatial_tables()
        
        return {
            "status": "success",
            "tables": tables,
            "count": len(tables)
        }
    except Exception as e:
        logger.error(f"获取空间表列表失败: {str(e)}")
        return {
            "error": "获取空间表列表失败",
            "details": str(e),
            "status": "error"
        }

@app.get("/geojson/table/{table_name}", summary="获取表的GeoJSON数据")
async def get_table_geojson(
    table_name: str, 
    geometry_column: str = "geom",
    where_clause: str = "",
    limit: int = 1000
) -> Dict[str, Any]:
    """
    获取指定表的GeoJSON数据
    
    Args:
        table_name: 表名
        geometry_column: 几何列名（默认为geom）
        where_clause: WHERE条件子句
        limit: 限制返回的记录数
    """
    try:
        connection_string = "postgresql://sagasama:cznb6666@localhost:5432/WGP_db"
        generator = GeoJSONGenerator(connection_string)
        
        geojson_data = generator.table_to_geojson(
            table_name, 
            geometry_column, 
            where_clause, 
            limit
        )
        
        return {
            "status": "success",
            "table": table_name,
            "geometry_column": geometry_column,
            "feature_count": len(geojson_data.get("features", [])),
            "geojson": geojson_data
        }
    except Exception as e:
        logger.error(f"获取表{table_name}的GeoJSON数据失败: {str(e)}")
        return {
            "error": f"获取表{table_name}的GeoJSON数据失败",
            "details": str(e),
            "status": "error"
        }

@app.get("/geojson/table/{table_name}/{geometry_type}", summary="按几何类型获取GeoJSON数据")
async def get_geojson_by_geometry_type(
    table_name: str,
    geometry_type: str,
    geometry_column: str = "geom",
    where_clause: str = "",
    limit: int = 1000
) -> Dict[str, Any]:
    """
    按几何类型获取指定表的GeoJSON数据
    
    Args:
        table_name: 表名
        geometry_type: 几何类型（point/line/polygon等）
        geometry_column: 几何列名（默认为geom）
        where_clause: WHERE条件子句
        limit: 限制返回的记录数
    """
    try:
        connection_string = "postgresql://sagasama:cznb6666@localhost:5432/WGP_db"
        generator = GeoJSONGenerator(connection_string)
        
        # 将几何类型转换为大写
        geometry_type_upper = geometry_type.upper()
        
        geojson_data = generator.get_features_by_geometry_type(
            table_name, 
            geometry_column, 
            geometry_type_upper, 
            where_clause, 
            limit
        )
        
        return {
            "status": "success",
            "table": table_name,
            "geometry_type": geometry_type,
            "geometry_column": geometry_column,
            "feature_count": len(geojson_data.get("features", [])),
            "geojson": geojson_data
        }
    except Exception as e:
        logger.error(f"获取表{table_name}的{geometry_type}类型数据失败: {str(e)}")
        return {
            "error": f"获取表{table_name}的{geometry_type}类型数据失败",
            "details": str(e),
            "status": "error"
        }

@app.get("/geojson/types/{table_name}", summary="获取表的几何类型统计")
async def get_geometry_types(table_name: str, geometry_column: str = "geom") -> Dict[str, Any]:
    """
    获取指定表中所有几何类型的统计信息
    
    Args:
        table_name: 表名
        geometry_column: 几何列名（默认为geom）
    """
    try:
        connection_string = "postgresql://sagasama:cznb6666@localhost:5432/WGP_db"
        generator = GeoJSONGenerator(connection_string)
        
        types_info = generator.get_all_geometry_types(table_name, geometry_column)
        
        return {
            "status": "success",
            "table": table_name,
            "geometry_column": geometry_column,
            "geometry_types": types_info
        }
    except Exception as e:
        logger.error(f"获取表{table_name}的几何类型统计失败: {str(e)}")
        return {
            "error": f"获取表{table_name}的几何类型统计失败",
            "details": str(e),
            "status": "error"
        }

@app.get("/nlq/{query_text}", summary="自然语言查询转GeoJSON")
async def natural_language_query_to_geojson(
    query_text: str, 
    limit: int = 1000
) -> Dict[str, Any]:
    """
    将自然语言查询转换为GeoJSON结果
    
    Args:
        query_text: 自然语言查询文本
        limit: 限制返回的记录数
        
    Returns:
        GeoJSON格式的查询结果
    """
    # 输入验证
    validation_error = validate_query_input(query_text)
    if validation_error:
        logger.warning(f"Invalid query input: {query_text}")
        return {"error": validation_error, "status": "error"}
    
    # 验证limit参数
    if limit < 1 or limit > 10000:
        return {
            "error": "limit参数必须在1到10000之间",
            "status": "error"
        }
    
    # 调用自然语言到GeoJSON转换函数
    return natural_language_to_geojson(query_text, limit)

@app.post("/nlq", summary="自然语言查询转GeoJSON（POST方式）")
async def natural_language_query_to_geojson_post(
    query_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    通过POST方式将自然语言查询转换为GeoJSON结果
    
    Args:
        query_data: 包含查询参数的JSON对象
            - query: 自然语言查询文本（必需）
            - limit: 限制返回的记录数（默认为1000）
            
    Returns:
        GeoJSON格式的查询结果
    """
    try:
        # 提取参数
        query_text = query_data.get("query", "")
        limit = query_data.get("limit", 1000)
        
        # 验证必需参数
        if not query_text:
            return {
                "error": "查询文本不能为空",
                "status": "error"
            }
        
        # 调用GET端点相同的验证逻辑
        validation_error = validate_query_input(query_text)
        if validation_error:
            return {"error": validation_error, "status": "error"}
        
        # 验证limit参数
        if limit < 1 or limit > 10000:
            return {
                "error": "limit参数必须在1到10000之间",
                "status": "error"
            }
        
        # 调用自然语言到GeoJSON转换函数
        return natural_language_to_geojson(query_text, limit)
        
    except Exception as e:
        logger.error(f"POST方式处理自然语言查询失败: {str(e)}")
        return {
            "error": f"处理查询失败: {str(e)}",
            "status": "error"
        }

# 新增空间查询端点
@app.get("/spatial/health", summary="空间查询健康检查")
async def spatial_health_check() -> Dict[str, Any]:
    """空间查询健康检查端点"""
    try:
        connector = SQLConnector()
        spatial_info = connector.get_database_spatial_info()
        connector.close()
        
        return {
            "status": "healthy",
            "message": "空间查询功能正常",
            "spatial_info": spatial_info
        }
    except Exception as e:
        logger.error(f"空间查询健康检查失败: {str(e)}")
        return {
            "status": "error",
            "error": f"空间查询健康检查失败: {str(e)}"
        }

@app.get("/spatial/tables", summary="获取空间表详细信息")
async def get_spatial_tables_detailed() -> Dict[str, Any]:
    """获取空间表的详细信息，包括索引信息"""
    try:
        connector = SQLConnector()
        spatial_tables = connector.get_spatial_tables()
        
        # 为每个表添加索引信息
        for table in spatial_tables:
            table_name = table["table_name"]
            indexes = connector.get_spatial_indexes(table_name)
            table["spatial_indexes"] = indexes
        
        connector.close()
        
        return {
            "status": "success",
            "spatial_tables": spatial_tables,
            "count": len(spatial_tables)
        }
    except Exception as e:
        logger.error(f"获取空间表详细信息失败: {str(e)}")
        return {
            "error": "获取空间表详细信息失败",
            "details": str(e),
            "status": "error"
        }

@app.get("/spatial/query/{query_text}", summary="执行空间SQL查询")
async def execute_spatial_query(query_text: str) -> Dict[str, Any]:
    """执行空间SQL查询"""
    # 输入验证
    validation_error = validate_query_input(query_text)
    if validation_error:
        logger.warning(f"Invalid spatial query input: {query_text}")
        return {"error": validation_error, "status": "error"}
    
    try:
        # 初始化空间查询代理
        spatial_agent = EnhancedSpatialSQLQueryAgent()
        
        logger.info(f"Processing spatial query: {query_text}")
        result = spatial_agent.run(query_text)
        
        # 分析查询优化建议
        analysis = spatial_agent.analyze_spatial_query(result)
        
        # 如果结果是SQL查询，尝试执行并返回结果
        if "SELECT" in result.upper() and "FROM" in result.upper():
            try:
                query_result = spatial_agent.execute_spatial_query(result)
                return {
                    "status": "success",
                    "query": result,
                    "analysis": analysis,
                    "result": query_result
                }
            except Exception as e:
                logger.warning(f"无法执行生成的SQL查询: {e}")
                return {
                    "status": "success",
                    "query": result,
                    "analysis": analysis,
                    "warning": f"生成的SQL查询无法执行: {str(e)}"
                }
        else:
            return {
                "status": "success",
                "result": result,
                "analysis": analysis
            }
            
    except Exception as e:
        logger.error(f"Error processing spatial query '{query_text}': {str(e)}")
        return {
            "error": "处理空间查询时发生错误", 
            "details": str(e),
            "status": "error"
        }

@app.post("/spatial/query", summary="执行空间SQL查询（POST方式）")
async def execute_spatial_query_post(
    query_data: Dict[str, Any]
) -> Dict[str, Any]:
    """通过POST方式执行空间SQL查询"""
    try:
        # 提取参数
        query_text = query_data.get("query", "")
        execute_sql = query_data.get("execute_sql", True)
        
        # 验证必需参数
        if not query_text:
            return {
                "error": "查询文本不能为空",
                "status": "error"
            }
        
        # 输入验证
        validation_error = validate_query_input(query_text)
        if validation_error:
            return {"error": validation_error, "status": "error"}
        
        # 初始化空间查询代理
        spatial_agent = EnhancedSpatialSQLQueryAgent()
        
        logger.info(f"Processing spatial query (POST): {query_text}")
        result = spatial_agent.run(query_text)
        
        # 分析查询优化建议
        analysis = spatial_agent.analyze_spatial_query(result)
        
        response_data = {
            "status": "success",
            "query": result,
            "analysis": analysis
        }
        
        # 如果要求执行SQL查询并且结果是有效的SQL
        if execute_sql and "SELECT" in result.upper() and "FROM" in result.upper():
            try:
                query_result = spatial_agent.execute_spatial_query(result)
                response_data["result"] = query_result
            except Exception as e:
                logger.warning(f"无法执行生成的SQL查询: {e}")
                response_data["warning"] = f"生成的SQL查询无法执行: {str(e)}"
        else:
            response_data["result"] = result
        
        spatial_agent.close()
        return response_data
        
    except Exception as e:
        logger.error(f"POST方式处理空间查询失败: {str(e)}")
        return {
            "error": f"处理空间查询失败: {str(e)}",
            "status": "error"
        }

@app.get("/spatial/functions", summary="获取可用空间函数列表")
async def get_spatial_functions() -> Dict[str, Any]:
    """获取数据库中可用的空间函数列表"""
    try:
        connector = SQLConnector()
        function_availability = connector.check_spatial_function_availability()
        connector.close()
        
        return {
            "status": "success",
            "spatial_functions": function_availability
        }
    except Exception as e:
        logger.error(f"获取空间函数列表失败: {str(e)}")
        return {
            "error": "获取空间函数列表失败",
            "details": str(e),
            "status": "error"
        }

@app.get("/spatial/examples", summary="获取空间查询示例")
async def get_spatial_query_examples() -> Dict[str, Any]:
    """获取空间查询示例"""
    examples = {
        "distance_queries": [
            {
                "description": "查找距离某个点5公里内的所有建筑",
                "query": "查找距离经度116.4、纬度39.9的点5公里内的所有建筑",
                "expected_sql": "SELECT * FROM buildings WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint(116.4, 39.9), 4326), 5000)"
            },
            {
                "description": "计算两点之间的距离",
                "query": "计算A点(116.4, 39.9)和B点(116.5, 39.8)之间的距离",
                "expected_sql": "SELECT ST_Distance(ST_SetSRID(ST_MakePoint(116.4, 39.9), 4326), ST_SetSRID(ST_MakePoint(116.5, 39.8), 4326)) as distance"
            }
        ],
        "spatial_relationship_queries": [
            {
                "description": "查找与某个多边形相交的所有道路",
                "query": "查找与某个多边形相交的所有道路",
                "expected_sql": "SELECT * FROM roads WHERE ST_Intersects(geom, ST_GeomFromText('POLYGON((...))'))"
            },
            {
                "description": "查找包含在某个区域内的所有点",
                "query": "查找包含在某个区域内的所有点",
                "expected_sql": "SELECT * FROM points WHERE ST_Within(geom, ST_GeomFromText('POLYGON((...))'))"
            }
        ],
        "routing_queries": [
            {
                "description": "计算从A点到B点的最短路径",
                "query": "计算从起点到终点的最短路径",
                "expected_sql": "SELECT * FROM pgr_dijkstra('SELECT id, source, target, cost FROM road_network', start_node_id, end_node_id)"
            },
            {
                "description": "查找距离某个点最近的设施",
                "query": "查找距离某个点最近的医院",
                "expected_sql": "SELECT * FROM hospitals ORDER BY ST_Distance(geom, ST_SetSRID(ST_MakePoint(116.4, 39.9), 4326)) LIMIT 1"
            }
        ],
        "topology_queries": [
            {
                "description": "分析两个多边形的拓扑关系",
                "query": "分析多边形A和多边形B的拓扑关系",
                "expected_sql": "SELECT ST_Relate(geom1, geom2) FROM polygons WHERE id IN (1, 2)"
            }
        ]
    }
    
    return {
        "status": "success",
        "examples": examples
    }

# 智能查询类型判断函数
def analyze_query_type(query_text: str) -> Dict[str, Any]:
    """
    分析查询类型，判断是否需要执行SQL查询、空间查询或数据总结
    
    Args:
        query_text: 自然语言查询文本
        
    Returns:
        查询类型分析结果
    """
    query_lower = query_text.lower()
    
    # 空间查询关键词
    spatial_keywords = [
        '距离', '附近', '周围', '范围内', '路径', '路线', '最短', '最近',
        '相交', '包含', '在内', '边界', '面积', '长度', '周长',
        '点', '线', '面', '多边形', '几何', '空间', '地理',
        'buffer', 'intersect', 'contain', 'within', 'distance',
        'route', 'path', 'shortest', 'nearest', 'proximity',
        'st_', 'geom', 'geometry', '坐标', '经纬度'
    ]
    
    # 数据总结关键词
    summary_keywords = [
        '总结', '统计', '汇总', '分析', '报告', '概况', '总数',
        '平均', '最大', '最小', '分布', '趋势', '比例',
        'summary', 'statistics', 'analyze', 'report', 'overview',
        'count', 'average', 'max', 'min', 'distribution'
    ]
    
    # SQL查询关键词
    sql_keywords = [
        '查询', '查找', '搜索', '获取', '显示', '列出',
        'select', 'find', 'search', 'get', 'show', 'list',
        'where', 'from', 'table', 'column'
    ]
    
    # 判断查询类型
    is_spatial = any(keyword in query_lower for keyword in spatial_keywords)
    is_summary = any(keyword in query_lower for keyword in summary_keywords)
    is_sql = any(keyword in query_lower for keyword in sql_keywords)
    
    # 优先级：空间查询 > 数据总结 > 普通SQL查询
    if is_spatial:
        query_type = "spatial"
        priority = 1
    elif is_summary:
        query_type = "summary"
        priority = 2
    elif is_sql:
        query_type = "sql"
        priority = 3
    else:
        query_type = "general"
        priority = 4
    
    return {
        "query_type": query_type,
        "priority": priority,
        "is_spatial": is_spatial,
        "is_summary": is_summary,
        "is_sql": is_sql,
        "spatial_keywords_found": [kw for kw in spatial_keywords if kw in query_lower],
        "summary_keywords_found": [kw for kw in summary_keywords if kw in query_lower],
        "sql_keywords_found": [kw for kw in sql_keywords if kw in query_lower]
    }

# 通用智能查询端点
@app.post("/agent/query", summary="智能代理查询")
async def intelligent_agent_query(query_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    智能代理查询接口，自动判断查询类型并返回标准化结果
    
    Args:
        query_data: 包含查询参数的JSON对象
            - question: 自然语言查询文本（必需）
            - chat_history: 聊天历史记录（可选）
            - execute_sql: 是否执行SQL查询（默认为True）
            - return_geojson: 是否返回GeoJSON格式（默认为True）
            
    Returns:
        标准化响应格式：{sql: (), geojson: (如有), question: {}, answer: {}}
    """
    try:
        # 提取参数
        question = query_data.get("question", "")
        chat_history = query_data.get("chat_history", [])
        execute_sql = query_data.get("execute_sql", True)
        return_geojson = query_data.get("return_geojson", True)
        
        # 验证必需参数
        if not question:
            return {
                "status": "error",
                "error": "查询问题不能为空",
                "question": {},
                "answer": {},
                "sql": None,
                "geojson": None
            }
        
        # 输入验证
        validation_error = validate_query_input(question)
        if validation_error:
            return {
                "status": "error",
                "error": validation_error,
                "question": {"text": question},
                "answer": {},
                "sql": None,
                "geojson": None
            }
        
        logger.info(f"处理智能代理查询: {question}")
        
        # 分析查询类型
        query_analysis = analyze_query_type(question)
        logger.info(f"查询类型分析: {query_analysis}")
        
        # 根据查询类型选择处理方式
        if query_analysis["query_type"] == "spatial":
            return await _handle_spatial_query(question, query_analysis, execute_sql, return_geojson)
        elif query_analysis["query_type"] == "summary":
            return await _handle_summary_query(question, query_analysis, execute_sql)
        else:
            return await _handle_general_query(question, query_analysis, execute_sql)
            
    except Exception as e:
        logger.error(f"智能代理查询处理失败: {str(e)}")
        return {
            "status": "error",
            "error": f"处理查询失败: {str(e)}",
            "question": {"text": question},
            "answer": {},
            "sql": None,
            "geojson": None
        }

async def _handle_spatial_query(question: str, query_analysis: Dict[str, Any], 
                               execute_sql: bool, return_geojson: bool) -> Dict[str, Any]:
    """处理空间查询"""
    try:
        # 检查并初始化代理
        if not agent_initialized or sql_query_agent is None:
            if not initialize_agent():
                raise Exception("SQL查询代理未初始化")
        
        # 执行空间查询并捕获完整思维链
        thought_chain_result = sql_query_agent.run_with_thought_chain(question)
        
        if thought_chain_result["status"] == "success":
            result = thought_chain_result["final_answer"]
            thought_chain = thought_chain_result["thought_chain"]
            step_count = thought_chain_result["step_count"]
            
            logger.info(f"捕获到{step_count}个思维链步骤")
            logger.info(f"最终答案长度: {len(result)}")
        else:
            # 如果思维链捕获失败，回退到原来的方法
            logger.warning("思维链捕获失败，使用回退方法")
            result = sql_query_agent.run(question)
            thought_chain = extract_thought_chain(result)
        
        # 提取SQL查询
        sql_queries = extract_sql_from_result(result)
        
        # 分析查询优化建议（SQLQueryAgent没有analyze_spatial_query方法）
        analysis = {
            "has_spatial_functions": any(func in result.upper() for func in ["ST_", "pgr_", "TopoGeo_"]),
            "spatial_functions_used": [func for func in ["ST_", "pgr_", "TopoGeo_"] if func in result.upper()],
            "suggestions": [],
            "optimization_tips": []
        }
        
        # 构建基础响应
        response = {
            "status": "success",
            "question": {
                "text": question,
                "type": "spatial",
                "analysis": query_analysis
            },
            "answer": {
                "text": result,
                "analysis": analysis,
                "thought_chain": thought_chain
            },
            "sql": sql_queries,
            "geojson": None
        }
        
        # 如果要求执行SQL查询并且有有效的SQL
        if execute_sql and sql_queries and len(sql_queries) > 0:
            # 使用第一个SQL查询执行
            sql_query = sql_queries[0]
            try:
                # 修复SQL查询中的表名问题
                # 如果查询使用了whupois表但实际数据在whupoi表中
                if "whupois" in sql_query.lower() and "whupoi" not in sql_query.lower():
                    # 尝试使用whupoi表
                    fixed_sql = sql_query.replace("whupois", "whupoi")
                    logger.info(f"修复SQL查询表名: {fixed_sql}")
                    sql_query = fixed_sql
                
                # 修复SQL查询中的SRID问题
                # 如果查询包含ST_Transform但几何数据没有SRID，需要修复
                if "ST_Transform" in sql_query.upper() and "SRID" not in sql_query.upper():
                    # 替换ST_Transform为ST_SetSRID
                    fixed_sql = sql_query.replace("ST_Transform(geom, 4326)", "ST_SetSRID(geom, 4326)")
                    logger.info(f"修复SQL查询SRID: {fixed_sql}")
                    sql_query = fixed_sql
                
                # 执行SQL查询
                connector = SQLConnector()
                query_result = connector.execute_query(sql_query)
                
                # 如果要求返回GeoJSON格式
                if return_geojson and "geom" in sql_query.lower():
                    try:
                        connection_string = "postgresql://sagasama:cznb6666@localhost:5432/WGP_db"
                        generator = GeoJSONGenerator(connection_string)
                        
                        # 使用修复后的SQL查询生成GeoJSON
                        geojson_data = generator.query_to_geojson(sql_query)
                        response["geojson"] = geojson_data
                        response["answer"]["feature_count"] = len(geojson_data.get("features", []))
                        
                        # 如果GeoJSON为空，尝试使用更简单的查询
                        if len(geojson_data.get("features", [])) == 0:
                            logger.info("GeoJSON为空，尝试使用简化查询")
                            
                            # 尝试1: 使用简单的几何查询
                            simple_sql = sql_query.replace("ST_AsGeoJSON(ST_Transform(geom, 4326))", "ST_AsGeoJSON(geom)")
                            simple_sql = simple_sql.replace("ST_AsGeoJSON(ST_SetSRID(geom, 4326))", "ST_AsGeoJSON(geom)")
                            try:
                                simple_geojson = generator.query_to_geojson(simple_sql)
                                if len(simple_geojson.get("features", [])) > 0:
                                    response["geojson"] = simple_geojson
                                    response["answer"]["feature_count"] = len(simple_geojson.get("features", []))
                                    logger.info(f"简化查询成功，获取到{len(simple_geojson.get('features', []))}个要素")
                            except Exception as simple_error:
                                logger.warning(f"简化查询失败: {simple_error}")
                            
                            # 尝试2: 使用基本的几何查询
                            if len(response.get("geojson", {}).get("features", [])) == 0:
                                logger.info("尝试基本几何查询")
                                basic_sql = "SELECT gid, name, ST_AsGeoJSON(geom) as geometry FROM whupoi WHERE name LIKE '%珞珈%' LIMIT 10"
                                try:
                                    basic_geojson = generator.query_to_geojson(basic_sql)
                                    if len(basic_geojson.get("features", [])) > 0:
                                        response["geojson"] = basic_geojson
                                        response["answer"]["feature_count"] = len(basic_geojson.get("features", []))
                                        logger.info(f"基本查询成功，获取到{len(basic_geojson.get('features', []))}个要素")
                                except Exception as basic_error:
                                    logger.warning(f"基本查询也失败: {basic_error}")
                        
                    except Exception as geojson_error:
                        logger.warning(f"生成GeoJSON失败: {geojson_error}")
                        response["answer"]["geojson_warning"] = f"生成GeoJSON失败: {str(geojson_error)}"
                
                response["answer"]["query_result"] = query_result
                connector.close()
                
            except Exception as sql_error:
                logger.warning(f"执行SQL查询失败: {sql_error}")
                response["answer"]["sql_warning"] = f"执行SQL查询失败: {str(sql_error)}"
        
        return response
        
    except Exception as e:
        logger.error(f"处理空间查询失败: {str(e)}")
        raise e

async def _handle_summary_query(question: str, query_analysis: Dict[str, Any], 
                               execute_sql: bool) -> Dict[str, Any]:
    """处理数据总结查询"""
    try:
        # 检查并初始化代理
        if not agent_initialized or sql_query_agent is None:
            if not initialize_agent():
                raise Exception("SQL查询代理未初始化")
        
        # 增强查询以包含总结提示
        enhanced_question = f"""
{question}

请生成一个SQL查询来总结和分析数据。查询应该：
1. 使用聚合函数（COUNT, SUM, AVG, MAX, MIN等）
2. 包含适当的分组（GROUP BY）
3. 提供有意义的统计信息
4. 如果可能，包含数据分布和趋势分析

请直接返回SQL查询语句和简要的分析说明。
"""
        
        # 执行查询
        result = sql_query_agent.run(enhanced_question)
        
        # 提取SQL查询
        sql_queries = extract_sql_from_result(result)
        
        # 提取思维链（Thought Chain）
        thought_chain = extract_thought_chain(result)
        
        # 构建响应
        response = {
            "status": "success",
            "question": {
                "text": question,
                "type": "summary",
                "analysis": query_analysis
            },
            "answer": {
                "text": result,
                "summary_analysis": "这是一个数据总结查询，提供了统计信息和分析",
                "thought_chain": thought_chain
            },
            "sql": sql_queries,
            "geojson": None
        }
        
        # 如果要求执行SQL查询并且有有效的SQL
        if execute_sql and sql_queries and len(sql_queries) > 0:
            # 使用第一个SQL查询执行
            sql_query = sql_queries[0]
            try:
                connector = SQLConnector()
                query_result = connector.execute_query(sql_query)
                connector.close()
                response["answer"]["summary_result"] = query_result
            except Exception as sql_error:
                logger.warning(f"执行总结SQL查询失败: {sql_error}")
                response["answer"]["sql_warning"] = f"执行SQL查询失败: {str(sql_error)}"
        
        return response
        
    except Exception as e:
        logger.error(f"处理总结查询失败: {str(e)}")
        raise e

async def _handle_general_query(question: str, query_analysis: Dict[str, Any], 
                               execute_sql: bool) -> Dict[str, Any]:
    """处理普通查询"""
    try:
        # 检查并初始化代理
        if not agent_initialized or sql_query_agent is None:
            if not initialize_agent():
                raise Exception("SQL查询代理未初始化")
        
        # 执行普通查询
        result = sql_query_agent.run(question)
        
        # 提取SQL查询
        sql_queries = extract_sql_from_result(result)
        
        # 提取思维链（Thought Chain）
        thought_chain = extract_thought_chain(result)
        
        # 构建响应
        response = {
            "status": "success",
            "question": {
                "text": question,
                "type": query_analysis["query_type"],
                "analysis": query_analysis
            },
            "answer": {
                "text": result,
                "thought_chain": thought_chain
            },
            "sql": sql_queries,
            "geojson": None
        }
        
        # 如果要求执行SQL查询并且有有效的SQL
        if execute_sql and sql_queries and len(sql_queries) > 0:
            # 使用第一个SQL查询执行
            sql_query = sql_queries[0]
            try:
                connector = SQLConnector()
                query_result = connector.execute_query(sql_query)
                connector.close()
                response["answer"]["query_result"] = query_result
            except Exception as sql_error:
                logger.warning(f"执行SQL查询失败: {sql_error}")
                response["answer"]["sql_warning"] = f"执行SQL查询失败: {str(sql_error)}"
        
        return response
        
    except Exception as e:
        logger.error(f"处理普通查询失败: {str(e)}")
        raise e

# GET方式的智能查询端点（简化版）
@app.get("/agent/query/{question}", summary="智能代理查询（GET方式）")
async def intelligent_agent_query_get(question: str) -> Dict[str, Any]:
    """
    GET方式的智能代理查询接口
    
    Args:
        question: 自然语言查询文本
        
    Returns:
        标准化响应格式
    """
    return await intelligent_agent_query({
        "question": question,
        "execute_sql": True,
        "return_geojson": True
    })

# 查询类型分析端点
@app.post("/agent/analyze", summary="分析查询类型")
async def analyze_query(query_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析查询类型和意图
    
    Args:
        query_data: 包含查询文本的JSON对象
            - question: 自然语言查询文本（必需）
            
    Returns:
        查询类型分析结果
    """
    question = query_data.get("question", "")
    
    # 验证必需参数
    if not question:
        return {
            "status": "error",
            "error": "查询问题不能为空"
        }
    
    # 分析查询类型
    query_analysis = analyze_query_type(question)
    
    return {
        "status": "success",
        "question": question,
        "analysis": query_analysis
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SQL Query API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8001, help="Port number")  # 改为8001避免冲突
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    uvicorn.run(
        app, 
        host=args.host, 
        port=args.port,
        log_level=args.log_level
    )
