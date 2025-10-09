#!/usr/bin/env python3
"""
最终测试缓存类型修复脚本
验证查询结果缓存和模式学习缓存的数据混淆问题是否已解决
"""

import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python', 'sight_server'))

def test_cache_type_separation():
    """直接测试缓存类型分离"""
    print("=== 测试缓存类型分离 ===")
    
    try:
        # 直接导入数据库连接器
        from core.database import DatabaseConnector
        db_connector = DatabaseConnector()
        
        # 测试查询结果缓存类型
        test_query_cache_key = "test_query_cache_key_123"
        test_query_data = {
            "result": {"data": "test_query_result"},
            "query": "测试查询",
            "cache_key": test_query_cache_key,
            "created_at": datetime.now().isoformat()
        }
        
        # 保存查询结果缓存
        query_success = db_connector.save_cache_data(
            cache_key=test_query_cache_key,
            cache_value=test_query_data,
            cache_type="query_result",
            ttl_seconds=3600
        )
        print(f"查询结果缓存保存: {'成功' if query_success else '失败'}")
        
        # 测试模式学习缓存类型
        test_pattern_cache_key = "success_pattern:测试 + 模式 + 学习"
        test_pattern_data = {
            "query_template": "测试 + 模式 + 学习",
            "sql_template": "SELECT * FROM test_table",
            "success": True,
            "result_count": 1,
            "response_time": 0.5,
            "learned_at": datetime.now().isoformat()
        }
        
        # 保存模式学习缓存
        pattern_success = db_connector.save_cache_data(
            cache_key=test_pattern_cache_key,
            cache_value=test_pattern_data,
            cache_type="success_pattern",
            ttl_seconds=86400
        )
        print(f"模式学习缓存保存: {'成功' if pattern_success else '失败'}")
        
        # 验证缓存类型
        query_cache = db_connector.get_cache_data(test_query_cache_key)
        pattern_cache = db_connector.get_cache_data(test_pattern_cache_key)
        
        query_type = query_cache.get("cache_type", "unknown") if query_cache else "not_found"
        pattern_type = pattern_cache.get("cache_type", "unknown") if pattern_cache else "not_found"
        
        print(f"查询结果缓存类型: {query_type}")
        print(f"模式学习缓存类型: {pattern_type}")
        
        # 验证分离是否成功
        if query_type == "query_result" and pattern_type == "success_pattern":
            print("✅ 缓存类型分离成功！")
            success = True
        else:
            print("❌ 缓存类型分离失败！")
            success = False
        
        # 清理测试数据
        db_connector.delete_cache_data(test_query_cache_key)
        db_connector.delete_cache_data(test_pattern_cache_key)
        
        return success
            
    except Exception as e:
        print(f"测试缓存类型分离失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试缓存类型修复...")
    success = test_cache_type_separation()
    print("\n=== 测试总结 ===")
    if success:
        print("✅ 缓存类型修复测试通过！")
        print("   查询结果缓存和模式学习缓存已正确分离")
    else:
        print("❌ 缓存类型修复测试失败！")
        print("   需要进一步检查缓存类型设置")

if __name__ == "__main__":
    main()
