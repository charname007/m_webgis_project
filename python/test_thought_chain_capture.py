#!/usr/bin/env python3
"""
测试思维链捕获功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spatial_sql_agent import SpatialSQLQueryAgent
from sql_query_agent import SQLQueryAgent

def test_spatial_agent_thought_chain():
    """测试空间代理的思维链捕获功能"""
    print("=== 测试空间代理思维链捕获 ===")
    
    try:
        # 创建空间查询代理
        spatial_agent = SpatialSQLQueryAgent()
        
        # 测试查询
        test_query = "查找武汉大学珞珈门附近1公里范围内的POI点"
        
        print(f"测试查询: {test_query}")
        
        # 使用思维链捕获功能
        result = spatial_agent.run_with_thought_chain(test_query)
        
        print(f"状态: {result['status']}")
        print(f"步骤数量: {result['step_count']}")
        print(f"最终答案长度: {len(result['final_answer'])}")
        
        # 显示思维链
        print("\n=== 思维链详情 ===")
        for i, step in enumerate(result['thought_chain']):
            print(f"\n步骤 {i+1}:")
            print(f"  类型: {step['type']}")
            if step['type'] == 'action':
                print(f"  动作: {step['action']}")
                print(f"  输入: {step['action_input'][:100]}...")
            elif step['type'] == 'final_answer':
                print(f"  内容: {step['content'][:200]}...")
            print(f"  日志: {step['log'][:100]}...")
        
        # 显示最终答案
        print(f"\n=== 最终答案 ===")
        print(result['final_answer'][:500] + "..." if len(result['final_answer']) > 500 else result['final_answer'])
        
        spatial_agent.close()
        return result
        
    except Exception as e:
        print(f"测试失败: {e}")
        return None

def test_sql_agent_thought_chain():
    """测试SQL代理的思维链捕获功能"""
    print("\n=== 测试SQL代理思维链捕获 ===")
    
    try:
        # 创建SQL查询代理
        sql_agent = SQLQueryAgent()
        
        # 测试查询
        test_query = "查询数据库中有哪些表"
        
        print(f"测试查询: {test_query}")
        
        # 使用思维链捕获功能
        result = sql_agent.run_with_thought_chain(test_query)
        
        print(f"状态: {result['status']}")
        print(f"步骤数量: {result['step_count']}")
        print(f"最终答案长度: {len(result['final_answer'])}")
        
        # 显示思维链
        print("\n=== 思维链详情 ===")
        for i, step in enumerate(result['thought_chain']):
            print(f"\n步骤 {i+1}:")
            print(f"  类型: {step['type']}")
            if step['type'] == 'action':
                print(f"  动作: {step['action']}")
                print(f"  输入: {step['action_input'][:100]}...")
            elif step['type'] == 'final_answer':
                print(f"  内容: {step['content'][:200]}...")
            print(f"  日志: {step['log'][:100]}...")
        
        # 显示最终答案
        print(f"\n=== 最终答案 ===")
        print(result['final_answer'][:500] + "..." if len(result['final_answer']) > 500 else result['final_answer'])
        
        sql_agent.close()
        return result
        
    except Exception as e:
        print(f"测试失败: {e}")
        return None

def compare_thought_chain_vs_regular():
    """比较思维链捕获和常规执行的差异"""
    print("\n=== 比较思维链捕获和常规执行 ===")
    
    try:
        # 创建代理
        agent = SpatialSQLQueryAgent()
        
        # 测试查询
        test_query = "查找距离珞珈门最近的10个POI点"
        
        print(f"测试查询: {test_query}")
        
        # 常规执行
        print("\n--- 常规执行 ---")
        regular_result = agent.run(test_query)
        print(f"常规结果长度: {len(regular_result)}")
        print(f"常规结果前200字符: {regular_result[:200]}...")
        
        # 思维链捕获执行
        print("\n--- 思维链捕获执行 ---")
        thought_chain_result = agent.run_with_thought_chain(test_query)
        print(f"思维链状态: {thought_chain_result['status']}")
        print(f"思维链步骤数: {thought_chain_result['step_count']}")
        print(f"最终答案长度: {len(thought_chain_result['final_answer'])}")
        
        # 比较结果
        print("\n--- 结果比较 ---")
        if regular_result == thought_chain_result['final_answer']:
            print("✓ 最终答案一致")
        else:
            print("⚠ 最终答案有差异")
            print(f"常规结果长度: {len(regular_result)}")
            print(f"思维链结果长度: {len(thought_chain_result['final_answer'])}")
        
        agent.close()
        
    except Exception as e:
        print(f"比较测试失败: {e}")

if __name__ == "__main__":
    print("开始测试思维链捕获功能...")
    
    # 测试空间代理
    spatial_result = test_spatial_agent_thought_chain()
    
    # 测试SQL代理
    sql_result = test_sql_agent_thought_chain()
    
    # 比较测试
    compare_thought_chain_vs_regular()
    
    print("\n=== 测试完成 ===")
    
    if spatial_result and spatial_result['status'] == 'success':
        print("✓ 空间代理思维链捕获功能正常")
    else:
        print("✗ 空间代理思维链捕获功能异常")
    
    if sql_result and sql_result['status'] == 'success':
        print("✓ SQL代理思维链捕获功能正常")
    else:
        print("✗ SQL代理思维链捕获功能异常")
