"""
结果验证器模块 - Sight Server
使用 LLM 验证查询结果是否符合用户需求
"""

import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging

# 设置日志
logger = logging.getLogger(__name__)


# ==================== 输出模型 ====================

class ValidationResult(BaseModel):
    """验证结果模型（结构化输出）"""

    is_valid: bool = Field(
        description="结果是否有效：true=符合要求，false=需要改进"
    )

    validation_message: str = Field(
        description="验证说明，解释为何有效或无效"
    )

    issues: List[str] = Field(
        default_factory=list,
        description="发现的问题列表（如果 is_valid=false）"
    )

    improvement_suggestions: List[str] = Field(
        default_factory=list,
        description="改进建议列表（如何修复问题）"
    )

    confidence: float = Field(
        ge=0.0, le=1.0, default=0.8,
        description="验证置信度（0-1之间）"
    )


# ==================== 验证器类 ====================

class ResultValidator:
    """
    结果验证器

    功能：
    - 使用 LLM 分析 SQL 结果是否符合用户需求
    - 检查数据完整性、准确性、相关性
    - 对于空间查询，检查是否包含必要的坐标信息
    - 对于统计查询，检查是否包含必要的维度和指标
    """

    def __init__(self, llm):
        """
        初始化验证器

        Args:
            llm: LLM 实例（支持结构化输出）
        """
        self.llm = llm
        self.logger = logging.getLogger(__name__)

    def validate(
        self,
        query: str,
        intent_info: Optional[Dict[str, Any]],
        current_result: Dict[str, Any],
        current_step: int
    ) -> ValidationResult:
        """
        验证查询结果是否符合用户需求

        Args:
            query: 用户原始查询
            intent_info: 查询意图信息
            current_result: 当前查询结果
            current_step: 当前步骤

        Returns:
            ValidationResult: 验证结果
        """
        # 提取数据
        data = current_result.get("data", [])
        count = len(data) if data else 0

        # 提取意图信息
        intent_type = intent_info.get("intent_type", "query") if intent_info else "query"
        is_spatial = intent_info.get("is_spatial", False) if intent_info else False

        # 构建验证提示词
        validation_prompt = self._build_validation_prompt(
            query=query,
            intent_type=intent_type,
            is_spatial=is_spatial,
            data=data,
            count=count,
            current_step=current_step
        )

        self.logger.debug(f"验证提示词：\n{validation_prompt}")

        try:
            # 调用 LLM 进行验证
            result = self.llm.invoke_with_structure(
                prompt=validation_prompt,
                structure=ValidationResult
            )

            self.logger.info(
                f"验证完成 - 步骤 {current_step}: "
                f"{'✅ 有效' if result.is_valid else '❌ 无效'} "
                f"(置信度: {result.confidence:.2f})"
            )

            if not result.is_valid:
                self.logger.warning(f"验证问题: {result.issues}")
                self.logger.info(f"改进建议: {result.improvement_suggestions}")

            return result

        except Exception as e:
            self.logger.error(f"验证过程出错: {e}")
            # 出错时返回默认通过（避免阻塞流程）
            return ValidationResult(
                is_valid=True,
                validation_message=f"验证过程出错，默认通过: {str(e)}",
                issues=[],
                improvement_suggestions=[],
                confidence=0.5
            )

    def _build_validation_prompt(
        self,
        query: str,
        intent_type: str,
        is_spatial: bool,
        data: List[Dict[str, Any]],
        count: int,
        current_step: int
    ) -> str:
        """
        构建验证提示词

        Args:
            query: 用户查询
            intent_type: 查询意图类型（query/summary）
            is_spatial: 是否空间查询
            data: 查询结果数据
            count: 结果数量
            current_step: 当前步骤

        Returns:
            str: 验证提示词
        """
        # 获取数据样例（前3条）
        sample_data = data[:3] if data else []
        sample_json = json.dumps(sample_data, ensure_ascii=False, indent=2)

        # 构建基础提示
        prompt = f"""你是专业的数据分析师，负责验证SQL查询结果是否符合用户需求。

**用户问题**: {query}

**查询意图**: {intent_type} (空间查询: {'是' if is_spatial else '否'})

**当前步骤**: 第 {current_step} 步

**查询结果统计**:
- 结果数量: {count} 条
- 数据样例（前3条）:
```json
{sample_json}
```

**验证任务**:

1. **完整性检查**:
   - 结果是否回答了用户的问题？
   - 数据是否包含必要的字段？
   """

        # 根据查询类型添加特定检查
        if intent_type == "summary":
            prompt += """   - 统计查询：是否包含必要的聚合维度和指标？
   - 是否有计数、总和、平均值等统计结果？
"""
        else:  # query
            prompt += """   - 数据查询：是否返回了具体的记录列表？
   - 字段是否完整（名称、地址、坐标等）？
"""

        # 空间查询特殊检查
        if is_spatial:
            prompt += """
2. **空间数据检查**:
   - 是否包含有效的坐标信息（经度、纬度）？
   - 坐标值是否合理（中国范围：经度73-135°，纬度18-54°）？
   - 如果涉及距离计算，是否包含距离字段？
"""

        # 数据质量检查
        prompt += """
3. **数据质量检查**:
   - 数据是否准确合理？
   - 是否存在明显的错误或异常？
   - 字段值是否符合预期（如等级、评分、门票等）？

4. **相关性检查**:
   - 查询结果是否与用户问题直接相关？
   - 是否存在无关的数据？
"""

        # 空结果特殊处理
        if count == 0:
            prompt += """

**注意**: 查询结果为空！请判断这是否合理：
- 如果用户查询的条件过于严格，空结果是合理的 → is_valid=true
- 如果应该有结果但返回为空，可能SQL有问题 → is_valid=false
"""

        # 要求返回结构化输出
        prompt += """

**输出要求**:

请返回结构化的验证结果：
```json
{
  "is_valid": true/false,  // 结果是否有效
  "validation_message": "验证说明（1-2句话）",
  "issues": ["问题1", "问题2"],  // 如果 is_valid=false，列出具体问题
  "improvement_suggestions": ["建议1", "建议2"],  // 改进建议
  "confidence": 0.85  // 验证置信度（0-1）
}
```

**判断标准**:
- is_valid=true: 结果完整、准确、相关，符合用户需求
- is_valid=false: 结果缺失关键信息、不准确、或不相关

**重要**:
- 如果结果基本符合要求，即使有小瑕疵也应该返回 is_valid=true
- 只有在结果明显无法回答用户问题时才返回 is_valid=false
- 空结果如果合理（如查询条件严格），也应返回 is_valid=true
"""

        return prompt

    def is_enabled(self, state: Dict[str, Any]) -> bool:
        """
        检查验证是否启用

        Args:
            state: Agent 状态

        Returns:
            bool: 是否启用验证
        """
        return state.get("is_validation_enabled", True)

    def should_retry(
        self,
        validation_result: ValidationResult,
        retry_count: int,
        max_retries: int
    ) -> bool:
        """
        判断是否需要重试

        Args:
            validation_result: 验证结果
            retry_count: 当前重试次数
            max_retries: 最大重试次数

        Returns:
            bool: 是否需要重试
        """
        # 验证通过，不需要重试
        if validation_result.is_valid:
            return False

        # 已达到最大重试次数
        if retry_count >= max_retries:
            self.logger.warning(f"验证重试次数已达上限 ({max_retries})，停止重试")
            return False

        # 置信度过低，不值得重试
        if validation_result.confidence < 0.3:
            self.logger.warning(f"验证置信度过低 ({validation_result.confidence:.2f})，停止重试")
            return False

        # 需要重试
        self.logger.info(f"验证失败，准备重试 (尝试 {retry_count + 1}/{max_retries})")
        return True


