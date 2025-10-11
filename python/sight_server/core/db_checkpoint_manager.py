
import logging
import json
import uuid
from typing import Dict, Any, Optional, List

from .database import DatabaseConnector
from .schemas_v12 import AgentStateV12 # We can reuse V12 state schema

logger = logging.getLogger(__name__)

class DbCheckpointManager:
    """
    基于数据库的对话存档管理器 (V15).
    """

    def __init__(self, db_connector: DatabaseConnector = None):
        self.db = db_connector if db_connector else DatabaseConnector()
        logger.info("DbCheckpointManager initialized.")

    def save_checkpoint(self, state: AgentStateV12) -> uuid.UUID:
        """将当前 Agent 状态保存到数据库。"""
        try:
            # Langchain messages aren't directly JSON serializable, so we need a custom encoder.
            # For simplicity, we'll just convert them to dicts here.
            state_to_save = state.copy()
            state_to_save['session_history'] = [msg.dict() for msg in state['session_history']]
            state_snapshot_json = json.dumps(state_to_save)

            conversation_id = state['conversation_id']
            step_number = state.get('intermediate_steps', []) and len(state['intermediate_steps']) or 0
            
            # The trigger in the DB will handle setting other `is_latest` to false.
            sql = """
            INSERT INTO conversation_checkpoints (conversation_id, state_snapshot, step_number, is_latest)
            VALUES (%s, %s, %s, TRUE)
            RETURNING checkpoint_id;
            """
            result = self.db.fetch_one(sql, (conversation_id, state_snapshot_json, step_number))
            checkpoint_id = result['checkpoint_id']
            logger.info(f"Checkpoint {checkpoint_id} saved for conversation {conversation_id}.")
            return checkpoint_id
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}", exc_info=True)
            raise

    def resume_from_checkpoint(self, checkpoint_id: uuid.UUID) -> Optional[AgentStateV12]:
        """从数据库中根据 checkpoint_id 恢复状态。"""
        try:
            sql = "SELECT state_snapshot FROM conversation_checkpoints WHERE checkpoint_id = %s;"
            result = self.db.fetch_one(sql, (checkpoint_id,))

            if result and result['state_snapshot']:
                logger.info(f"Resuming from checkpoint {checkpoint_id}.")
                # Here we would need to deserialize messages back to Langchain objects,
                # but for now, we'll leave them as dicts, which might require adjustment in the agent logic.
                return result['state_snapshot']
            return None
        except Exception as e:
            logger.error(f"Failed to resume from checkpoint {checkpoint_id}: {e}", exc_info=True)
            return None
    
    def get_latest_checkpoint(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取一个会话最新的存档。"""
        try:
            sql = """
            SELECT checkpoint_id, state_snapshot, created_at 
            FROM conversation_checkpoints 
            WHERE conversation_id = %s AND is_latest = TRUE;            
            """
            result = self.db.fetch_one(sql, (conversation_id,))
            if result:
                logger.info(f"Found latest checkpoint for conversation {conversation_id}.")
                return result
            return None
        except Exception as e:
            logger.error(f"Failed to get latest checkpoint for {conversation_id}: {e}", exc_info=True)
            return None
