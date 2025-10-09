#!/usr/bin/env python3
"""
清理缓存元数据文件，删除错误的缓存条目
"""

import json
import os

def cleanup_metadata():
    """清理元数据文件，删除错误的缓存条目"""
    metadata_file = './cache/query_cache_metadata.json'
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print('清理前的元数据:')
        print(f'缓存条目数: {len(metadata.get("cache_entries", {}))}')
        
        # 删除所有错误的缓存条目（查询字段是哈希值的）
        cleaned_entries = {}
        for key, entry in metadata.get('cache_entries', {}).items():
            query = entry.get('query', '')
            # 如果查询字段是哈希值（32位十六进制字符串），则删除
            if len(query) == 32 and all(c in '0123456789abcdef' for c in query):
                print(f'删除错误的缓存条目: {key} -> {query}')
            else:
                cleaned_entries[key] = entry
        
        metadata['cache_entries'] = cleaned_entries
        
        # 保存清理后的元数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f'清理后的元数据:')
        print(f'缓存条目数: {len(cleaned_entries)}')
    else:
        print('元数据文件不存在')

if __name__ == "__main__":
    cleanup_metadata()