# ==================== 测试代码 ====================

if __name__ == "__main__":
    from core.llm import LLMFactory

    print("=== 测试 ResultValidator ===\n")

    # 初始化 LLM
    llm = LLMFactory.create_llm()
    validator = ResultValidator(llm)

    # 测试案例 1: 有效结果
    print("--- 测试案例 1: 有效的查询结果 ---")
    result1 = validator.validate(
        query="查询浙江省的5A景区",
        intent_info={"intent_type": "query", "is_spatial": False},
        current_result={
            "data": [
                {"name": "西湖", "level": "5A", "province": "浙江省"},
                {"name": "普陀山", "level": "5A", "province": "浙江省"}
            ]
        },
        current_step=1
    )
    print(f"验证结果: {result1.model_dump_json(indent=2)}")
    print()

    # 测试案例 2: 缺少关键字段
    print("--- 测试案例 2: 缺少坐标的空间查询 ---")
    result2 = validator.validate(
        query="查询杭州附近10公里的景区",
        intent_info={"intent_type": "query", "is_spatial": True},
        current_result={
            "data": [
                {"name": "西湖", "level": "5A"}  # 缺少坐标
            ]
        },
        current_step=1
    )
    print(f"验证结果: {result2.model_dump_json(indent=2)}")
    print()

    # 测试案例 3: 空结果
    print("--- 测试案例 3: 空结果 ---")
    result3 = validator.validate(
        query="查询浙江省的6A景区",
        intent_info={"intent_type": "query", "is_spatial": False},
        current_result={"data": []},
        current_step=1
    )
    print(f"验证结果: {result3.model_dump_json(indent=2)}")
