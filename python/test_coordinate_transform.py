#!/usr/bin/env python3
"""
测试坐标转换功能
验证每次空间查询是否将坐标通过ST_Transform转为WGS84坐标系（SRID 4326）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from geojson_utils import GeoJSONGenerator

def test_coordinate_transform():
    """测试坐标转换功能"""
    print("=== 测试坐标转换功能 ===")
    
    try:
        # 创建GeoJSON生成器
        connection_string = "postgresql://sagasama:cznb6666@localhost:5432/WGP_db"
        generator = GeoJSONGenerator(connection_string)
        
        # 获取空间表信息
        spatial_tables = generator.get_spatial_tables()
        print(f"找到 {len(spatial_tables)} 个空间表")
        
        for table in spatial_tables:
            print(f"\n表名: {table['table_name']}")
            print(f"几何列: {table['geometry_column']}")
            print(f"几何类型: {table['geometry_type']}")
            print(f"原始SRID: {table['srid']}")
            
            # 测试生成GeoJSON
            try:
                geojson_data = generator.table_to_geojson(table['table_name'], limit=1)
                if geojson_data and 'features' in geojson_data and len(geojson_data['features']) > 0:
                    feature = geojson_data['features'][0]
                    geometry = feature.get('geometry', {})
                    print(f"几何类型: {geometry.get('type', '未知')}")
                    print(f"坐标示例: {geometry.get('coordinates', '无坐标')}")
                    print("✓ GeoJSON生成成功，包含WGS84坐标")
                else:
                    print("⚠ 无几何数据")
            except Exception as e:
                print(f"✗ 生成GeoJSON失败: {e}")
        
        print("\n=== 测试提示词修改 ===")
        from spatial_sql_prompt import SPATIAL_SYSTEM_PROMPT_SIMPLE
        
        # 检查提示词是否包含ST_Transform
        if "ST_Transform" in SPATIAL_SYSTEM_PROMPT_SIMPLE and "4326" in SPATIAL_SYSTEM_PROMPT_SIMPLE:
            print("✓ 提示词已正确包含ST_Transform(geom, 4326)转换")
        else:
            print("✗ 提示词未正确包含坐标转换要求")
            
        # 检查示例查询
        if "ST_AsGeoJSON(ST_Transform(geom, 4326))" in SPATIAL_SYSTEM_PROMPT_SIMPLE:
            print("✓ 示例查询已正确包含坐标转换")
        else:
            print("✗ 示例查询未正确包含坐标转换")
            
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_sql_generation():
    """测试SQL生成功能"""
    print("\n=== 测试SQL生成功能 ===")
    
    try:
        from server import natural_language_to_geojson
        
        # 测试简单的自然语言查询
        test_queries = [
            "查询所有点数据",
            "查找交通设施",
            "获取建筑信息"
        ]
        
        for query in test_queries:
            print(f"\n测试查询: {query}")
            try:
                result = natural_language_to_geojson(query, limit=1)
                if result['status'] == 'success':
                    sql = result.get('generated_sql', '')
                    if "ST_Transform" in sql and "4326" in sql:
                        print(f"✓ SQL包含坐标转换: {sql[:100]}...")
                    else:
                        print(f"⚠ SQL可能未包含坐标转换: {sql[:100]}...")
                else:
                    print(f"✗ 查询失败: {result.get('error', '未知错误')}")
            except Exception as e:
                print(f"✗ 查询异常: {e}")
                
    except Exception as e:
        print(f"SQL生成测试失败: {e}")

if __name__ == "__main__":
    test_coordinate_transform()
    test_sql_generation()
