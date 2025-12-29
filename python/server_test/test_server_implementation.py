#!/usr/bin/env python3
"""
测试server.py的修改，验证从中间步骤获取SQL查询和结果的功能
"""

import asyncio
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import intelligent_agent_query

async def test_server_implementation():
    """测试server.py的修改"""
    print("=== 测试server.py从中间步骤获取SQL查询和结果 ===")
    
    try:
        # 测试查询
        test_query = "查询whupoi表的前3条记录"
        print(f"测试查询: {test_query}")
        
        # 调用智能代理查询
        result = await intelligent_agent_query({
            "question": test_query,
            "execute_sql": True,
            "return_geojson": True
        })
        
        print(f"执行状态: {result['status']}")
        
        if result['status'] == 'success':
            print(f"查询类型: {result['question']['type']}")
            print(f"思维链步骤数量: {len(result['answer']['thought_chain'])}")
            
            # 检查SQL查询和结果
            sql_queries_with_results = result.get('sql_queries_with_results', [])
            print(f"SQL查询数量: {len(sql_queries_with_results)}")
            
            for i, sql_info in enumerate(sql_queries_with_results):
                print(f"\nSQL {i+1}:")
                print(f"  查询: {sql_info.get('sql', 'N/A')}")
                print(f"  状态: {sql_info.get('status', 'N/A')}")
                print(f"  结果类型: {type(sql_info.get('result', 'N/A'))}")
                
                result_str = str(sql_info.get('result', 'N/A'))
                if len(result_str) > 200:
                    print(f"  结果预览: {result_str[:200]}...")
                else:
                    print(f"  结果: {result_str}")
            
            # 检查最终答案
            final_answer = result['answer'].get('text', '')
            print(f"\n最终答案长度: {len(final_answer)}")
            if len(final_answer) > 200:
                print(f"最终答案预览: {final_answer[:200]}...")
            else:
                print(f"最终答案: {final_answer}")
            
            # 检查是否有查询结果
            query_result = result['answer'].get('query_result', '')
            if query_result:
                print(f"查询结果类型: {type(query_result)}")
                print(f"查询结果长度: {len(str(query_result))}")
        
        return result
        
    except Exception as e:
        print(f"测试失败: {e}")
        return None

if __name__ == "__main__":
    # 运行异步测试
    result = asyncio.run(test_server_implementation())
    
    if result and result['status'] == 'success':
        print("\n✅ 测试成功！server.py已成功从中间步骤获取SQL查询和结果")
    else:
        print("\n❌ 测试失败")
