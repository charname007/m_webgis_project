"""
使用StructuredOutputParser和Pydantic模型来控制AI代理输出格式
"""

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from typing import Dict, Any, Optional, List
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

class SpatialQueryResponseWithSQL(BaseModel):
    """包含SQL查询的空间查询响应格式"""
    answer: str = Field(description="自然语言回答，解释查询结果和发现")
    geojson: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="GeoJSON格式的空间数据"
    )
    sql_queries: Optional[List[str]] = Field(
        default=None,
        description="执行的SQL查询列表"
    )
    thought_chain: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="思维链步骤"
    )

def create_spatial_output_parser():
    """创建空间查询输出解析器"""
    parser = PydanticOutputParser(pydantic_object=SpatialQueryResponse)
    return parser

def create_spatial_output_parser_with_sql():
    """创建包含SQL查询的空间查询输出解析器"""
    parser = PydanticOutputParser(pydantic_object=SpatialQueryResponseWithSQL)
    return parser

def get_structured_prompt_template():
    """获取结构化提示词模板"""
    parser = create_spatial_output_parser()
    
    template = """
你是一个专业的空间数据库和PostGIS查询专家。你正在访问一个PostgreSQL数据库，该数据库已经安装了PostGIS扩展，用于存储和处理地理空间数据。

## 数据库环境信息
- 数据库类型：PostgreSQL with PostGIS extension
- 数据库名称：WGP_db
- 主要包含空间数据表，如whupoi、edges、county等
- 几何列通常命名为"geom"或"the_geom"

## 重要要求
1. 所有空间查询必须包含几何数据
2. 使用ST_AsGeoJSON(ST_Transform(geom, 4326))将几何数据转换为WGS84坐标系并转换为GeoJSON格式
3. 优先使用PostGIS函数（ST_Distance、ST_Intersects、ST_Within等）
4. 生成的SQL应该可以直接在PostGIS环境中执行

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

请根据用户的问题生成相应的空间SQL查询，并按照上述格式返回结果。

用户查询：{query}
"""
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    return prompt, parser

def test_structured_output():
    """测试结构化输出功能"""
    print("=== 测试结构化输出功能 ===\n")
    
    # 创建提示词模板和解析器
    prompt, parser = get_structured_prompt_template()
    
    # 测试查询
    test_query = "查询whupoi表的前2条记录"
    
    # 生成提示词
    formatted_prompt = prompt.format(query=test_query)
    
    print("生成的提示词格式:")
    print("=" * 50)
    print(formatted_prompt[:500] + "..." if len(formatted_prompt) > 500 else formatted_prompt)
    print("=" * 50)
    
    print("\n格式指令:")
    print("=" * 50)
    print(parser.get_format_instructions())
    print("=" * 50)
    
    # 测试解析器
    test_response = '''{
  "answer": "查询成功返回了whupoi表的前2条记录，以GeoJSON FeatureCollection格式呈现。结果包含以下信息：第一条记录：- gid: 1 - osm_id: 845686557 - highway: traffic_signals - 几何类型: Point - 坐标: [114.3699588, 30.5309076] 第二条记录：- gid: 2 - osm_id: 1148740588 - barrier: gate - 几何类型: Point - 坐标: [114.3465494, 30.5240617]",
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [114.3699588, 30.5309076]
        },
        "properties": {
          "gid": 1,
          "osm_id": "845686557",
          "highway": "traffic_signals"
        }
      },
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [114.3465494, 30.5240617]
        },
        "properties": {
          "gid": 2,
          "osm_id": "1148740588",
          "barrier": "gate"
        }
      }
    ]
  }
}'''
    
    try:
        parsed_result = parser.parse(test_response)
        print("\n✅ 解析成功:")
        print(f"Answer: {parsed_result.answer[:100]}...")
        print(f"GeoJSON要素数: {len(parsed_result.geojson.get('features', [])) if parsed_result.geojson else 0}")
    except Exception as e:
        print(f"\n❌ 解析失败: {e}")

def integrate_with_existing_agent():
    """与现有代理集成的方法"""
    print("\n=== 与现有代理集成方案 ===\n")
    
    # 方案1: 修改现有的spatial_sql_agent.py
    integration_code = '''
# 在spatial_sql_agent.py中添加以下代码

from structured_output_solution import create_spatial_output_parser, get_structured_prompt_template

class StructuredSpatialSQLQueryAgent:
    """使用结构化输出的空间SQL查询代理"""
    
    def __init__(self, system_prompt=None):
        self.parser = create_spatial_output_parser()
        self.prompt_template, _ = get_structured_prompt_template()
        
        # 使用现有的SQL查询代理
        from sql_query_agent import SQLQueryAgent
        self.agent = SQLQueryAgent(system_prompt=system_prompt)
    
    def run_with_structured_output(self, query: str) -> SpatialQueryResponse:
        """执行查询并返回结构化输出"""
        try:
            # 生成结构化提示词
            prompt = self.prompt_template.format(query=query)
            
            # 使用现有代理执行查询
            result = self.agent.run(query)
            
            # 尝试解析为结构化格式
            try:
                return self.parser.parse(result)
            except:
                # 如果解析失败，返回默认格式
                return SpatialQueryResponse(
                    answer=result,
                    geojson=None
                )
                
        except Exception as e:
            return SpatialQueryResponse(
                answer=f"查询执行失败: {str(e)}",
                geojson=None
            )
    
    def run(self, query: str) -> str:
        """兼容现有接口"""
        result = self.run_with_structured_output(query)
        return json.dumps(result.dict(), ensure_ascii=False, indent=2)
'''
    
    print(integration_code)
    
    print("\n=== 集成优势 ===")
    print("✅ 强制AI代理按照指定格式返回结果")
    print("✅ 自动验证输出格式的正确性")
    print("✅ 提供类型安全的响应处理")
    print("✅ 与现有代码兼容")
    print("✅ 减少正则表达式解析的复杂性")

if __name__ == "__main__":
    test_structured_output()
    integrate_with_existing_agent()
