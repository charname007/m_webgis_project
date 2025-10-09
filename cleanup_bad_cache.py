#!/usr/bin/env python3
"""
清理错误缓存数据脚本
删除查询文本为缓存键的错误缓存记录
"""

import os
import sys
import json
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "python"))

from sight_server.core.database import DatabaseConnector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cleanup_bad_cache():
    """清理错误的缓存数据"""
    try:
        # 创建数据库连接
        db = DatabaseConnector()
        
        # 获取所有查询缓存
        all_caches = db.get_all_query_caches()
        
        bad_cache_count = 0
        good_cache_count = 0
        
        for cache in all_caches:
            query_text = cache.get("query_text", "")
            cache_key = cache.get("cache_key", "")
            
            # 检查查询文本是否为缓存键格式（32位十六进制字符串）
            if len(query_text) == 32 and all(c in '0123456789abcdef' for c in query_text):
                # 这是错误的缓存记录，查询文本是缓存键
                logger.warning(f"发现错误缓存记录: ID={cache.get('id')}, 查询文本='{query_text}', 缓存键='{cache_key}'")
                
                # 删除错误的缓存记录
                if db.delete_query_cache(cache_key):
                    logger.info(f"已删除错误缓存记录: {cache_key}")
                    bad_cache_count += 1
                else:
                    logger.error(f"删除缓存记录失败: {cache_key}")
            else:
                # 这是正常的缓存记录
                good_cache_count += 1
        
        logger.info(f"清理完成: 删除了 {bad_cache_count} 个错误缓存记录，保留了 {good_cache_count} 个正常缓存记录")
        
        # 关闭数据库连接
        db.close()
        
        return bad_cache_count
        
    except Exception as e:
        logger.error(f"清理缓存数据失败: {e}")
        return 0

def main():
    """主函数"""
    print("=== 清理错误缓存数据 ===")
    print("正在扫描数据库中的缓存记录...")
    
    deleted_count = cleanup_bad_cache()
    
    if deleted_count > 0:
        print(f"✓ 成功删除了 {deleted_count} 个错误缓存记录")
    else:
        print("✓ 未发现需要清理的错误缓存记录")
    
    print("清理完成！")

if __name__ == "__main__":
    main()
