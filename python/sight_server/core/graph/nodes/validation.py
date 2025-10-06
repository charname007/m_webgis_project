from __future__ import annotations

from typing import Any, Dict, List, Optional

from ...schemas import AgentState
from .base import NodeBase


class ValidateResultsNode(NodeBase):
    """Validate query results using LLM feedback."""

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        try:
            query = state["query"]
            final_data: Optional[List[Dict[str, Any]]
                                 ] = state.get("final_data")
            count = len(final_data) if final_data else 0
            query_intent = state.get("query_intent")
            current_step = state.get("current_step", 0)

            self.logger.info(
                "[Node: validate_results] Validating results for %s records",
                count,
            )
            self.logger.info(
                "[Node: validate_results] Query intent: %s",
                query_intent,
            )

            if count == 0 or not final_data:
                self.logger.info(
                    "[Node: validate_results] No data to validate, passing through",
                )
                return {
                    "validation_passed": True,
                    "validation_reason": "无数据，跳过验证",
                    "thought_chain": [
                        {
                            "step": current_step + 6,
                            "type": "result_validation",
                            "action": "skip_validation",
                            "output": "无数据，跳过验证",
                            "status": "skipped",
                        }
                    ],
                }

            validation_result = self._validate_with_llm(
                query=query,
                data=final_data,
                count=count,
                query_intent=query_intent or "query",
            )

            if validation_result["passed"]:
                self.logger.info(
                    "[Node: validate_results] ✅ Validation passed")
                return {
                    "validation_passed": True,
                    "validation_reason": validation_result["reason"],
                    "thought_chain": [
                        {
                            "step": current_step + 6,
                            "type": "result_validation",
                            "action": "validate_results",
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
                "[Node: validate_results] ❗ Validation failed: %s",
                validation_result["reason"],
            )
            return {
                "validation_passed": False,
                "validation_error": validation_result["reason"],
                "validation_guidance": validation_result["guidance"],
                "should_continue": True,
                "fallback_strategy": "retry_sql",
                "last_error": f"结果验证失败: {validation_result['reason']}",
                "thought_chain": [
                    {
                        "step": current_step + 6,
                        "type": "result_validation",
                        "action": "validate_results",
                        "output": {
                            "passed": False,
                            "reason": validation_result["reason"],
                            "guidance": validation_result["guidance"],
                            "confidence": validation_result["confidence"],
                        },
                        "status": "completed",
                    }
                ],
            }

        except Exception as exc:
            self.logger.error("[Node: validate_results] Error: %s", exc)
            return {
                "validation_passed": True,
                "validation_reason": f"验证流程出现异常，默认通过: {str(exc)}",
                "thought_chain": [
                    {
                        "step": state.get("current_step", 0) + 6,
                        "type": "result_validation",
                        "error": str(exc),
                        "status": "failed",
                    }
                ],
            }

    # ------------------------------------------------------------------
    def _validate_with_llm(
        self,
        query: str,
        data: List[Dict[str, Any]],
        count: int,
        query_intent: str,
    ) -> Dict[str, Any]:
        try:
            if not self.llm:
                return {
                    "passed": True,
                    "reason": "无LLM可用，默认通过验证",
                    "confidence": 0.5,
                    "guidance": "",
                }

            data_preview = self._prepare_validation_data_preview(data, count)
            prompt = f"""请扮演资深的数据验证专家，判断以下查询结果是否满足用户需求

## 用户查询
{query}

## 查询意图
{query_intent}

## 查询结果
- 结果条目数: {count}
- 结果预览: {data_preview}

## 验证标准
请从以下维度进行分析

### 1. 相关性
- 结果是否直接回答了用户问题？
- 结果是否与查询意图匹配？

### 2. 完整性
- 结果是否存在信息缺失？
- 如果是统计查询，是否足够全面？

### 3. 准确性
- 数据内容是否可信且准确？
- 是否存在异常值或离群点？

### 4. 实用性
- 这些结果对用户是否有实际帮助？
- 是否需要补充更多信息？

请给出结论：
- 如果结果合理，请说明原因
- 如果结果不合理，请指出问题并给出改进建议

请输出："""

            response = self.llm.llm.invoke(prompt)
            validation_text = (
                response.content.strip()
                if hasattr(response, "content")
                else str(response).strip()
            )
            return self._parse_validation_result(validation_text, query, count)

        except Exception as exc:
            self.logger.error("LLM validation failed: %s", exc)
            return {
                "passed": True,
                "reason": f"验证流程出现异常，默认通过: {str(exc)}",
                "confidence": 0.3,
                "guidance": "建议人工复核结果",
            }

    def _prepare_validation_data_preview(
        self,
        data: List[Dict[str, Any]],
        count: int,
    ) -> str:
        if not data:
            return "无数据"

        preview_count = min(5, len(data))
        preview_data = data[:preview_count]
        preview_lines: List[str] = []

        for idx, record in enumerate(preview_data):
            key_info: List[str] = []
            for field in ["name", "level", "地区", "所属省份", "景区类型"]:
                if field in record and record[field]:
                    key_info.append(f"{field}: {record[field]}")
            if key_info:
                preview_lines.append(f"记录 {idx + 1}: {', '.join(key_info)}")

        preview_text = "\n".join(preview_lines)
        if count > preview_count:
            preview_text += f"\n... 还有 {count - preview_count} 条记录"
        return preview_text

    def _parse_validation_result(
        self,
        validation_text: str,
        query: str,
        count: int,
    ) -> Dict[str, Any]:
        validation_lower = validation_text.lower()
        passed_keywords = [
            "合理",
            "满足",
            "满意",
            "通过",
            "correct",
            "appropriate",
            "sufficient",
        ]
        failed_keywords = [
            "不足",
            "不够",
            "缺乏",
            "问题",
            "失败",
            "incomplete",
            "irrelevant",
            "wrong",
            "failed",
        ]

        passed = any(
            keyword in validation_lower for keyword in passed_keywords)
        failed = any(
            keyword in validation_lower for keyword in failed_keywords)

        if passed and not failed:
            confidence = 0.8
            reason = "结果内容合理，满足用户查询需求"
            guidance = ""
        elif failed and not passed:
            confidence = 0.2
            reason = "结果存在问题，需要改进"
            guidance = self._extract_guidance(validation_text)
        else:
            confidence = 0.5
            reason = "结果存在争议，建议进一步验证"
            guidance = "建议再次查询并补充数据来源"

        return {
            "passed": passed,
            "reason": reason,
            "confidence": confidence,
            "guidance": guidance,
            "raw_validation": validation_text,
        }

    def _extract_guidance(self, validation_text: str) -> str:
        guidance_keywords = [
            "建议",
            "改进",
            "应当",
            "需要",
            "补充",
            "suggest",
            "recommend",
            "should",
            "need",
            "could",
        ]
        guidance_lines = [
            line.strip()
            for line in validation_text.split("\n")
            if any(keyword in line.lower() for keyword in guidance_keywords)
        ]
        if guidance_lines:
            return "\n".join(guidance_lines[:3])
        return "建议补充数据并重新执行查询"


class CheckResultsNode(NodeBase):
    """Decide whether further querying is required based on LLM analysis."""

    def __call__(self, state: AgentState) -> Dict[str, Any]:
        try:
            current_step = state.get("current_step", 0)
            max_iterations = state.get("max_iterations", 3)
            final_data: Optional[List[Dict[str, Any]]
                                 ] = state.get("final_data")
            query = state.get("query", "")
            query_intent = state.get("query_intent", "query")

            self.logger.info(
                "[Node: check_results] Checking results for step %s",
                current_step,
            )

            if current_step >= max_iterations - 1:
                if not final_data:
                    reason = f"达到最大迭代次数 ({current_step + 1}/{max_iterations})，查询无结果"
                    self.logger.warning(
                        "[Node: check_results] No data returned, stopping")
                    return {
                        "current_step": current_step + 1,
                        "should_continue": False,
                        "thought_chain": [
                            {
                                "step": current_step + 5,
                                "type": "result_check",
                                "action": "check_completeness",
                                "output": {
                                    "should_continue": False,
                                    "reason": reason,
                                },
                                "status": "completed",
                            }
                        ],
                    }
                else:
                    reason = f"达到最大迭代次数 ({current_step + 1}/{max_iterations})"
                    self.logger.info(reason)
                    return {
                        "current_step": current_step + 1,
                        "should_continue": False,
                        "thought_chain": [
                            {
                                "step": current_step + 5,
                                "type": "result_check",
                                "action": "check_completeness",
                                "output": {
                                    "should_continue": False,
                                    "reason": reason,
                                },
                                "status": "completed",
                            }
                        ],
                    }

            if self.llm:
                decision = self._make_llm_decision(
                    query=query,
                    final_data=final_data,
                    current_step=current_step,
                    query_intent=query_intent,
                )
                should_continue = decision.get("should_continue", False)
                reason = decision.get("reason", "LLM判断需要继续查询")
                supplement_suggestions = decision.get(
                    "supplement_suggestions", [])
                guidance_for_next_step = decision.get(
                    "guidance_for_next_step", "")
            else:
                data_count = len(final_data)
                if data_count < 3 and query_intent == "query":
                    should_continue = True
                    reason = f"返回结果仅 {data_count} 条，建议补充"
                else:
                    should_continue = False
                    reason = f"返回结果 {data_count} 条，已满足 {query_intent} 需求"
                supplement_suggestions = []
                guidance_for_next_step = ""

            thought_output = {
                "should_continue": should_continue,
                "reason": reason,
                "supplement_suggestions": supplement_suggestions,
                "guidance_for_next_step": guidance_for_next_step,
                "data_count": len(final_data),
                "current_step": current_step,
            }

            thought_step = {
                "step": current_step + 5,
                "type": "result_check",
                "action": "llm_decision_check",
                "output": thought_output,
                "status": "completed",
            }

            result: Dict[str, Any] = {
                "current_step": current_step + 1,
                "should_continue": should_continue,
                "thought_chain": [thought_step],
            }

            if should_continue:
                result["supplement_suggestions"] = supplement_suggestions
                result["enhancement_guidance"] = guidance_for_next_step
                result["supplement_needed"] = True

            return result

        except Exception as exc:
            self.logger.error("[Node: check_results] Error: %s", exc)
            return {
                "should_continue": False,
                "thought_chain": [
                    {
                        "step": state.get("current_step", 0) + 5,
                        "type": "result_check",
                        "error": str(exc),
                        "status": "failed",
                    }
                ],
            }

    # ------------------------------------------------------------------
    def _make_llm_decision(
        self,
        query: str,
        final_data: List[Dict[str, Any]],
        current_step: int,
        query_intent: str,
    ) -> Dict[str, Any]:
        try:
            if not self.llm:
                return {
                    "should_continue": False,
                    "reason": "无LLM可用，默认停止",
                    "supplement_suggestions": [],
                    "guidance_for_next_step": "",
                }

            data_preview = self._prepare_llm_decision_data_preview(final_data)
            prompt = f"""请扮演资深的数据分析顾问，判断是否需要继续补充查询。

## 用户查询
{query}

## 查询意图
{query_intent}

## 当前结果
- 返回条数: {len(final_data)}
- 当前迭代: {current_step}
- 结果预览: {data_preview}

请判断是否需要继续补充查询，并给出票据。"""

            response = self.llm.llm.invoke(prompt)
            decision_text = (
                response.content.strip()
                if hasattr(response, "content")
                else str(response).strip()
            )
            return self._parse_llm_decision(decision_text, query, len(final_data))

        except Exception as exc:
            self.logger.error("LLM decision failed: %s", exc)
            return {
                "should_continue": False,
                "reason": f"LLM 调用失败，默认停止: {str(exc)}",
                "supplement_suggestions": [],
                "guidance_for_next_step": "",
            }

    def _parse_llm_decision(
        self,
        decision_text: str,
        query: str,
        count: int,
    ) -> Dict[str, Any]:
        decision_lower = decision_text.lower()
        should_continue = False
        reason = ""

        if any(
            keyword in decision_lower
            for keyword in ["补充", "继续", "缺失", "需要", "建议", "expand", "more", "missing"]
        ):
            should_continue = True
            reason = "LLM 认为需要继续补充查询"
        elif any(
            keyword in decision_lower
            for keyword in ["停止", "足够", "充分", "sufficient", "enough", "complete"]
        ):
            should_continue = False
            reason = "LLM 认为当前结果已经足够"
        elif count < 3 and len(decision_text) > 100:
            should_continue = True
            reason = f"结果仅 {count} 条且分析较详尽，建议补充"
        else:
            should_continue = False
            reason = "LLM 未明确要求补充，默认停止"

        supplement_suggestions = self._extract_decision_suggestions(
            decision_text)
        guidance_for_next_step = self._generate_decision_guidance(
            decision_text, should_continue
        )

        return {
            "should_continue": should_continue,
            "reason": reason,
            "supplement_suggestions": supplement_suggestions,
            "guidance_for_next_step": guidance_for_next_step,
        }

    def _extract_decision_suggestions(
        self,
        decision_text: str,
    ) -> List[Dict[str, Any]]:
        suggestions: List[Dict[str, Any]] = []
        for line in decision_text.split("\n"):
            line = line.strip()
            if not line or len(line) < 10:
                continue
            if any(
                keyword in line.lower()
                for keyword in ["建议", "应当", "需要", "推荐", "补充", "should", "recommend"]
            ):
                content = self._extract_suggestion_content(line)
                if content:
                    suggestions.append(
                        {
                            "type": self._classify_suggestion_type(content),
                            "description": content,
                            "reason": f"源自 LLM 建议: {content[:50]}...",
                        }
                    )

        if not suggestions:
            suggestions.append(
                {
                    "type": "field_completion",
                    "description": "补充缺失的关键信息",
                    "reason": "建议补充景区名称、门票、开放时间等字段",
                }
            )

        return suggestions[:3]

    def _extract_suggestion_content(self, line: str) -> Optional[str]:
        markers = ["建议", "应当", "需要", "推荐", "补充"]
        for marker in markers:
            if marker in line:
                parts = line.split(marker, 1)
                if len(parts) > 1:
                    content = parts[1].strip().strip("：:，,。.;；")
                    if content and len(content) > 5:
                        return content
        return None

    def _classify_suggestion_type(self, suggestion_content: str) -> str:
        content_lower = suggestion_content.lower()
        if any(keyword in content_lower for keyword in ["字段", "信息", "详情", "描述"]):
            return "field_completion"
        if any(keyword in content_lower for keyword in ["扩展", "更多", "additional", "expand"]):
            return "data_expansion"
        if any(keyword in content_lower for keyword in ["详细", "深度", "分析", "洞察"]):
            return "analysis_enhancement"
        return "general_improvement"

    def _generate_decision_guidance(
        self,
        decision_text: str,
        should_continue: bool,
    ) -> str:
        if should_continue:
            if "字段" in decision_text or "信息" in decision_text:
                return "根据 LLM 建议补充缺失字段"
            if "扩展" in decision_text or "更多" in decision_text:
                return "扩展查询范围，获取更多样本"
            if "详细" in decision_text or "深入" in decision_text:
                return "获取更详细的数据描述"
            return "根据 LLM 建议继续补充查询"
        return "当前结果充足，可生成最终回答"

    def _prepare_llm_decision_data_preview(
        self,
        data: List[Dict[str, Any]],
    ) -> str:
        if not data:
            return "无数据"

        preview_count = min(3, len(data))
        preview_lines: List[str] = []
        for idx, record in enumerate(data[:preview_count]):
            key_info: List[str] = []
            for field in ["name", "level", "地区", "门票", "开放时间", "所属省份", "景区类型"]:
                value = record.get(field)
                key_info.append(f"{field}: {value if value else '缺失'}")
            preview_lines.append(f"记录 {idx + 1}: {', '.join(key_info[:5])}")

        preview_text = "\n".join(preview_lines)
        if len(data) > preview_count:
            preview_text += f"\n... 还有 {len(data) - preview_count} 条记录"
        return preview_text
