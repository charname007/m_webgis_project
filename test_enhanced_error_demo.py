#!/usr/bin/env python3
"""
增强错误处理演示脚本
演示改进后的错误上下文传递效果
"""

import sys
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_enhanced_error_context():
    """演示增强的错误上下文"""
    print("=== 增强错误上下文演示 ===")
    
    # 模拟一个导致超时的复杂SQL
    complex_sql = """
    SELECT json_agg(json_build_object(
        'name', COALESCE(ts.name, a.name),
        'level', a.level,
        'address', COALESCE(ts."地址", a.address),
        'province', a."所属省份",
        'city', COALESCE(ts."城市", a."所属城市"),
        'description', COALESCE(ts."描述", a.description),
        'rating', a.rating,
        'ticket_price', a."门票价格",
        'opening_hours', a."开放时间"
    ))
    FROM tourist_spots ts 
    FULL OUTER JOIN attractions a ON ts.name = a.name
    WHERE ts.name LIKE '%故宫%' OR a.name LIKE '%故宫%'
    """
    
    print("📋 原始错误信息:")
    print("   '查询超时（120秒）'")
    
    print("\n🔍 增强的错误上下文:")
    enhanced_error = {
        "failed_sql": complex_sql,
        "error_type": "execution_timeout",
        "timeout_seconds": 120,
        "query_complexity": "high",
        "problematic_parts": [
            "complex_json_build",
            "multiple_coalesce_functions", 
            "full_outer_join",
            "no_limit_clause"
        ],
        "optimization_suggestions": [
            "简化JSON构建结构",
            "减少COALESCE函数使用",
            "使用LEFT JOIN代替FULL OUTER JOIN",
            "添加LIMIT限制结果数量",
            "考虑分步查询"
        ]
    }
    
    for key, value in enhanced_error.items():
        if key == "failed_sql":
            print(f"  {key}: {value[:150]}...")
        else:
            print(f"  {key}: {value}")


def demo_llm_prompt_comparison():
    """演示LLM提示对比"""
    print("\n=== LLM提示对比 ===")
    
    print("❌ 改进前提示:")
    old_prompt = "SQL执行超时，请重新生成SQL"
    print(f"   '{old_prompt}'")
    
    print("\n✅ 改进后提示:")
    new_prompt = """
    之前的SQL执行超时（120秒），请分析问题并生成优化的SQL：

    失败的SQL:
    SELECT json_agg(json_build_object('name', COALESCE(ts.name, a.name), 'level', a.level, ...)) 
    FROM tourist_spots ts 
    FULL OUTER JOIN attractions a ON ts.name = a.name
    WHERE ts.name LIKE '%故宫%'

    问题分析:
    - 查询复杂度: 高
    - 问题部分: 复杂JSON构建、多表JOIN、缺少LIMIT
    - 错误类型: 执行超时

    优化建议:
    1. 简化JSON构建结构
    2. 减少JOIN表数量或使用更简单的JOIN类型
    3. 添加LIMIT限制结果数量
    4. 考虑分步查询而不是单次复杂查询

    请生成优化后的SQL:
    """
    print(new_prompt)


def demo_expected_improvement():
    """演示预期改进效果"""
    print("\n=== 预期改进效果 ===")
    
    print("📈 改进前问题:")
    print("   - LLM: '不知道具体问题，重新生成类似SQL'")
    print("   - 结果: '再次超时120秒'")
    print("   - 循环: '无限重复相同错误'")
    
    print("\n🚀 改进后效果:")
    print("   - LLM: '看到具体SQL和问题分析'")
    print("   - 优化: '生成简化的查询结构'")
    print("   - 结果: '查询成功执行，0.5秒返回结果'")
    
    print("\n💡 具体优化示例:")
    print("   原始SQL → 复杂JSON构建 + FULL OUTER JOIN")
    print("   优化SQL → 简单SELECT + LEFT JOIN + LIMIT 100")


def main():
    """主演示函数"""
    print("=== 增强错误处理演示 ===")
    print("演示改进错误上下文传递机制的效果")
    
    try:
        demo_enhanced_error_context()
        demo_llm_prompt_comparison()
        demo_expected_improvement()
        
        print("\n=== 改进总结 ===")
        print("✅ 完整的错误上下文: SQL语句 + 复杂度分析 + 优化建议")
        print("✅ 智能的LLM提示: 具体问题 + 分析指导 + 优化方向")
        print("✅ 有效的学习机制: LLM能够从具体错误中学习")
        print("✅ 避免重复错误: 针对性优化而不是盲目重试")
        
        print("\n=== 下一步行动 ===")
        print("1. 在实际查询中测试改进效果")
        print("2. 监控LLM生成的SQL质量")
        print("3. 验证查询成功率提升")
        print("4. 优化查询复杂度分析算法")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
