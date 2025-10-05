"""
简化测试 - 验证check_results节点的核心逻辑
"""

import sys
import os

# 直接测试核心逻辑，避免复杂的导入
def test_heuristic_parsing():
    """测试启发式解析逻辑"""
    print("=== 测试启发式解析逻辑 ===\n")
    
    # 模拟启发式解析方法
    def parse_llm_analysis_heuristic(analysis_text, query, count):
        """启发式解析LLM分析结果"""
        analysis_lower = analysis_text.lower()

        # 启发式判断是否需要继续
        should_continue = False
        reason = ""

        # 启发式规则1：检查是否提到数据不足或需要补充
        if any(keyword in analysis_lower for keyword in ['不足', '不够', '缺少', '缺失', '需要补充', '建议补充', '应该补充']):
            should_continue = True
            reason = "LLM分析认为数据不足，需要补充"
        # 启发式规则2：检查是否提到数据完整或足够
        elif any(keyword in analysis_lower for keyword in ['完整', '足够', '充分', '满足', '不需要补充', '无需补充']):
            should_continue = False
            reason = "LLM分析认为数据已足够完整"
        # 启发式规则3：检查是否提到具体改进建议
        elif any(keyword in analysis_lower for keyword in ['建议', '改进', '优化', '提升', '增强']):
            should_continue = True
            reason = "LLM分析提供了改进建议，需要补充数据"
        # 启发式规则4：默认情况下，如果数据量较少且分析文本较长，认为需要补充
        elif count < 5 and len(analysis_text) > 100:
            should_continue = True
            reason = f"数据量较少({count}条)且分析详细，建议补充更多数据"
        else:
            # 默认不继续
            should_continue = False
            reason = "LLM分析未明确建议补充数据"

        # 启发式提取补充建议
        supplement_suggestions = extract_suggestions_heuristic(analysis_text)

        # 生成下一步指导
        guidance_for_next_step = generate_guidance_heuristic(analysis_text, should_continue)

        return {
            "should_continue": should_continue,
            "reason": reason,
            "supplement_suggestions": supplement_suggestions,
            "guidance_for_next_step": guidance_for_next_step
        }

    def extract_suggestions_heuristic(analysis_text):
        """启发式提取补充建议"""
        suggestions = []
        lines = analysis_text.split('\n')

        # 启发式规则：基于自然语言理解提取建议
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:  # 跳过短行
                continue

            # 检查是否包含建议性内容
            if any(keyword in line.lower() for keyword in ['建议', '可以', '应该', '需要', '推荐', '考虑']):
                # 尝试提取具体建议内容
                suggestion_content = extract_suggestion_content(line)
                if suggestion_content:
                    # 根据内容类型分类建议
                    suggestion_type = classify_suggestion_type(suggestion_content)
                    suggestions.append({
                        "type": suggestion_type,
                        "description": suggestion_content,
                        "reason": f"基于分析文本的建议: {suggestion_content[:50]}..."
                    })

        # 如果没有找到具体建议，添加默认建议
        if not suggestions:
            suggestions.append({
                "type": "field_completion",
                "description": "补充景区详细信息",
                "reason": "建议补充景区的评分、门票、开放时间等详细信息"
            })

        return suggestions[:3]  # 最多返回3条建议

    def extract_suggestion_content(line):
        """从文本行中提取建议内容"""
        # 简单的启发式提取
        suggestion_markers = ['建议', '可以', '应该', '需要', '推荐', '考虑']
        
        for marker in suggestion_markers:
            if marker in line:
                # 提取标记后的内容
                parts = line.split(marker, 1)
                if len(parts) > 1:
                    content = parts[1].strip()
                    # 清理标点符号
                    content = content.strip('：:，,。.；;')
                    if content and len(content) > 5:  # 确保内容有意义
                        return content
        
        return None

    def classify_suggestion_type(suggestion_content):
        """分类建议类型"""
        content_lower = suggestion_content.lower()

        # 基于关键词分类
        if any(keyword in content_lower for keyword in ['字段', '信息', '数据', '属性']):
            return "field_completion"
        elif any(keyword in content_lower for keyword in ['更多', '扩展', '增加', '补充']):
            return "data_expansion"
        elif any(keyword in content_lower for keyword in ['详细', '描述', '介绍', '说明']):
            return "detail_enhancement"
        elif any(keyword in content_lower for keyword in ['分类', '统计', '分析', '趋势']):
            return "analysis_enhancement"
        else:
            return "general_improvement"

    def generate_guidance_heuristic(analysis_text, should_continue):
        """生成启发式下一步指导"""
        if should_continue:
            # 如果需要继续，基于分析文本生成具体指导
            if '字段' in analysis_text or '信息' in analysis_text:
                return "请根据LLM分析的建议，补充缺失的字段信息"
            elif '更多' in analysis_text or '扩展' in analysis_text:
                return "请扩展查询范围，获取更多相关数据"
            elif '详细' in analysis_text or '描述' in analysis_text:
                return "请获取更详细的数据描述信息"
            else:
                return "请根据LLM分析的建议，补充相关数据"
        else:
            # 如果不需要继续，提供总结性指导
            return "数据已足够完整，可以生成最终答案"

    # 测试用例1: 需要补充数据的分析文本
    print("--- 测试1: 需要补充数据的分析文本 ---")
    analysis_text1 = """
    当前查询结果基本回答了用户的问题，找到了浙江省的5A景区。
    但是数据还不够完整，建议补充以下信息：
    1. 景区的评分和门票价格
    2. 景区的开放时间和游客评价
    3. 更多相关的景区信息
    这样可以提供更全面的旅游建议。
    """
    
    result1 = parse_llm_analysis_heuristic(analysis_text1, "查询浙江省的5A景区", 2)
    print(f"结果: should_continue={result1['should_continue']}")
    print(f"原因: {result1['reason']}")
    print(f"指导: {result1['guidance_for_next_step']}")
    print("补充建议:")
    for suggestion in result1['supplement_suggestions']:
        print(f"  - 类型: {suggestion['type']}")
        print(f"    描述: {suggestion['description']}")
        print(f"    原因: {suggestion['reason']}")
    print()

    # 测试用例2: 数据完整的分析文本
    print("--- 测试2: 数据完整的分析文本 ---")
    analysis_text2 = """
    当前查询结果非常完整，已经找到了所有浙江省的5A景区。
    数据质量很好，包含了所有必要的信息。
    不需要补充更多数据，可以直接生成最终答案。
    """
    
    result2 = parse_llm_analysis_heuristic(analysis_text2, "查询浙江省的5A景区", 10)
    print(f"结果: should_continue={result2['should_continue']}")
    print(f"原因: {result2['reason']}")
    print(f"指导: {result2['guidance_for_next_step']}")
    print()

    # 测试用例3: 模糊的分析文本
    print("--- 测试3: 模糊的分析文本 ---")
    analysis_text3 = """
    查询结果基本符合要求，但还有一些改进空间。
    可以考虑优化数据展示方式。
    """
    
    result3 = parse_llm_analysis_heuristic(analysis_text3, "查询浙江省的5A景区", 3)
    print(f"结果: should_continue={result3['should_continue']}")
    print(f"原因: {result3['reason']}")
    print(f"指导: {result3['guidance_for_next_step']}")
    print()

    print("=== 测试完成 ===")


if __name__ == "__main__":
    test_heuristic_parsing()
