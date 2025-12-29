"""
Checkpoint管理模块 - Sight Server
提供状态持久化和断点续传功能
"""

import logging
import json
import pickle
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from decimal import Decimal

logger = logging.getLogger(__name__)


class DecimalEncoder(json.JSONEncoder):
    """
    自定义 JSON 编码器 - 支持 Decimal 和 datetime 类型

    处理 Agent State 中的特殊类型:
    - Decimal → float (保持数值精度)
    - datetime → ISO格式字符串
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class CheckpointManager:
    """
    Checkpoint管理器

    功能:
    - 保存Agent执行状态
    - 支持断点续传
    - 状态持久化到磁盘
    - 异常恢复
    """

    def __init__(self, checkpoint_dir: str = "./checkpoints"):
        """
        初始化Checkpoint管理器

        Args:
            checkpoint_dir: Checkpoint保存目录
        """
        self.logger = logger
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"CheckpointManager initialized with dir: {checkpoint_dir}")

    def save_checkpoint(
        self,
        checkpoint_id: str,
        state: Dict[str, Any],
        step: int
    ) -> bool:
        """
        保存Checkpoint

        Args:
            checkpoint_id: Checkpoint标识符
            state: 当前状态
            step: 当前步骤

        Returns:
            是否保存成功
        """
        try:
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.pkl"

            checkpoint_data = {
                "checkpoint_id": checkpoint_id,
                "step": step,
                "state": state,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }

            # 使用pickle保存（支持复杂Python对象）
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)

            # 同时保存JSON版本（便于查看，使用 DecimalEncoder 处理特殊类型）
            json_file = self.checkpoint_dir / f"{checkpoint_id}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                # 转换state为可序列化格式
                serializable_state = self._make_serializable(state)
                json.dump({
                    "checkpoint_id": checkpoint_id,
                    "step": step,
                    "timestamp": checkpoint_data["timestamp"],
                    "state_summary": self._summarize_state(serializable_state)
                }, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)

            self.logger.info(
                f"Checkpoint saved: {checkpoint_id} at step {step}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            return False

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        加载Checkpoint

        Args:
            checkpoint_id: Checkpoint标识符

        Returns:
            Checkpoint数据，如果不存在则返回None
        """
        try:
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.pkl"

            if not checkpoint_file.exists():
                self.logger.warning(f"Checkpoint not found: {checkpoint_id}")
                return None

            with open(checkpoint_file, 'rb') as f:
                checkpoint_data = pickle.load(f)

            self.logger.info(
                f"Checkpoint loaded: {checkpoint_id} from step {checkpoint_data['step']}"
            )

            return checkpoint_data

        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            return None

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        删除Checkpoint

        Args:
            checkpoint_id: Checkpoint标识符

        Returns:
            是否删除成功
        """
        try:
            checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.pkl"
            json_file = self.checkpoint_dir / f"{checkpoint_id}.json"

            deleted = False

            if checkpoint_file.exists():
                checkpoint_file.unlink()
                deleted = True

            if json_file.exists():
                json_file.unlink()

            if deleted:
                self.logger.info(f"Checkpoint deleted: {checkpoint_id}")

            return deleted

        except Exception as e:
            self.logger.error(f"Failed to delete checkpoint: {e}")
            return False

    def list_checkpoints(self) -> list:
        """
        列出所有Checkpoint

        Returns:
            Checkpoint列表
        """
        checkpoints = []

        try:
            for pkl_file in self.checkpoint_dir.glob("*.pkl"):
                checkpoint_id = pkl_file.stem

                # 读取对应的JSON文件获取元数据
                json_file = self.checkpoint_dir / f"{checkpoint_id}.json"
                if json_file.exists():
                    with open(json_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        checkpoints.append(metadata)

            return sorted(checkpoints, key=lambda x: x.get("timestamp", ""), reverse=True)

        except Exception as e:
            self.logger.error(f"Failed to list checkpoints: {e}")
            return []

    def auto_save(
        self,
        state: Dict[str, Any],
        step: int,
        save_interval: int = 3
    ) -> Optional[str]:
        """
        自动保存Checkpoint（每隔N步）

        Args:
            state: 当前状态
            step: 当前步骤
            save_interval: 保存间隔（步数）

        Returns:
            Checkpoint ID（如果保存了）
        """
        if step % save_interval == 0:
            conversation_id = state.get("conversation_id", "unknown")
            checkpoint_id = f"{conversation_id}_step{step}_{int(datetime.now().timestamp())}"

            if self.save_checkpoint(checkpoint_id, state, step):
                return checkpoint_id

        return None

    def resume_from_checkpoint(
        self,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        从Checkpoint恢复执行

        Args:
            checkpoint_id: Checkpoint标识符

        Returns:
            恢复的状态，包含is_resumed标志
        """
        checkpoint_data = self.load_checkpoint(checkpoint_id)

        if checkpoint_data:
            state = checkpoint_data["state"]
            # 使用重命名后的字段名（避免LangGraph保留字段冲突）
            state["is_resumed_from_checkpoint"] = True
            state["saved_checkpoint_id"] = checkpoint_id
            state["saved_checkpoint_step"] = checkpoint_data["step"]
            state["last_checkpoint_time"] = checkpoint_data["timestamp"]

            self.logger.info(
                f"Resumed from checkpoint {checkpoint_id} at step {checkpoint_data['step']}"
            )

            return state

        return None

    def _make_serializable(self, obj: Any) -> Any:
        """
        将对象转换为可JSON序列化的格式

        Args:
            obj: 任意对象

        Returns:
            可序列化的对象
        """
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, Decimal):
            # ✅ Decimal 转为 float（保持数值类型）
            return float(obj)
        elif isinstance(obj, datetime):
            # ✅ datetime 转为 ISO 格式字符串
            return obj.isoformat()
        else:
            # 其他未知类型转为字符串
            return str(obj)

    def _summarize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成状态摘要（用于JSON保存）

        Args:
            state: 状态字典

        Returns:
            状态摘要
        """
        return {
            "query": state.get("query", ""),
            "current_step": state.get("current_step", 0),
            "max_iterations": state.get("max_iterations", 0),
            "sql_count": len(state.get("sql_history", [])),
            "status": state.get("status", ""),
            "has_error": state.get("error") is not None
        }

    def cleanup_old_checkpoints(self, keep_latest: int = 10) -> int:
        """
        清理旧的Checkpoint（保留最新的N个）

        Args:
            keep_latest: 保留的最新Checkpoint数量

        Returns:
            删除的Checkpoint数量
        """
        try:
            checkpoints = self.list_checkpoints()

            if len(checkpoints) <= keep_latest:
                return 0

            # 删除旧的checkpoint
            to_delete = checkpoints[keep_latest:]
            deleted_count = 0

            for checkpoint in to_delete:
                if self.delete_checkpoint(checkpoint["checkpoint_id"]):
                    deleted_count += 1

            self.logger.info(f"Cleaned up {deleted_count} old checkpoints")
            return deleted_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup checkpoints: {e}")
            return 0


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== CheckpointManager 测试 ===\n")

    manager = CheckpointManager(checkpoint_dir="./test_checkpoints")

    # 测试1: 保存Checkpoint
    print("--- 测试1: 保存Checkpoint ---")
    test_state = {
        "query": "测试查询",
        "current_step": 2,
        "sql_history": ["SQL1", "SQL2"],
        "status": "running"
    }
    success = manager.save_checkpoint("test-001", test_state, 2)
    print(f"Save result: {success}\n")

    # 测试2: 加载Checkpoint
    print("--- 测试2: 加载Checkpoint ---")
    loaded = manager.load_checkpoint("test-001")
    if loaded:
        print(f"Loaded checkpoint at step: {loaded['step']}")
        print(f"State: {loaded['state']['query']}\n")

    # 测试3: 列出所有Checkpoint
    print("--- 测试3: 列出Checkpoint ---")
    checkpoints = manager.list_checkpoints()
    print(f"Found {len(checkpoints)} checkpoints:")
    for cp in checkpoints:
        print(f"  - {cp['checkpoint_id']} at {cp['timestamp']}\n")

    # 测试4: 自动保存
    print("--- 测试4: 自动保存 ---")
    for step in range(1, 7):
        test_state["current_step"] = step
        checkpoint_id = manager.auto_save(test_state, step, save_interval=2)
        if checkpoint_id:
            print(f"Auto-saved at step {step}: {checkpoint_id}")
    print()

    # 测试5: 恢复
    print("--- 测试5: 从Checkpoint恢复 ---")
    resumed_state = manager.resume_from_checkpoint("test-001")
    if resumed_state:
        print(f"Resumed: is_resumed={resumed_state['is_resumed']}")
        print(f"From step: {resumed_state['checkpoint_step']}\n")

    # 测试6: 清理
    print("--- 测试6: 清理旧Checkpoint ---")
    deleted = manager.cleanup_old_checkpoints(keep_latest=3)
    print(f"Deleted {deleted} old checkpoints")
