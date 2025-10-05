"""
简单测试结果验证功能
"""

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_validation_logic():
    """测试验证逻辑"""
    print("=== 测试验证逻辑 ===\n")
    
    # 模拟验证结果解析
    def parse_validation_result(validation_text, query, count):
        """解析LLM验证结果"""
        validation_lower = validation_text.lower()

        # 判断验证是否通过
        passed_keywords = ['良好', '合适', '符合', '正确', '通过', 'good', 'suitable', 'appropriate', 'correct']
        failed_keywords = ['不佳', '不完整', '不相关', '错误', '失败', 'poor', 'incomplete', 'irrelevant', 'wrong', 'failed']

        passed = any(keyword in validation_lower for keyword in passed_keywords)
        failed = any(keyword in validation_lower for keyword in failed_keywords)

        # 计算置信度
        if passed and not failed:
            confidence = 0.8
            reason = "结果质量良好，符合用户查询要求"
            guidance = ""
        elif failed and not passed:
            confidence = 0.2
            reason = "结果质量不佳，需要改进"
            # 提取改进建议
            guidance = extract_guidance(validation_text)
        else:
            # 不确定的情况
            confidence = 0.5
            reason = "结果质量一般，建议进一步验证"
            guidance = "请检查查询条件和数据源"

        return {
            "passed": passed,
            "reason": reason,
            "confidence": confidence,
            "guidance": guidance,
            "raw_validation": validation_text
        }

    def extract_guidance(validation_text):
        """从验证文本中提取改进建议"""
        guidance_keywords = ['建议', '改进', '应该', '需要', '可以', 'suggest', 'recommend', 'should', 'need', 'could']
        
        lines = validation_text.split('\n')
        guidance_lines = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in guidance_keywords):
                guidance_lines.append(line.strip())
        
        if guidance_lines:
            return "\n".join(guidance_lines[:3])  # 最多返回3条建议
        
        return "请调整查询条件或检查数据源"

    # 测试用例
    test_cases = [
        {
            "name": "良好结果",
            "validation_text": "结果质量良好，数据完整且相关，符合用户查询要求。",
            "expected_passed": True
        },
        {
            "name": "不佳结果",
            "validation_text": "结果质量不佳，数据不完整，建议补充更多信息。",
            "expected_passed": False
        },
        {
            "name": "混合结果",
            "validation_text": "结果一般，部分数据符合要求，但需要进一步验证。",
            "expected_passed": True  # 默认通过
        },
        {
            "name": "英文良好结果",
            "validation_text": "The results are good and suitable for the user query.",
            "expected_passed": True
        },
        {
            "name": "英文不佳结果",
            "validation_text": "The results are poor and incomplete, need improvement.",
            "expected_passed": False
        }
    ]

    for test_case in test_cases:
        print(f"--- 测试: {test_case['name']} ---")
        result = parse_validation_result(
            test_case['validation_text'],
            "测试查询",
            10
        )
        print(f"验证文本: {test_case['validation_text']}")
        print(f"解析结果: {result}")
        print(f"是否通过: {result['passed']} (期望: {test_case['expected_passed']})")
        print(f"置信度: {result['confidence']}")
        print(f"原因: {result['reason']}")
        if result['guidance']:
            print(f"改进建议: {result['guidance']}")
        print()

def test_enhanced_answer_logic():
    """测试增强答案逻辑"""
    print("=== 测试增强答案逻辑 ===\n")
    
    def generate_basic_analysis(query, data, count):
        """生成基本分析回答（回退方法）"""
        answer_parts = [f"根据您的查询「{query}」，共找到 {count} 条相关记录。"]

        # 添加基本统计信息
        if data and count > 0:
            # 检查是否有等级信息
            if 'level' in data[0]:
                levels = {}
                for record in data:
                    level = record.get('level')
                    if level:
                        levels[level] = levels.get(level, 0) + 1

                if levels:
                    level_text = "，其中" + "、".join(
                        f"{level}级{num}个" for level, num in sorted(levels.items())
                    )
                    answer_parts.append(level_text)

            # 检查是否有评分信息
            if '评分' in data[0]:
                valid_scores = [float(r['评分']) for r in data if r.get('评分') and is_numeric(r['评分'])]
                if valid_scores:
                    avg_score = sum(valid_scores) / len(valid_scores)
                    answer_parts.append(f"，平均评分 {avg_score:.1f}")

        return "".join(answer_parts) + "。"

    def is_numeric(value):
        """检查值是否为数字"""
        try:
            float(str(value))
            return True
        except (ValueError, TypeError):
            return False

    # 测试数据
    test_data = [
        {"name": "西湖", "level": "5A", "评分": "4.8", "门票": "免费"},
        {"name": "千岛湖", "level": "5A", "评分": "4.6", "门票": "150元"},
        {"name": "灵隐寺", "level": "4A", "评分": "4.7", "门票": "75元"}
    ]

    # 测试用例
    test_cases = [
        {
            "name": "正常数据",
            "query": "查询浙江省的5A景区",
            "data": test_data,
            "count": 3
        },
        {
            "name": "无数据",
            "query": "查询西藏的5A景区",
            "data": None,
            "count": 0
        },
        {
            "name": "部分数据",
            "query": "查询杭州市的景区",
            "data": test_data[:2],
            "count": 2
        }
    ]

    for test_case in test_cases:
        print(f"--- 测试: {test_case['name']} ---")
        answer = generate_basic_analysis(
            test_case['query'],
            test_case['data'],
            test_case['count']
        )
        print(f"查询: {test_case['query']}")
        print(f"数据数量: {test_case['count']}")
        print(f"生成答案: {answer}")
        print()

if __name__ == "__main__":
    print("开始测试增强答案生成器和结果验证功能...\n")
    
    try:
        test_validation_logic()
        test_enhanced_answer_logic()
        
        print("✓ 所有测试完成！")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
