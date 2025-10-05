#!/usr/bin/env python3
"""
对比测试脚本：比较LangGraph方案和原始方案在SQL查询结果捕获方面的效果
"""

import json
from spatial_sql_agent import SpatialSQLQueryAgent
from spatial_sql_agent_langgraph import SpatialSQLQueryAgentLangGraph

def test_original_agent():
    """测试原始方案"""
    print("=== 测试原始SQL Agent方案 ===")
    
    agent = SpatialSQLQueryAgent()
    
    try:
        # 测试查询
        test_query = "查询whupoi表的前3条记录"
        print(f"测试查询: {test_query}")
        
        # 使用思维链模式获取详细结果
        result = agent.run_with_thought_chain(test_query)
        
        print(f"执行状态: {result['status']}")
        print(f"步骤数量: {result['step_count']}")
        print(f"SQL查询数量: {len(result['sql_queries_with_results'])}")
        
        # 检查SQL查询结果是否被正确捕获
        sql_results_captured = 0
        for sql_info in result['sql_queries_with_results']:
            if sql_info['status'] == 'completed' and sql_info['result']:
                sql_results_captured += 1
                print(f"  ✓ SQL查询 {sql_info['step']}: 结果已捕获")
            else:
                print(f"  ✗ SQL查询 {sql_info['step']}: 结果未捕获")
        
        # 检查思维链中的observation字段
        observations_captured = 0
        for step in result['thought_chain']:
            if step.get('type') == 'action' and step.get('observation'):
                observations_captured += 1
        
        print(f"SQL查询结果捕获率: {sql_results_captured}/{len(result['sql_queries_with_results'])}")
        print(f"思维链观察结果捕获率: {observations_captured}/{len([s for s in result['thought_chain'] if s.get('type') == 'action'])}")
        
        return result
        
    except Exception as e:
        print(f"原始方案测试失败: {e}")
        return None
    finally:
        agent.close()

def test_langgraph_agent():
    """测试LangGraph方案"""
    print("\n=== 测试LangGraph SQL Agent方案 ===")
    
    agent = SpatialSQLQueryAgentLangGraph()
    
    try:
        # 测试查询
        test_query = "查询whupoi表的前3条记录"
        print(f"测试查询: {test_query}")
        
        # 使用思维链模式获取详细结果
        result = agent.run_with_thought_chain(test_query)
        
        print(f"执行状态: {result['status']}")
        print(f"步骤数量: {result['step_count']}")
        print(f"SQL查询数量: {len(result['sql_queries_with_results'])}")
        
        # 检查SQL查询结果是否被正确捕获
        sql_results_captured = 0
        for sql_info in result['sql_queries_with_results']:
            if sql_info['status'] == 'completed' and sql_info['result']:
                sql_results_captured += 1
                print(f"  ✓ SQL查询 {sql_info['step']}: 结果已捕获")
                # 显示部分结果
                result_str = str(sql_info['result'])
                if len(result_str) > 100:
                    print(f"    结果预览: {result_str[:100]}...")
                else:
                    print(f"    结果: {result_str}")
            else:
                print(f"  ✗ SQL查询 {sql_info['step']}: 结果未捕获")
        
        # 检查思维链中的observation字段
        observations_captured = 0
        for step in result['thought_chain']:
            if step.get('type') == 'action' and step.get('observation'):
                observations_captured += 1
        
        print(f"SQL查询结果捕获率: {sql_results_captured}/{len(result['sql_queries_with_results'])}")
        print(f"思维链观察结果捕获率: {observations_captured}/{len([s for s in result['thought_chain'] if s.get('type') == 'action'])}")
        
        return result
        
    except Exception as e:
        print(f"LangGraph方案测试失败: {e}")
        return None
    finally:
        agent.close()

def compare_results(original_result, langgraph_result):
    """对比两个方案的结果"""
    print("\n=== 方案对比分析 ===")
    
    if not original_result or not langgraph_result:
        print("无法进行对比：至少有一个方案测试失败")
        return
    
    print("原始方案:")
    print(f"  - 状态: {original_result['status']}")
    print(f"  - 步骤数量: {original_result['step_count']}")
    print(f"  - SQL查询数量: {len(original_result['sql_queries_with_results'])}")
    
    original_sql_captured = sum(1 for sql in original_result['sql_queries_with_results'] 
                               if sql['status'] == 'completed' and sql['result'])
    print(f"  - SQL结果捕获: {original_sql_captured}/{len(original_result['sql_queries_with_results'])}")
    
    print("\nLangGraph方案:")
    print(f"  - 状态: {langgraph_result['status']}")
    print(f"  - 步骤数量: {langgraph_result['step_count']}")
    print(f"  - SQL查询数量: {len(langgraph_result['sql_queries_with_results'])}")
    
    langgraph_sql_captured = sum(1 for sql in langgraph_result['sql_queries_with_results'] 
                                if sql['status'] == 'completed' and sql['result'])
    print(f"  - SQL结果捕获: {langgraph_sql_captured}/{len(langgraph_result['sql_queries_with_results'])}")
    
    print("\n=== 对比结论 ===")
    if langgraph_sql_captured > original_sql_captured:
        print("✓ LangGraph方案在SQL查询结果捕获方面表现更好")
    elif langgraph_sql_captured < original_sql_captured:
        print("✗ 原始方案在SQL查询结果捕获方面表现更好")
    else:
        print("= 两个方案在SQL查询结果捕获方面表现相同")
    
    # 显示LangGraph方案捕获的具体SQL结果
    if langgraph_sql_captured > 0:
        print("\nLangGraph方案捕获的SQL查询结果示例:")
        for i, sql_info in enumerate(langgraph_result['sql_queries_with_results'][:2]):  # 只显示前2个
            if sql_info['status'] == 'completed' and sql_info['result']:
                print(f"\nSQL {i+1}: {sql_info['sql']}")
                result_str = str(sql_info['result'])
                if len(result_str) > 200:
                    print(f"结果预览: {result_str[:200]}...")
                else:
                    print(f"结果: {result_str}")

def main():
    """主测试函数"""
    print("开始对比测试...")
    
    # 测试原始方案
    original_result = test_original_agent()
    
    # 测试LangGraph方案
    langgraph_result = test_langgraph_agent()
    
    # 对比结果
    compare_results(original_result, langgraph_result)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()
