"""
测试空间数据库和PostGIS提示词配置
"""

import sys
import os
from sql_query_agent import SQLQueryAgent

def test_spatial_prompt():
    """测试空间数据库提示词配置"""
    try:
        print("正在初始化SQL查询代理...")
        agent = SQLQueryAgent()
        print("✅ SQL查询代理初始化成功")
        
        # 测试简单的空间查询
        test_queries = [
            "查询所有的点数据",
            "查找距离某个点1000米范围内的所有要素",
            "查询包含几何数据的表",
            "生成一个包含ST_AsGeoJSON的查询"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- 测试查询 {i}: {query} ---")
            try:
                result = agent.run(query)
                print(f"✅ 查询执行成功")
                print(f"结果长度: {len(result)} 字符")
                print(f"结果预览: {result[:200]}...")
                
                # 检查结果中是否包含PostGIS相关关键词
                postgis_keywords = ["ST_AsGeoJSON", "geom", "ST_Distance", "ST_Intersects", "POINT", "LINESTRING", "POLYGON"]
                found_keywords = [kw for kw in postgis_keywords if kw in result]
                if found_keywords:
                    print(f"✅ 检测到PostGIS关键词: {found_keywords}")
                else:
                    print("⚠️ 未检测到PostGIS关键词")
                    
            except Exception as e:
                print(f"❌ 查询执行失败: {e}")
        
        agent.close()
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_spatial_prompt()
