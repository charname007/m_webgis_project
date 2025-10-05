#!/usr/bin/env python3
"""
测试SQL生成器的意图组合优化效果
"""

import sys
import os
import logging

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'python'))

from sight_server.core.processors.sql_generator import SQLGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MockLLM:
    """模拟LLM用于测试"""
    
    def __init__(self):
        self.llm = self
    
    def invoke(self, prompt):
        """模拟LLM响应"""
        logger.info("Mock LLM invoked with prompt")
        logger.debug(f"Prompt preview: {prompt[:200]}...")
        
        # 根据意图类型返回不同的SQL
        if "武汉市景区的空间分布" in prompt:
            if "intent_type=summary" in prompt and "is_spatial=True" in prompt:
                # 空间统计查询 - 返回地理网格分布
                return """
                SELECT 
                  ST_GeoHash(lng_wgs84, lat_wgs84, 4) as grid_id,
                  COUNT(*) as count,
                  ST_AsText(ST_Centroid(ST_Collect(ST_Point(lng_wgs84, lat_wgs84)))) as center
                FROM a_sight 
                WHERE "所属城市" = '武汉市' 
                  AND lng_wgs84 IS NOT NULL 
                  AND lat_wgs84 IS NOT NULL
                GROUP BY ST_GeoHash(lng_wgs84, lat_wgs84, 4)
                ORDER BY count DESC
                """
            elif "intent_type=summary" in prompt and "is_spatial=False" in prompt:
                # 普通统计查询 - 返回简单计数
                return "SELECT COUNT(*) as count FROM a_sight WHERE \"所属城市\" = '武汉市'"
            elif "intent_type=query" in prompt and "is_spatial=True" in prompt:
                # 空间数据查询 - 返回带坐标的记录
                return """
                SELECT json_agg(json_build_object(
                    'name', name,
                    'level', level,
                    'coordinates', json_build_array(lng_wgs84, lat_wgs84)
                )) as result
                FROM a_sight 
                WHERE "所属城市" = '武汉市'
                  AND lng_wgs84 IS NOT NULL 
                  AND lat_wgs84 IS NOT NULL
                """
            else:
                # 普通数据查询
                return """
                SELECT json_agg(json_build_object(
                    'name', name,
                    'level', level
                )) as result
                FROM a_sight WHERE "所属城市" = '武汉市'
                """
        
        # 其他查询的默认响应
        return "SELECT COUNT(*) as count FROM a_sight"


def test_intent_combinations():
    """测试所有意图组合"""
    print("=== 测试SQL生成器的意图组合优化效果 ===\n")
    
    # 创建SQL生成器
    base_prompt = "这是一个测试提示词，用于生成SQL查询。"
    mock_llm = MockLLM()
    sql_generator = SQLGenerator(mock_llm, base_prompt)
    
    # 测试用例：所有意图组合
    test_cases = [
        {
            "name": "Summary + Spatial (空间统计查询)",
            "query": "武汉市景区的空间分布",
            "intent_info": {
                "intent_type": "summary",
                "is_spatial": True,
                "confidence": 0.9,
                "keywords_matched": ["分布", "空间"]
            }
        },
        {
            "name": "Summary + Non-Spatial (普通统计查询)",
            "query": "武汉市景区的数量统计",
            "intent_info": {
                "intent_type": "summary",
                "is_spatial": False,
                "confidence": 0.8,
                "keywords_matched": ["数量", "统计"]
            }
        },
        {
            "name": "Query + Spatial (空间数据查询)",
            "query": "武汉市景区的具体位置",
            "intent_info": {
                "intent_type": "query",
                "is_spatial": True,
                "confidence": 0.85,
                "keywords_matched": ["位置", "坐标"]
            }
        },
        {
            "name": "Query + Non-Spatial (普通数据查询)",
            "query": "武汉市的所有景区",
            "intent_info": {
                "intent_type": "query",
                "is_spatial": False,
                "confidence": 0.7,
                "keywords_matched": ["所有", "景区"]
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        print(f"查询: {test_case['query']}")
        print(f"意图: {test_case['intent_info']['intent_type']}, 空间: {test_case['intent_info']['is_spatial']}")
        
        try:
            # 生成SQL
            sql = sql_generator.generate_initial_sql(
                query=test_case['query'],
                intent_info=test_case['intent_info']
            )
            
            print(f"生成的SQL:")
            print(sql)
            print("-" * 50)
            
        except Exception as e:
            print(f"生成SQL失败: {e}")
            print("-" * 50)


def test_original_problem():
    """测试原始问题：武汉市景区的空间分布"""
    print("\n=== 测试原始问题：武汉市景区的空间分布 ===\n")
    
    base_prompt = "这是一个测试提示词，用于生成SQL查询。"
    mock_llm = MockLLM()
    sql_generator = SQLGenerator(mock_llm, base_prompt)
    
    # 原始问题的意图分析
    intent_info = {
        "intent_type": "summary",
        "is_spatial": True,
        "confidence": 0.9,
        "keywords_matched": ["分布", "空间"],
        "reasoning": "用户查询'武汉市景区的空间分布'中，关键词'分布'明确指向统计汇总意图，用户需要了解景区在武汉市范围内的空间分布特征，而不是获取具体的景区列表信息。同时，'空间分布'明确涉及位置、地理分布等空间概念，属于空间查询范畴。"
    }
    
    query = "武汉市景区的空间分布"
    
    print(f"查询: {query}")
    print(f"意图分析: {intent_info}")
    
    try:
        sql = sql_generator.generate_initial_sql(
            query=query,
            intent_info=intent_info
        )
        
        print(f"\n优化后的SQL:")
        print(sql)
        
        # 验证SQL是否符合空间统计查询的要求
        sql_lower = sql.lower()
        is_spatial_summary = (
            'st_geohash' in sql_lower or 
            'st_collect' in sql_lower or 
            'st_centroid' in sql_lower or
            'round(' in sql_lower
        ) and 'group by' in sql_lower
        
        print(f"\n验证结果:")
        print(f"- 是否包含空间聚合函数: {'✓' if is_spatial_summary else '✗'}")
        print(f"- 是否返回分布统计: {'✓' if 'count' in sql_lower and is_spatial_summary else '✗'}")
        print(f"- 是否避免简单计数: {'✓' if not ('count(*)' in sql_lower and not is_spatial_summary) else '✗'}")
        
    except Exception as e:
        print(f"生成SQL失败: {e}")


if __name__ == "__main__":
    test_intent_combinations()
    test_original_problem()
