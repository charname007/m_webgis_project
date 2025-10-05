#!/usr/bin/env python3
"""
测试API修复效果
验证思维链提取是否正常工作
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import requests
import json
import time

def test_agent_query_api():
    """测试智能代理查询API"""
    print("测试智能代理查询API")
    print("=" * 60)
    
    # 测试查询
    test_question = "查找珞珈山附近1公里范围内的POI点"
    
    try:
        # 发送POST请求到智能代理查询接口
        url = "http://localhost:8001/agent/query"
        payload = {
            "question": test_question,
            "execute_sql": True,
            "return_geojson": True
        }
        
        print(f"发送查询: {test_question}")
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"API响应状态: {result.get('status', 'unknown')}")
            
            if result["status"] == "success":
                # 检查思维链
                thought_chain = result.get("answer", {}).get("thought_chain", [])
                print(f"思维链步骤数: {len(thought_chain)}")
                
                # 显示思维链详情
                for step in thought_chain:
                    if step['type'] == 'thought' or step['type'] == 'final_answer':
                        print(f"  步骤 {step['step']} ({step['type']}): {step['content'][:100]}...")
                    elif step['type'] == 'action':
                        print(f"  步骤 {step['step']} ({step['type']}): {step['action']} - {step['action_input'][:50]}...")
                
                # 检查SQL查询
                sql_queries = result.get("sql", [])
                print(f"提取的SQL查询数: {len(sql_queries)}")
                
                # 检查GeoJSON结果
                geojson = result.get("geojson")
                if geojson:
                    feature_count = len(geojson.get("features", []))
                    print(f"GeoJSON要素数: {feature_count}")
                
                # 检查查询类型分析
                query_analysis = result.get("question", {}).get("analysis", {})
                print(f"查询类型: {query_analysis.get('query_type', 'unknown')}")
                
                print("\n✅ API调用成功，思维链提取正常！")
            else:
                print(f"❌ API调用失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("请确保服务器正在运行 (python server.py)")

def test_direct_answer_scenario():
    """测试直接答案场景"""
    print("\n\n测试直接答案场景")
    print("=" * 60)
    
    # 模拟直接答案查询
    test_question = "珞珈山附近有哪些POI点"
    
    try:
        url = "http://localhost:8001/agent/query"
        payload = {
            "question": test_question,
            "execute_sql": False,  # 不执行SQL，只测试思维链提取
            "return_geojson": False
        }
        
        print(f"发送查询: {test_question}")
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"API响应状态: {result.get('status', 'unknown')}")
            
            if result["status"] == "success":
                thought_chain = result.get("answer", {}).get("thought_chain", [])
                print(f"思维链步骤数: {len(thought_chain)}")
                
                for step in thought_chain:
                    if step['type'] == 'thought' or step['type'] == 'final_answer':
                        print(f"  步骤 {step['step']} ({step['type']}): {step['content'][:100]}...")
                    elif step['type'] == 'action':
                        print(f"  步骤 {step['step']} ({step['type']}): {step['action']} - {step['action_input'][:50]}...")
                
                # 分析思维链类型
                thought_count = sum(1 for step in thought_chain if step['type'] == 'thought')
                action_count = sum(1 for step in thought_chain if step['type'] == 'action')
                final_answer_count = sum(1 for step in thought_chain if step['type'] == 'final_answer')
                
                print(f"\n思维链统计:")
                print(f"  - Thought步骤: {thought_count}")
                print(f"  - Action步骤: {action_count}")
                print(f"  - Final Answer步骤: {final_answer_count}")
                
                if thought_count > 0 or action_count > 0:
                    print("✅ 成功提取了推理过程！")
                else:
                    print("⚠️ 可能返回了直接答案")
                    
            else:
                print(f"❌ API调用失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    # 检查服务器是否运行
    try:
        health_response = requests.get("http://localhost:8001/", timeout=5)
        if health_response.status_code == 200:
            print("✅ 服务器运行正常")
            test_agent_query_api()
            test_direct_answer_scenario()
        else:
            print("❌ 服务器未运行或响应异常")
            print("请先启动服务器: python server.py")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("请先启动服务器: python server.py")
    except Exception as e:
        print(f"❌ 检查服务器状态失败: {e}")
