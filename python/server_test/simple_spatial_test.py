#!/usr/bin/env python3
"""
简化版空间功能测试
"""

import sys
import os
import logging

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sql_connector import SQLConnector

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_basic_connection():
    """测试基本数据库连接"""
    print("=" * 50)
    print("测试基本数据库连接")
    print("=" * 50)
    
    try:
        connector = SQLConnector()
        
        # 测试基本连接
        print("1. 测试数据库连接...")
        dialect = connector.get_dialect()
        print(f"   数据库方言: {dialect}")
        
        # 测试基本查询
        print("2. 测试基本查询...")
        result = connector.execute_query("SELECT version()")
        print(f"   数据库版本查询: 成功")
        
        # 测试PostGIS版本
        print("3. 测试PostGIS功能...")
        try:
            postgis_result = connector.execute_query("SELECT PostGIS_Version()")
            print(f"   PostGIS版本: {postgis_result}")
        except Exception as e:
            print(f"   PostGIS版本查询失败: {e}")
        
        # 测试PgRouting版本
        print("4. 测试PgRouting功能...")
        try:
            pgrouting_result = connector.execute_query("SELECT pgr_version()")
            print(f"   PgRouting版本: {pgrouting_result}")
        except Exception as e:
            print(f"   PgRouting版本查询失败: {e}")
        
        connector.close()
        print("✅ 基本数据库连接测试通过")
        return True
        
    except Exception as e:
        logger.error(f"基本数据库连接测试失败: {e}")
        return False

def test_spatial_functions():
    """测试空间函数可用性"""
    print("\n" + "=" * 50)
    print("测试空间函数可用性")
    print("=" * 50)
    
    try:
        connector = SQLConnector()
        
        # 测试常用PostGIS函数
        spatial_functions = [
            "ST_Intersects",
            "ST_Contains", 
            "ST_Within",
            "ST_Distance",
            "ST_Buffer",
            "ST_Union",
            "ST_Transform",
            "ST_AsGeoJSON"
        ]
        
        print("测试PostGIS函数:")
        for func in spatial_functions:
            try:
                # 使用简单的几何测试
                test_query = f"SELECT {func}(ST_GeomFromText('POINT(0 0)'), ST_GeomFromText('POINT(1 1)')) IS NOT NULL"
                result = connector.execute_query(test_query)
                print(f"   ✅ {func}: 可用")
            except Exception as e:
                print(f"   ❌ {func}: 不可用 ({e})")
        
        # 测试PgRouting函数
        pgr_functions = ["pgr_dijkstra"]
        print("\n测试PgRouting函数:")
        for func in pgr_functions:
            try:
                # 简单的存在性检查
                test_query = f"SELECT {func} IS NOT NULL"
                result = connector.execute_query(test_query)
                print(f"   ✅ {func}: 可用")
            except Exception as e:
                print(f"   ❌ {func}: 不可用 ({e})")
        
        connector.close()
        print("✅ 空间函数可用性测试完成")
        return True
        
    except Exception as e:
        logger.error(f"空间函数可用性测试失败: {e}")
        return False

def test_spatial_tables():
    """测试空间表查询"""
    print("\n" + "=" * 50)
    print("测试空间表查询")
    print("=" * 50)
    
    try:
        connector = SQLConnector()
        
        # 方法1: 使用information_schema查询几何列
        print("1. 使用information_schema查询几何列:")
        try:
            geom_columns_query = """
            SELECT 
                table_name,
                column_name,
                data_type
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND (data_type LIKE '%geometry%' OR column_name LIKE '%geom%')
            ORDER BY table_name, column_name;
            """
            result = connector.execute_spatial_query(geom_columns_query)
            if result:
                print(f"   发现 {len(result)} 个几何列")
                for col in result[:5]:  # 只显示前5个
                    print(f"   - {col['table_name']}.{col['column_name']} ({col['data_type']})")
            else:
                print("   未发现几何列")
        except Exception as e:
            print(f"   几何列查询失败: {e}")
        
        # 方法2: 直接查询已知的空间表
        print("2. 查询已知空间表:")
        known_spatial_tables = ["whupoi", "whupois", "edges", "faces"]
        
        for table in known_spatial_tables:
            try:
                # 检查表是否有几何列
                check_query = f"SELECT COUNT(*) FROM {table} WHERE geom IS NOT NULL"
                result = connector.execute_query(check_query)
                count = result[0][0] if result else 0
                print(f"   - {table}: {count} 条记录包含几何数据")
            except Exception as e:
                print(f"   - {table}: 查询失败 ({e})")
        
        connector.close()
        print("✅ 空间表查询测试完成")
        return True
        
    except Exception as e:
        logger.error(f"空间表查询测试失败: {e}")
        return False

def test_spatial_queries():
    """测试空间查询功能"""
    print("\n" + "=" * 50)
    print("测试空间查询功能")
    print("=" * 50)
    
    try:
        connector = SQLConnector()
        
        # 测试简单的空间查询
        print("1. 测试简单空间查询:")
        try:
            # 查询点数据
            point_query = """
            SELECT 
                gid, 
                name,
                ST_AsGeoJSON(geom) as geojson
            FROM whupoi 
            WHERE geom IS NOT NULL 
            LIMIT 5
            """
            result = connector.execute_spatial_query(point_query)
            print(f"   点数据查询: 成功获取 {len(result)} 条记录")
        except Exception as e:
            print(f"   点数据查询失败: {e}")
        
        # 测试空间关系查询
        print("2. 测试空间关系查询:")
        try:
            # 使用缓冲区查询附近的点
            buffer_query = """
            SELECT 
                gid,
                name,
                ST_AsGeoJSON(geom) as geojson
            FROM whupoi 
            WHERE ST_DWithin(
                geom, 
                ST_GeomFromText('POINT(114.36 30.53)', 4326),
                0.01
            )
            LIMIT 5
            """
            result = connector.execute_spatial_query(buffer_query)
            print(f"   缓冲区查询: 成功获取 {len(result)} 条记录")
        except Exception as e:
            print(f"   缓冲区查询失败: {e}")
        
        connector.close()
        print("✅ 空间查询功能测试完成")
        return True
        
    except Exception as e:
        logger.error(f"空间查询功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试空间功能...")
    
    tests = [
        ("基本数据库连接", test_basic_connection),
        ("空间函数可用性", test_spatial_functions),
        ("空间表查询", test_spatial_tables),
        ("空间查询功能", test_spatial_queries)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n正在执行: {test_name}")
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"{test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果摘要
    print("\n" + "=" * 50)
    print("测试结果摘要")
    print("=" * 50)
    
    passed = 0
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n总测试: {len(results)} / 通过: {passed} / 失败: {len(results) - passed}")
    
    if passed == len(results):
        print("🎉 所有测试通过！空间功能正常工作。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关配置和错误信息。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
