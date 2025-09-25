"""
简单的空间数据库提示词测试
"""

from sql_query_agent import SQLQueryAgent

def simple_test():
    """简单的测试函数"""
    try:
        print("初始化SQL查询代理...")
        agent = SQLQueryAgent()
        print("✅ 代理初始化成功")
        
        # 测试一个简单的空间查询
        query = "查询包含几何数据的表"
        print(f"\n测试查询: {query}")
        
        result = agent.run(query)
        print(f"✅ 查询执行成功")
        print(f"结果长度: {len(result)} 字符")
        print(f"结果预览: {result[:500]}...")
        
        # 检查是否包含空间数据库相关内容
        spatial_keywords = ["geom", "geometry", "POINT", "LINESTRING", "POLYGON", "ST_", "PostGIS"]
        found_keywords = [kw for kw in spatial_keywords if kw in result]
        
        if found_keywords:
            print(f"✅ 检测到空间数据库关键词: {found_keywords}")
        else:
            print("⚠️ 未检测到空间数据库关键词")
            
        agent.close()
        print("\n✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_test()
