#!/usr/bin/env python3
"""
调试缓存键生成问题
"""

import json
import hashlib

def debug_cache_key_generation():
    """调试缓存键生成过程"""
    print("=== 缓存键生成调试 ===\n")
    
    # 测试查询
    test_query = "武汉大学"
    
    # 不同的上下文配置
    contexts = [
        {
            "enable_spatial": False,
            "query_intent": "query", 
            "include_sql": True
        },
        {
            "enable_spatial": True,
            "query_intent": "query",
            "include_sql": True
        },
        {
            "enable_spatial": False,
            "query_intent": "summary",
            "include_sql": True
        },
        {
            "enable_spatial": False,
            "query_intent": "query",
            "include_sql": False
        }
    ]
    
    print(f"测试查询: '{test_query}'\n")
    
    for i, context in enumerate(contexts, 1):
        print(f"--- 上下文配置 {i} ---")
        print(f"  上下文: {context}")
        
        # 标准化查询文本
        normalized_query = " ".join(test_query.lower().strip().split())
        print(f"  标准化查询: '{normalized_query}'")
        
        # 构建键上下文
        key_context = {
            "query": normalized_query,
            "enable_spatial": context.get("enable_spatial", True),
            "query_intent": context.get("query_intent", "query"),
            "include_sql": context.get("include_sql", False)
        }
        
        print(f"  键上下文: {key_context}")
        
        # 排序确保一致性
        key_data = json.dumps(key_context, sort_keys=True, ensure_ascii=False)
        print(f"  排序后的键数据: {key_data}")
        
        # 生成MD5哈希
        cache_key = hashlib.md5(key_data.encode('utf-8')).hexdigest()
        print(f"  生成的缓存键: {cache_key}\n")
    
    # 检查现有缓存文件中的实际查询
    print("=== 检查现有缓存文件中的查询 ===")
    import os
    
    # 检查我们之前看到的缓存文件
    cache_file = "./cache/ae14bc7d7e2a37bd95a6158d9c124567.json"
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        print(f"缓存文件: {cache_file}")
        print(f"缓存中的查询: '{cache_data.get('query_text', 'N/A')}'")
        print(f"缓存中的意图信息: {cache_data.get('intent_info', {}).get('intent_type', 'N/A')}")
        print(f"缓存中的空间查询: {cache_data.get('intent_info', {}).get('is_spatial', 'N/A')}")

if __name__ == "__main__":
    debug_cache_key_generation()
