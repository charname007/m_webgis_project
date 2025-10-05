#!/usr/bin/env python3
"""
测试增强查询功能，验证坐标转换提示词是否被正确应用
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spatial_sql_agent import SpatialSQLQueryAgent

def test_enhanced_query():
    """测试增强查询功能"""
    print("=== 测试增强查询功能 ===")
    
    agent = SpatialSQLQueryAgent()
    
    try:
        # 测试查询空间表
        test_query = "查询whupoi表的前3条记录"
        
        print(f"原始查询: {test_query}")
        
        # 测试增强查询功能
        enhanced_query = agent._enhance_spatial_query(test_query)
        print(f"增强后的查询: {enhanced_query}")
        
        # 检查增强查询是否包含坐标转换要求
        if "ST_AsGeoJSON" in enhanced_query and "ST_Transform" in enhanced_query:
            print("✅ 增强查询包含坐标转换要求")
        else:
            print("❌ 增强查询缺少坐标转换要求")
        
        # 检查是否检测到空间表
        spatial_tables = ['whupoi', 'map_elements', 'edges', 'faces', 'place', 'county', 'state']
        has_spatial_table = any(table in test_query.lower() for table in spatial_tables)
        print(f"检测到空间表: {has_spatial_table}")
        
        # 检查是否检测到空间关键词
        spatial_keywords = [
            '距离', '附近', '周围', '范围内', '路径', '路线', '最短', '最近',
            '相交', '包含', '在内', '边界', '面积', '长度', '周长',
            '点', '线', '面', '多边形', '几何', '空间', '地理'
        ]
        has_spatial_keyword = any(keyword in test_query.lower() for keyword in spatial_keywords)
        print(f"检测到空间关键词: {has_spatial_keyword}")
        
        # 执行查询并检查结果
        print("\n执行查询...")
        result = agent.run_with_thought_chain(test_query)
        
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
        
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False
    finally:
        agent.close()

if __name__ == "__main__":
    success = test_enhanced_query()
    
    if success:
        print("\n✅ 增强查询测试完成")
    else:
        print("\n❌ 增强查询测试失败")
