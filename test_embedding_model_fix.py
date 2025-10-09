#!/usr/bin/env python3
"""
测试 Embedding 模型加载修复
验证新的模型加载逻辑是否解决了网络连接问题
"""

import os
import sys
import logging

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_embedding_model_loading():
    """测试 Embedding 模型加载"""
    print("=== 测试 Embedding 模型加载修复 ===\n")
    
    try:
        from sight_server.core.cache_manager import QueryCacheManager
        
        # 测试1: 默认配置
        print("--- 测试1: 默认配置 ---")
        cache_manager1 = QueryCacheManager(
            cache_dir="./test_cache_fix",
            enable_semantic_search=True,
            embedding_model="paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        print(f"语义搜索状态: {'启用' if cache_manager1.enable_semantic_search else '禁用'}")
        print(f"模型加载状态: {'成功' if cache_manager1.embedding_model else '失败'}")
        
        # 测试2: 强制离线模式
        print("\n--- 测试2: 强制离线模式 ---")
        os.environ["EMBEDDING_MODEL_OFFLINE_MODE"] = "true"
        
        cache_manager2 = QueryCacheManager(
            cache_dir="./test_cache_fix_offline",
            enable_semantic_search=True,
            embedding_model="paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        print(f"语义搜索状态: {'启用' if cache_manager2.enable_semantic_search else '禁用'}")
        print(f"模型加载状态: {'成功' if cache_manager2.embedding_model else '失败'}")
        
        # 测试3: 短超时时间
        print("\n--- 测试3: 短超时时间 ---")
        os.environ["EMBEDDING_MODEL_TIMEOUT"] = "5"
        os.environ["EMBEDDING_MODEL_RETRY_COUNT"] = "1"
        
        cache_manager3 = QueryCacheManager(
            cache_dir="./test_cache_fix_timeout",
            enable_semantic_search=True,
            embedding_model="paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        print(f"语义搜索状态: {'启用' if cache_manager3.enable_semantic_search else '禁用'}")
        print(f"模型加载状态: {'成功' if cache_manager3.embedding_model else '失败'}")
        
        # 清理环境变量
        if "EMBEDDING_MODEL_OFFLINE_MODE" in os.environ:
            del os.environ["EMBEDDING_MODEL_OFFLINE_MODE"]
        if "EMBEDDING_MODEL_TIMEOUT" in os.environ:
            del os.environ["EMBEDDING_MODEL_TIMEOUT"]
        if "EMBEDDING_MODEL_RETRY_COUNT" in os.environ:
            del os.environ["EMBEDDING_MODEL_RETRY_COUNT"]
            
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedding_model_loading()
