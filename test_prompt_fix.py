"""
测试提示词模板修复效果
验证提示词模板是否已经更新，避免FULL OUTER JOIN错误
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_prompt_templates():
    """测试提示词模板内容"""
    print("=== 测试提示词模板修复效果 ===\n")
    
    try:
        # 直接导入PromptManager而不依赖LLM
        from python.sight_server.core.prompts import PromptManager
        
        # 获取景区查询提示词
        scenic_prompt = PromptManager.get_scenic_query_prompt()
        
        print("--- 检查景区查询提示词 ---")
        
        # 检查是否包含FULL OUTER JOIN警告
        if "FULL OUTER JOIN" in scenic_prompt.upper():
            print("❌ 提示词中仍然包含FULL OUTER JOIN")
        else:
            print("✅ 提示词中已移除FULL OUTER JOIN")
            
        # 检查是否包含UNION ALL策略
        if "UNION ALL" in scenic_prompt.upper():
            print("✅ 提示词中包含UNION ALL策略")
        else:
            print("❌ 提示词中缺少UNION ALL策略")
            
        # 检查是否包含正确的连接策略说明
        if "需要完整数据：使用 UNION ALL 策略" in scenic_prompt:
            print("✅ 提示词中包含正确的连接策略说明")
        else:
            print("❌ 提示词中缺少连接策略说明")
            
        # 检查是否包含FROM子句要求
        if "必须包含完整的 FROM 子句" in scenic_prompt:
            print("✅ 提示词中包含FROM子句要求")
        else:
            print("❌ 提示词中缺少FROM子句要求")
            
        print(f"\n提示词长度: {len(scenic_prompt)} 字符")
        print(f"提示词前500字符预览:\n{scenic_prompt[:500]}...")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_sql_generator_prompts():
    """测试SQL生成器的提示词模板"""
    print("\n\n=== 测试SQL生成器提示词模板 ===")
    
    try:
        # 读取SQL生成器文件内容
        sql_generator_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "python/sight_server/core/processors/sql_generator.py"
        )
        
        with open(sql_generator_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("--- 检查SQL生成器提示词 ---")
        
        # 检查初始查询提示词
        if "使用 UNION ALL 策略" in content:
            print("✅ SQL生成器提示词包含UNION ALL策略")
        else:
            print("❌ SQL生成器提示词缺少UNION ALL策略")
            
        if "必须 LEFT JOIN tourist_spot 表" in content:
            print("⚠️ SQL生成器提示词仍然强制要求LEFT JOIN")
        else:
            print("✅ SQL生成器提示词不再强制要求LEFT JOIN")
            
        # 检查修复SQL提示词
        if "需要完整数据：使用 UNION ALL 策略" in content:
            print("✅ 修复SQL提示词包含正确的连接策略")
        else:
            print("❌ 修复SQL提示词缺少连接策略")
            
        print(f"\nSQL生成器文件大小: {len(content)} 字符")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_prompt_templates()
    test_sql_generator_prompts()
