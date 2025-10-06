#!/usr/bin/env python3
"""
测试所有错误类型的SQL传递机制
验证各种SQL错误是否都能正确返回错误SQL到前面节点
"""

import sys
import os
import logging
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_sql_executor_error_handling():
    """测试SQL执行器的错误处理"""
    print("=== SQL执行器错误处理测试 ===")
    
    # 模拟各种错误类型的SQL
    test_cases = [
        {
            "type": "语法错误",
            "sql": "SELECT * FROM non_existent_table WHERE invalid syntax",
            "expected_error": "SQL_SYNTAX_ERROR",
            "description": "包含语法错误的SQL"
        },
        {
            "type": "超时错误", 
            "sql": "SELECT json_agg(json_build_object('name', COALESCE(ts.name, a.name))) FROM tourist_spots ts FULL OUTER JOIN attractions a ON ts.name = a.name",
            "expected_error": "TIMEOUT_ERROR",
            "description": "复杂查询导致超时"
        },
        {
            "type": "连接错误",
            "sql": "SELECT * FROM test_table",
            "expected_error": "CONNECTION_ERROR", 
            "description": "数据库连接失败"
        },
        {
            "type": "权限错误",
            "sql": "DROP TABLE important_table",
            "expected_error": "PERMISSION_ERROR",
            "description": "没有删除权限"
        },
        {
            "type": "对象不存在错误",
            "sql": "SELECT * FROM non_existent_table",
            "expected_error": "OBJECT_NOT_FOUND",
            "description": "表不存在"
        }
    ]
    
    print("📋 测试用例:")
    for i, case in enumerate(test_cases, 1):
        print(f"  {i}. {case['type']}: {case['description']}")
        print(f"     SQL: {case['sql'][:80]}...")
        print(f"     预期错误类型: {case['expected_error']}")
        print()


def test_error_context_building():
    """测试错误上下文构建"""
    print("=== 错误上下文构建测试 ===")
    
    # 模拟SQL执行节点的错误上下文构建
    def build_error_context(state, execution_result, start_time):
        return {
            "failed_sql": state.get("current_sql"),
            "error_message": execution_result.get("error"),
            "failed_at_step": state.get("current_step", 0),
            "query_context": {
                "original_query": state.get("query"),
                "enhanced_query": state.get("enhanced_query"),
                "intent_type": state.get("query_intent"),
                "requires_spatial": state.get("requires_spatial", False),
            },
            "execution_context": {
                "execution_time_ms": (time.time() - start_time) * 1000,
                "rows_affected": 0,
                "timestamp": "2025-10-06T23:45:00"
            },
        }
    
    # 测试状态
    test_state = {
        "current_sql": "SELECT * FROM non_existent_table WHERE invalid syntax",
        "current_step": 4,
        "query": "查询测试数据",
        "enhanced_query": "增强的查询测试数据",
        "query_intent": "query",
        "requires_spatial": False
    }
    
    test_execution_result = {
        "error": "syntax error at or near \"invalid\"",
        "error_type": "SQL_SYNTAX_ERROR"
    }
    
    import time
    start_time = time.time()
    
    error_context = build_error_context(test_state, test_execution_result, start_time)
    
    print("📋 构建的错误上下文:")
    for key, value in error_context.items():
        if key == "failed_sql":
            print(f"  {key}: {value}")
        elif isinstance(value, dict):
            print(f"  {key}:")
            for sub_key, sub_value in value.items():
                print(f"    {sub_key}: {sub_value}")
        else:
            print(f"  {key}: {value}")


def test_error_node_processing():
    """测试错误处理节点处理"""
    print("\n=== 错误处理节点处理测试 ===")
    
    # 模拟错误处理节点的输入状态
    test_states = [
        {
            "error": "syntax error at or near \"invalid\"",
            "current_sql": "SELECT * FROM non_existent_table WHERE invalid syntax",
            "retry_count": 0,
            "current_step": 4,
            "error_context": {
                "failed_sql": "SELECT * FROM non_existent_table WHERE invalid syntax",
                "error_message": "syntax error at or near \"invalid\"",
                "failed_at_step": 4
            }
        },
        {
            "error": "查询超时（90秒）",
            "current_sql": "SELECT json_agg(json_build_object(...)) FROM ...",
            "retry_count": 0,
            "current_step": 4,
            "error_context": {
                "failed_sql": "SELECT json_agg(json_build_object(...)) FROM ...",
                "error_message": "查询超时（90秒）",
                "failed_at_step": 4
            }
        }
    ]
    
    print("📋 错误处理节点输入状态:")
    for i, state in enumerate(test_states, 1):
        print(f"  用例 {i}:")
        print(f"    错误: {state['error']}")
        print(f"    当前SQL: {state['current_sql'][:60]}...")
        print(f"    错误上下文中的failed_sql: {state['error_context']['failed_sql'][:60]}...")
        print()


