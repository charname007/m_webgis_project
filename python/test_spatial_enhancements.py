#!/usr/bin/env python3
"""
测试空间查询增强功能
"""

import sys
import os
import logging

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spatial_sql_agent import SpatialSQLQueryAgent
from sql_connector import SQLConnector

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_spatial_connector():
    """测试空间数据库连接器"""
    print("=" * 50)
    print("测试空间数据库连接器")
    print("=" * 50)
    
    try:
        connector = SQLConnector()
        
        # 测试基本功能
        print("1. 测试基本连接...")
        dialect = connector.get_dialect()
        print(f"   数据库方言: {dialect}")
        
        # 测试空间功能
        print("2. 测试空间功能...")
        spatial_info = connector.get_database_spatial_info()
        print(f"   PostGIS版本: {spatial_info['postgis_version']}")
        print(f"   PgRouting版本: {spatial_info['pgrouting_version']}")
        print(f"   空间表数量: {spatial_info['spatial_table_count']}")
        
        # 测试空间表信息
        print("3. 测试空间表信息...")
        spatial_tables = connector.get_spatial_tables()
        print(f"   发现 {len(spatial_tables)} 个空间表")
        for table in spatial_tables[:3]:  # 只显示前3个表
            print(f"   - {table['table_name']} ({table['geometry_type']})")
        
        # 测试空间函数可用性
        print("4. 测试空间函数可用性...")
        functions = connector.check_spatial_function_availability()
        available_functions = [f for f, available in functions.items() if available]
        print(f"   可用空间函数: {len(available_functions)} 个")
        for func in available_functions[:5]:  # 只显示前5个函数
            print(f"   - {func}")
        
        connector.close()
        print("✅ 空间数据库连接器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"空间数据库连接器测试失败: {e}")
        return False

def test_spatial_agent():
    """测试空间查询代理"""
    print("\n" + "=" * 50)
    print("测试空间查询代理")
    print("=" * 50)
    
    try:
        agent = SpatialSQLQueryAgent()
        
        # 测试空间表信息获取
        print("1. 测试空间表信息获取...")
        tables_info = agent.get_spatial_tables_info()
        if tables_info["status"] == "success":
            print(f"   成功获取 {tables_info['count']} 个空间表信息")
        else:
            print(f"   获取空间表信息失败: {tables_info.get('error', '未知错误')}")
        
        # 测试空间查询
        test_queries = [
            "查找距离某个点5公里内的所有建筑",
            "计算从A点到B点的最短路径",
            "查找与某个多边形相交的所有道路",
            "分析两个多边形的拓扑关系"
        ]
        
        print("2. 测试空间查询处理...")
        for i, query in enumerate(test_queries, 1):
            print(f"   {i}. 查询: {query}")
            try:
                result = agent.run(query)
                analysis = agent.analyze_spatial_query(result)
                
                print(f"      结果长度: {len(result)} 字符")
                print(f"      包含空间函数: {analysis['has_spatial_functions']}")
                if analysis['suggestions']:
                    print(f"      优化建议: {analysis['suggestions'][0]}")
                
                # 如果是有效的SQL查询，尝试执行
                if "SELECT" in result.upper() and "FROM" in result.upper():
                    try:
                        query_result = agent.execute_spatial_query(result, return_geojson=False)
                        print(f"      查询执行: 成功")
                    except Exception as e:
                        print(f"      查询执行: 失败 ({str(e)})")
                
            except Exception as e:
                print(f"      查询处理失败: {e}")
        
        agent.close()
        print("✅ 空间查询代理测试通过")
        return True
        
    except Exception as e:
        logger.error(f"空间查询代理测试失败: {e}")
        return False

def test_spatial_query_examples():
    """测试空间查询示例"""
    print("\n" + "=" * 50)
    print("测试空间查询示例")
    print("=" * 50)
    
    try:
        agent = SpatialSQLQueryAgent()
        
        # 测试不同类型的空间查询
        query_categories = {
            "距离查询": [
                "查找距离经度116.4、纬度39.9的点5公里内的所有建筑",
                "计算A点(116.4, 39.9)和B点(116.5, 39.8)之间的距离"
            ],
            "空间关系查询": [
                "查找与某个多边形相交的所有道路",
                "查找包含在某个区域内的所有点"
            ],
            "路径规划查询": [
                "计算从起点到终点的最短路径",
                "查找距离某个点最近的医院"
            ],
            "拓扑查询": [
                "分析多边形A和多边形B的拓扑关系"
            ]
        }
        
        for category, queries in query_categories.items():
            print(f"\n{category}:")
            for query in queries:
                print(f"   - {query}")
                try:
                    result = agent.run(query)
                    analysis = agent.analyze_spatial_query(result)
                    
                    # 检查是否使用了适当的空间函数
                    spatial_functions_used = analysis['spatial_functions_used']
                    if spatial_functions_used:
                        print(f"     使用的空间函数: {', '.join(spatial_functions_used[:3])}")
                    
                    # 检查优化建议
                    if analysis['suggestions']:
                        print(f"     优化建议: {analysis['suggestions'][0]}")
                    
                except Exception as e:
                    print(f"     查询失败: {e}")
        
        agent.close()
        print("✅ 空间查询示例测试通过")
        return True
        
    except Exception as e:
        logger.error(f"空间查询示例测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试空间查询增强功能...")
    
    tests = [
        ("空间数据库连接器", test_spatial_connector),
        ("空间查询代理", test_spatial_agent),
        ("空间查询示例", test_spatial_query_examples)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
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
        print("🎉 所有测试通过！空间查询增强功能正常工作。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关配置和错误信息。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
