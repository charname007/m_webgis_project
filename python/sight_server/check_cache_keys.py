#!/usr/bin/env python3
"""
检查缓存键生成和匹配问题
"""

import hashlib
import json
import os

def check_cache_keys():
    """检查缓存键生成和匹配问题"""
    print("=== 检查缓存键生成和匹配问题 ===\n")
    
    # 测试不同的查询文本生成什么缓存键
    test_queries = ['武汉大学', '武汉大学 ', '武汉大学  ', '武汉大学\n', '武汉大学\t']
    
    print("=== 不同查询文本的缓存键生成 ===")
    for query in test_queries:
        normalized = ' '.join(query.lower().strip().split())
        cache_key = hashlib.md5(normalized.encode('utf-8')).hexdigest()
        print(f'查询: {repr(query)} -> 标准化: {repr(normalized)} -> 缓存键: {cache_key}')
    
    # 检查现有缓存文件中的查询文本
    print("\n=== 检查现有缓存文件中的查询文本 ===")
    
    # 检查我们之前看到的缓存文件
    cache_file = './cache/ae14bc7d7e2a37bd95a6158d9c124567.json'
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        print(f'缓存文件: {cache_file}')
        print(f'缓存中的查询文本: {repr(cache_data.get("query_text", "N/A"))}')
        print(f'缓存元数据中的查询: {repr(cache_data.get("query", "N/A"))}')
        
        # 检查元数据文件
        metadata_file = './cache/query_cache_metadata.json'
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            print(f'\n元数据中的缓存条目:')
            for key, entry in metadata.get('cache_entries', {}).items():
                print(f'  缓存键: {key} -> 查询: {repr(entry.get("query", "N/A"))}')

if __name__ == "__main__":
    check_cache_keys()
