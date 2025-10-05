"""
LangGraph图构建器模块 - Sight Server
负责构建和编译LangGraph工作流
"""

import logging
from langgraph.graph import StateGraph, END

from ..schemas import AgentState
from .nodes import AgentNodes
from .edges import should_continue_querying, should_retry_or_fail, should_requery

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    LangGraph图构建器

    功能:
    - 构建多步查询工作流
    - 连接所有节点
    - 设置条件边
    - 编译为可执行图
    - 支持 Fallback 错误重试机制
    """

    @staticmethod
    def build(nodes: AgentNodes):
        """
        构建LangGraph工作流

        工作流结构:
        ```
        START
          ↓
        fetch_schema (获取数据库Schema)
          ↓
        analyze_intent (分析查询意图)
          ↓
        enhance_query (增强查询文本)
          ↓
        generate_sql (生成SQL)
          ↓
        execute_sql (执行SQL)
          ↓
        [条件边] should_retry_or_fail
          ├─→ handle_error (有错误) → generate_sql (重试)
          └─→ validate_results (无错误或重试次数用尽)
               ↓
        [条件边] should_requery (✅ 新增)
          ├─→ generate_sql (验证失败，重新查询)
          └─→ check_results (验证通过，继续)
               ↓
        [条件边] should_continue_querying
          ├─→ generate_sql (继续查询，循环)
          └─→ generate_answer (生成答案，结束)
               ↓
              END
        ```

        Args:
            nodes: AgentNodes实例

        Returns:
            编译后的LangGraph
        """
        logger.info("Building LangGraph workflow with Fallback support...")

        # 创建StateGraph
        workflow = StateGraph(AgentState)

        # ==================== 添加所有节点 ====================
        workflow.add_node("fetch_schema", nodes.fetch_schema)  # ✅ 新增：Schema获取
        workflow.add_node("analyze_intent", nodes.analyze_intent)
        workflow.add_node("enhance_query", nodes.enhance_query)
        workflow.add_node("generate_sql", nodes.generate_sql)
        workflow.add_node("execute_sql", nodes.execute_sql)
        workflow.add_node("handle_error", nodes.handle_error)
        workflow.add_node("check_results", nodes.check_results)
        workflow.add_node("validate_results", nodes.validate_results)  # ✅ 新增：结果验证节点
        workflow.add_node("generate_answer", nodes.generate_answer)

        logger.info("✓ Added 9 nodes to workflow (including fetch_schema, handle_error, and validate_results)")

        # ==================== 设置入口点 ====================
        workflow.set_entry_point("fetch_schema")  # ✅ 改为从fetch_schema开始

        # ==================== 添加固定边 ====================
        # fetch_schema → analyze_intent
        workflow.add_edge("fetch_schema", "analyze_intent")

        # analyze_intent → enhance_query
        workflow.add_edge("analyze_intent", "enhance_query")

        # enhance_query → generate_sql
        workflow.add_edge("enhance_query", "generate_sql")

        # generate_sql → execute_sql
        workflow.add_edge("generate_sql", "execute_sql")

        logger.info("✓ Added sequential edges")

        # ==================== 添加条件边（错误处理）====================
        # ✅ execute_sql → [条件判断]
        #   - 有错误且可重试 → handle_error
        #   - 无错误或重试次数用尽 → validate_results
        workflow.add_conditional_edges(
            "execute_sql",
            should_retry_or_fail,
            {
                "handle_error": "handle_error",
                "validate_results": "validate_results"
            }
        )

        logger.info("✓ Added conditional edge for error handling")

        # ✅ 新增：handle_error → generate_sql (重试循环)
        workflow.add_edge("handle_error", "generate_sql")

        logger.info("✓ Added retry loop edge")

        # ==================== 添加条件边（结果验证）====================
        # ✅ 新增：validate_results → [条件判断]
        #   - 验证失败且可重试 → generate_sql (重新查询)
        #   - 验证通过或重试次数用尽 → check_results
        workflow.add_conditional_edges(
            "validate_results",
            should_requery,
            {
                "generate_sql": "generate_sql",
                "check_results": "check_results"
            }
        )

        logger.info("✓ Added conditional edge for result validation")

        # ==================== 添加条件边（循环控制）====================
        # check_results → [条件判断]
        #   - 继续查询 → generate_sql (循环)
        #   - 结束查询 → generate_answer (生成答案)
        workflow.add_conditional_edges(
            "check_results",
            should_continue_querying,
            {
                "generate_sql": "generate_sql",
                "generate_answer": "generate_answer"
            }
        )

        logger.info("✓ Added conditional edge for iteration control")

        # ==================== 添加结束边 ====================
        # generate_answer → END
        workflow.add_edge("generate_answer", END)

        logger.info("✓ Added end edge")

        # ==================== 编译图 ====================
        compiled_graph = workflow.compile()

        logger.info("✓ LangGraph workflow built and compiled successfully with Fallback support")

        return compiled_graph

    @staticmethod
    def visualize(graph):
        """
        可视化工作流（可选功能）

        Args:
            graph: 编译后的图

        Returns:
            图的Mermaid表示（字符串）
        """
        try:
            # LangGraph支持生成Mermaid图
            mermaid_str = graph.get_graph().draw_mermaid()
            return mermaid_str
        except Exception as e:
            logger.warning(f"Failed to visualize graph: {e}")
            return None


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== GraphBuilder 测试 ===\n")

    # 注意: 实际测试需要真实的处理器实例
    # 这里仅演示构建过程

    print("--- 测试: 构建工作流 ---")
    print("需要真实的 AgentNodes 实例才能完整测试")
    print()

    # 工作流说明
    print("--- 工作流说明 ---")
    print("""
LangGraph 多步查询工作流:

1. analyze_intent - 分析查询意图
   ↓
2. enhance_query - 增强查询文本
   ↓
3. generate_sql - 生成SQL查询
   ↓
4. execute_sql - 执行SQL
   ↓
5. check_results - 检查结果完整性
   ↓
   [条件判断]
   ├─→ 如果需要继续: 返回步骤3 (最多3次)
   └─→ 如果完成: 进入步骤6
       ↓
6. generate_answer - 生成最终答案
   ↓
   END

特性:
- 支持多步迭代查询
- 自动检测结果完整性
- 智能补充缺失信息
- 完整的思维链记录
    """)
