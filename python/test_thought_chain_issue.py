#!/usr/bin/env python3
"""
测试思维链提取问题
检查为什么实际API调用中思维链仍然只有1个步骤
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from parsing_fix import LLMResponseParser
from server import extract_thought_chain

def test_actual_llm_response():
    """测试实际的LLM响应内容"""
    print("测试实际LLM响应内容")
    print("=" * 60)
    
    # 模拟实际API调用中可能返回的LLM响应
    actual_response = """
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

根据查询结果，我找到了珞珈山周围1公里范围内的POI（兴趣点）。以下是距离珞珈山最近的10个POI：

1. **珞珈山** (距离：0米)
   - 类型：山峰(natural=peak)
   - 坐标：114.3646204, 30.5369429

2. **珞珈山水塔** (距离：210米)
   - 类型：水塔(water_tower)
   - 坐标：114.3667529, 30.5373594

3. **无名POI** (距离：321米)
   - 坐标：114.366223, 30.5343982

4. **校车珞珈山庄站** (距离：344米)
   - 类型：公交站(bus_stop)
   - 坐标：114.3619079, 30.5389708

5. **无名POI** (距离：344米)
   - 坐标：114.3616247, 30.535235

6. **自强超市** (距离：371米)
   - 类型：便利店(shop=convenience)
   - 坐标：114.3625206, 30.5341376

7. **无名POI** (距离：393米)
   - 坐标：114.3683789, 30.5355361

8. **珈园小观园** (距离：410米)
   - 类型：餐厅(amenity=restaurant)
   - 坐标：114.36207, 30.5339782

9. **无名POI** (距离：465米)
   - 坐标：114.3602728, 30.5387927

10. **校车经管院站** (距离：478米)
    - 类型：公交站(bus_stop)
    - 坐标：114.3666973, 30.5408644

这些POI包含了山峰、公交站、商店、餐厅等多种类型，距离从0米到478米不等，都在珞珈山1公里范围内。
"""
    
    print("原始响应长度:", len(actual_response))
    print("前500字符:", actual_response[:500])
    print()
    
    # 测试新解析器
    parser = LLMResponseParser()
    parsed_result = parser.parse_llm_response(actual_response)
    
    print("新解析器结果:")
    print(f"  状态: {parsed_result['status']}")
    print(f"  类型: {parsed_result.get('type', 'unknown')}")
    print(f"  思维链步骤数: {len(parsed_result.get('thought_chain', []))}")
    
    if 'thought_chain' in parsed_result:
        for step in parsed_result['thought_chain']:
            if step['type'] == 'thought' or step['type'] == 'final_answer':
                print(f"  步骤 {step['step']} ({step['type']}): {step['content'][:50]}...")
            elif step['type'] == 'action':
                print(f"  步骤 {step['step']} ({step['type']}): {step['action']} - {step['action_input'][:30]}...")
    
    print()
    
    # 测试服务器中的extract_thought_chain函数
    thought_chain = extract_thought_chain(actual_response)
    
    print("服务器提取结果:")
    print(f"  思维链步骤数: {len(thought_chain)}")
    
    for step in thought_chain:
        if step['type'] == 'thought' or step['type'] == 'final_answer':
            print(f"  步骤 {step['step']} ({step['type']}): {step['content'][:50]}...")
        elif step['type'] == 'action':
            print(f"  步骤 {step['step']} ({step['type']}): {step['action']} - {step['action_input'][:30]}...")

def test_direct_answer_scenario():
    """测试直接答案场景"""
    print("\n\n测试直接答案场景")
    print("=" * 60)
    
    # 模拟用户提到的直接答案场景
    direct_answer_response = """
根据查询结果，我找到了珞珈山周围1公里范围内的POI（兴趣点）。以下是距离珞珈山最近的10个POI：

1. **珞珈山** (距离：0米)
   - 类型：山峰(natural=peak)
   - 坐标：114.3646204, 30.5369429

2. **珞珈山水塔** (距离：210米)
   - 类型：水塔(water_tower)
   - 坐标：114.3667529, 30.5373594

3. **无名POI** (距离：321米)
   - 坐标：114.366223, 30.5343982

4. **校车珞珈山庄站** (距离：344米)
   - 类型：公交站(bus_stop)
   - 坐标：114.3619079, 30.5389708

5. **无名POI** (距离：344米)
   - 坐标：114.3616247, 30.535235

6. **自强超市** (距离：371米)
   - 类型：便利店(shop=convenience)
   - 坐标：114.3625206, 30.5341376

7. **无名POI** (距离：393米)
   - 坐标：114.3683789, 30.5355361

8. **珈园小观园** (距离：410米)
   - 类型：餐厅(amenity=restaurant)
   - 坐标：114.36207, 30.5339782

9. **无名POI** (距离：465米)
   - 坐标：114.3602728, 30.5387927

10. **校车经管院站** (距离：478米)
    - 类型：公交站(bus_stop)
    - 坐标：114.3666973, 30.5408644

这些POI包含了山峰、公交站、商店、餐厅等多种类型，距离从0米到478米不等，都在珞珈山1公里范围内。
"""
    
    print("直接答案响应长度:", len(direct_answer_response))
    
    # 测试新解析器
    parser = LLMResponseParser()
    parsed_result = parser.parse_llm_response(direct_answer_response)
    
    print("新解析器结果:")
    print(f"  状态: {parsed_result['status']}")
    print(f"  类型: {parsed_result.get('type', 'unknown')}")
    print(f"  思维链步骤数: {len(parsed_result.get('thought_chain', []))}")
    
    if 'thought_chain' in parsed_result:
        for step in parsed_result['thought_chain']:
            print(f"  步骤 {step['step']} ({step['type']}): {step['content'][:50]}...")
    
    print()
    
    # 测试服务器中的extract_thought_chain函数
    thought_chain = extract_thought_chain(direct_answer_response)
    
    print("服务器提取结果:")
    print(f"  思维链步骤数: {len(thought_chain)}")
    
    for step in thought_chain:
        print(f"  步骤 {step['step']} ({step['type']}): {step['content'][:50]}...")

if __name__ == "__main__":
    test_actual_llm_response()
    test_direct_answer_scenario()
