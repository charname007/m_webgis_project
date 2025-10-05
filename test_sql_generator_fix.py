"""
测试SQL生成器修复效果
验证SQL生成器是否能够生成正确的SQL语句，避免FULL OUTER JOIN错误
"""

import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量以使用正确的配置
os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))

from python.sight_server.core.llm import BaseLLM
from python.sight_server.core.processors.sql_generator import SQLGenerator
from python.sight_server.core.prompts import PromptManager, PromptType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_sql_generation():
    """测试SQL生成功能"""
    print("=== 测试SQL生成器修复效果 ===\n")
    
    try:
        # 初始化LLM
        llm = BaseLLM()
        
        # 获取景区查询提示词
        base_prompt = PromptManager.get_scenic_query_prompt()
        
        # 初始化SQL生成器
        sql_generator = SQLGenerator(llm, base_prompt)
        
        # 测试查询列表
        test_queries = [
            "查询浙江省的5A景区",
            "统计浙江省有多少个4A景区", 
            "查找距离杭州10公里内的景点",
            "查询杭州市的景区列表"
        ]
        
        print("--- 测试SQL生成 ---")
        for query in test_queries:
            print(f"\n查询: {query}")
            try:
                # 生成SQL
                sql = sql_generator.generate_initial_sql(query)
                print(f"生成的SQL: {sql[:200]}...")
                
                # 检查是否包含FULL OUTER JOIN
                if "FULL OUTER JOIN" in sql.upper():
                    print("❌ 错误：仍然包含FULL OUTER JOIN")
                elif "UNION ALL" in sql.upper():
                    print("✅ 正确：使用了UNION ALL策略")
                elif "LEFT JOIN" in sql.upper():
                    print("✅ 正确：使用了LEFT JOIN策略")
                elif "COUNT" in sql.upper() or "SUM" in sql.upper() or "AVG" in sql.upper():
                    print("✅ 正确：使用了聚合函数")
                else:
                    print("⚠️  警告：未识别连接策略")
                    
                # 检查是否包含完整的FROM子句
                if "FROM" in sql.upper():
                    print("✅ 包含FROM子句")
                else:
                    print("❌ 缺少FROM子句")
                    
            except Exception as e:
                print(f"❌ SQL生成失败: {e}")
                
    except Exception as e:
        print(f"❌ 测试初始化失败: {e}")
        import traceback
        traceback.print_exc()

def test_error_handling():
    """测试错误处理功能"""
    print("\n\n=== 测试错误处理功能 ===")
    
    try:
        # 初始化组件
        llm = BaseLLM()
        base_prompt = PromptManager.get_scenic_query_prompt()
        sql_generator = SQLGenerator(llm, base_prompt)
        
        # 模拟错误SQL
        bad_sql = "SELECT * FROM a_sight FULL OUTER JOIN tourist_spot ON a_sight.name = tourist_spot.name"
        error_msg = "错误: 只有在合并连接或哈希连接的查询条件中才支持FULL JOIN"
        
        print(f"原始错误SQL: {bad_sql}")
        print(f"错误信息: {error_msg}")
        
        # 尝试修复
        fixed_sql = sql_generator.fix_sql_with_error(bad_sql, error_msg, "查询浙江省的景区")
        print(f"修复后的SQL: {fixed_sql[:200]}...")
        
        # 检查修复效果
        if "FULL OUTER JOIN" in fixed_sql.upper():
            print("❌ 修复失败：仍然包含FULL OUTER JOIN")
        else:
            print("✅ 修复成功：移除了FULL OUTER JOIN")
            
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")

if __name__ == "__main__":
    test_sql_generation()
    test_error_handling()
