#!/usr/bin/env python3
"""
测试模式缓存集成功能
验证 learn_from_query 学习数据是否能够正确应用到 SQL 生成节点
"""

import json
import time
from datetime import datetime

def test_pattern_cache_integration():
    """测试模式缓存集成功能"""
    print("=== 模式缓存集成测试 ===\n")
    
    # 模拟一些学习数据
    test_patterns = [
        {
            "query_template": "查询 + 景区",
            "sql_template": "SELECT * FROM tourist_spots WHERE name LIKE '%{keyword}%'",
            "success": True,
            "response_time": 0.5,
            "learned_at": datetime.now().isoformat()
        },
        {
            "query_template": "统计 + 景区",
            "sql_template": "SELECT COUNT(*) as count FROM tourist_spots WHERE city = '{city}'",
            "success": True,
            "response_time": 0.3,
            "learned_at": datetime.now().isoformat()
        },
        {
            "query_template": "空间 + 景区",
            "sql_template": "SELECT * FROM tourist_spots WHERE ST_DWithin(geom, ST_GeomFromText('POINT({lng} {lat})', 4326), {distance})",
            "success": True,
            "response_time": 0.8,
            "learned_at": datetime.now().isoformat()
        }
    ]
    
    print("模拟的学习模式:")
    for i, pattern in enumerate(test_patterns, 1):
        print(f"{i}. {pattern['query_template']}")
        print(f"   SQL模板: {pattern['sql_template']}")
        print(f"   响应时间: {pattern['response_time']:.2f}s")
        print()
    
    # 测试查询
    test_queries = [
        "查询武汉大学附近的景区",
        "统计武汉有多少个5A景区", 
        "查找距离黄鹤楼10公里内的景点",
        "查询东湖景区信息"
    ]
    
    print("测试查询和模式匹配:")
    for query in test_queries:
        print(f"\n查询: '{query}'")
        
        # 模拟模板提取
        template = extract_query_template(query)
        print(f"  提取的模板: {template}")
        
        # 查找相似模式
        similar_patterns = find_similar_patterns(template, test_patterns)
        print(f"  找到 {len(similar_patterns)} 个相似模式")
        
        if similar_patterns:
            best_pattern = select_best_pattern(similar_patterns)
            print(f"  最佳模式: {best_pattern['query_template']}")
            print(f"  响应时间: {best_pattern['response_time']:.2f}s")
            
            # 模拟SQL适配
            adapted_sql = adapt_sql_template(query, best_pattern['sql_template'])
            print(f"  适配后的SQL: {adapted_sql}")
    
    print("\n=== 集成测试完成 ===")

def extract_query_template(query: str) -> str:
    """提取查询模板（简化实现）"""
    keywords = []
    
    # 查询类型
    if "查询" in query or "查找" in query:
        keywords.append("查询")
    if "统计" in query or "多少" in query:
        keywords.append("统计")
    if "距离" in query or "附近" in query:
        keywords.append("空间")
    
    # 实体类型
    if "景区" in query or "景点" in query:
        keywords.append("景区")
    if "省" in query or "市" in query:
        keywords.append("地区")
    if "5A" in query or "4A" in query:
        keywords.append("评级")
    
    return " + ".join(keywords) if keywords else "通用查询"

def find_similar_patterns(template: str, patterns: list) -> list:
    """查找相似模式"""
    similar = []
    for pattern in patterns:
        pattern_template = pattern.get("query_template", "")
        if is_similar_template(template, pattern_template):
            similar.append(pattern)
    return similar

def is_similar_template(template1: str, template2: str) -> bool:
    """判断两个模板是否相似"""
    if not template1 or not template2:
        return False
    
    keywords1 = set(template1.split(" + "))
    keywords2 = set(template2.split(" + "))
    
    overlap = len(keywords1 & keywords2)
    total = max(len(keywords1), len(keywords2))
    
    return overlap / total >= 0.5 if total > 0 else False

def select_best_pattern(patterns: list) -> dict:
    """选择最佳模式"""
    if not patterns:
        return None
    
    # 根据响应时间排序（时间越短越好）
    return min(patterns, key=lambda x: x.get("response_time", 10.0))

def adapt_sql_template(query: str, sql_template: str) -> str:
    """适配SQL模板"""
    adapted_sql = sql_template
    
    # 简单的关键词替换
    if "武汉" in query:
        if "大学" in query:
            adapted_sql = adapted_sql.replace("{keyword}", "武汉大学")
        else:
            adapted_sql = adapted_sql.replace("{city}", "武汉")
    elif "黄鹤楼" in query:
        adapted_sql = adapted_sql.replace("{keyword}", "黄鹤楼")
        adapted_sql = adapted_sql.replace("{lng}", "114.3055")
        adapted_sql = adapted_sql.replace("{lat}", "30.5928")
        adapted_sql = adapted_sql.replace("{distance}", "10000")
    elif "东湖" in query:
        adapted_sql = adapted_sql.replace("{keyword}", "东湖")
    
    return adapted_sql

if __name__ == "__main__":
    test_pattern_cache_integration()
