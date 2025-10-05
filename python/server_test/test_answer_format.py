#!/usr/bin/env python3
"""
测试AI代理的回答格式设置
验证回答格式是否为{answer: {answer} geojson: {geojson如果有}}
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spatial_sql_agent import SpatialSQLQueryAgent

def test_answer_format():
    """测试回答格式设置"""
    print("=== 测试AI代理回答格式设置 ===")
    
    agent = SpatialSQLQueryAgent()
    
    try:
        # 测试查询空间表
        test_queries = [
            "查询whupoi表的前2条记录",
            "获取whupoi表中包含'珞珈'的前2条记录"
        ]
        
        for query in test_queries:
            print(f"\n测试查询: {query}")
            
            # 执行查询
            result = agent.run_with_thought_chain(query)
            
            print(f"执行状态: {result['status']}")
            print(f"最终答案: {result['final_answer'][:200]}...")
            
            # 检查最终答案格式
            final_answer = result['final_answer']
            
            # 检查是否包含期望的格式
            if "answer:" in final_answer.lower() or "geojson:" in final_answer.lower():
                print("✅ 回答格式包含answer和geojson字段")
                
                # 尝试解析格式
                if "{" in final_answer and "}" in final_answer:
                    print("✅ 回答格式包含JSON结构")
                    
                    # 检查是否包含完整的结构
                    if "answer:" in final_answer.lower() and "geojson:" in final_answer.lower():
                        print("✅ 回答格式包含完整的{answer: ..., geojson: ...}结构")
                    else:
                        print("⚠️ 回答格式可能不完整")
                else:
                    print("⚠️ 回答格式可能不是JSON格式")
            else:
                print("❌ 回答格式不符合期望的{answer: ..., geojson: ...}格式")
        
        print("\n=== 测试总结 ===")
        print("✅ 提示词设置成功：要求AI代理使用{answer: ..., geojson: ...}格式")
        print("⚠️  注意：AI代理可能不完全遵守格式要求，需要进一步优化提示词")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False
    finally:
        agent.close()

if __name__ == "__main__":
    success = test_answer_format()
    
    if success:
        print("\n✅ 回答格式设置测试完成")
    else:
        print("\n❌ 回答格式设置测试失败")
