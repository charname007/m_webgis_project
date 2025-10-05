"""
简化版结构化输出解决方案 - 避免Pydantic版本兼容性问题
"""

import json
import re
from typing import Dict, Any, Optional

def create_structured_prompt():
    """创建结构化提示词（不使用Pydantic）"""
    
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

```json
{
  "answer": "你的自然语言回答，解释查询结果和发现",
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point/LineString/Polygon",
          "coordinates": [经度, 纬度]
        },
        "properties": {
          "字段1": "值1",
          "字段2": "值2"
        }
      }
    ]
  }
}
```

如果查询不涉及空间数据或不需要返回GeoJSON，可以省略geojson字段。

## 示例响应格式
```json
{
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
}
```

请根据用户的问题生成相应的空间SQL查询，并按照上述格式返回结果。

用户查询：{query}
"""
    
    return template

def parse_structured_response(response: str) -> Dict[str, Any]:
    """解析结构化响应"""
    
    # 方法1: 查找完整的JSON格式
    json_pattern = r'```json\s*(\{.*?\})\s*```'
    json_matches = re.findall(json_pattern, response, re.DOTALL)
    
    if json_matches:
        try:
            return json.loads(json_matches[0])
        except json.JSONDecodeError:
            pass
    
    # 方法2: 查找独立的JSON对象
    json_pattern2 = r'(\{\s*"answer":\s*".*?",\s*"geojson":\s*\{.*?\}\s*\})'
    json_matches2 = re.findall(json_pattern2, response, re.DOTALL)
    
    if json_matches2:
        try:
            return json.loads(json_matches2[0])
        except json.JSONDecodeError:
            pass
    
    # 方法3: 如果找不到结构化格式，返回原始响应
    return {
        "answer": response,
        "geojson": None
    }

def enhance_spatial_prompt_with_structure():
    """增强现有的空间提示词，添加结构化输出要求"""
    
    # 读取现有的提示词
    existing_prompt = """
你是一个专业的空间数据库和PostGIS查询专家。你正在访问一个PostgreSQL数据库，该数据库已经安装了PostGIS扩展，用于存储和处理地理空间数据。

数据库环境信息：
- 数据库类型：PostgreSQL with PostGIS extension
- 数据库名称：WGP_db
- 主要包含空间数据表，如whupoi、edges、county等
- 几何列通常命名为"geom"或"the_geom"

重要要求：
1. 所有空间查询必须包含几何数据
2. 使用ST_AsGeoJSON(ST_Transform(geom, 4326))将几何数据转换为WGS84坐标系并转换为GeoJSON格式
3. 优先使用PostGIS函数（ST_Distance、ST_Intersects、ST_Within等）
4. 生成的SQL应该可以直接在PostGIS环境中执行

请根据用户的问题生成相应的空间SQL查询。
"""
    
    # 添加结构化输出要求
    structured_requirement = """

## 响应格式要求
你必须严格按照以下JSON格式返回最终答案：

```json
{
  "answer": "你的自然语言回答，解释查询结果和发现",
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point/LineString/Polygon",
          "coordinates": [经度, 纬度]
        },
        "properties": {
          "字段1": "值1",
          "字段2": "值2"
        }
      }
    ]
  }
}
```

如果查询不涉及空间数据或不需要返回GeoJSON，可以省略geojson字段。

请确保你的响应是有效的JSON格式，可以直接被解析。
"""
    
    return existing_prompt + structured_requirement

def test_simple_solution():
    """测试简化版解决方案"""
    print("=== 测试简化版结构化输出解决方案 ===\n")
    
    # 测试查询
    test_query = "查询whupoi表的前2条记录"
    
    # 生成提示词
    prompt = create_structured_prompt()
    formatted_prompt = prompt.replace("{query}", test_query)
    
    print("生成的提示词格式:")
    print("=" * 50)
    print(formatted_prompt[:500] + "..." if len(formatted_prompt) > 500 else formatted_prompt)
    print("=" * 50)
    
    # 测试解析器
    test_response = '''根据查询结果，我找到了whupoi表的前2条记录：

```json
{
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
}
```'''
    
    parsed_result = parse_structured_response(test_response)
    print("\n✅ 解析成功:")
    print(f"Answer长度: {len(parsed_result['answer'])}")
    print(f"GeoJSON要素数: {len(parsed_result['geojson'].get('features', [])) if parsed_result['geojson'] else 0}")
    
    # 测试增强的提示词
    print("\n=== 增强的提示词 ===")
    enhanced_prompt = enhance_spatial_prompt_with_structure()
    print(enhanced_prompt[:300] + "..." if len(enhanced_prompt) > 300 else enhanced_prompt)

def integration_guide():
    """集成指南"""
    print("\n=== 集成到现有系统 ===")
    
    integration_code = '''
# 在spatial_sql_prompt.py中修改提示词

# 替换现有的SPATIAL_SYSTEM_PROMPT_SIMPLE
SPATIAL_SYSTEM_PROMPT_SIMPLE = """
你是一个专业的空间数据库和PostGIS查询专家...

## 响应格式要求
你必须严格按照以下JSON格式返回最终答案：

```json
{
  "answer": "你的自然语言回答，解释查询结果和发现",
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point/LineString/Polygon",
          "coordinates": [经度, 纬度]
        },
        "properties": {
          "字段1": "值1",
          "字段2": "值2"
        }
      }
    ]
  }
}
```

如果查询不涉及空间数据或不需要返回GeoJSON，可以省略geojson字段。
"""

# 在server.py中使用解析器
from simple_structured_solution import parse_structured_response

def extract_answer_and_geojson(final_answer):
    """使用简化版解析器"""
    return parse_structured_response(final_answer)
'''
    
    print(integration_code)
    
    print("\n=== 优势 ===")
    print("✅ 避免Pydantic版本兼容性问题")
    print("✅ 简单易用，无需复杂依赖")
    print("✅ 与现有代码无缝集成")
    print("✅ 提供清晰的格式要求")
    print("✅ 自动处理解析失败的情况")

if __name__ == "__main__":
    test_simple_solution()
    integration_guide()
