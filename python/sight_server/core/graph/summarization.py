"""
对话总结节点模块 - Sight Server
负责处理过长的短期记忆，生成对话总结
"""

import logging
from typing import Dict, Any, List

from ..schemas import AgentState

logger = logging.getLogger(__name__)


def summarize_conversation(state: AgentState) -> Dict[str, Any]:
    """
    总结对话历史，减少短期记忆长度
    
    当 session_history 过长时触发总结：
    - 生成对话摘要
    - 清理过时的历史记录
    - 保留最近的关键信息
    
    Args:
        state: 当前Agent状态
        
    Returns:
        更新后的状态字段
    """
    logger.info("开始总结对话历史...")
    
    # 获取现有总结
    current_summary = state.get("conversation_summary", "")
    session_history = state.get("session_history", [])
    current_step = state.get("current_step", 0)
    
    if not session_history:
        logger.info("会话历史为空，无需总结")
        return {
            "conversation_summary": current_summary,
            "last_summary_step": current_step
        }
    
    # 构建总结提示
    if current_summary:
        summary_prompt = (
            f"这是对话历史的当前总结: {current_summary}\n\n"
            "基于新的对话内容扩展这个总结:"
        )
    else:
        summary_prompt = "创建对话历史的总结:"
    
    # 准备对话历史内容用于总结
    conversation_content = _prepare_conversation_for_summary(session_history)
    
    # 使用 LLM 生成总结
    # 这里需要调用现有的 LLM 组件，暂时使用简化版本
    new_summary = _generate_summary_with_llm(conversation_content, summary_prompt)
    
    # 清理历史记录，保留最近的关键信息
    cleaned_history = _cleanup_session_history(session_history)
    
    logger.info(f"对话总结完成，历史记录从 {len(session_history)} 条减少到 {len(cleaned_history)} 条")
    
    return {
        "conversation_summary": new_summary,
        "session_history": cleaned_history,
        "last_summary_step": current_step
    }


def _prepare_conversation_for_summary(session_history: List[Dict[str, Any]]) -> str:
    """
    准备对话历史内容用于总结
    
    Args:
        session_history: 会话历史记录
        
    Returns:
        格式化的对话内容
    """
    conversation_lines = []
    
    for i, history_item in enumerate(session_history):
        # 提取关键信息
        query = history_item.get("query", "")
        answer = history_item.get("answer", "")
        intent = history_item.get("intent_info", {})
        
        if query:
            conversation_lines.append(f"用户查询 {i+1}: {query}")
        if answer:
            conversation_lines.append(f"系统回答 {i+1}: {answer}")
        if intent:
            intent_type = intent.get("intent_type", "")
            if intent_type:
                conversation_lines.append(f"查询意图: {intent_type}")
    
    return "\n".join(conversation_lines)


def _generate_summary_with_llm(conversation_content: str, summary_prompt: str) -> str:
    """
    使用 LLM 生成对话总结
    
    Args:
        conversation_content: 对话内容
        summary_prompt: 总结提示
        
    Returns:
        生成的总结文本
    """
    # TODO: 这里需要集成实际的 LLM 调用
    # 目前使用简化版本，实际实现时需要调用现有的 LLM 组件
    
    if not conversation_content:
        return "暂无对话历史"
    
    # 简化实现：提取关键信息
    lines = conversation_content.split('\n')
    user_queries = [line for line in lines if line.startswith("用户查询")]
    system_answers = [line for line in lines if line.startswith("系统回答")]
    
    summary = f"对话总结:\n"
    summary += f"- 用户进行了 {len(user_queries)} 次查询\n"
    summary += f"- 系统提供了 {len(system_answers)} 次回答\n"
    
    # 提取最近的几个查询作为示例
    if user_queries:
        recent_queries = user_queries[-3:]  # 最近3个查询
        summary += f"- 最近的查询包括: {', '.join([q.split(': ')[1] for q in recent_queries])}\n"
    
    return summary


def _cleanup_session_history(session_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    清理会话历史，保留关键信息
    
    Args:
        session_history: 原始会话历史
        
    Returns:
        清理后的会话历史
    """
    if len(session_history) <= 5:
        # 如果历史记录不多，全部保留
        return session_history
    
    # 保留最近的5条记录
    recent_history = session_history[-5:]
    
    # 从更早的记录中提取关键信息
    older_history = session_history[:-5]
    key_info = _extract_key_information(older_history)
    
    # 将关键信息添加到最近历史中
    if key_info:
        recent_history.insert(0, {
            "type": "summary_context",
            "key_information": key_info,
            "original_count": len(older_history)
        })
    
    return recent_history


def _extract_key_information(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    从历史记录中提取关键信息
    
    Args:
        history: 历史记录
        
    Returns:
        关键信息字典
    """
    key_info = {
        "total_queries": len(history),
        "query_types": {},
        "spatial_queries": 0,
        "common_topics": []
    }
    
    for item in history:
        intent_info = item.get("intent_info", {})
        intent_type = intent_info.get("intent_type", "")
        
        if intent_type:
            key_info["query_types"][intent_type] = key_info["query_types"].get(intent_type, 0) + 1
        
        if intent_info.get("is_spatial", False):
            key_info["spatial_queries"] += 1
        
        # 提取查询中的关键词
        query = item.get("query", "")
        if query:
            # 简单的关键词提取（实际实现可以更复杂）
            words = query.lower().split()
            for word in words:
                if len(word) > 3 and word not in ["查询", "搜索", "查找", "什么", "哪里"]:
                    if word not in key_info["common_topics"]:
                        key_info["common_topics"].append(word)
    
    # 限制主题数量
    key_info["common_topics"] = key_info["common_topics"][:10]
    
    return key_info