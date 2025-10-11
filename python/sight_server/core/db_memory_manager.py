
import logging
import json
import numpy as np # For embedding simulation
from typing import Dict, Any

from .database import DatabaseConnector

logger = logging.getLogger(__name__)

# Placeholder for a real sentence embedding model
# from sentence_transformers import SentenceTransformer
# embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

class DbMemoryManager:
    """
    基于数据库的知识库管理器 (V15).
    """

    def __init__(self, db_connector: DatabaseConnector = None):
        self.db = db_connector if db_connector else DatabaseConnector()
        logger.info("DbMemoryManager initialized.")

    def _get_embedding(self, text: str) -> List[float]:
        """Simulates generating a sentence embedding."""
        # In a real implementation, you would use a model like:
        # return embedding_model.encode(text).tolist()
        
        # For now, a mock, deterministic embedding:
        np.random.seed(abs(hash(text)) % (2**32 - 1))
        return np.random.rand(1536).tolist()

    def learn_from_query(self, query: str, sql: str, result: Dict[str, Any], success: bool):
        """将成功的查询作为知识点存入数据库。"""
        if not success or not sql:
            return

        try:
            embedding = self._get_embedding(query)
            result_summary_json = json.dumps(result)

            # 使用UPSERT逻辑：如果query_text已存在，则什么都不做
            # 这避免了重复知识，并依赖于查询文本的唯一约束
            insert_sql = """
            INSERT INTO memory_knowledge_base (query_text, query_embedding, sql_query, result_summary)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (query_text) DO NOTHING;
            """
            self.db.execute_commit(insert_sql, (query, embedding, sql, result_summary_json))
            logger.info(f"Knowledge learned and stored for query: {query[:50]}...")
        except Exception as e:
            logger.error(f"Failed to learn from query: {e}", exc_info=True)

    def get_similar_knowledge(self, query: str, threshold: float = 0.9) -> Dict[str, Any]:
        """
        从数据库中通过向量相似度搜索，查找相似的知识点。
        pgvector extension uses a special operator `<=>` for Euclidean distance.
        """
        try:
            embedding = self._get_embedding(query)
            
            search_sql = """
            SELECT query_text, sql_query, result_summary
            FROM memory_knowledge_base
            ORDER BY query_embedding <=> %s
            LIMIT 1;
            """
            
            # Note: The vector needs to be passed as a string representation
            records = self.db.fetch_all(search_sql, (str(embedding),))
            
            if records:
                # This is a simplified similarity check. Real cosine similarity would be 1 - (distance / 2)
                # For now, let's assume any result is good enough for demonstration
                logger.info(f"Found similar knowledge in DB for query: {query[:50]}...")
                return records[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get similar knowledge: {e}", exc_info=True)
            return None

    # Note: Session management logic is now handled by CheckpointManager + AgentState
    # so methods like `start_session`, `add_query_to_session` are no longer needed here.
