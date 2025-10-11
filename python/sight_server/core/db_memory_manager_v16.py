
import json
import logging
import os
import socket
import time
from typing import Any, Dict, List, Optional, Tuple

from .database import DatabaseConnector

# 配置默认值
DEFAULT_EMBEDDING_MODEL_OFFLINE_MODE = False
DEFAULT_EMBEDDING_MODEL_TIMEOUT = 30
DEFAULT_EMBEDDING_MODEL_RETRY_COUNT = 2
DEFAULT_EMBEDDING_MODEL_RETRY_DELAY = 5

logger = logging.getLogger(__name__)

# ✅ 延迟导入 sentence-transformers
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
            logger.info("✓ sentence-transformers imported successfully for DbMemoryManager")
        except ImportError as e:
            logger.warning(f"sentence-transformers not available for DbMemoryManager: {e}")
            SENTENCE_TRANSFORMERS_AVAILABLE = False

class DbMemoryManager:
    """
    通过 PostgreSQL 管理代理的长期知识库 (V16)。
    - 使用 pgvector 进行高效的语义相似度搜索。
    - 集成真实的 sentence-transformers 模型加载逻辑。
    """

    def __init__(
        self,
        db_connector: DatabaseConnector,
        embedding_model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        cache_dir: str = "./cache",
    ):
        """
        初始化 DbMemoryManager。

        Args:
            db_connector: DatabaseConnector 的实例。
            embedding_model_name: 用于生成嵌入的 SentenceTransformer 模型。
            cache_dir: 用于存储下载的 embedding 模型的目录。
        """
        self.db = db_connector
        self.embedding_model = None

        # 延迟导入并安全地初始化模型
        _lazy_import_sentence_transformers()
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = self._initialize_embedding_model_safely(
                    embedding_model_name, cache_dir
                )
                if self.embedding_model:
                    logger.info(f"✓ DbMemoryManager: Embedding model '{embedding_model_name}' loaded successfully.")
                else:
                    logger.warning("DbMemoryManager: Embedding model not available, semantic search will be disabled.")
            except Exception as e:
                logger.error(f"DbMemoryManager: Failed to load embedding model: {e}. Semantic search disabled.", exc_info=True)
        else:
            logger.warning("DbMemoryManager: sentence-transformers not installed. Semantic search disabled. Please run 'pip install sentence-transformers'.")

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        使用真实的 sentence-transformer 模型为给定文本生成 embedding。

        Args:
            text: 输入文本。

        Returns:
            表示 embedding 的浮点数列表，如果模型不可用则返回 None。
        """
        if not self.embedding_model:
            return None
        try:
            # 标准化文本以获得更好的嵌入效果
            normalized_text = " ".join(text.lower().strip().split())
            embedding = self.embedding_model.encode(normalized_text)
            # pgvector 需要一个 numpy 数组或列表
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: '{text[:50]}...'", exc_info=True)
            return None

    def find_similar_knowledge(self, query: str, similarity_threshold: float = 0.85, top_k: int = 3) -> Optional[List[Dict[str, Any]]]:
        """
        在数据库中查找与给定查询语义相似的知识点。
        使用 pgvector 的 <=> (cosine distance) 操作符。

        Args:
            query: 用户查询。
            similarity_threshold: 相似度阈值 (余弦相似度)。
            top_k: 返回最相似结果的数量。

        Returns:
            一个包含相似知识点的字典列表，如果没有找到则返回 None。
        """
        embedding = self._get_embedding(query)
        if embedding is None:
            logger.warning("Cannot perform similarity search because embedding model is not available.")
            return None

        try:
            # 余弦距离从0(相同)到2(相反)。相似度 = 1 - 余弦距离。
            # 所以，距离 < (1 - 相似度阈值)
            distance_threshold = 1 - similarity_threshold

            sql = """
            SELECT
                query_text,
                sql_query,
                result_summary,
                1 - (query_embedding <=> %s) AS similarity
            FROM
                memory_knowledge_base
            WHERE
                1 - (query_embedding <=> %s) > %s
            ORDER BY
                similarity DESC
            LIMIT %s;
            """
            results = self.db.fetch_all(sql, (embedding, embedding, similarity_threshold, top_k))

            if results:
                logger.info(f"Found {len(results)} similar knowledge entries for query: '{query[:50]}...'")
                return results
            return None
        except Exception as e:
            logger.error(f"Failed to find similar knowledge: {e}", exc_info=True)
            return None

    def learn_from_query(self, query: str, sql: str, result: Dict[str, Any], success: bool):
        """
        将成功的查询作为知识点存入数据库。

        Args:
            query: 原始用户查询。
            sql: 生成的 SQL 查询。
            result: 查询结果的摘要。
            success: 查询是否成功。
        """
        if not success or not sql:
            return

        embedding = self._get_embedding(query)
        if embedding is None:
            logger.warning("Cannot learn from query because embedding could not be generated.")
            return

        try:
            result_summary_json = json.dumps(result)
            # 使用 ON CONFLICT (query_text) DO UPDATE 来更新已存在的条目
            # 这样可以更新 SQL 或结果摘要，并重置访问计数
            insert_sql = """
            INSERT INTO memory_knowledge_base (query_text, query_embedding, sql_query, result_summary, access_count, last_accessed_at)
            VALUES (%s, %s, %s, %s, 1, NOW())
            ON CONFLICT (query_text) DO UPDATE SET
                sql_query = EXCLUDED.sql_query,
                query_embedding = EXCLUDED.query_embedding,
                result_summary = EXCLUDED.result_summary,
                access_count = memory_knowledge_base.access_count + 1,
                last_accessed_at = NOW();
            """
            self.db.execute_commit(insert_sql, (query, embedding, sql, result_summary_json))
            logger.info(f"Successfully learned from query and saved to knowledge base: '{query[:50]}...'")
        except Exception as e:
            logger.error(f"Failed to learn from query: {e}", exc_info=True)

    # --- 安全模型加载逻辑 (从 QueryCacheManager V15 迁移) ---
    def _check_network_connectivity(self) -> bool:
        """检查网络连接状态"""
        try:
            socket.create_connection(("huggingface.co", 443), timeout=5)
            return True
        except OSError:
            return False

    def _load_embedding_model_with_retry(self, embedding_model_name: str, cache_dir: str):
        """带重试和超时的模型加载方法"""
        import requests

        offline_mode = os.getenv("EMBEDDING_MODEL_OFFLINE_MODE", str(DEFAULT_EMBEDDING_MODEL_OFFLINE_MODE)).lower() == "true"
        model_timeout = int(os.getenv("EMBEDDING_MODEL_TIMEOUT", DEFAULT_EMBEDDING_MODEL_TIMEOUT))
        retry_count = int(os.getenv("EMBEDDING_MODEL_RETRY_COUNT", DEFAULT_EMBEDDING_MODEL_RETRY_COUNT))
        retry_delay = int(os.getenv("EMBEDDING_MODEL_RETRY_DELAY", DEFAULT_EMBEDDING_MODEL_RETRY_DELAY))

        if offline_mode:
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_HUB_OFFLINE"] = "1"
            logger.info("✓ Offline mode enabled for embedding model")

        socket.setdefaulttimeout(model_timeout)

        for attempt in range(retry_count + 1):
            try:
                logger.info(f"Loading embedding model (attempt {attempt + 1}/{retry_count + 1}): {embedding_model_name}")

                model_path = os.path.join(cache_dir, "models", embedding_model_name.replace("/", "_"))

                if os.path.exists(model_path):
                    logger.info(f"Using cached model from: {model_path}")
                    return SentenceTransformer(model_path)
                else:
                    return SentenceTransformer(
                        embedding_model_name,
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

    def _initialize_embedding_model_safely(self, embedding_model_name: str, cache_dir: str):
        """安全的模型初始化"""
        try:
            if not self._check_network_connectivity():
                logger.warning("No network connectivity, forcing offline mode for model loading.")
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                os.environ["HF_HUB_OFFLINE"] = "1"

            return self._load_embedding_model_with_retry(embedding_model_name, cache_dir)
        except Exception as e:
            logger.error(f"Fatal error during embedding model initialization: {e}", exc_info=True)
            return None
