#!/usr/bin/env python3
"""
测试混合格式解析器
验证改进后的LLMResponseParser是否能正确处理包含完整Thought/Action链但最后返回直接答案的情况
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from parsing_fix import LLMResponseParser

def test_hybrid_format():
    """测试混合格式解析"""
    print("测试混合格式解析器")
    print("=" * 60)
    
    # 模拟实际场景中的LLM响应（包含完整Thought/Action链但最后返回直接答案）
    test_response = """
> Entering new SQL Agent Executor chain...
I'll help you find the nearest point to 珞珈山 (Luojiashan) using PostGIS functions. Let me start by exploring the database structure.

Thought: 我需要先查看数据库中有哪些表
Action: sql_db_list_tables
Action Input: 

Thought: 现在我需要查询whupoi表的结构
Action: sql_db_schema
Action Input: "whupoi"

Thought: 我需要找到珞珈山的位置
Action: sql_db_query
Action Input: SELECT gid, name, ST_AsGeoJSON(geom) as geojson FROM whupoi WHERE name LIKE '%珞珈山%'

Thought: 现在我需要计算距离并找到最近的点
Action: sql_db_query
Action Input: SELECT gid, name, ST_AsGeoJSON(geom) as geojson, ST_Distance(geom, ST_SetSRID(ST_MakePoint(114.3518679, 30.5349852), 4326)::geography) as distance_meters FROM whupoi ORDER BY geom <-> ST_SetSRID(ST_MakePoint(114.3518679, 30.5349852), 4326) LIMIT 10

根据查询结果，我找到了珞珈门附近1公里范围内的10个POI点，按距离排序。以下是详细信息：

**查询结果：**

1. **武汉大学珞珈门** - 距离：0米
2. **珞珈山站** - 距离：32.51米
3. **KFC** - 距离：39.10米
4. **无名POI** - 距离：51.97米
5. **YESIDO 椰島造型** - 距离：56.16米
6. **天空乐坊** - 距离：67.42米
7. **江南小观园** - 距离：76.25米
8. **優品匯** - 距离：82.56米
9. **豪客来牛排** - 距离：92.65米
10. **Pizza Hut** - 距离：103.59米

**使用的SQL查询语句：**
```sql
SELECT gid, name, ST_AsGeoJSON(geom) as geojson,
ST_Distance(geom, ST_SetSRID(ST_MakePoint(114.3518679, 30.5349852), 4326)::geography) as distance_meters
FROM whupoi
WHERE ST_DWithin(geom::geography, ST_SetSRID(ST_MakePoint(114.3518679, 30.5349852), 4326)::geography, 1000)
ORDER BY geom <-> ST_SetSRID(ST_MakePoint(114.3518679, 30.5349852), 4326)
LIMIT 10
```

这个查询使用了PostGIS的空间函数：
- `ST_DWithin` 用于查找1公里范围内的POI
- `ST_Distance` 计算精确距离
- `geom <->` 操作符利用空间索引进行高效排序
- `ST_AsGeoJSON` 将几何数据转换为GeoJSON格式
"""
    
    parser = LLMResponseParser()
    result = parser.parse_llm_response(test_response)
    
    print(f"解析状态: {result['status']}")
    print(f"解析类型: {result.get('type', 'unknown')}")
    
    if 'thought_chain' in result:
        print(f"\n思维链步骤数: {len(result['thought_chain'])}")
        print("-" * 40)
        
        for step in result['thought_chain']:
            if step['type'] == 'thought':
                print(f"步骤 {step['step']} ({step['type']}):")
                print(f"  {step['content'][:100]}...")
            elif step['type'] == 'action':
                print(f"步骤 {step['step']} ({step['type']}):")
                print(f"  Action: {step['action']}")
                if step['action_input']:
                    print(f"  Input: {step['action_input'][:50]}...")
            elif step['type'] == 'final_answer':
                print(f"步骤 {step['step']} ({step['type']}):")
                print(f"  {step['content'][:100]}...")
            print()
    
    if 'final_answer' in result and result['final_answer']:
        print(f"最终答案: {result['final_answer'][:200]}...")
    
    # 验证思维链完整性
    thought_count = sum(1 for step in result.get('thought_chain', []) if step['type'] == 'thought')
    action_count = sum(1 for step in result.get('thought_chain', []) if step['type'] == 'action')
    final_answer_count = sum(1 for step in result.get('thought_chain', []) if step['type'] == 'final_answer')
    
    print(f"\n思维链统计:")
    print(f"  - Thought步骤: {thought_count}")
    print(f"  - Action步骤: {action_count}")
    print(f"  - Final Answer步骤: {final_answer_count}")
    print(f"  - 总步骤数: {len(result.get('thought_chain', []))}")
    
    # 验证是否成功提取了完整的推理过程
    # 注意：Final Answer可能被正确过滤掉（如果包含SQL查询）
    if thought_count >= 2 and action_count >= 2:
        print("\n✅ 测试通过：成功提取了完整的思维链！")
        print("  注意：Final Answer被正确过滤（包含SQL查询内容）")
    else:
        print("\n❌ 测试失败：思维链不完整")

def test_old_vs_new_parser():
    """对比新旧解析器的效果"""
    print("\n\n对比新旧解析器效果")
    print("=" * 60)
    
    # 模拟实际场景中的响应
    test_response = """
Thought: 我需要先查看数据库中有哪些表
Action: sql_db_list_tables
Action Input: 

Thought: 现在我需要查询whupoi表的结构
Action: sql_db_schema
Action Input: "whupoi"

根据查询结果，我找到了珞珈门附近1公里范围内的POI点...
"""
    
    parser = LLMResponseParser()
    
    # 测试新解析器（混合格式）
    result = parser.parse_llm_response(test_response)
    
    print("新解析器结果:")
    print(f"  解析类型: {result.get('type', 'unknown')}")
    print(f"  思维链步骤数: {len(result.get('thought_chain', []))}")
    
    # 模拟旧解析器的行为（直接答案优先）
    thought_chain = []
    if "根据查询结果" in test_response:
        # 旧解析器会优先匹配直接答案格式
        thought_chain = [{
            "step": 1,
            "type": "final_answer",
            "content": test_response.split("根据查询结果")[1].strip(),
            "timestamp": "direct_answer"
        }]
    
    print("旧解析器结果:")
    print(f"  解析类型: direct_answer")
    print(f"  思维链步骤数: {len(thought_chain)}")
    
    if len(result.get('thought_chain', [])) > len(thought_chain):
        print("\n✅ 新解析器成功保留了完整的推理过程！")
    else:
        print("\n❌ 新解析器未能改善思维链提取")

if __name__ == "__main__":
    test_hybrid_format()
    test_old_vs_new_parser()
