#!/usr/bin/env python3
"""
测试智能代理API接口的脚本
测试通用型REST API接口，验证智能查询类型判断和标准化返回格式
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8001"

def test_health_check():
    """测试健康检查端点"""
    print("=== 测试健康检查 ===")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return True
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def test_query_analysis(question):
    """测试查询类型分析"""
    print(f"\n=== 测试查询类型分析: '{question}' ===")
    try:
        response = requests.post(f"{BASE_URL}/agent/analyze", json={"question": question})
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"分析结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result
    except Exception as e:
        print(f"查询分析失败: {e}")
        return None

def test_intelligent_agent_query(question, execute_sql=True, return_geojson=True):
    """测试智能代理查询"""
    print(f"\n=== 测试智能代理查询: '{question}' ===")
    try:
        data = {
            "question": question,
            "execute_sql": execute_sql,
            "return_geojson": return_geojson
        }
        response = requests.post(f"{BASE_URL}/agent/query", json=data)
        print(f"状态码: {response.status_code}")
        result = response.json()
        
        # 打印关键信息
        print(f"查询状态: {result.get('status')}")
        print(f"查询类型: {result.get('question', {}).get('type', 'unknown')}")
        
        # 打印SQL查询
        sql_queries = result.get('sql', [])
        if sql_queries:
            print(f"生成的SQL查询数量: {len(sql_queries)}")
            for i, sql in enumerate(sql_queries):
                print(f"SQL {i+1}: {sql[:200]}...")
        
        # 打印GeoJSON信息
        geojson = result.get('geojson')
        if geojson:
            feature_count = len(geojson.get('features', []))
            print(f"GeoJSON要素数量: {feature_count}")
        
        # 打印答案摘要
        answer = result.get('answer', {})
        if answer:
            text = answer.get('text', '')
            if text:
                print(f"答案摘要: {text[:300]}...")
        
        return result
    except Exception as e:
        print(f"智能查询失败: {e}")
        return None

def test_spatial_queries():
    """测试空间查询"""
    print("\n" + "="*50)
    print("测试空间查询")
    print("="*50)
    
    spatial_questions = [
        "查找距离珞珈山最近的点",
        "查询武汉大学周围的建筑",
        "显示所有道路数据",
        "查找包含在某个区域内的点",
        "计算两点之间的距离"
    ]
    
    for question in spatial_questions:
        test_intelligent_agent_query(question)
        time.sleep(1)  # 避免请求过快

def test_summary_queries():
    """测试数据总结查询"""
    print("\n" + "="*50)
    print("测试数据总结查询")
    print("="*50)
    
    summary_questions = [
        "统计whupoi表中的数据总数",
        "分析道路类型的分布情况",
        "总结建筑数据的特征",
        "计算平均距离"
    ]
    
    for question in summary_questions:
        test_intelligent_agent_query(question, return_geojson=False)
        time.sleep(1)

def test_general_queries():
    """测试普通查询"""
    print("\n" + "="*50)
    print("测试普通查询")
    print("="*50)
    
    general_questions = [
        "查询所有表名",
        "显示数据库信息",
        "获取系统状态"
    ]
    
    for question in general_questions:
        test_intelligent_agent_query(question, return_geojson=False)
        time.sleep(1)

def test_get_endpoint():
    """测试GET端点"""
    print("\n" + "="*50)
    print("测试GET端点")
    print("="*50)
    
    questions = [
        "查找珞珈山附近的点",
        "统计数据总数"
    ]
    
    for question in questions:
        print(f"\n测试GET查询: '{question}'")
        try:
            # URL编码问题
            import urllib.parse
            encoded_question = urllib.parse.quote(question)
            response = requests.get(f"{BASE_URL}/agent/query/{encoded_question}")
            print(f"状态码: {response.status_code}")
            result = response.json()
            print(f"查询类型: {result.get('question', {}).get('type', 'unknown')}")
            print(f"SQL查询数量: {len(result.get('sql', []))}")
        except Exception as e:
            print(f"GET查询失败: {e}")
        time.sleep(1)

def main():
    """主测试函数"""
    print("开始测试智能代理API接口")
    print("="*60)
    
    # 等待服务器完全启动
    time.sleep(2)
    
    # 测试健康检查
    if not test_health_check():
        print("服务器健康检查失败，请检查服务器状态")
        return
    
    # 测试查询类型分析
    test_questions = [
        "查找距离珞珈山最近的点",  # 空间查询
        "统计whupoi表中的数据总数",  # 总结查询
        "查询所有表名"  # 普通查询
    ]
    
    for question in test_questions:
        test_query_analysis(question)
        time.sleep(1)
    
    # 测试不同类型的查询
    test_spatial_queries()
    test_summary_queries()
    test_general_queries()
    
    # 测试GET端点
    test_get_endpoint()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("API接口地址: http://localhost:8001")
    print("主要端点:")
    print("- POST /agent/query - 智能代理查询")
    print("- GET  /agent/query/{question} - GET方式查询")
    print("- POST /agent/analyze - 查询类型分析")
    print("- GET  / - 健康检查")

if __name__ == "__main__":
    main()
