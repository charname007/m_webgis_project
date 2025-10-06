from __future__ import annotations

from typing import Any, Dict, List, Optional

from ...schemas import AgentState
from .base import NodeBase


class FinalValidationNode(NodeBase):
    """Validate final answer quality and provide improvement suggestions."""

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        try:
            query = state["query"]
            answer = state.get("answer", "")
            final_data: Optional[List[Dict[str, Any]]] = state.get("final_data")
            count = len(final_data) if final_data else 0
            query_intent = state.get("query_intent", "query")
            current_step = state.get("current_step", 0)

            self.logger.info(
                "[Node: final_validation] Validating final answer quality"
            )
            self.logger.info(
                "[Node: final_validation] Query intent: %s, Answer length: %s",
                query_intent,
                len(answer),
            )

            # 如果答案为空，跳过验证
            if not answer.strip():
                self.logger.info(
                    "[Node: final_validation] Empty answer, skipping validation"
                )
                return {
                    "final_validation_passed": True,
                    "final_validation_reason": "答案为空，跳过验证",
                    "thought_chain": [
                        {
                            "step": current_step + 8,
                            "type": "final_validation",
                            "action": "skip_validation",
                            "output": "答案为空，跳过验证",
                            "status": "skipped",
                        }
                    ],
                }

            # 使用LLM进行最终答案质量验证
            validation_result = self._validate_answer_with_llm(
                query=query,
                answer=answer,
                final_data=final_data,
                count=count,
                query_intent=query_intent,
            )

            if validation_result["passed"]:
                self.logger.info(
                    "[Node: final_validation] ✅ Final validation passed"
                )
                return {
                    "final_validation_passed": True,
                    "final_validation_reason": validation_result["reason"],
                    "final_validation_confidence": validation_result["confidence"],
                    "thought_chain": [
                        {
                            "step": current_step + 8,
                            "type": "final_validation",
                            "action": "validate_answer_quality",
                            "output": {
                                "passed": True,
                                "reason": validation_result["reason"],
                                "confidence": validation_result["confidence"],
                            },
                            "status": "completed",
                        }
                    ],
                }

            self.logger.warning(
                "[Node: final_validation] ❗ Final validation failed: %s",
                validation_result["reason"],
            )
            return {
                "final_validation_passed": False,
                "final_validation_error": validation_result["reason"],
                "final_validation_suggestions": validation_result["suggestions"],
                "final_validation_confidence": validation_result["confidence"],
                "thought_chain": [
                    {
                        "step": current_step + 8,
                        "type": "final_validation",
                        "action": "validate_answer_quality",
                        "output": {
                            "passed": False,
                            "reason": validation_result["reason"],
                            "suggestions": validation_result["suggestions"],
                            "confidence": validation_result["confidence"],
                        },
                        "status": "completed",
                    }
                ],
            }

        except Exception as exc:
            self.logger.error("[Node: final_validation] Error: %s", exc)
            return {
                "final_validation_passed": True,
                "final_validation_reason": f"最终验证流程出现异常，默认通过: {str(exc)}",
                "thought_chain": [
                    {
                        "step": state.get("current_step", 0) + 8,
                        "type": "final_validation",
                        "error": str(exc),
                        "status": "failed",
                    }
                ],
            }

    # ------------------------------------------------------------------
    def _validate_answer_with_llm(
        self,
        query: str,
        answer: str,
        final_data: Optional[List[Dict[str, Any]]],
        count: int,
        query_intent: str,
    ) -> Dict[str, Any]:
        try:
            if not self.llm:
                return {
                    "passed": True,
                    "reason": "无LLM可用，默认通过验证",
                    "confidence": 0.5,
                    "suggestions": [],
                }

            data_preview = self._prepare_final_validation_data_preview(final_data, count)
            prompt = f"""请扮演资深的答案质量评估专家，评估以下AI生成的答案质量。

## 用户查询
{query}

## 查询意图
{query_intent}

## 查询结果
- 结果条目数: {count}
- 结果预览: {data_preview}

## AI生成的答案
{answer}

## 评估标准
请从以下维度进行分析：

### 1. 准确性
- 答案是否基于查询结果？
- 是否存在事实错误或误导性信息？

### 2. 完整性
- 答案是否全面回答了用户问题？
- 是否遗漏了重要信息？

### 3. 清晰度
- 答案表达是否清晰易懂？
- 语言是否流畅自然？

### 4. 实用性
- 答案对用户是否有实际帮助？
- 是否提供了有价值的见解？

### 5. 结构化
- 答案是否有良好的组织结构？
- 是否使用了适当的格式（如列表、段落等）？

请给出评估结论：
- 如果答案质量良好，请说明原因
- 如果答案需要改进，请指出具体问题并提供改进建议

请输出："""

            response = self.llm.llm.invoke(prompt)
            validation_text = (
                response.content.strip()
                if hasattr(response, "content")
                else str(response).strip()
            )
            return self._parse_final_validation_result(validation_text, query, count)

        except Exception as exc:
            self.logger.error("LLM final validation failed: %s", exc)
            return {
                "passed": True,
                "reason": f"最终验证流程出现异常，默认通过: {str(exc)}",
                "confidence": 0.3,
                "suggestions": ["建议人工复核答案质量"],
            }

    def _prepare_final_validation_data_preview(
        self,
        data: Optional[List[Dict[str, Any]]],
        count: int,
    ) -> str:
        if not data:
            return "无数据"

        preview_count = min(3, len(data))
        preview_data = data[:preview_count]
        preview_lines: List[str] = []

        for idx, record in enumerate(preview_data):
            key_info: List[str] = []
            for field in ["name", "level", "地区", "所属省份"]:
                if field in record and record[field]:
                    key_info.append(f"{field}: {record[field]}")
            if key_info:
                preview_lines.append(f"记录 {idx + 1}: {', '.join(key_info)}")

        preview_text = "\n".join(preview_lines)
        if count > preview_count:
            preview_text += f"\n... 还有 {count - preview_count} 条记录"
        return preview_text

    def _parse_final_validation_result(
        self,
        validation_text: str,
        query: str,
        count: int,
    ) -> Dict[str, Any]:
        validation_lower = validation_text.lower()
        passed_keywords = [
            "良好", "优秀", "满意", "通过", "合理", "准确", "完整", "清晰",
            "good", "excellent", "satisfactory", "pass", "reasonable", "accurate", "complete", "clear"
        ]
        failed_keywords = [
            "不足", "不够", "缺乏", "问题", "失败", "错误", "模糊", "混乱",
            "incomplete", "inaccurate", "unclear", "confusing", "failed", "wrong", "missing"
        ]

        passed = any(keyword in validation_lower for keyword in passed_keywords)
        failed = any(keyword in validation_lower for keyword in failed_keywords)

        if passed and not failed:
            confidence = 0.8
            reason = "答案质量良好，满足用户需求"
            suggestions = []
        elif failed and not passed:
            confidence = 0.2
            reason = "答案质量需要改进"
            suggestions = self._extract_improvement_suggestions(validation_text)
        else:
            confidence = 0.5
            reason = "答案质量存在争议，建议进一步优化"
            suggestions = ["建议优化答案结构和表达"]

        return {
            "passed": passed,
            "reason": reason,
            "confidence": confidence,
            "suggestions": suggestions,
            "raw_validation": validation_text,
        }

    def _extract_improvement_suggestions(self, validation_text: str) -> List[str]:
        """从验证文本中提取改进建议"""
        suggestion_keywords = [
            "建议", "改进", "应当", "需要", "可以", "推荐", "最好",
            "suggest", "recommend", "should", "could", "better"
        ]
        
        suggestions: List[str] = []
        lines = validation_text.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
                
            # 检查是否包含建议关键词
            if any(keyword in line.lower() for keyword in suggestion_keywords):
                # 提取建议内容
                content = self._extract_suggestion_content(line)
                if content and content not in suggestions:
                    suggestions.append(content)
        
        # 如果没有找到具体建议，提供通用建议
        if not suggestions:
            suggestions = [
                "优化答案结构和逻辑",
                "确保信息准确性和完整性",
                "提高语言表达的清晰度"
            ]
        
        return suggestions[:5]  # 最多返回5条建议

    def _extract_suggestion_content(self, line: str) -> Optional[str]:
        """从行中提取建议内容"""
        markers = ["建议", "改进", "应当", "需要", "可以", "推荐", "最好"]
        for marker in markers:
            if marker in line:
                parts = line.split(marker, 1)
                if len(parts) > 1:
                    content = parts[1].strip().strip("：:，,。.;；")
                    if content and len(content) > 5:
                        return content
        return None
