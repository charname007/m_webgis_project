"""
测试会话ID功能

验证所有API端点是否正确地支持会话ID参数
"""

import requests
import json
import time

# 服务器配置
BASE_URL = "http://localhost:8000"

def test_get_query_with_session_id():
    """测试 GET /query 端点会话ID功能"""
    print("=== 测试 GET /query 端点会话ID功能 ===")
    
    # 测试1: 不提供会话ID（自动生成）
    print("\n--- 测试1: 不提供会话ID ---")
    response1 = requests.get(f"{BASE_URL}/query", params={"q": "查询浙江省的5A景区"})
    print(f"状态码: {response1.status_code}")
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"自动生成的会话ID: {data1.get('conversation_id')}")
        print(f"查询状态: {data1.get('status')}")
        print(f"结果数量: {data1.get('count')}")
    
    # 测试2: 提供自定义会话ID
    print("\n--- 测试2: 提供自定义会话ID ---")
    custom_session_id = "test-session-12345"
    response2 = requests.get(
        f"{BASE_URL}/query", 
        params={
            "q": "查询杭州市的景区", 
            "conversation_id": custom_session_id
        }
    )
    print(f"状态码: {response2.status_code}")
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"返回的会话ID: {data2.get('conversation_id')}")
        print(f"查询状态: {data2.get('status')}")
        print(f"结果数量: {data2.get('count')}")
    
    # 测试3: 使用相同的会话ID进行多轮查询
    print("\n--- 测试3: 多轮查询（相同会话ID） ---")
    response3 = requests.get(
        f"{BASE_URL}/query", 
        params={
            "q": "查询4A景区", 
            "conversation_id": custom_session_id
        }
    )
    print(f"状态码: {response3.status_code}")
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"返回的会话ID: {data3.get('conversation_id')}")
        print(f"查询状态: {data3.get('status')}")
        print(f"结果数量: {data3.get('count')}")

def test_post_query_with_session_id():
    """测试 POST /query 端点会话ID功能"""
    print("\n=== 测试 POST /query 端点会话ID功能 ===")
    
    # 测试1: 不提供会话ID
    print("\n--- 测试1: 不提供会话ID ---")
    payload1 = {
        "query": "查询浙江省的5A景区",
        "include_sql": True
    }
    response1 = requests.post(f"{BASE_URL}/query", json=payload1)
    print(f"状态码: {response1.status_code}")
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"自动生成的会话ID: {data1.get('conversation_id')}")
        print(f"查询状态: {data1.get('status')}")
    
    # 测试2: 提供自定义会话ID
    print("\n--- 测试2: 提供自定义会话ID ---")
    custom_session_id = "test-post-session-67890"
    payload2 = {
        "query": "查询杭州市的景区",
        "include_sql": True,
        "conversation_id": custom_session_id
    }
    response2 = requests.post(f"{BASE_URL}/query", json=payload2)
    print(f"状态码: {response2.status_code}")
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"返回的会话ID: {data2.get('conversation_id')}")
        print(f"查询状态: {data2.get('status')}")

def test_geojson_with_session_id():
    """测试 GeoJSON 端点会话ID功能"""
    print("\n=== 测试 GeoJSON 端点会话ID功能 ===")
    
    payload = {
        "query": "查询浙江省的5A景区",
        "coordinate_system": "wgs84",
        "include_properties": True,
        "conversation_id": "test-geojson-session-11111"
    }
    
    response = requests.post(f"{BASE_URL}/query/geojson", json=payload)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"GeoJSON 类型: {data.get('type')}")
        print(f"要素数量: {data.get('metadata', {}).get('count')}")
        print(f"会话ID在元数据中: {'conversation_id' in data.get('metadata', {})}")

def test_thought_chain_with_session_id():
    """测试思维链端点会话ID功能"""
    print("\n=== 测试思维链端点会话ID功能 ===")
    
    payload = {
        "query": "查询浙江省的5A景区",
        "verbose": True,
        "conversation_id": "test-thought-session-22222"
    }
    
    response = requests.post(f"{BASE_URL}/query/thought-chain", json=payload)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"思维链步骤数: {data.get('step_count')}")
        print(f"SQL查询数量: {len(data.get('sql_queries', []))}")
        print(f"最终答案: {data.get('final_answer', '')[:100]}...")

def test_cache_with_session_id():
    """测试缓存与会话ID的集成"""
    print("\n=== 测试缓存与会话ID的集成 ===")
    
    # 第一次查询（缓存未命中）
    print("\n--- 第一次查询（缓存未命中） ---")
    start_time = time.time()
    response1 = requests.get(
        f"{BASE_URL}/query", 
        params={
            "q": "查询浙江省的5A景区", 
            "conversation_id": "cache-test-session"
        }
    )
    first_time = time.time() - start_time
    print(f"第一次查询时间: {first_time:.3f}s")
    
    # 第二次查询（缓存命中）
    print("\n--- 第二次查询（缓存命中） ---")
    start_time = time.time()
    response2 = requests.get(
        f"{BASE_URL}/query", 
        params={
            "q": "查询浙江省的5A景区", 
            "conversation_id": "cache-test-session"
        }
    )
    second_time = time.time() - start_time
    print(f"第二次查询时间: {second_time:.3f}s")
    
    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()
        print(f"第一次执行时间: {data1.get('execution_time')}s")
        print(f"第二次执行时间: {data2.get('execution_time')}s")
        print(f"缓存是否生效: {second_time < first_time * 0.5}")

def main():
    """主测试函数"""
    print("开始测试会话ID功能...")
    
    try:
        # 检查服务器是否运行
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ 服务器未运行，请先启动服务器")
            return
        
        print("✅ 服务器连接正常")
        
        # 运行各个测试
        test_get_query_with_session_id()
        test_post_query_with_session_id()
        test_geojson_with_session_id()
        test_thought_chain_with_session_id()
        test_cache_with_session_id()
        
        print("\n✅ 所有测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")

if __name__ == "__main__":
    main()
