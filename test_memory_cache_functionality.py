#!/usr/bin/env python3
"""
测试数据库memory和cache功能
"""

import sys
import os
import json
from datetime import datetime, date

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'python', 'sight_server'))

from core.database import DatabaseConnector


def test_memory_cache_functionality():
    """测试memory和cache功能"""
    print("=== 测试数据库Memory和Cache功能 ===\n")
    
    try:
        # 创建数据库连接
        with DatabaseConnector() as db:
            print("✓ 数据库连接成功")
            
            # 测试会话ID
            session_id = "test_session_001"
            
            # 1. 测试会话历史记录
            print("\n1. 测试会话历史记录")
            history_id = db.save_conversation_history(
                session_id=session_id,
                query_text="查询武汉市的所有景点",
                query_intent={"type": "spatial_query", "location": "武汉市"},
                sql_query="SELECT * FROM tourist_spots WHERE city = '武汉'",
                result_data={"count": 25, "spots": ["黄鹤楼", "东湖"]},
                execution_time=0.45,
                status="success"
            )
            print(f"✓ 会话历史记录已保存，ID: {history_id}")
            
            # 获取会话历史
            history = db.get_conversation_history(session_id)
            print(f"✓ 获取到 {len(history)} 条会话历史记录")
            
            # 2. 测试AI上下文
            print("\n2. 测试AI上下文")
            context_id = db.save_ai_context(
                session_id=session_id,
                context_data={
                    "conversation_history": [
                        {"role": "user", "content": "查询武汉市景点"},
                        {"role": "assistant", "content": "找到25个景点"}
                    ],
                    "user_preferences": {"language": "zh-CN", "location": "武汉"}
                },
                context_type="conversation"
            )
            print(f"✓ AI上下文已保存，ID: {context_id}")
            
            # 获取AI上下文
            contexts = db.get_ai_context(session_id)
            print(f"✓ 获取到 {len(contexts)} 条AI上下文记录")
            
            # 3. 测试缓存数据
            print("\n3. 测试缓存数据")
            cache_key = "spatial_query:武汉:景点"
            cache_id = db.save_cache_data(
                cache_key=cache_key,
                cache_value={
                    "query": "SELECT * FROM tourist_spots WHERE city = '武汉'",
                    "result": {"count": 25, "spots": ["黄鹤楼", "东湖"]},
                    "timestamp": datetime.now().isoformat()
                },
                cache_type="spatial_query",
                ttl_seconds=3600  # 1小时过期
            )
            print(f"✓ 缓存数据已保存，ID: {cache_id}")
            
            # 获取缓存数据
            cached_data = db.get_cache_data(cache_key)
            if cached_data:
                print(f"✓ 缓存数据获取成功: {cached_data['cache_key']}")
            else:
                print("✗ 缓存数据获取失败")
            
            # 4. 测试会话统计
            print("\n4. 测试会话统计")
            stats = db.get_session_statistics(session_id)
            # 处理datetime序列化问题
            def json_serial(obj):
                """JSON序列化辅助函数"""
                if isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
            
            print(f"✓ 会话统计信息: {json.dumps(stats, indent=2, ensure_ascii=False, default=json_serial)}")
            
            # 5. 测试缓存清理
            print("\n5. 测试缓存清理")
            deleted_count = db.cleanup_expired_cache()
            print(f"✓ 清理了 {deleted_count} 条过期缓存记录")
            
            # 6. 测试删除缓存
            print("\n6. 测试删除缓存")
            deleted = db.delete_cache_data(cache_key)
            if deleted:
                print(f"✓ 缓存数据删除成功: {cache_key}")
            else:
                print(f"✗ 缓存数据删除失败: {cache_key}")
            
            print("\n=== 所有测试完成 ===")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_memory_cache_functionality()