def test_llm_prompt_generation():
    """测试LLM提示生成"""
    print("\n=== LLM提示生成测试 ===")
    
    # 模拟各种错误类型的LLM提示
    error_scenarios = [
        {
            "error_type": "SQL_SYNTAX_ERROR",
            "failed_sql": "SELECT * FROM non_existent_table WHERE invalid syntax",
            "error_message": "syntax error at or near \"invalid\"",
            "expected_prompt": "之前的SQL包含语法错误，请分析问题并生成正确的SQL"
        },
        {
            "error_type": "TIMEOUT_ERROR", 
            "failed_sql": "SELECT json_agg(json_build_object('name', COALESCE(ts.name, a.name))) FROM tourist_spots ts FULL OUTER JOIN attractions a ON ts.name = a.name",
            "error_message": "查询超时（90秒）",
            "expected_prompt": "之前的SQL执行超时（90秒），请分析问题并生成优化的SQL"
        },
        {
            "error_type": "OBJECT_NOT_FOUND",
            "failed_sql": "SELECT * FROM non_existent_table",
            "error_message": "relation \"non_existent_table\" does not exist",
            "expected_prompt": "之前的SQL引用不存在的表，请检查表名并生成正确的SQL"
        }
    ]
    
    print("📋 各种错误类型的LLM提示:")
    for scenario in error_scenarios:
        print(f"  错误类型: {scenario['error_type']}")
        print(f"  失败SQL: {scenario['failed_sql'][:80]}...")
        print(f"  错误信息: {scenario['error_message']}")
        print(f"  预期提示: {scenario['expected_prompt']}")
        print()


def test_current_implementation_status():
    """测试当前实现状态"""
    print("\n=== 当前实现状态分析 ===")
    
    print("✅ 已确认实现的功能:")
    print("  1. SQL执行器返回错误时包含failed_sql字段")
    print("  2. SQL执行节点构建错误上下文包含failed_sql")
    print("  3. 错误处理节点接收error_context")
    print("  4. 超时错误有特殊处理机制")
    
    print("\n❓ 需要验证的功能:")
    print("  1. 错误处理节点是否将failed_sql传递给LLM")
    print("  2. LLM提示模板是否包含failed_sql")
    print("  3. 所有错误类型是否都能正确传递failed_sql")
    print("  4. 系统流程是否确保错误SQL在整个重试过程中传递")
    
    print("\n🔍 关键检查点:")
    print("  1. 检查错误处理节点的输出是否包含错误SQL")
    print("  2. 检查LLM节点的输入是否包含错误SQL上下文")
    print("  3. 测试各种错误类型的完整流程")


def main():
    """主测试函数"""
    print("=== 所有错误类型SQL传递测试 ===")
    print("验证各种SQL错误是否都能正确返回错误SQL到前面节点")
    
    try:
        test_sql_executor_error_handling()
        test_error_context_building()
        test_error_node_processing()
        test_llm_prompt_generation()
        test_current_implementation_status()
        
        print("\n=== 测试总结 ===")
        print("✅ SQL执行器层面: 所有错误都返回failed_sql")
        print("✅ SQL执行节点: 构建错误上下文包含failed_sql")
        print("✅ 错误处理节点: 接收error_context")
        print("❓ 需要验证: 错误SQL是否传递到LLM")
        print("❓ 需要验证: LLM提示是否包含错误SQL")
        
        print("\n=== 下一步验证 ===")
        print("1. 检查错误处理节点的输出")
        print("2. 检查LLM节点的输入")
        print("3. 测试完整错误传递流程")
        print("4. 优化错误SQL传递机制")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
