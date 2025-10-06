#!/usr/bin/env python3
"""
测试 SQLGenerator 模板修复
"""

import sys
import os
import logging

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python', 'sight_server'))

from core.processors.sql_generator import SQLGenerator
from core.llm import BaseLLM

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_sql_generator_templates():
    """测试 SQLGenerator 模板初始化"""
    print("=== 测试 SQLGenerator 模板修复 ===")
    
    try:
        # 创建模拟 LLM
        class MockLLM:
            def __init__(self):
                self.llm = self
            
            def invoke(self, prompt):
                # 返回一个简单的 SQL 响应
                return "SELECT COUNT(*) as count FROM a_sight WHERE level = '5A'"
        
        # 创建 SQLGenerator 实例
        print("1. 创建 SQLGenerator 实例...")
        llm = MockLLM()
        base_prompt = "测试基础提示词"
        generator = SQLGenerator(llm, base_prompt)
        
        print("2. 测试模板属性是否存在...")
        # 检查模板属性
        if hasattr(generator, 'sql_generation_template') and generator.sql_generation_template:
            print("✓ sql_generation_template 存在且已初始化")
        else:
            print("✗ sql_generation_template 不存在或为空")
            return False
        
        if hasattr(generator, 'followup_query_template') and generator.followup_query_template:
            print("✓ followup_query_template 存在且已初始化")
        else:
            print("✗ followup_query_template 不存在或为空")
            return False
        
        print("3. 测试模板构建方法...")
        # 测试模板构建方法
        try:
            generation_prompt = generator._build_sql_generation_prompt("fuzzy")
            print("✓ _build_sql_generation_prompt 成功")
        except Exception as e:
            print(f"✗ _build_sql_generation_prompt 失败: {e}")
            return False
        
        try:
            followup_prompt = generator._build_followup_prompt("fuzzy")
            print("✓ _build_followup_prompt 成功")
        except Exception as e:
            print(f"✗ _build_followup_prompt 失败: {e}")
            return False
        
        print("4. 测试 SQL 生成...")
        # 测试 SQL 生成
        try:
            sql = generator.generate_initial_sql("查询5A景区")
            print(f"✓ SQL 生成成功: {sql[:50]}...")
        except Exception as e:
            print(f"✗ SQL 生成失败: {e}")
            return False
        
        print("\n🎉 所有测试通过！SQLGenerator 模板问题已修复")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sql_generator_templates()
    sys.exit(0 if success else 1)
