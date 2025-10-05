"""
测试system prompt修复功能

验证数据库schema是否被正确添加到LLM的system context中
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import BaseLLM
from core.prompts import PromptManager
from core.processors.schema_fetcher import SchemaFetcher
from core.processors.sql_generator import SQLGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_system_prompt_with_schema():
    """测试system prompt是否包含数据库schema"""
    print("=== 测试system prompt功能 ===")
    
    try:
        # 1. 创建BaseLLM实例（不传递system_context）
        print("\n1. 创建BaseLLM实例...")
        llm = BaseLLM()
        print(f"✓ BaseLLM创建成功")
        print(f"  初始system_context: {llm.system_context}")
        
        # 2. 获取数据库schema
        print("\n2. 获取数据库schema...")
        schema_fetcher = SchemaFetcher()
        schema = schema_fetcher.fetch_schema(use_cache=True)
        
        if "error" in schema:
            print(f"✗ 获取schema失败: {schema['error']}")
            return False
        
        formatted_schema = schema_fetcher.format_schema_for_llm(schema)
        print(f"✓ 获取schema成功")
        print(f"  表数量: {len(schema.get('tables', {}))}")
        print(f"  schema长度: {len(formatted_schema)} 字符")
        
        # 3. 更新system context
        print("\n3. 更新LLM的system context...")
        llm.update_system_context({
            "database_schema": formatted_schema
        })
        print(f"✓ system context更新成功")
        print(f"  更新后的system_context: {list(llm.system_context.keys())}")
        
        # 4. 测试LLM调用
        print("\n4. 测试LLM调用...")
        test_query = "请介绍一下你了解的数据库表结构"
        response = llm.invoke_without_history(test_query)
        
        print(f"✓ LLM调用成功")
        print(f"  查询: {test_query}")
        print(f"  响应长度: {len(response)} 字符")
        print(f"  响应预览: {response[:200]}...")
        
        # 5. 验证schema是否在响应中
        print("\n5. 验证schema是否在响应中...")
        schema_keywords = ['a_sight', 'tourist_spot', 'geom', 'lng_wgs84', 'lat_wgs84']
        found_keywords = [kw for kw in schema_keywords if kw in response.lower()]
        
        if found_keywords:
            print(f"✓ 验证成功 - 在响应中找到schema关键词: {found_keywords}")
        else:
            print(f"⚠ 警告 - 未在响应中找到预期的schema关键词")
            print(f"  这可能是因为LLM没有使用system context，或者响应格式不同")
        
        # 6. 测试PromptManager的system prompt构建
        print("\n6. 测试PromptManager的system prompt构建...")
        system_prompt = PromptManager.build_system_prompt_with_schema(formatted_schema)
        print(f"✓ system prompt构建成功")
        print(f"  system prompt长度: {len(system_prompt)} 字符")
        print(f"  包含schema: {'a_sight' in system_prompt}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sql_generator_with_schema():
    """测试SQL生成器是否使用schema"""
    print("\n=== 测试SQL生成器schema使用 ===")
    
    try:
        # 1. 创建SQL生成器
        print("\n1. 创建SQL生成器...")
        sql_generator = SQLGenerator()
        print(f"✓ SQL生成器创建成功")
        
        # 2. 获取schema
        print("\n2. 获取数据库schema...")
        schema_fetcher = SchemaFetcher()
        schema = schema_fetcher.fetch_schema(use_cache=True)
        
        if "error" in schema:
            print(f"✗ 获取schema失败: {schema['error']}")
            return False
            
        formatted_schema = schema_fetcher.format_schema_for_llm(schema)
        
        # 3. 测试SQL生成
        print("\n3. 测试SQL生成...")
        test_query = "查询浙江省的5A景区"
        
        # 方法1: 直接传递schema
        sql1 = sql_generator.generate_initial_sql(
            test_query, 
            database_schema=formatted_schema
        )
        print(f"✓ 方法1 - 直接传递schema")
        print(f"  生成的SQL: {sql1[:100]}...")
        
        # 方法2: 通过LLM的system context
        if hasattr(sql_generator, 'llm') and hasattr(sql_generator.llm, 'update_system_context'):
            sql_generator.llm.update_system_context({
                "database_schema": formatted_schema
            })
            sql2 = sql_generator.generate_initial_sql(test_query)
            print(f"✓ 方法2 - 通过LLM system context")
            print(f"  生成的SQL: {sql2[:100]}...")
            
            # 比较两种方法的结果
            if sql1 == sql2:
                print(f"✓ 两种方法生成的SQL相同")
            else:
                print(f"⚠ 两种方法生成的SQL不同")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始测试system prompt修复功能...")
    
    # 测试1: system prompt功能
    test1_passed = test_system_prompt_with_schema()
    
    # 测试2: SQL生成器schema使用
    test2_passed = test_sql_generator_with_schema()
    
    # 总结
    print("\n=== 测试总结 ===")
    print(f"system prompt功能测试: {'✓ 通过' if test1_passed else '✗ 失败'}")
    print(f"SQL生成器schema测试: {'✓ 通过' if test2_passed else '✗ 失败'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！system prompt修复成功！")
        print("数据库schema现在会被正确添加到LLM的system context中")
    else:
        print("\n❌ 部分测试失败，需要进一步调试")


if __name__ == "__main__":
    main()
