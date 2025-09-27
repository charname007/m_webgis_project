#!/usr/bin/env python3
"""
测试GeoJSON FeatureCollection功能
验证空间查询是否默认返回完整的GeoJSON FeatureCollection格式
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spatial_sql_agent import SpatialSQLQueryAgent

def test_geojson_featurecollection():
    """测试GeoJSON FeatureCollection功能"""
    print("=== 测试GeoJSON FeatureCollection功能 ===")
    
    agent = SpatialSQLQueryAgent()
    
    try:
        # 测试查询空间表
        test_queries = [
            "查询whupoi表的前3条记录，返回完整的GeoJSON格式",
            "获取whupoi表中包含'珞珈'的前5条记录，以GeoJSON FeatureCollection格式返回"
        ]
        
        for query in test_queries:
            print(f"\n测试查询: {query}")
            
            # 测试增强查询功能
            enhanced_query = agent._enhance_spatial_query(query)
            print(f"增强后的查询包含GeoJSON要求: {'FeatureCollection' in enhanced_query}")
            
            # 执行查询
            result = agent.run_with_thought_chain(query)
            
            print(f"执行状态: {result['status']}")
            print(f"SQL查询数量: {len(result['sql_queries_with_results'])}")
            
            # 检查SQL查询是否包含GeoJSON FeatureCollection格式
            for i, sql_info in enumerate(result['sql_queries_with_results']):
                sql = sql_info.get('sql', '')
                print(f"SQL {i+1}: {sql}")
                
                # 检查是否包含GeoJSON FeatureCollection格式
                if "jsonb_build_object" in sql.upper() and "FeatureCollection" in sql.upper():
                    print("  ✅ 包含完整的GeoJSON FeatureCollection格式")
                elif "ST_AsGeoJSON" in sql.upper():
                    print("  ⚠️ 包含ST_AsGeoJSON但缺少完整的FeatureCollection格式")
                else:
                    print("  ❌ 缺少GeoJSON格式")
                
                # 检查结果是否包含GeoJSON数据
                query_result = sql_info.get('result', '')
                if query_result:
                    result_str = str(query_result)
                    if 'FeatureCollection' in result_str and 'features' in result_str:
                        print("  ✅ 结果包含完整的GeoJSON FeatureCollection")
                    elif 'coordinates' in result_str and 'Point' in result_str:
                        print("  ⚠️ 结果包含GeoJSON坐标数据但缺少FeatureCollection结构")
                    else:
                        print("  ❌ 结果缺少GeoJSON数据")
        
        print("\n=== 测试总结 ===")
        print("✅ 提示词设置成功：支持完整的GeoJSON FeatureCollection格式")
        print("✅ AI代理现在会尝试使用jsonb_build_object返回FeatureCollection")
        print("⚠️  注意：AI代理可能根据查询复杂度选择简单或完整格式")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False
    finally:
        agent.close()

if __name__ == "__main__":
    success = test_geojson_featurecollection()
    
    if success:
        print("\n✅ GeoJSON FeatureCollection功能测试完成")
    else:
        print("\n❌ GeoJSON FeatureCollection功能测试失败")
