#!/usr/bin/env python3
"""
测试修复后的服务器功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server import _handle_spatial_query, initialize_agent
from spatial_sql_agent import SpatialSQLQueryAgent as EnhancedSpatialSQLQueryAgent

import asyncio

async def test_server_spatial_query():
    """测试服务器空间查询功能"""
    try:
        print("初始化服务器代理...")
        # 初始化全局代理
        initialize_agent()
        
        # 测试查询
        test_question = "查找距离珞珈山5公里内的所有POI点"
        
        print(f"执行服务器空间查询: {test_question}")
        
        # 模拟查询分析结果
        query_analysis = {
            "query_type": "spatial",
            "priority": 1,
            "is_spatial": True,
            "is_summary": False,
            "is_sql": True
        }
        
        # 调用服务器处理函数（异步）
        result = await _handle_spatial_query(test_question, query_analysis, True, True)
        
        print(f"服务器响应状态: {result['status']}")
        
        if result['status'] == 'success':
            print("✅ 服务器测试成功！")
            print(f"思维链步骤数: {len(result['answer']['thought_chain'])}")
            print(f"SQL查询数量: {len(result.get('sql_queries_with_results', []))}")
            print(f"最终答案长度: {len(result['answer']['text'])}")
            
            # 显示思维链摘要
            for step in result['answer']['thought_chain'][:3]:  # 只显示前3步
                step_type = step.get('type', 'unknown')
                if step_type == 'action':
                    print(f"步骤 {step['step']}: {step['type']} - {step.get('action', '')}")
                elif step_type == 'final_answer':
                    print(f"步骤 {step['step']}: {step['type']} - {step.get('content', '')[:100]}...")
                else:
                    print(f"步骤 {step['step']}: {step['type']}")
                    
        else:
            print("❌ 服务器测试失败")
            print(f"错误: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 服务器测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_server_spatial_query()

if __name__ == "__main__":
    asyncio.run(main())
