#!/usr/bin/env python3
"""
测试修复后的空间SQL查询代理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spatial_sql_agent import SpatialSQLQueryAgent

def test_spatial_agent():
    """测试空间查询代理"""
    try:
        print("创建空间查询代理...")
        spatial_agent = SpatialSQLQueryAgent()
        
        # 测试查询
        test_query = "查找距离珞珈山10公里内的所有POI点"
        
        print(f"执行查询: {test_query}")
        
        # 使用run_with_thought_chain方法
        result = spatial_agent.run_with_thought_chain(test_query)
        
        print(f"结果状态: {result['status']}")
        print(f"思维链步骤数: {result['step_count']}")
        print(f"SQL查询数量: {len(result['sql_queries_with_results'])}")
        
        if result['status'] in ['success', 'partial_success']:
            print("✅ 测试成功！")
            print(f"最终答案长度: {len(result['final_answer'])}")
            
            # 显示思维链摘要
            for step in result['thought_chain']:
                print(f"步骤 {step['step']}: {step['type']} - {step.get('action', step.get('content', ''))[:100]}...")
                
        else:
            print("❌ 测试失败")
            print(f"错误: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if 'spatial_agent' in locals():
            spatial_agent.close()

if __name__ == "__main__":
    test_spatial_agent()
