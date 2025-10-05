#!/usr/bin/env python3
"""
测试坐标转换提示词功能
验证每次查询空间表时是否使用ST_AsGeoJSON(ST_Transform(geom, 4326))
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spatial_sql_agent import SpatialSQLQueryAgent

def test_coordinate_conversion():
    """测试坐标转换提示词功能"""
    print("=== 测试坐标转换提示词功能 ===")
    
    agent = SpatialSQLQueryAgent()
    
    try:
        # 测试查询空间表
        test_queries = [
            "查询whupoi表的前3条记录",
            "查找whupoi表中包含'珞珈'的记录",
            "获取whupoi表的所有记录"
        ]
        
        for query in test_queries:
            print(f"\n测试查询: {query}")
            
            # 使用思维链模式获取详细结果
            result = agent.run_with_thought_chain(query)
            
            print(f"执行状态: {result['status']}")
            print(f"步骤数量: {result['step_count']}")
            print(f"SQL查询数量: {len(result['sql_queries_with_results'])}")
            
            # 检查SQL查询是否包含坐标转换
            for i, sql_info in enumerate(result['sql_queries_with_results']):
                sql = sql_info.get('sql', '')
                print(f"\nSQL {i+1}:")
                print(f"  查询: {sql}")
                
                # 检查是否包含坐标转换
                if "ST_AsGeoJSON" in sql.upper() and "ST_Transform" in sql.upper():
                    print("  ✅ 包含坐标转换: ST_AsGeoJSON(ST_Transform(geom, 4326))")
                elif "ST_AsGeoJSON" in sql.upper():
                    print("  ⚠️ 包含ST_AsGeoJSON但缺少ST_Transform")
                else:
                    print("  ❌ 缺少坐标转换函数")
                
                # 检查结果
                query_result = sql_info.get('result', '')
                if query_result:
                    result_str = str(query_result)
                    print(f"  结果长度: {len(result_str)}")
                    if len(result_str) > 200:
                        print(f"  结果预览: {result_str[:200]}...")
                    else:
                        print(f"  结果: {result_str}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False
    finally:
        agent.close()

if __name__ == "__main__":
    success = test_coordinate_conversion()
    
    if success:
        print("\n✅ 坐标转换提示词测试完成")
    else:
        print("\n❌ 坐标转换提示词测试失败")
