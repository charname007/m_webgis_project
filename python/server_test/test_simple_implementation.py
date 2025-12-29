#!/usr/bin/env python3
"""
测试简化后的实现
"""

from spatial_sql_agent import SpatialSQLQueryAgent

def test_simple_implementation():
    """测试简化后的实现"""
    print("=== 测试简化后的实现 ===")
    
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
        
        # 显示SQL查询和结果
        for i, sql_info in enumerate(result['sql_queries_with_results']):
            print(f"\nSQL {i+1}:")
            print(f"  查询: {sql_info['sql']}")
            print(f"  状态: {sql_info['status']}")
            print(f"  结果类型: {type(sql_info['result'])}")
            
            if sql_info['result']:
                result_str = str(sql_info['result'])
                print(f"  结果长度: {len(result_str)}")
                if len(result_str) > 200:
                    print(f"  结果预览: {result_str[:200]}...")
                else:
                    print(f"  结果: {result_str}")
        
        # 检查是否包含intermediate_steps
        if 'intermediate_steps' in result:
            print(f"\n包含原始中间步骤: {len(result['intermediate_steps'])}个")
            for i, (action, observation) in enumerate(result['intermediate_steps']):
                if action.tool == 'sql_db_query':
                    print(f"  步骤 {i+1}: {action.tool} -> {type(observation)}")
        
        return result
        
    except Exception as e:
        print(f"测试失败: {e}")
        return None
    finally:
        agent.close()

if __name__ == "__main__":
    test_simple_implementation()
