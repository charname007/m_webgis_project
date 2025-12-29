from __future__ import annotations

from typing import Any, Dict, List, Optional

from ...schemas import AgentState, ValidationResult
from .base import NodeBase
from .memory_decorators import with_memory_tracking
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate


class ValidateResultsNode(NodeBase):
    """Validate query results using LLM feedback."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = None  # 初始化 parser 属性

    @with_memory_tracking("result_validation")
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
            
            # 使用结构化输出解析器
            try:
                # 初始化解析器
                if self.parser is None:
                    self.parser = PydanticOutputParser(pydantic_object=ValidationResult)

                # 创建提示词模板
                prompt_template = ChatPromptTemplate.from_template("""请扮演资深的数据验证专家，判断以下查询结果是否满足用户需求

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

请基于以上分析给出结构化验证结果：

{format_instructions}""")

                # 构建完整的链式调用: prompt | llm | parser
                structured_chain = (
                    prompt_template.partial(format_instructions=self.parser.get_format_instructions())
                    | self.llm.llm
                    | self.parser
                )

                # 调用链
                validation_result = structured_chain.invoke({
                    "query": query,
                    "query_intent": query_intent,
                    "count": count,
                    "data_preview": data_preview
                })
                self.logger.info(msg=f'validation_result:\n   f{validation_result}')
                return self._parse_structured_validation(validation_result)

            except Exception as structured_exc:
                self.logger.warning(
                    "Structured validation failed, falling back to text parsing: %s",
                    structured_exc
                )
                # 回退到文本解析方法
                return self._validate_with_llm_text(query, data, count, query_intent)

        except Exception as exc:
            self.logger.error("LLM validation failed: %s", exc)
            return {
                "passed": True,
                "reason": f"验证流程出现异常，默认通过: {str(exc)}",
                "confidence": 0.3,
                "guidance": "建议人工复核结果",
            }

    def _validate_with_llm_text(
        self,
        query: str,
        data: List[Dict[str, Any]],
        count: int,
        query_intent: str,
    ) -> Dict[str, Any]:
        """回退方法：使用文本解析的验证"""
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

    def _parse_structured_validation(
        self,
        validation_result: ValidationResult,
    ) -> Dict[str, Any]:
        """解析结构化验证结果"""
        try:
            # 将Pydantic模型转换为字典格式
            result_dict = validation_result.model_dump()

            # 确保返回格式与现有代码兼容
            return {
                "passed": result_dict["validation_passed"],
                "reason": result_dict["summary_reason"],
                "confidence": result_dict["overall_confidence"],
                "guidance": "\n".join(result_dict["improvement_suggestions"]) if result_dict["improvement_suggestions"] else "",
                "raw_validation": f"结构化验证结果: {result_dict}",
                "dimension_scores": result_dict["dimension_scores"],
                "detailed_analysis": result_dict["detailed_analysis"]
            }
        except Exception as exc:
            self.logger.error("Failed to parse structured validation: %s", exc)
            # 如果解析失败，返回默认通过的结果
            return {
                "passed": True,
                "reason": f"结构化验证解析失败: {str(exc)}",
                "confidence": 0.5,
                "guidance": "",
                "raw_validation": f"解析失败: {str(exc)}"
            }

    def _prepare_validation_data_preview(
        self,
        data: List[Dict[str, Any]],
        count: int,
    ) -> str:
        if not data:
            return "无数据"

        preview_count = min(15, len(data))
        preview_data = data[:preview_count]
        preview_lines: List[str] = []

        for idx, record in enumerate(preview_data):
            preview_lines.append(f"记录 {idx + 1}: {str(record)}")
            # key_info: List[str] = []
            # for field in ["name", "level", "地区", "所属省份", "景区类型"]:
            #     if field in record and record[field]:
            #         key_info.append(f"{field}: {record[field]}")
            # if key_info:
            #     preview_lines.append(f"记录 {idx + 1}: {', '.join(key_info)}")

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
    """Decide whether further querying is required based on rule-based analysis."""

    @with_memory_tracking("check_results")
    def __call__(self, state: AgentState) -> Dict[str, Any]:
        try:
            current_step = state.get("current_step", 0)
            max_iterations = state.get("max_iterations", 3)
            final_data: Optional[List[Dict[str, Any]]] = state.get("final_data")
            query_intent = state.get("query_intent", "query")
            validation_passed = state.get("validation_passed", True)

            self.logger.info(
                "[Node: check_results] Checking results for step %s",
                current_step,
            )

            # 检查迭代限制
            if current_step >= max_iterations - 1:
                reason = f"达到最大迭代次数 ({current_step + 1}/{max_iterations})"
                self.logger.info(reason)
                return self._build_stop_result(current_step, reason)

            # 检查验证结果
            if not validation_passed:
                reason = "结果验证失败，需要重新查询"
                self.logger.warning(reason)
                return self._build_continue_result(current_step, reason)

            # 基于规则的迭代决策
            decision = self._make_rule_decision(
                final_data=final_data,
                current_step=current_step,
                query_intent=query_intent,
            )
            
            self.logger.info('[Node: check_results] decision: %s', decision)

            thought_output = {
                "should_continue": decision["should_continue"],
                "reason": decision["reason"],
                "data_count": len(final_data) if final_data else 0,
                "current_step": current_step,
                "decision_type": "rule_based",
            }

            thought_step = {
                "step": current_step + 5,
                "type": "result_check",
                "action": "rule_decision_check",
                "output": thought_output,
                "status": "completed",
            }

            result: Dict[str, Any] = {
                "current_step": current_step + 1,
                "should_continue": decision["should_continue"],
                "thought_chain": [thought_step],
            }

            if decision["should_continue"]:
                result["supplement_needed"] = True
                result["enhancement_guidance"] = decision.get("guidance", "")

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
    def _build_stop_result(self, current_step: int, reason: str) -> Dict[str, Any]:
        """构建停止迭代的结果"""
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

    def _build_continue_result(self, current_step: int, reason: str) -> Dict[str, Any]:
        """构建继续迭代的结果"""
        return {
            "current_step": current_step + 1,
            "should_continue": True,
            "supplement_needed": True,
            "thought_chain": [
                {
                    "step": current_step + 5,
                    "type": "result_check",
                    "action": "check_completeness",
                    "output": {
                        "should_continue": True,
                        "reason": reason,
                    },
                    "status": "completed",
                }
            ],
        }

    def _make_rule_decision(
        self,
        final_data: Optional[List[Dict[str, Any]]],
        current_step: int,
        query_intent: str,
    ) -> Dict[str, Any]:
        """基于规则的迭代决策"""
        data_count = len(final_data) if final_data else 0
        
        # 规则1: 无数据时继续查询
        if data_count == 0:
            return {
                "should_continue": True,
                "reason": "无返回结果，需要继续查询",
                "guidance": "尝试不同的查询条件或扩展查询范围"
            }
        
        # # 规则2: 查询意图为"query"且数据量较少时继续
        # if query_intent == "query" and data_count < 3:
        #     return {
        #         "should_continue": True,
        #         "reason": f"返回结果仅 {data_count} 条，建议补充",
        #         "guidance": "扩展查询范围获取更多样本"
        #     }
        
        # # 规则3: 查询意图为"summary"且数据量较少时继续
        # if query_intent == "summary" and data_count < 5:
        #     return {
        #         "should_continue": True,
        #         "reason": f"统计查询结果仅 {data_count} 条，建议补充",
        #         "guidance": "获取更多数据以支持统计分析"
        #     }
        
        # # 规则4: 数据质量检查 - 检查关键字段完整性
        # if final_data and self._has_missing_key_fields(final_data):
        #     return {
        #         "should_continue": True,
        #         "reason": "关键字段信息缺失，需要补充",
        #         "guidance": "补充景区名称、等级、位置等关键信息"
        #     }
        
        # 默认停止
        return {
            "should_continue": False,
            "reason": f"返回结果 {data_count} 条，已满足 {query_intent} 需求",
            "guidance": ""
        }

    def _has_missing_key_fields(self, data: List[Dict[str, Any]]) -> bool:
        """检查数据中关键字段是否缺失"""
        if not data:
            return False
            
        key_fields = ["name", "level", "所属省份", "地区"]
        missing_count = 0
        
        for record in data:
            for field in key_fields:
                if field not in record or not record[field]:
                    missing_count += 1
                    break  # 每个记录只计一次缺失
        
        # 如果超过30%的记录缺少关键字段，认为需要补充
        missing_ratio = missing_count / len(data)
        return missing_ratio > 0.2
