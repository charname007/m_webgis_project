"""
准确的system prompt测试脚本

验证数据库schema是否真正被LLM使用
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import BaseLLM

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_system_prompt_accurate():
    """准确测试system prompt功能"""
    print("=== 准确测试system prompt功能 ===")
    
    try:
        # 1. 创建模拟schema
        print("\n1. 创建模拟schema...")
        mock_schema = """
=== 数据库Schema信息 ===

数据库: PostgreSQL 14.0
PostGIS: 3.2.0
表数量: 2
空间表数量: 1

--- 表结构 (2个表) ---

表名: a_sight [空间表]
  字段:
    - id: integer NOT NULL [PK]
    - name: character varying(100) NOT NULL
    - level: character varying(10) NULL
    - lng_wgs84: numeric NULL
    - lat_wgs84: numeric NULL
  空间列: geom (POINT, SRID=4326)
  主键: id

表名: tourist_spot
  字段:
    - id: integer NOT NULL [PK]
    - name: character varying(100) NOT NULL
    - rating: numeric NULL
    - ticket_price: character varying(50) NULL
    - description: text NULL
  主键: id
"""
        
        # 2. 创建BaseLLM实例并更新system context
        print("\n2. 创建BaseLLM实例并更新system context...")
        llm = BaseLLM()
        llm.update_system_context({
            "database_schema": mock_schema
        })
        print(f"✓ system context更新成功")
        
        # 3. 使用正确的方法测试LLM调用
        print("\n3. 使用正确的方法测试LLM调用...")
        test_query = "请详细介绍a_sight表的结构，包括所有字段和数据类型"
        
        # 使用BaseLLM提供的标准方法，而不是直接调用底层LLM
        response = llm.invoke_without_history(test_query)
        
        print(f"✓ LLM调用成功")
        print(f"  查询: {test_query}")
        print(f"  响应长度: {len(response)} 字符")
        print(f"  响应预览: {response[:300]}...")
        
        # 4. 详细验证schema是否在响应中
        print("\n4. 详细验证schema是否在响应中...")
        schema_keywords = ['a_sight', 'tourist_spot', 'geom', 'lng_wgs84', 'lat_wgs84', 'integer', 'character varying', 'numeric', 'text']
        found_keywords = [kw for kw in schema_keywords if kw in response.lower()]
        
        if found_keywords:
            print(f"✓ 验证成功 - 在响应中找到schema关键词: {found_keywords}")
            print(f"  找到的关键词数量: {len(found_keywords)}/{len(schema_keywords)}")
        else:
            print(f"❌ 验证失败 - 未在响应中找到任何预期的schema关键词")
            print(f"  这可能说明system prompt没有正确工作")
        
        # 5. 检查响应是否包含"无法访问"等拒绝信息
        print("\n5. 检查响应是否包含拒绝信息...")
        rejection_phrases = ['无法直接访问', '无法提供', '没有权限', '无法查看', '无法获取']
        has_rejection = any(phrase in response for phrase in rejection_phrases)
        
        if has_rejection:
            print(f"⚠ 警告 - 响应中包含拒绝信息，说明LLM可能没有使用system context")
        else:
            print(f"✓ 良好 - 响应中没有拒绝信息")
        
        return len(found_keywords) > 0 and not has_rejection
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_without_schema():
    """测试没有schema时的行为"""
    print("\n=== 对比测试：没有schema时的行为 ===")
    
    try:
        # 1. 创建BaseLLM实例（不添加schema）
        print("\n1. 创建BaseLLM实例（不添加schema）...")
        llm = BaseLLM()
        print(f"✓ BaseLLM创建成功，system_context: {list(llm.system_context.keys())}")
        
        # 2. 测试相同的查询
        print("\n2. 测试相同的查询...")
        test_query = "请详细介绍a_sight表的结构，包括所有字段和数据类型"
        response = llm.invoke_without_history(test_query)
        
        print(f"✓ LLM调用成功")
        print(f"  查询: {test_query}")
        print(f"  响应长度: {len(response)} 字符")
        print(f"  响应预览: {response[:300]}...")
        
        # 3. 检查是否包含拒绝信息
        print("\n3. 检查是否包含拒绝信息...")
        rejection_phrases = ['无法直接访问', '无法提供', '没有权限', '无法查看', '无法获取']
        has_rejection = any(phrase in response for phrase in rejection_phrases)
        
        if has_rejection:
            print(f"✓ 预期行为 - 没有schema时LLM确实无法访问表结构")
        else:
            print(f"⚠ 意外行为 - 没有schema时LLM仍然能回答表结构问题")
        
        return has_rejection
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("开始准确测试system prompt功能...")
    
    # 测试1: 有schema时的行为
    test1_passed = test_system_prompt_accurate()
    
    # 测试2: 没有schema时的行为（对比）
    test2_passed = test_without_schema()
    
    # 总结
    print("\n=== 测试总结 ===")
    print(f"有schema时的system prompt测试: {'✓ 通过' if test1_passed else '✗ 失败'}")
    print(f"没有schema时的对比测试: {'✓ 通过' if test2_passed else '✗ 失败'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过！system prompt功能正常！")
        print("LLM现在能够正确使用system context中的数据库schema信息")
    else:
        print("\n❌ 部分测试失败，需要进一步调试")
        if not test1_passed:
            print("  - 有schema时LLM没有正确使用schema信息")
        if not test2_passed:
            print("  - 没有schema时LLM行为异常")


if __name__ == "__main__":
    main()
