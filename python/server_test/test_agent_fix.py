#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Agent 修复效果
"""

import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_agent():
    """测试 Agent 是否能正常工作"""
    try:
        logger.info("=" * 60)
        logger.info("开始测试 SpatialSQLQueryAgent")
        logger.info("=" * 60)

        from spatial_sql_agent import SpatialSQLQueryAgent

        logger.info("✓ 导入成功，开始初始化 Agent...")
        agent = SpatialSQLQueryAgent()
        logger.info("✓ Agent 初始化成功")

        # 测试一个简单查询
        test_query = "列出所有5A景区"
        logger.info(f"\n测试查询: {test_query}")
        logger.info("-" * 60)

        result = agent.run_with_thought_chain(test_query)

        logger.info("\n查询结果:")
        logger.info(f"状态: {result.get('status')}")
        logger.info(f"步骤数: {result.get('step_count')}")
        logger.info(f"SQL查询数: {len(result.get('sql_queries_with_results', []))}")

        # 显示思维链
        thought_chain = result.get('thought_chain', [])
        logger.info(f"\n思维链 ({len(thought_chain)} 步):")
        for step in thought_chain:
            logger.info(f"  步骤 {step['step']}: {step['type']}")
            if step['type'] == 'action':
                logger.info(f"    动作: {step.get('action')}")
            elif step['type'] == 'final_answer':
                answer = step.get('content', '')[:100]
                logger.info(f"    答案: {answer}...")

        # 检查是否有解析错误
        final_answer = result.get('final_answer', '')
        if 'Agent stopped' in final_answer or 'iteration limit' in final_answer:
            logger.error("\n❌ 检测到 Agent 停止错误")
            logger.error(f"Final answer: {final_answer[:200]}")
            return False

        logger.info("\n✅ 测试通过！")
        agent.close()
        return True

    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agent()
    sys.exit(0 if success else 1)
