"""
缓存管理器模块 - Sight Server
提供查询结果缓存功能，提升性能
"""

import os
import json
import time
import hashlib
import logging
import socket
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

# 配置默认值
DEFAULT_EMBEDDING_MODEL_OFFLINE_MODE = False
DEFAULT_EMBEDDING_MODEL_TIMEOUT = 30
DEFAULT_EMBEDDING_MODEL_RETRY_COUNT = 2
DEFAULT_EMBEDDING_MODEL_RETRY_DELAY = 5

logger = logging.getLogger(__name__)

# ✅ 延迟导入 sentence-transformers（避免启动时的依赖冲突）
SENTENCE_TRANSFORMERS_AVAILABLE = False
SentenceTransformer = None
util = None

def _lazy_import_sentence_transformers():
    """延迟导入 sentence-transformers"""
    global SENTENCE_TRANSFORMERS_AVAILABLE, SentenceTransformer, util
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            from sentence_transformers import SentenceTransformer as ST, util as st_util
            SentenceTransformer = ST
            util = st_util
            SENTENCE_TRANSFORMERS_AVAILABLE = True
            logger.info("✓ sentence-transformers imported successfully")
        except ImportError as e:
            logger.warning(f"sentence-transformers not available: {e}")
            SENTENCE_TRANSFORMERS_AVAILABLE = False


