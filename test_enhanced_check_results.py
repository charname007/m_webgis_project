"""
测试增强的check_results节点功能
验证启发式LLM分析和补充建议功能
"""

import sys
import os
import logging

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

from sight_server.core.graph.nodes import AgentNodes
from sight_server.core.schemas import AgentState

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_enhanced_check_results():
    """测试增强的check_results节点功能"""
    print("=== 测试增强的check_results节点功能 ===\n")
    
    # 创建模拟的AgentNodes实例
    # 注意：这里使用模拟对象，实际使用时需要真实的组件
    agent_nodes = AgentNodes(
        sql_generator=None,
        sql_executor=None,
        result_parser=None,
        answer_generator=None,
        schema_fetcher=None,
        llm=None  # 没有LLM时使用启发式逻辑
    )
    
    # 测试状态1: 有数据但需要补充
    print("--- 测试1: 有数据但需要补充 ---")
    state1: AgentState = {
        "query": "查询浙江省的5A景区",
        "enhanced_query": "查询浙江省的5A景区",
        "query_intent": "query",
        "requires_spatial": False,
        "intent_info": {"intent_type": "query", "is_spatial": False, "confidence": 0.8},
        "database_schema": {},
        "schema_fetched": True,
        "sql_history": ["SELECT * FROM scenic_spots WHERE level = '5A' AND province = '浙江省'"],
        "execution_results": [{"status": "success", "data": [], "count": 0}],
        "thought_chain": [],
        "current_step": 0,
        "current_sql": "SELECT * FROM scenic_spots WHERE level = '5A' AND province = '浙江省'",
        "current_result": {"status": "success", "data": [], "count": 0},
        "should_continue": True,
        "max_iterations": 3,
        "error": None,
        "retry_count": 0,
        "max_retries": 5,
        "last_error": None,
        "error_history": [],
        "fallback_strategy": None,
        "error_type": None,
        "final_data": [
            {"name": "西湖", "level": "5A", "province": "浙江省", "city": "杭州市"},
            {"name": "千岛湖", "level": "5A", "province": "浙江省", "city": "杭州市"}
        ],
        "answer": "",
        "status": "pending",
        "message": "",
        "session_history": [],
        "conversation_id": "test-001",
        "knowledge_base": {},
        "learned_patterns": [],
        "saved_checkpoint_id": None,
        "saved_checkpoint_step": None,
        "is_resumed_from_checkpoint": False,
        "last_checkpoint_time": None,
        "error_context": {},
        "query_id": "test-query-001",
        "query_start_time": "",
        "node_execution_logs": [],
        "validation_history": [],
        "validation_retry_count": 0,
        "max_validation_retries": 3,
        "validation_feedback": "",
        "is_validation_enabled": True,
        "should_return_data": True,
        "analysis": "",
        "insights": [],
        "suggestions": [],
        "analysis_type": ""
    }
    
    try:
        result1 = agent_nodes.check_results(state1)
        print(f"测试1结果: should_continue={result1.get('should_continue')}")
        print(f"原因: {result1.get('thought_chain', [{}])[0].get('output', {}).get('reason', '未知')}")
        
        if result1.get('supplement_suggestions'):
            print("补充建议:")
            for suggestion in result1['supplement_suggestions']:
                print(f"  - {suggestion.get('description', '未知')}")
        
        print()
        
    except Exception as e:
        print(f"测试1失败: {e}")
    
    # 测试状态2: 无数据情况
    print("--- 测试2: 无数据情况 ---")
    state2 = state1.copy()
    state2["final_data"] = []
    
    try:
        result2 = agent_nodes.check_results(state2)
        print(f"测试2结果: should_continue={result2.get('should_continue')}")
        print(f"原因: {result2.get('thought_chain', [{}])[0].get('output', {}).get('reason', '未知')}")
        print()
        
    except Exception as e:
        print(f"测试2失败: {e}")
    
    # 测试状态3: 达到最大迭代次数
    print("--- 测试3: 达到最大迭代次数 ---")
    state3 = state1.copy()
    state3["current_step"] = 2  # 达到最大迭代次数
    
    try:
        result3 = agent_nodes.check_results(state3)
        print(f"测试3结果: should_continue={result3.get('should_continue')}")
        print(f"原因: {result3.get('thought_chain', [{}])[0].get('output', {}).get('reason', '未知')}")
        print()
        
    except Exception as e:
        print(f"测试3失败: {e}")
    
    # 测试启发式解析方法
    print("--- 测试4: 启发式解析方法 ---")
    try:
        # 模拟LLM分析文本
        analysis_text = """
        当前查询结果基本回答了用户的问题，找到了浙江省的5A景区。
        但是数据还不够完整，建议补充以下信息：
        1. 景区的评分和门票价格
        2. 景区的开放时间和游客评价
        3. 更多相关的景区信息
        这样可以提供更全面的旅游建议。
        """
        
        heuristic_result = agent_nodes._parse_llm_analysis_heuristic(analysis_text, "查询浙江省的5A景区", 2)
        print(f"启发式解析结果: should_continue={heuristic_result.get('should_continue')}")
        print(f"原因: {heuristic_result.get('reason')}")
        print(f"指导: {heuristic_result.get('guidance_for_next_step')}")
        
        if heuristic_result.get('supplement_suggestions'):
            print("启发式建议:")
            for suggestion in heuristic_result['supplement_suggestions']:
                print(f"  - 类型: {suggestion.get('type')}")
                print(f"    描述: {suggestion.get('description')}")
                print(f"    原因: {suggestion.get('reason')}")
        
        print()
        
    except Exception as e:
        print(f"测试4失败: {e}")
    
    print("=== 测试完成 ===")


if __name__ == "__main__":
    test_enhanced_check_results()
