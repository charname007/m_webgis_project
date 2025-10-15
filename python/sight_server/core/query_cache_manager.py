"""
查询缓存管理器模块 - Sight Server
使用分离存储方案，专门处理查询结果缓存
"""

import os
import json
import time
import hashlib
import logging
import difflib
import socket
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timedelta
from decimal import Decimal

from sympy import true
# from sentence_transformers import SentenceTransformer as ST, util as st_util

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
    """

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        return super().default(obj)


class QueryCacheManager:
    """
    查询缓存管理器（使用分离存储方案）

    功能:
    - 专门处理查询结果缓存
    - 使用 query_cache 表进行数据库存储
    - 支持文件系统缓存作为备份
    - 自动清理过期缓存
    """

    def __init__(
        self,
        cache_dir: str = "./cache",
        ttl: int = 3600,
        max_size: int = 500,  # ✅ 修改：默认缓存总量限制为500条
        # enable_database_persistence: bool = True,  # ✅ 新增：启用数据库持久化
        database_connector=None,                 # ✅ 新增：数据库连接器实例
        cache_strategy: str = "hybrid",
        enable_semantic_search: bool = True,
        similarity_threshold: float = 0.95,
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2",
        lazy_load_embedding: bool = True,        # ✅ 新增：懒加载模型
    ):
        """
        初始化查询缓存管理器（支持语义相似度搜索）

        Args:
            cache_dir: 缓存文件目录
            ttl: 缓存生存时间（秒），默认1小时
            max_size: 最大缓存条目数
            database_connector: 数据库连接器实例
            cache_strategy: 缓存策略 hybrid/db_only/file_only
            enable_semantic_search: 是否启用语义相似度搜索（✅ 新增）
            similarity_threshold: 语义相似度阈值（0-1），默认0.92（✅ 新增）
            embedding_model: Embedding模型名称（✅ 新增）
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.max_size = max_size
        self.cache_metadata_file = os.path.join(
            cache_dir, "query_cache_metadata.json")
        self.database_connector = database_connector
        self.cache_strategy = cache_strategy

        # ✅ 语义搜索配置
        self.enable_semantic_search = enable_semantic_search
        self.similarity_threshold = similarity_threshold

        # ✅ 初始化 Embedding 模型（仅在启用语义搜索时，延迟导入）
        self.embedding_model = None
        self.query_embeddings = {}  # 缓存查询向量，避免重复计算
        self.lazy_load_embedding = lazy_load_embedding
        self.embedding_model_name = embedding_model
        self.model_cache_dir = os.path.join(cache_dir, "models")

        if self.enable_semantic_search and not self.lazy_load_embedding:
            # 如果启用语义搜索且不懒加载，则立即加载模型
            self._load_embedding_model()
        elif self.enable_semantic_search:
            logger.info("✓ Embedding model will be loaded lazily when needed")

        # ✅ 新增：数据库持久化配置
        # self.enable_database_persistence = enable_database_persistence
        self.database_connector = database_connector
        self.cache_strategy = cache_strategy

        # 验证缓存策略
        valid_strategies = ["hybrid", "db_only", "file_only"]
        if self.cache_strategy not in valid_strategies:
            logger.warning(
                f"Invalid cache strategy: {self.cache_strategy}, using 'hybrid'")
            self.cache_strategy = "hybrid"

        # 检查数据库连接器
        if self.cache_strategy in ["db_only", "hybrid"] and not self.database_connector:
            logger.warning(
                "Database strategy selected but no database connector provided. Switching to file_only.")
            self.cache_strategy = "file_only"

        # 创建缓存目录
        os.makedirs(cache_dir, exist_ok=True)

        # 加载缓存元数据
        self.metadata = self._load_metadata()

        # ✅ 新增：语义搜索统计
        self.metadata["semantic_stats"] = {
            "semantic_hits": 0,
            "semantic_misses": 0,
            "last_semantic_search": None
        }

        semantic_status = "enabled" if self.enable_semantic_search else "disabled"
        lazy_status = "lazy" if self.lazy_load_embedding else "eager"
        logger.info(
            f"QueryCacheManager initialized: dir={cache_dir}, ttl={ttl}s, max_size={max_size}, strategy={self.cache_strategy}, semantic_search={semantic_status}, loading={lazy_status}")

    def _check_network_connectivity(self) -> bool:
        """检查网络连接状态"""
        try:
            socket.create_connection(
                ("huggingface.co", 443), timeout=3)  # 减少超时时间
            return True
        except:
            return False

    def _load_embedding_model_with_retry(self, embedding_model: str, cache_dir: str):
        """带重试和超时的模型加载方法"""
        import requests

        # 从环境变量获取配置
        offline_mode = os.getenv("EMBEDDING_MODEL_OFFLINE_MODE", str(
            DEFAULT_EMBEDDING_MODEL_OFFLINE_MODE)).lower() == "true"
        model_timeout = int(
            os.getenv("EMBEDDING_MODEL_TIMEOUT", DEFAULT_EMBEDDING_MODEL_TIMEOUT))
        retry_count = int(os.getenv("EMBEDDING_MODEL_RETRY_COUNT",
                          DEFAULT_EMBEDDING_MODEL_RETRY_COUNT))
        retry_delay = int(os.getenv("EMBEDDING_MODEL_RETRY_DELAY",
                          DEFAULT_EMBEDDING_MODEL_RETRY_DELAY))

        # 设置环境变量强制离线模式
        if offline_mode:
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_HUB_OFFLINE"] = "1"
            logger.info("✓ Offline mode enabled for embedding model")

        # 设置超时
        socket.setdefaulttimeout(model_timeout)

        # 创建模型缓存目录
        os.makedirs(os.path.join(cache_dir, "models"), exist_ok=True)

        for attempt in range(retry_count + 1):
            try:
                logger.info(
                    f"Loading embedding model (attempt {attempt + 1}/{retry_count + 1}): {embedding_model}")

                # 使用本地缓存目录
                # model_path = os.path.join(cache_dir, "models", 'models--sentence-transformers--'+embedding_model.replace("/", "--"))
                model_path = os.path.join(cache_dir, "models")
                # 检查本地是否已有模型（优先使用本地缓存）
                if os.path.exists(model_path):
                    logger.info(f"Using cached model from: {model_path}")
                #     # 在这个目录里找 snapshot 子目录
                #     snapshot_dir = os.path.join(model_path, "snapshots")
                #     if os.path.isdir(snapshot_dir):
                #      # 找到最新或第一个 snapshot 子目录
                #       subdirs = [d for d in os.listdir(snapshot_dir) if os.path.isdir(
                #       os.path.join(snapshot_dir, d))]
                #       if subdirs:
                #          model_path = os.path.join(snapshot_dir, subdirs[0])
                #          logger.info(f"Using cached snapshot model from: {model_path}")
                    return SentenceTransformer(model_name_or_path=embedding_model,
                                               cache_folder=model_path,
                                               local_files_only=True,                     # 强制只读本地文件
                                               )
                    # return SentenceTransformer(embedding_model)
                else:
                    # 检查网络连接，如果无网络且不是离线模式，则使用更小的模型
                    logger.info(f"Model path not found: {model_path}")
                    if not self._check_network_connectivity() and not offline_mode:
                        logger.warning(
                            "No network connectivity and offline mode not enabled, using fallback model")
                        # 尝试使用更小的本地模型作为降级方案
                        fallback_model = "all-MiniLM-L6-v2"  # 更小的模型
                        fallback_path = os.path.join(
                            cache_dir, "models", fallback_model)
                        if os.path.exists(fallback_path):
                            logger.info(
                                f"Using fallback model: {fallback_model}")
                            return SentenceTransformer(fallback_path,local_files_only=True)
                        else:
                            raise Exception(
                                "No network connectivity and no cached model available")

                    # 在线下载，但使用本地缓存
                    logger.info(f"Downloading model to cache: {model_path}")
                    return SentenceTransformer(
                        embedding_model,
                        cache_folder=os.path.join(cache_dir, "models")
                    )

            except (socket.timeout, requests.exceptions.Timeout) as e:
                logger.warning(
                    f"Model loading timeout (attempt {attempt + 1}): {e}")
                if attempt < retry_count:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise Exception(
                        f"Failed to load model after {retry_count + 1} attempts: {e}")

            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    def _initialize_embedding_model_safely(self, embedding_model: str, cache_dir: str):
        """
        安全初始化嵌入模型，处理网络异常并提供降级方案

        Args:
            embedding_model (str): 要加载的嵌入模型名称或路径
            cache_dir (str): 模型缓存目录路径

        Returns:
            Optional[Any]: 成功时返回加载的模型对象，失败时返回None并禁用语义搜索功能

        Raises:
            不直接抛出异常，但会捕获并记录以下异常情况：
            - 网络连接异常时强制进入离线模式
            - 模型加载失败时自动禁用语义搜索功能
        """
        try:
            # 检查网络连接
            if not self._check_network_connectivity():
                logger.warning("No network connectivity, forcing offline mode")
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                os.environ["HF_HUB_OFFLINE"] = "1"

            # 尝试加载模型
            model = self._load_embedding_model_with_retry(
                embedding_model, cache_dir)
            if model is None:
                logger.warning("Failed to load embedding model after retries")
                self.enable_semantic_search = False
            return model

        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")

            # 降级方案：禁用语义搜索
            self.enable_semantic_search = False
            logger.warning(
                "Semantic search disabled due to model loading failure")
            return None

    def _load_embedding_model(self):
        """加载embedding模型（懒加载或立即加载）"""
        if self.embedding_model is not None:
            return  # 模型已加载

        if not self.enable_semantic_search:
            return  # 语义搜索已禁用

        # 延迟导入 sentence-transformers
        _lazy_import_sentence_transformers()

        if SENTENCE_TRANSFORMERS_AVAILABLE and SentenceTransformer:
            try:
                # 使用改进的模型加载方法
                self.embedding_model = self._initialize_embedding_model_safely(
                    self.embedding_model_name, self.cache_dir
                )

                if self.embedding_model:
                    logger.info("✓ Embedding model loaded successfully")
                else:
                    logger.warning(
                        "Embedding model not available, semantic search disabled")
                    self.enable_semantic_search = False

            except Exception as e:
                logger.warning(
                    f"Failed to load embedding model: {e}. Semantic search disabled.")
                self.enable_semantic_search = False
        else:
            logger.warning(
                "sentence-transformers not available. Semantic search disabled. Install with: pip install sentence-transformers")
            self.enable_semantic_search = False

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
        生成查询缓存键（简化版本，只基于查询文本）

        Args:
            query: 查询文本
            context: 上下文信息（不再用于生成缓存键）

        Returns:
            缓存键（MD5哈希）
        """
        # 标准化查询文本
        normalized_query = " ".join(query.lower().strip().split())

        # 只基于查询文本生成缓存键，忽略上下文参数
        return hashlib.md5(normalized_query.encode('utf-8')).hexdigest()

    def save_query_cache(
        self,
        query_text: str,
        result_data: Dict[str, Any],
        response_time: Optional[float] = None,
        ttl_seconds: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        保存查询结果缓存到 query_cache 表

        Args:
            query_text: 查询文本
            result_data: 结果数据
            response_time: 响应时间
            ttl_seconds: 生存时间（秒）
            context: 上下文信息（可选）

        Returns:
            缓存记录ID
        """
        cache_context = context or {}
        cache_key = self.get_cache_key(query_text, cache_context)

        try:
            # ✅ 新增：检查缓存容量，如果超过限制则淘汰最近最少使用的缓存
            total_entries = len(self.metadata["cache_entries"])
            if total_entries >= self.max_size:
                self._evict_lru_entries(total_entries - self.max_size + 1)

            record_id = 0

            # 保存到数据库
            if self.cache_strategy in ["db_only", "hybrid"]:
                record_id = self.database_connector.save_query_cache(
                    cache_key=cache_key,
                    query_text=query_text,
                    result_data=result_data,
                    response_time=response_time,
                    ttl_seconds=ttl_seconds or self.ttl
                )
                logger.debug(f"查询结果缓存已保存到数据库，键: {cache_key}")

            # 保存到文件系统
            if self.cache_strategy in ["file_only", "hybrid"]:
                self._save_to_filesystem(cache_key, result_data, query_text)
                logger.debug(f"查询结果缓存已保存到文件系统，键: {cache_key}")

            return record_id

        except Exception as e:
            logger.error(f"保存查询结果缓存失败: {e}")
            raise

    def get_query_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        获取查询结果缓存

        Args:
            cache_key: 缓存键

        Returns:
            缓存结果，如果不存在或已过期则返回None
        """
        # 根据缓存策略决定获取顺序
        if self.cache_strategy == "db_only":
            # 只从数据库获取
            result = self._get_from_database(cache_key)
            if result:
                self.metadata["total_hits"] += 1
                return result
            else:
                self.metadata["total_misses"] += 1
                return None

        elif self.cache_strategy == "file_only":
            # 只从文件系统获取
            return self._get_from_filesystem(cache_key)

        else:  # hybrid 策略
            # 优先从数据库获取
            result = self._get_from_database(cache_key)
            if result:
                self.metadata["total_hits"] += 1
                # 如果文件系统没有，则同步到文件系统
                cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
                if not os.path.exists(cache_file):
                    self._save_to_filesystem(cache_key, result)
                return result

            # 数据库没有，尝试文件系统
            result = self._get_from_filesystem(cache_key)
            if result:
                # 如果数据库没有，则同步到数据库
                self._save_to_database(cache_key, result)
                return result

            # 都没有找到
            self.metadata["total_misses"] += 1
            return None

    def _get_from_database(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        从数据库获取查询结果缓存

        Args:
            cache_key: 缓存键

        Returns:
            缓存结果，如果不存在或已过期则返回None
        """
        if not self.database_connector:
            return None

        try:
            db_result = self.database_connector.get_query_cache(cache_key)
            if db_result:
                logger.debug(f"数据库查询缓存命中，键: {cache_key}")

                # ✅ 修复：正确处理 result_data 字段
                result_data = db_result.get("result_data", {})
                if isinstance(result_data, str):
                    try:
                        result_data = json.loads(result_data)
                    except json.JSONDecodeError:
                        result_data = {}
                elif not isinstance(result_data, dict):
                    result_data = {}

                # ✅ 修复：直接返回 result_data，而不是包装在 result_data 字段中
                # 这样 main.py 可以直接使用 data、answer、count 等字段
                if result_data:
                    # 添加查询文本和响应时间到结果中
                    result_data["query_text"] = db_result.get("query_text", "")
                    result_data["response_time"] = db_result.get(
                        "response_time")
                    result_data["hit_count"] = db_result.get("hit_count", 0)
                    return result_data
                else:
                    return None
            else:
                return None

        except Exception as e:
            logger.warning(f"从数据库获取查询缓存失败，键 {cache_key}: {e}")
            return None

    def _save_to_database(self, cache_key: str, result: Dict[str, Any]) -> bool:
        """
        保存查询结果缓存到数据库

        Args:
            cache_key: 缓存键
            result: 要缓存的结果

        Returns:
            是否成功
        """
        if not self.database_connector:
            return False

        try:
            self.database_connector.save_query_cache(
                cache_key=cache_key,
                query_text=result.get("query_text", ""),
                result_data=result.get("result_data", {}),
                response_time=result.get("response_time"),
                ttl_seconds=self.ttl
            )
            return True

        except Exception as e:
            logger.warning(f"保存查询缓存到数据库失败，键 {cache_key}: {e}")
            return False

    def _get_from_filesystem(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        从文件系统获取查询结果缓存

        Args:
            cache_key: 缓存键

        Returns:
            缓存结果，如果不存在或已过期则返回None
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

        if not os.path.exists(cache_file):
            return None

        try:
            # 检查是否过期
            file_mtime = os.path.getmtime(cache_file)
            if time.time() - file_mtime > self.ttl:
                logger.debug(f"文件缓存已过期，键: {cache_key}")
                self._remove_cache_file(cache_key)
                return None

            # 读取缓存文件
            with open(cache_file, 'r', encoding='utf-8') as f:
                result = json.load(f)

            # 更新元数据
            self.metadata["total_hits"] += 1
            if cache_key in self.metadata["cache_entries"]:
                self.metadata["cache_entries"][cache_key]["hit_count"] += 1
                self.metadata["cache_entries"][cache_key]["last_accessed"] = datetime.now(
                ).isoformat()
                self.metadata["cache_entries"][cache_key]["updated_at"] = datetime.now(
                ).isoformat()  # ✅ 新增：更新访问时间

            self._save_metadata()
            logger.debug(f"文件查询缓存命中，键: {cache_key}")
            return result

        except Exception as e:
            logger.error(f"读取查询缓存文件失败 {cache_file}: {e}")
            return None

    def _save_to_filesystem(self, cache_key: str, result: Dict[str, Any], query: str = "") -> bool:
        """
        保存查询结果缓存到文件系统

        Args:
            cache_key: 缓存键
            result: 要缓存的结果
            query: 原始查询

        Returns:
            是否成功
        """
        try:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")

            # 在结果中添加查询文本，确保语义搜索能正常工作
            enhanced_result = result.copy()
            enhanced_result["query_text"] = query

            # 保存缓存文件
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced_result, f, ensure_ascii=False,
                          indent=2, cls=DecimalEncoder)

            # 更新元数据 - 确保存储原始查询文本而不是哈希值
            self.metadata["cache_entries"][cache_key] = {
                "query": query,  # 存储原始查询文本
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),  # ✅ 新增：更新时间字段
                "last_accessed": datetime.now().isoformat(),
                "hit_count": 1,
                "size": len(json.dumps(enhanced_result, ensure_ascii=False, cls=DecimalEncoder))
            }

            self._save_metadata()
            logger.debug(f"文件查询缓存已保存，键: {cache_key}")
            return True

        except Exception as e:
            logger.error(f"保存查询缓存到文件系统失败，键 {cache_key}: {e}")
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
            logger.error(f"删除查询缓存文件失败，键 {cache_key}: {e}")

    def _evict_lru_entries(self, count: int = 1):
        """
        淘汰最近最少使用的缓存条目（基于updated_at字段）

        Args:
            count: 要淘汰的条目数量
        """
        if count <= 0:
            return

        logger.info(f"开始淘汰 {count} 个最近最少使用的缓存条目...")

        # 获取所有缓存条目并按updated_at排序
        cache_entries = list(self.metadata["cache_entries"].items())
        if not cache_entries:
            return

        # 按updated_at升序排序（最早的在前）
        cache_entries.sort(key=lambda x: x[1].get("updated_at", ""))

        evicted_count = 0
        for cache_key, _ in cache_entries[:count]:
            try:
                # 删除文件系统缓存
                cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
                if os.path.exists(cache_file):
                    os.remove(cache_file)

                # 删除数据库缓存
                if self.database_connector and self.cache_strategy in ["db_only", "hybrid"]:
                    self.database_connector.delete_query_cache(cache_key)

                # 从元数据中移除
                if cache_key in self.metadata["cache_entries"]:
                    del self.metadata["cache_entries"][cache_key]

                evicted_count += 1
                logger.debug(f"淘汰缓存条目: {cache_key}")

            except Exception as e:
                logger.warning(f"淘汰缓存条目失败 {cache_key}: {e}")

        logger.info(f"成功淘汰 {evicted_count} 个最近最少使用的缓存条目")
        self._save_metadata()

    def cleanup_expired_entries(self) -> int:
        """
        清理过期缓存条目

        Returns:
            清理的数量
        """
        logger.info("Cleaning up expired query cache entries...")
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

        logger.info(f"Cleaned up {removed_count} expired query cache entries")
        return removed_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息（包含语义搜索统计）

        Returns:
            缓存统计信息
        """
        total_hits = self.metadata["total_hits"]
        total_misses = self.metadata["total_misses"]
        total_requests = total_hits + total_misses

        hit_rate = (total_hits / total_requests *
                    100) if total_requests > 0 else 0

        stats = {
            "total_entries": len(self.metadata["cache_entries"]),
            "total_hits": total_hits,
            "total_misses": total_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_dir": self.cache_dir,
            "ttl_seconds": self.ttl,
            "max_size": self.max_size,
            "created_at": self.metadata["created_at"],
            "last_cleanup": self.metadata["last_cleanup"],
            "cache_strategy": self.cache_strategy
        }

        # ✅ 新增：语义搜索统计
        if self.enable_semantic_search:
            semantic_stats = self.get_semantic_search_stats()
            stats["semantic_search"] = semantic_stats

        return stats

    def clear_all(self) -> int:
        """
        清除所有缓存

        Returns:
            清除的条目数量
        """
        logger.info("Clearing all query cache entries...")
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
        logger.info(f"Cleared all {removed_count} query cache entries")
        return removed_count

    def get_with_similarity_search(
        self,
        query: str,
        context: Dict[str, Any],
        similarity_threshold: float = 0.8,
        max_results: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        基于查询相似度搜索缓存

        Args:
            query: 查询文本
            context: 上下文信息
            similarity_threshold: 相似度阈值 (0.0-1.0)
            max_results: 最大返回结果数

        Returns:
            最相似的缓存结果，如果相似度超过阈值则返回
        """
        # 首先尝试精确匹配
        cache_key = self.get_cache_key(query, context)
        exact_match = self.get_query_cache(cache_key)
        if exact_match:
            logger.info(f"精确匹配缓存命中，键: {cache_key}")
            return exact_match

        # 如果没有精确匹配，进行相似度搜索
        logger.info(f"精确匹配未命中，开始相似度搜索，阈值: {similarity_threshold}")

        # 获取所有缓存的查询
        cached_queries = self._get_all_cached_queries()
        if not cached_queries:
            return None

        # 计算相似度
        similarities = []
        for cached_query, cache_data in cached_queries.items():
            similarity = self._calculate_similarity(query, cached_query)
            # if similarity >= similarity_threshold:
            similarities.append((similarity, cached_query, cache_data))

        if similarities:
            # 按相似度排序
            similarities.sort(key=lambda x: x[0], reverse=True)
            best_match = similarities[0]
            similarity_score, matched_query, cache_data = best_match
            if similarity_score >= similarity_threshold:
                logger.info(
                    f"相似度搜索命中: '{query}' -> '{matched_query}' (相似度: {similarity_score:.2f})")

                # 返回最相似的结果
                return cache_data
            else:
                logger.info(
                    f"相似度搜索未找到匹配，最高相似度: {similarity_score}")
                return None
        else:
            logger.info(
                f"相似度搜索未找到匹配，最高相似度: {similarities[0][0] if similarities else 0}")
            return None

    def _get_all_cached_queries(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有缓存的查询

        Returns:
            查询文本到缓存数据的映射
        """
        cached_queries = {}

        # 从文件系统获取
        for cache_key, metadata in self.metadata["cache_entries"].items():
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    cached_queries[metadata["query"]] = cache_data
                except Exception as e:
                    logger.warning(f"读取缓存文件失败 {cache_file}: {e}")

        # 从数据库获取（如果支持）
        if self.database_connector and self.cache_strategy in ["db_only", "hybrid"]:
            try:
                db_caches = self.database_connector.get_all_query_caches()
                for db_cache in db_caches:
                    query_text = db_cache.get("query_text", "")
                    if query_text:
                        # 处理 result_data - 检查数据类型
                        result_data = db_cache.get("result_data", "{}")
                        if isinstance(result_data, str):
                            try:
                                result_data = json.loads(result_data)
                            except json.JSONDecodeError:
                                result_data = {}
                        elif not isinstance(result_data, dict):
                            result_data = {}

                        cached_queries[query_text] = {
                            "result_data": result_data,
                            "query_text": query_text,
                            "response_time": db_cache.get("response_time"),
                            "hit_count": db_cache.get("hit_count", 0)
                        }
            except Exception as e:
                logger.warning(f"从数据库获取所有缓存失败: {e}")

        return cached_queries

    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """
        计算两个查询的相似度

        Args:
            query1: 查询1
            query2: 查询2

        Returns:
            相似度分数 (0.0-1.0)
        """
        # 标准化查询
        normalized1 = " ".join(query1.lower().strip().split())
        normalized2 = " ".join(query2.lower().strip().split())

        # 使用 difflib 计算相似度
        similarity = difflib.SequenceMatcher(
            None, normalized1, normalized2).ratio()

        # 添加基于关键词的相似度
        words1 = set(normalized1.split())
        words2 = set(normalized2.split())

        if words1 and words2:
            jaccard_similarity = len(words1.intersection(
                words2)) / len(words1.union(words2))
            # 结合两种相似度
            combined_similarity = (similarity + jaccard_similarity) / 2
            return combined_similarity
        else:
            return similarity

    def get_similar_cache_stats(self, query: str, similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        获取相似度缓存统计信息

        Args:
            query: 查询文本
            similarity_threshold: 相似度阈值

        Returns:
            相似度缓存统计
        """
        cached_queries = self._get_all_cached_queries()
        similarities = []

        for cached_query in cached_queries.keys():
            similarity = self._calculate_similarity(query, cached_query)
            if similarity >= similarity_threshold:
                similarities.append({
                    "query": cached_query,
                    "similarity": round(similarity, 3),
                    "cache_key": self.get_cache_key(cached_query, {})
                })

        # 按相似度排序
        similarities.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "query": query,
            "similarity_threshold": similarity_threshold,
            "total_similar": len(similarities),
            "similar_queries": similarities[:10],  # 返回前10个最相似的
            "max_similarity": similarities[0]["similarity"] if similarities else 0.0
        }

    # ✅ 新增：语义相似度搜索方法

    def find_similar_query(self, query: str, context: Dict[str, Any]):
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
        if not self.enable_semantic_search:
            return None

        # 懒加载模型
        if self.embedding_model is None:
            self._load_embedding_model()

        if not self.embedding_model:
            return None

        try:
            # 1. 标准化查询文本（与 get_cache_key 一致）
            normalized_query = " ".join(query.lower().strip().split())

            # 2. 编码当前查询
            query_embedding = self.embedding_model.encode(
                normalized_query, convert_to_tensor=True)

            # 3. 遍历已缓存的查询
            best_match = None
            best_similarity = 0.0
            target_intent = context.get("query_intent", "query")
            target_spatial = context.get("enable_spatial", True)
            # 获取所有缓存的查询
            cached_queries = self._get_all_cached_queries()
            if not cached_queries:
                return None
            for cached_query, cache_data in cached_queries.items():
                # cached_query = cached_entry.get("query", "")
                # if not cached_query:
                #     continue

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
                similarity = util.cos_sim(
                    query_embedding, cached_embedding).item()

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = cached_query

            # 4. 如果相似度超过阈值，返回缓存键
            if best_match and best_similarity >= self.similarity_threshold:
                logger.info(
                    f"✓ Found similar cached query (similarity={best_similarity:.2%}): "
                    f"'{cached_query[:50]}:'{query[:50]}...'"
                )
                return (best_match, best_similarity, cache_data)

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
        cached_result = self.get_query_cache(cache_key=exact_key)

        if cached_result:
            logger.debug(f"✓ Cache HIT (exact match): {query[:50]}...")
            return cached_result

        # 2. 尝试语义匹配（仅在启用时）
        if self.enable_semantic_search:
            similar_result = self.find_similar_query(query, context)
            if similar_result:
                similar_query, similarity, similar_data = similar_result
                # cached_result = self.get_query_cache(similar_key)
                # if cached_result:
                #     logger.info(f"✓ Cache HIT (semantic match, {similarity:.2%}): {query[:50]}...")
                #     # ✅ 记录语义匹配统计
                #     self.metadata["semantic_stats"]["semantic_hits"] += 1
                #     self.metadata["semantic_stats"]["last_semantic_search"] = datetime.now().isoformat()
                #     self._save_metadata()
                #     return cached_result
                if similar_data:
                    logger.info(
                        f"✓ Cache HIT (semantic match, {similarity:.2%}): {query[:50]}...")
                    # ✅ 记录语义匹配统计
                    self.metadata["semantic_stats"]["semantic_hits"] += 1
                    self.metadata["semantic_stats"]["last_semantic_search"] = datetime.now(
                    ).isoformat()
                    self._save_metadata()
                    return similar_data

        # 3. 缓存未命中
        logger.debug(f"✗ Cache MISS: {query[:50]}...")
        self.metadata["semantic_stats"]["semantic_misses"] += 1
        self._save_metadata()
        return None

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        兼容性方法：调用 get_query_cache 方法
        确保与 cache_manager.py 的接口一致性

        Args:
            cache_key: 缓存键

        Returns:
            缓存结果，如果不存在或已过期则返回None
        """
        return self.get_query_cache(cache_key)

    def get_semantic_search_stats(self) -> Dict[str, Any]:
        """
        获取语义搜索统计信息

        Returns:
            语义搜索统计信息
        """
        semantic_stats = self.metadata["semantic_stats"]
        total_searches = semantic_stats["semantic_hits"] + \
            semantic_stats["semantic_misses"]

        semantic_hit_rate = (
            semantic_stats["semantic_hits"] / total_searches * 100) if total_searches > 0 else 0

        return {
            "enabled": self.enable_semantic_search,
            "semantic_hits": semantic_stats["semantic_hits"],
            "semantic_misses": semantic_stats["semantic_misses"],
            "semantic_hit_rate_percent": round(semantic_hit_rate, 2),
            "similarity_threshold": self.similarity_threshold,
            "last_semantic_search": semantic_stats["last_semantic_search"],
            "embedding_model_loaded": self.embedding_model is not None
        }

    def get_with_semantic_fallback(
        self,
        query: str,
        context: Dict[str, Any],
        similarity_threshold: float = 0.8,
        max_results: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存（语义搜索优先，失败时回退到相似度搜索）

        流程：
        1. 精确匹配优先（缓存键完全一致）
        2. 语义匹配兜底（相似度 > threshold）
        3. 相似度搜索回退（语义搜索不可用或未找到匹配）

        Args:
            query: 查询文本
            context: 上下文信息
            similarity_threshold: 相似度阈值 (0.0-1.0)
            max_results: 最大返回结果数

        Returns:
            缓存结果，如果不存在则返回 None
        """
        # 1. 尝试精确匹配
        cache_key = self.get_cache_key(query, context)
        exact_match = self.get_query_cache(cache_key)
        if exact_match:
            logger.info(f"精确匹配缓存命中，键: {cache_key}")
            return exact_match

        # 2. 尝试语义匹配（仅在启用时）
        if self.enable_semantic_search:
            semantic_result = self.get_with_semantic_search(query, context)
            if semantic_result:
                logger.info(f"语义搜索命中: '{query[:50]}...'")
                return semantic_result
            else:
                logger.info(f"语义搜索未命中，尝试相似度搜索回退: '{query[:50]}...'")

        # 3. 语义搜索不可用或未命中，回退到相似度搜索
        similarity_result = self.get_with_similarity_search(
            query,
            context,
            similarity_threshold=similarity_threshold,
            max_results=max_results
        )

        if similarity_result:
            logger.info(f"相似度搜索回退命中: '{query[:50]}...'")

        return similarity_result


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== 测试查询缓存管理器 ===\n")

    # 创建缓存管理器
    cache_manager = QueryCacheManager(
        cache_dir="./test_query_cache", ttl=60, max_size=10)

    # 测试1: 设置缓存
    print("--- 测试1: 设置缓存 ---")
    test_result = {"data": [1, 2, 3], "count": 3, "status": "success"}

    success = cache_manager.save_query_cache("测试查询", test_result)
    print(f"设置查询缓存: {'成功' if success else '失败'}")

    # 测试2: 获取缓存
    print("\n--- 测试2: 获取缓存 ---")
    cache_key = cache_manager.get_cache_key("测试查询", {})
    cached_result = cache_manager.get_query_cache(cache_key)
    print(f"获取查询缓存: {cached_result}")

    # 测试3: 获取统计信息
    print("\n--- 测试3: 缓存统计 ---")
    stats = cache_manager.get_cache_stats()
    print(f"查询缓存统计: {stats}")

    # 测试4: 清理缓存
    print("\n--- 测试4: 清理缓存 ---")
    cleared_count = cache_manager.clear_all()
    print(f"清理了 {cleared_count} 个查询缓存条目")
