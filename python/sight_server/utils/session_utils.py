"""
会话管理工具 - Sight Server
提供会话ID生成和管理功能
"""

import uuid
import time
from typing import Optional


def generate_conversation_id(prefix: str = "session") -> str:
    """
    生成唯一的会话ID
    
    Args:
        prefix: 会话ID前缀，默认为"session"
        
    Returns:
        str: 格式为 "prefix-timestamp-uuid" 的唯一会话ID
    """
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())
    return f"{prefix}-{timestamp}-{unique_id}"


def validate_conversation_id(conversation_id: str) -> bool:
    """
    验证会话ID格式是否有效
    
    Args:
        conversation_id: 要验证的会话ID
        
    Returns:
        bool: 如果格式有效返回True，否则返回False
    """
    if not conversation_id or not isinstance(conversation_id, str):
        return False
    
    # 检查基本格式：prefix-timestamp-uuid
    parts = conversation_id.split('-')
    if len(parts) < 3:
        return False
    
    # 检查时间戳部分是否为数字
    try:
        timestamp = int(parts[1])
        # 检查时间戳是否合理（在最近一年内）
        current_time = int(time.time())
        if timestamp < current_time - 31536000 or timestamp > current_time + 3600:  # 一年前到一小时后
            return False
    except (ValueError, IndexError):
        return False
    
    # 检查UUID部分
    try:
        uuid_part = '-'.join(parts[2:])
        uuid.UUID(uuid_part)
    except (ValueError, IndexError):
        return False
    
    return True


def get_or_create_conversation_id(conversation_id: Optional[str] = None) -> str:
    """
    获取或创建会话ID
    
    Args:
        conversation_id: 可选的现有会话ID
        
    Returns:
        str: 如果提供了有效的会话ID则返回该ID，否则生成新的会话ID
    """
    if conversation_id and validate_conversation_id(conversation_id):
        return conversation_id
    else:
        return generate_conversation_id()


def extract_timestamp_from_conversation_id(conversation_id: str) -> Optional[int]:
    """
    从会话ID中提取时间戳
    
    Args:
        conversation_id: 会话ID
        
    Returns:
        Optional[int]: 时间戳，如果提取失败则返回None
    """
    try:
        parts = conversation_id.split('-')
        if len(parts) >= 2:
            return int(parts[1])
    except (ValueError, IndexError):
        pass
    return None


def is_conversation_expired(conversation_id: str, max_age_hours: int = 24) -> bool:
    """
    检查会话是否已过期
    
    Args:
        conversation_id: 会话ID
        max_age_hours: 最大有效小时数，默认为24小时
        
    Returns:
        bool: 如果会话已过期返回True，否则返回False
    """
    timestamp = extract_timestamp_from_conversation_id(conversation_id)
    if timestamp is None:
        return True
    
    current_time = int(time.time())
    age_seconds = current_time - timestamp
    max_age_seconds = max_age_hours * 3600
    
    return age_seconds > max_age_seconds


# 测试代码
if __name__ == "__main__":
    print("=== 测试会话工具 ===\n")
    
    # 测试1: 生成会话ID
    print("--- 测试1: 生成会话ID ---")
    session_id = generate_conversation_id()
    print(f"生成的会话ID: {session_id}")
    
    # 测试2: 验证会话ID
    print("\n--- 测试2: 验证会话ID ---")
    print(f"验证生成的ID: {validate_conversation_id(session_id)}")
    print(f"验证无效ID: {validate_conversation_id('invalid-id')}")
    
    # 测试3: 获取或创建会话ID
    print("\n--- 测试3: 获取或创建会话ID ---")
    existing_id = get_or_create_conversation_id(session_id)
    print(f"使用现有ID: {existing_id}")
    new_id = get_or_create_conversation_id()
    print(f"创建新ID: {new_id}")
    
    # 测试4: 提取时间戳
    print("\n--- 测试4: 提取时间戳 ---")
    timestamp = extract_timestamp_from_conversation_id(session_id)
    print(f"提取的时间戳: {timestamp}")
    
    # 测试5: 检查过期
    print("\n--- 测试5: 检查过期 ---")
    print(f"会话是否过期: {is_conversation_expired(session_id)}")
    
    print("\n✅ 所有测试完成！")
