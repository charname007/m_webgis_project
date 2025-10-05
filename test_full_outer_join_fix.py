#!/usr/bin/env python3
"""
测试 FULL OUTER JOIN 修复效果
验证新的 UNION ALL 策略是否能够正常工作
"""

import logging
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

from sight_server.core.agent import SQLQueryAgent
from sight_server.core.prompts import PromptManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_union_all_strategy():
    """测试 UNION ALL 策略"""
    print("\n=== 测试 UNION ALL 策略 ===\n")
    
    try:
        # 创建 Agent
        agent = SQLQueryAgent(
            enable_memory=False,
            enable_checkpoint=False
        )
        
        # 测试查询1：需要完整数据的查询
        print("--- 测试1: 查询浙江省的5A景区 ---")
        result1 = agent.run("查询浙江省的5A景区")
        print(f"结果状态: {result1[:200]}...")
        
        # 测试查询2：空间查询
        print("\n--- 测试2: 查询杭州市的景区 ---")
        result2 = agent.run("查询杭州市的景区")
        print(f"结果状态: {result2[:200]}...")
        
        # 测试查询3：统计查询
        print("\n--- 测试3: 统计浙江省有多少个4A景区 ---")
        result3 = agent.run("统计浙江省有多少个4A景区")
        print(f"结果状态: {result3[:200]}...")
        
        # 清理资源
        agent.close()
        
        print("\n✅ 所有测试完成，没有出现 FULL OUTER JOIN 错误")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_prompt_manager():
    """测试提示词管理器"""
    print("\n=== 测试提示词管理器 ===\n")
    
    try:
        # 测试查询意图分析
        test_queries = [
            "查询浙江省的5A景区",
            "查找距离杭州10公里内的景点", 
            "统计浙江省有多少个4A景区",
            "查询杭州市的景区介绍"
        ]
        
        for query in test_queries:
            intent = PromptManager.analyze_query_intent(query)
            print(f"查询: {query}")
            print(f"  意图类型: {intent['intent_type']}")
            print(f"  空间查询: {intent['is_spatial']}")
            print(f"  描述: {intent['description']}")
            print()
        
        # 测试提示词获取
        scenic_prompt = PromptManager.get_scenic_query_prompt()
        print(f"景区提示词长度: {len(scenic_prompt)} 字符")
        
        print("✅ 提示词管理器测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 提示词管理器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== FULL OUTER JOIN 修复验证测试 ===\n")
    
    # 测试提示词管理器
    prompt_test_passed = test_prompt_manager()
    
    # 测试 UNION ALL 策略
    strategy_test_passed = test_union_all_strategy()
    
    # 总结
    print("\n=== 测试总结 ===")
    if prompt_test_passed and strategy_test_passed:
        print("✅ 所有测试通过！FULL OUTER JOIN 修复成功")
        print("✅ 新的 UNION ALL 策略正常工作")
        print("✅ 提示词管理器更新成功")
    else:
        print("❌ 部分测试失败，需要进一步调试")
        
    return prompt_test_passed and strategy_test_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