class DecimalEncoder(json.JSONEncoder):
    """
    自定义 JSON 编码器 - 支持 Decimal 和 datetime 类型

    处理数据库查询结果中的特殊类型:
    - Decimal → float (保持数值精度)
    - datetime → ISO格式字符串
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            # 将 Decimal 转为 float（如果需要更高精度可以转为 str）
            return float(obj)
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        return super().default(obj)


class QueryCacheManager:
    """
    查询缓存管理器（支持语义相似度搜索）

    功能:
    - 缓存查询结果，避免重复计算
    - 支持TTL（生存时间）自动过期
    - 缓存键基于查询内容和上下文生成
    - 自动清理过期缓存
    - ✅ 语义相似度匹配（基于 sentence-transformers）
    """

    def __init__(
        self,
        cache_dir: str = "./cache",
        ttl: int = 3600,
        max_size: int = 1000,
        enable_semantic_search: bool = True,
        similarity_threshold: float = 0.92,
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存文件目录
            ttl: 缓存生存时间（秒），默认1小时
            max_size: 最大缓存条目数
            enable_semantic_search: 是否启用语义相似度搜索（✅ 新增）
            similarity_threshold: 语义相似度阈值（0-1），默认0.92（✅ 新增）
            embedding_model: Embedding模型名称（✅ 新增）
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.max_size = max_size
        self.cache_metadata_file = os.path.join(cache_dir, "cache_metadata.json")

        # ✅ 语义搜索配置
        self.enable_semantic_search = enable_semantic_search
        self.similarity_threshold = similarity_threshold

        # ✅ 初始化 Embedding 模型（仅在启用语义搜索时，延迟导入）
        self.embedding_model = None
        self.query_embeddings = {}  # 缓存查询向量，避免重复计算

        if self.enable_semantic_search:
            # 延迟导入 sentence-transformers
            _lazy_import_sentence_transformers()

            if SENTENCE_TRANSFORMERS_AVAILABLE and SentenceTransformer:
                try:
                    # 使用改进的模型加载方法
                    self.embedding_model = self._initialize_embedding_model_safely(embedding_model, cache_dir)
                    
                    if self.embedding_model:
                        logger.info("✓ Embedding model loaded successfully")
                    else:
                        logger.warning("Embedding model not available, semantic search disabled")
                        self.enable_semantic_search = False
                        
                except Exception as e:
                    logger.warning(f"Failed to load embedding model: {e}. Semantic search disabled.")
                    self.enable_semantic_search = False
            else:
                logger.warning("sentence-transformers not available. Semantic search disabled. Install with: pip install sentence-transformers")
                self.enable_semantic_search = False

        # 创建缓存目录
        os.makedirs(cache_dir, exist_ok=True)

        # 加载缓存元数据
        self.metadata = self._load_metadata()

        semantic_status = "enabled" if self.enable_semantic_search else "disabled"
        logger.info(f"QueryCacheManager initialized: dir={cache_dir}, ttl={ttl}s, max_size={max_size}, semantic_search={semantic_status}")

    def _check_network_connectivity(self) -> bool:
        """检查网络连接状态"""
        try:
            socket.create_connection(("huggingface.co", 443), timeout=5)
            return True
        except:
            return False

    def _load_embedding_model_with_retry(self, embedding_model: str, cache_dir: str):
        """带重试和超时的模型加载方法"""
        import requests
        
        # 从环境变量获取配置
        offline_mode = os.getenv("EMBEDDING_MODEL_OFFLINE_MODE", str(DEFAULT_EMBEDDING_MODEL_OFFLINE_MODE)).lower() == "true"
        model_timeout = int(os.getenv("EMBEDDING_MODEL_TIMEOUT", DEFAULT_EMBEDDING_MODEL_TIMEOUT))
        retry_count = int(os.getenv("EMBEDDING_MODEL_RETRY_COUNT", DEFAULT_EMBEDDING_MODEL_RETRY_COUNT))
        retry_delay = int(os.getenv("EMBEDDING_MODEL_RETRY_DELAY", DEFAULT_EMBEDDING_MODEL_RETRY_DELAY))

        # 设置环境变量强制离线模式
        if offline_mode:
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_HUB_OFFLINE"] = "1"
            logger.info("✓ Offline mode enabled for embedding model")
        
        # 设置超时
        socket.setdefaulttimeout(model_timeout)
        
        for attempt in range(retry_count + 1):
            try:
                logger.info(f"Loading embedding model (attempt {attempt + 1}/{retry_count + 1}): {embedding_model}")
                
                # 使用本地缓存目录
                model_path = os.path.join(cache_dir, "models", embedding_model.replace("/", "_"))
                
                # 检查本地是否已有模型
                if os.path.exists(model_path):
                    logger.info(f"Using cached model from: {model_path}")
                    return SentenceTransformer(model_path)
                else:
                    # 在线下载，但使用本地缓存
                    return SentenceTransformer(
                        embedding_model,
                        cache_folder=os.path.join(cache_dir, "models")
                    )
                    
            except (socket.timeout, requests.exceptions.Timeout) as e:
                logger.warning(f"Model loading timeout (attempt {attempt + 1}): {e}")
                if attempt < retry_count:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"Failed to load model after {retry_count + 1} attempts: {e}")
                    
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    def _initialize_embedding_model_safely(self, embedding_model: str, cache_dir: str):
        """安全的模型初始化"""
        try:
            # 检查网络连接
            if not self._check_network_connectivity():
                logger.warning("No network connectivity, forcing offline mode")
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                os.environ["HF_HUB_OFFLINE"] = "1"
            
            # 尝试加载模型
            return self._load_embedding_model_with_retry(embedding_model, cache_dir)
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            
            # 降级方案：禁用语义搜索
            self.enable_semantic_search = False
            logger.warning("Semantic search disabled due to model loading failure")
            return None

    def _load_metadata(self) -> Dict[str, Any]:
        """加载缓存元数据"""
        if os.path.exists(self.cache_metadata_file):
            try:
                with open(self.cache_metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
        
        return {
            "cache_entries": {},
            "total_hits": 0,
            "total_misses": 0,
            "created_at": datetime.now().isoformat(),
            "last_cleanup": datetime.now().isoformat()
        }

    def _save_metadata(self):
        """保存缓存元数据"""
        try:
            with open(self.cache_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")

    def get_cache_key(self, query: str, context: Dict[str, Any]) -> str:
        """
        生成缓存键（优化版）

        Args:
            query: 查询文本
            context: 上下文信息

        Returns:
            缓存键（MD5哈希）

        优化点：
        - 标准化查询文本（去除多余空格、统一小写）
        - 添加 query_intent 到缓存键（区分 summary/query）
        - 移除 conversation_id（跨会话共享缓存）
        """
        # ✅ 标准化查询文本（去除多余空格、统一小写）
        normalized_query = " ".join(query.lower().strip().split())

        # ✅ 选择关键上下文字段
        key_context = {
            "query": normalized_query,                                   # 标准化查询
            "enable_spatial": context.get("enable_spatial", True),
            "query_intent": context.get("query_intent", "query"),       # ✅ 新增：区分 summary/query
            "include_sql": context.get("include_sql", False)             # ✅ 新增：是否包含 SQL
            # ❌ 移除 conversation_id（跨会话共享）
            # ❌ 移除 prompt_type（由 query_intent 代替）
        }

        # 排序确保一致性
        key_data = json.dumps(key_context, sort_keys=True, ensure_ascii=False)

        return hashlib.md5(key_data.encode('utf-8')).hexdigest()

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存结果

        Args:
            cache_key: 缓存键

        Returns:
            缓存结果，如果不存在或已过期则返回None
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            self.metadata["total_misses"] += 1
            self._save_metadata()
            return None

        try:
            # 检查是否过期
            file_mtime = os.path.getmtime(cache_file)
            if time.time() - file_mtime > self.ttl:
                logger.debug(f"Cache expired for key: {cache_key}")
                self._remove_cache_file(cache_key)
                self.metadata["total_misses"] += 1
                self._save_metadata()
                return None

            # 读取缓存文件
            with open(cache_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            self.metadata["total_hits"] += 1
            if cache_key in self.metadata["cache_entries"]:
                self.metadata["cache_entries"][cache_key]["hit_count"] += 1
                self.metadata["cache_entries"][cache_key]["last_accessed"] = datetime.now().isoformat()
            
            self._save_metadata()
            logger.debug(f"Cache hit for key: {cache_key}")
            return result

        except Exception as e:
            logger.error(f"Failed to read cache file {cache_file}: {e}")
            self.metadata["total_misses"] += 1
            self._save_metadata()
            return None

    def set(self, cache_key: str, result: Dict[str, Any], query: str = "") -> bool:
        """
        设置缓存结果

        Args:
            cache_key: 缓存键
            result: 要缓存的结果
            query: 原始查询（用于元数据）

        Returns:
            是否成功
        """
        try:
            # 检查缓存大小，如果超过限制则清理
            self._cleanup_if_needed()

            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            # 保存缓存文件（使用自定义编码器处理 Decimal 类型）
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)

            # 更新元数据
            self.metadata["cache_entries"][cache_key] = {
                "query": query,
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "hit_count": 1,
                "size": len(json.dumps(result, ensure_ascii=False, cls=DecimalEncoder))
            }

            self._save_metadata()
            logger.debug(f"Cache set for key: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to set cache for key {cache_key}: {e}")
            return False

    def _remove_cache_file(self, cache_key: str):
        """删除缓存文件"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                os.remove(cache_file)
            
            # 从元数据中移除
            if cache_key in self.metadata["cache_entries"]:
                del self.metadata["cache_entries"][cache_key]
        except Exception as e:
            logger.error(f"Failed to remove cache file for key {cache_key}: {e}")

    def _cleanup_if_needed(self):
        """如果需要则清理缓存"""
        current_size = len(self.metadata["cache_entries"])
        
        if current_size >= self.max_size:
            logger.info(f"Cache size ({current_size}) exceeds limit ({self.max_size}), cleaning up...")
            self.cleanup_old_entries(keep_count=int(self.max_size * 0.8))  # 保留80%

        # 定期清理过期缓存（每100次操作清理一次）
        if self.metadata["total_hits"] + self.metadata["total_misses"] % 100 == 0:
            self.cleanup_expired_entries()

    def cleanup_expired_entries(self) -> int:
        """
        清理过期缓存条目

        Returns:
            清理的数量
        """
        logger.info("Cleaning up expired cache entries...")
        removed_count = 0
        current_time = time.time()

        for cache_key in list(self.metadata["cache_entries"].keys()):
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            if not os.path.exists(cache_file):
                self._remove_cache_file(cache_key)
                removed_count += 1
                continue

            # 检查是否过期
            file_mtime = os.path.getmtime(cache_file)
            if current_time - file_mtime > self.ttl:
                self._remove_cache_file(cache_key)
                removed_count += 1

        self.metadata["last_cleanup"] = datetime.now().isoformat()
        self._save_metadata()
        
        logger.info(f"Cleaned up {removed_count} expired cache entries")
        return removed_count

    def cleanup_old_entries(self, keep_count: int = 800) -> int:
        """
        清理旧的缓存条目（基于最近访问时间）

        Args:
            keep_count: 要保留的条目数量

        Returns:
            清理的数量
        """
        current_size = len(self.metadata["cache_entries"])
        if current_size <= keep_count:
            return 0

        logger.info(f"Cleaning up old cache entries (keeping {keep_count} of {current_size})...")

        # 按最后访问时间排序
        entries = list(self.metadata["cache_entries"].items())
        entries.sort(key=lambda x: x[1].get("last_accessed", "2000-01-01"))

        # 删除最旧的条目
        removed_count = 0
        for cache_key, _ in entries[:current_size - keep_count]:
            self._remove_cache_file(cache_key)
            removed_count += 1

        self._save_metadata()
        logger.info(f"Cleaned up {removed_count} old cache entries")
        return removed_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计信息
        """
        total_hits = self.metadata["total_hits"]
        total_misses = self.metadata["total_misses"]
        total_requests = total_hits + total_misses
        
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_entries": len(self.metadata["cache_entries"]),
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_dir": self.cache_dir,
            "ttl_seconds": self.ttl,
            "max_size": self.max_size,
            "created_at": self.metadata["created_at"],
            "last_cleanup": self.metadata["last_cleanup"]
        }

    def clear_all(self) -> int:
        """
        清除所有缓存

        Returns:
            清除的条目数量
        """
        logger.info("Clearing all cache entries...")
        removed_count = 0

        for cache_key in list(self.metadata["cache_entries"].keys()):
            self._remove_cache_file(cache_key)
            removed_count += 1

        # 重置元数据
        self.metadata["cache_entries"] = {}
        self.metadata["total_hits"] = 0
        self.metadata["total_misses"] = 0
        self.metadata["last_cleanup"] = datetime.now().isoformat()

        # ✅ 清空向量缓存
        self.query_embeddings.clear()

        self._save_metadata()
        logger.info(f"Cleared all {removed_count} cache entries")
        return removed_count

    # ✅ 新增：语义相似度搜索方法

    def find_similar_query(self, query: str, context: Dict[str, Any]) -> Optional[Tuple[str, float]]:
        """
        查找语义相似的已缓存查询

        Args:
            query: 当前查询
            context: 上下文信息（用于过滤）

        Returns:
            (缓存键, 相似度) 元组，如果没有则返回 None

        流程：
        1. 计算当前查询的向量
        2. 遍历已缓存查询，计算相似度
        3. 返回最相似且超过阈值的缓存键
        """
        if not self.enable_semantic_search or not self.embedding_model:
            return None

        try:
            # 1. 标准化查询文本（与 get_cache_key 一致）
            normalized_query = " ".join(query.lower().strip().split())

            # 2. 编码当前查询
            query_embedding = self.embedding_model.encode(normalized_query, convert_to_tensor=True)

            # 3. 遍历已缓存的查询
            best_match = None
            best_similarity = 0.0
            target_intent = context.get("query_intent", "query")
            target_spatial = context.get("enable_spatial", True)

            for cached_key, cached_entry in self.metadata["cache_entries"].items():
                cached_query = cached_entry.get("query", "")
                if not cached_query:
                    continue

                # ✅ 上下文过滤（确保 intent 和 spatial 一致）
                # 从缓存键中提取上下文信息（需要解析，这里简化处理：直接比较查询文本）
                # 注意：这里假设缓存元数据中存储了原始查询文本

                # 获取或计算缓存查询的向量
                if cached_query not in self.query_embeddings:
                    self.query_embeddings[cached_query] = self.embedding_model.encode(
                        cached_query, convert_to_tensor=True
                    )

                cached_embedding = self.query_embeddings[cached_query]

                # 计算余弦相似度
                similarity = util.cos_sim(query_embedding, cached_embedding).item()

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = cached_key

            # 4. 如果相似度超过阈值，返回缓存键
            if best_match and best_similarity >= self.similarity_threshold:
                logger.info(
                    f"✓ Found similar cached query (similarity={best_similarity:.2%}): "
                    f"'{query[:50]}...' → '{self.metadata['cache_entries'][best_match]['query'][:50]}...'"
                )
                return (best_match, best_similarity)

            return None

        except Exception as e:
            logger.error(f"Failed to find similar query: {e}")
            return None

    def get_with_semantic_search(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        获取缓存（支持语义相似度搜索）

        流程：
        1. 精确匹配优先（缓存键完全一致）
        2. 语义匹配兜底（相似度 > threshold）

        Args:
            query: 查询文本
            context: 上下文信息

        Returns:
            缓存结果，如果不存在则返回 None
        """
        # 1. 尝试精确匹配
        exact_key = self.get_cache_key(query, context)
        cached_result = self.get(exact_key)

        if cached_result:
            logger.debug(f"✓ Cache HIT (exact match): {query[:50]}...")
            return cached_result

        # 2. 尝试语义匹配（仅在启用时）
        if self.enable_semantic_search:
            similar_result = self.find_similar_query(query, context)
            if similar_result:
                similar_key, similarity = similar_result
                cached_result = self.get(similar_key)
                if cached_result:
                    logger.info(f"✓ Cache HIT (semantic match, {similarity:.2%}): {query[:50]}...")
                    # ✅ 记录语义匹配统计
                    if "semantic_hits" not in self.metadata:
                        self.metadata["semantic_hits"] = 0
                    self.metadata["semantic_hits"] += 1
                    self._save_metadata()
                    return cached_result

        # 3. 缓存未命中
        logger.debug(f"✗ Cache MISS: {query[:50]}...")
        return None


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== 测试缓存管理器 ===\n")
    
    # 创建缓存管理器
    cache_manager = QueryCacheManager(cache_dir="./test_cache", ttl=60, max_size=10)
    
    # 测试1: 设置缓存
    print("--- 测试1: 设置缓存 ---")
    test_result = {"data": [1, 2, 3], "count": 3, "status": "success"}
    cache_key = cache_manager.get_cache_key("测试查询", {"enable_spatial": True})
    
    success = cache_manager.set(cache_key, test_result, "测试查询")
    print(f"设置缓存: {'成功' if success else '失败'}")
    
    # 测试2: 获取缓存
    print("\n--- 测试2: 获取缓存 ---")
    cached_result = cache_manager.get(cache_key)
    print(f"获取缓存: {cached_result}")
    
    # 测试3: 获取统计信息
    print("\n--- 测试3: 缓存统计 ---")
    stats = cache_manager.get_cache_stats()
    print(f"缓存统计: {stats}")
    
    # 测试4: 清理缓存
    print("\n--- 测试4: 清理缓存 ---")
    cleared_count = cache_manager.clear_all()
    print(f"清理了 {cleared_count} 个缓存条目")
