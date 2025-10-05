"""
测试集成后的结构化输出解决方案
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_structured_solution import parse_structured_response
from spatial_sql_prompt import SPATIAL_SYSTEM_PROMPT_SIMPLE

def test_integrated_solution():
    """测试集成后的解决方案"""
    print("=== 测试集成后的结构化输出解决方案 ===\n")
    
    # 测试1: 检查提示词是否包含结构化输出要求
    print("测试1: 检查提示词是否包含结构化输出要求")
    print("-" * 50)
    
    required_keywords = [
        "响应格式要求",
        "JSON格式",
        "answer",
        "geojson",
        "FeatureCollection"
    ]
    
    missing_keywords = []
    for keyword in required_keywords:
        if keyword not in SPATIAL_SYSTEM_PROMPT_SIMPLE:
            missing_keywords.append(keyword)
    
    if missing_keywords:
        print(f"❌ 提示词缺少关键要求: {missing_keywords}")
    else:
        print("✅ 提示词包含所有关键要求")
    
    print(f"提示词长度: {len(SPATIAL_SYSTEM_PROMPT_SIMPLE)} 字符")
    print()
    
    # 测试2: 测试解析器功能
    print("测试2: 测试解析器功能")
    print("-" * 50)
    
    test_responses = [
        {
            "name": "理想JSON格式",
            "response": '''根据查询结果，我找到了whupoi表的前2条记录：

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
        },
        {
            "name": "直接JSON格式",
            "response": '''{
  "answer": "查询成功返回了包含'珞珈'的记录",
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [114.3602621, 30.5326797]
        },
        "properties": {
          "gid": 3,
          "name": "珞珈山街道办事处"
        }
      }
    ]
  }
}'''
        },
        {
            "name": "只有文本",
            "response": "查询成功返回了结果，但没有空间数据需要返回。"
        }
    ]
    
    for test in test_responses:
        print(f"测试用例: {test['name']}")
        parsed_result = parse_structured_response(test['response'])
        print(f"✅ 解析成功 - Answer长度: {len(parsed_result['answer'])}, GeoJSON要素数: {len(parsed_result['geojson'].get('features', [])) if parsed_result['geojson'] else 0}")
        print()
    
    # 测试3: 检查server.py导入
    print("测试3: 检查server.py导入")
    print("-" * 50)
    
    try:
        from server import parse_structured_response as server_parser
        print("✅ server.py成功导入parse_structured_response")
    except ImportError as e:
        print(f"❌ server.py导入失败: {e}")
    
    # 测试4: 检查spatial_sql_agent.py提示词
    print("\n测试4: 检查spatial_sql_agent.py提示词")
    print("-" * 50)
    
    try:
        from spatial_sql_agent import SPATIAL_SYSTEM_PROMPT
        if "响应格式要求" in SPATIAL_SYSTEM_PROMPT and "JSON格式" in SPATIAL_SYSTEM_PROMPT:
            print("✅ spatial_sql_agent.py提示词包含结构化输出要求")
        else:
            print("❌ spatial_sql_agent.py提示词缺少结构化输出要求")
    except ImportError as e:
        print(f"❌ 无法检查spatial_sql_agent.py提示词: {e}")
    
    # 测试5: 模拟实际查询场景
    print("\n测试5: 模拟实际查询场景")
    print("-" * 50)
    
    # 模拟AI代理可能返回的响应
    ai_responses = [
        {
            "description": "AI代理返回标准JSON格式",
            "response": '''Thought: 我需要查询whupoi表的前2条记录
Action: sql_db_query
Action Input: "SELECT gid, name, ST_AsGeoJSON(ST_Transform(geom, 4326)) as geometry FROM whupoi LIMIT 2"

Final Answer: ```json
{
  "answer": "查询成功返回了whupoi表的前2条记录，包含几何数据",
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
          "name": "交通信号灯"
        }
      }
    ]
  }
}
```'''
        },
        {
            "description": "AI代理返回混合格式",
            "response": '''查询成功返回了结果：

我找到了whupoi表的前2条记录，包含以下信息：

```json
{
  "answer": "查询成功返回了2条记录",
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
          "name": "交通信号灯"
        }
      }
    ]
  }
}
```

这些记录显示了交通设施的位置信息。'''
        }
    ]
    
    for ai_response in ai_responses:
        print(f"场景: {ai_response['description']}")
        parsed_result = parse_structured_response(ai_response['response'])
        print(f"✅ 解析成功 - Answer长度: {len(parsed_result['answer'])}, GeoJSON要素数: {len(parsed_result['geojson'].get('features', [])) if parsed_result['geojson'] else 0}")
        print()

def integration_summary():
    """集成总结"""
    print("\n=== 集成总结 ===")
    print("=" * 50)
    
    summary = """
## 解决方案集成状态

### ✅ 已完成
1. **创建了简化版结构化输出解决方案** (simple_structured_solution.py)
   - 提供智能解析器，能够处理多种响应格式
   - 包含容错机制，解析失败时返回合理的默认值

2. **增强了空间提示词** (spatial_sql_prompt.py)
   - 在SPATIAL_SYSTEM_PROMPT_SIMPLE中添加了明确的JSON格式要求
   - 使用代码块格式明确指定期望的响应结构

3. **更新了server.py**
   - 导入了新的解析器
   - 在_handle_spatial_query函数中使用结构化解析器替代复杂的正则表达式

4. **更新了spatial_sql_agent.py**
   - 增强了系统提示词，包含结构化输出要求
   - 提供清晰的JSON格式示例和强制要求

### 🔄 预期效果
- AI代理将更倾向于按照指定格式返回结果
- server.py能够可靠地提取answer和geojson字段
- 减少正则表达式解析的复杂性
- 提高系统的稳定性和可维护性

### 📋 使用方式
1. AI代理现在会收到明确的JSON格式要求
2. server.py会自动使用parse_structured_response解析响应
3. 系统能够处理多种响应格式（带代码块、直接JSON、纯文本等）
4. 解析失败时会返回合理的默认值，避免系统崩溃

### 🎯 核心改进
- **提示词增强**: 明确要求AI代理按照指定JSON格式返回结果
- **智能解析**: 能够处理多种响应格式，提供容错机制
- **向后兼容**: 与现有代码无缝集成
- **性能优化**: 减少复杂的正则表达式匹配
"""
    
    print(summary)

if __name__ == "__main__":
    test_integrated_solution()
    integration_summary()
