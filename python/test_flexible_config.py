"""
测试灵活的空间数据库提示词配置
"""

from sql_query_agent import SQLQueryAgent
from spatial_sql_prompt import SQL_AGENT_SPATIAL_PROMPT, SpatialSQLQueryAgent

def test_flexible_config():
    """测试灵活的空间数据库提示词配置"""
    
    print("=== 测试灵活的空间数据库提示词配置 ===\n")
    
    # 测试1：使用默认提示词
    print("1. 测试默认提示词配置")
    try:
        agent_default = SQLQueryAgent()  # 不传入提示词，使用默认配置
        result = agent_default.run("查询包含几何数据的表")
        print("✅ 默认配置测试成功")
        print(f"结果预览: {result[:200]}...")
        agent_default.close()
    except Exception as e:
        print(f"❌ 默认配置测试失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试2：使用空间数据库提示词
    print("2. 测试空间数据库提示词配置")
    try:
        agent_spatial = SQLQueryAgent(system_prompt=SQL_AGENT_SPATIAL_PROMPT)
        result = agent_spatial.run("查询包含几何数据的表")
        print("✅ 空间数据库提示词配置测试成功")
        print(f"结果预览: {result[:200]}...")
        
        # 检查是否包含空间数据库相关内容
        spatial_keywords = ["geom", "geometry", "POINT", "LINESTRING", "POLYGON", "ST_", "PostGIS"]
        found_keywords = [kw for kw in spatial_keywords if kw in result]
        if found_keywords:
            print(f"✅ 检测到空间数据库关键词: {found_keywords}")
        else:
            print("⚠️ 未检测到空间数据库关键词")
            
        agent_spatial.close()
    except Exception as e:
        print(f"❌ 空间数据库提示词配置测试失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试3：使用空间数据库查询代理子类
    print("3. 测试空间数据库查询代理子类")
    try:
        agent_subclass = SpatialSQLQueryAgent()
        result = agent_subclass.run("查询包含几何数据的表")
        print("✅ 空间数据库查询代理子类测试成功")
        print(f"结果预览: {result[:200]}...")
        
        # 检查是否包含空间数据库相关内容
        spatial_keywords = ["geom", "geometry", "POINT", "LINESTRING", "POLYGON", "ST_", "PostGIS"]
        found_keywords = [kw for kw in spatial_keywords if kw in result]
        if found_keywords:
            print(f"✅ 检测到空间数据库关键词: {found_keywords}")
        else:
            print("⚠️ 未检测到空间数据库关键词")
            
        agent_subclass.close()
    except Exception as e:
        print(f"❌ 空间数据库查询代理子类测试失败: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试4：测试server.py中使用的简化提示词
    print("4. 测试简化空间提示词")
    try:
        from spatial_sql_prompt import SPATIAL_SYSTEM_PROMPT_SIMPLE
        agent_simple = SQLQueryAgent(system_prompt=SPATIAL_SYSTEM_PROMPT_SIMPLE)
        result = agent_simple.run("查询包含几何数据的表")
        print("✅ 简化空间提示词测试成功")
        print(f"结果预览: {result[:200]}...")
        
        # 检查是否包含空间数据库相关内容
        spatial_keywords = ["geom", "geometry", "POINT", "LINESTRING", "POLYGON", "ST_", "PostGIS"]
        found_keywords = [kw for kw in spatial_keywords if kw in result]
        if found_keywords:
            print(f"✅ 检测到空间数据库关键词: {found_keywords}")
        else:
            print("⚠️ 未检测到空间数据库关键词")
            
        agent_simple.close()
    except Exception as e:
        print(f"❌ 简化空间提示词测试失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_flexible_config()
