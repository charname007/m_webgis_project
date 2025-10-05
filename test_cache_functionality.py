"""
测试缓存功能是否正常工作
"""

import requests
import json
import time

# Sight Server 地址
BASE_URL = "http://localhost:8000"

def test_cache_functionality():
    """测试缓存功能"""
    print("=== 测试缓存功能 ===\n")
    
    # 1. 获取初始缓存统计
    print("1. 获取初始缓存统计...")
    try:
        stats_response = requests.get(f"{BASE_URL}/cache/stats")
        if stats_response.status_code == 200:
            initial_stats = stats_response.json()
            print(f"   初始缓存统计: {json.dumps(initial_stats, indent=2, ensure_ascii=False)}")
        else:
            print(f"   获取缓存统计失败: {stats_response.status_code}")
    except Exception as e:
        print(f"   连接失败: {e}")
        return
    
    # 2. 第一次查询（应该缓存未命中）
    print("\n2. 第一次查询（缓存未命中）...")
    query1 = "查询浙江省的5A景区"
    start_time = time.time()
    response1 = requests.get(f"{BASE_URL}/query", params={"q": query1})
    execution_time1 = time.time() - start_time
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"   查询: {query1}")
        print(f"   执行时间: {execution_time1:.3f}s")
        print(f"   结果数量: {result1.get('count', 0)}")
        print(f"   状态: {result1.get('status')}")
    else:
        print(f"   查询失败: {response1.status_code}")
        return
    
    # 3. 第二次相同查询（应该缓存命中）
    print("\n3. 第二次相同查询（缓存命中）...")
    start_time = time.time()
    response2 = requests.get(f"{BASE_URL}/query", params={"q": query1})
    execution_time2 = time.time() - start_time
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"   查询: {query1}")
        print(f"   执行时间: {execution_time2:.3f}s")
        print(f"   结果数量: {result2.get('count', 0)}")
        print(f"   状态: {result2.get('status')}")
        print(f"   消息: {result2.get('message')}")
        
        # 检查是否是缓存命中
        if "缓存" in result2.get('message', ''):
            print("   ✅ 缓存命中确认")
        else:
            print("   ⚠️ 可能未命中缓存")
    else:
        print(f"   查询失败: {response2.status_code}")
        return
    
    # 4. 语义相似查询（应该语义缓存命中）
    print("\n4. 语义相似查询（语义缓存命中）...")
    query2 = "查找浙江省的5A级景区"  # 与第一次查询语义相似
    start_time = time.time()
    response3 = requests.get(f"{BASE_URL}/query", params={"q": query2})
    execution_time3 = time.time() - start_time
    
    if response3.status_code == 200:
        result3 = response3.json()
        print(f"   查询: {query2}")
        print(f"   执行时间: {execution_time3:.3f}s")
        print(f"   结果数量: {result3.get('count', 0)}")
        print(f"   状态: {result3.get('status')}")
        print(f"   消息: {result3.get('message')}")
        
        # 检查是否是缓存命中
        if "缓存" in result3.get('message', ''):
            print("   ✅ 语义缓存命中确认")
        else:
            print("   ⚠️ 语义缓存可能未命中")
    else:
        print(f"   查询失败: {response3.status_code}")
        return
    
    # 5. 获取最终缓存统计
    print("\n5. 获取最终缓存统计...")
    try:
        final_stats_response = requests.get(f"{BASE_URL}/cache/stats")
        if final_stats_response.status_code == 200:
            final_stats = final_stats_response.json()
            print(f"   最终缓存统计: {json.dumps(final_stats, indent=2, ensure_ascii=False)}")
            
            # 分析缓存效果
            cache_stats = final_stats.get('cache_stats', {})
            total_hits = cache_stats.get('total_hits', 0)
            total_misses = cache_stats.get('total_misses', 0)
            hit_rate = cache_stats.get('hit_rate_percent', 0)
            
            print(f"\n=== 缓存效果分析 ===")
            print(f"总命中次数: {total_hits}")
            print(f"总未命中次数: {total_misses}")
            print(f"命中率: {hit_rate}%")
            
            if total_hits > 0:
                print("✅ 缓存功能正常工作")
            else:
                print("❌ 缓存可能未正常工作")
                
        else:
            print(f"   获取缓存统计失败: {final_stats_response.status_code}")
    except Exception as e:
        print(f"   连接失败: {e}")
    
    # 6. 测试清除缓存
    print("\n6. 测试清除缓存...")
    try:
        clear_response = requests.delete(f"{BASE_URL}/cache/clear")
        if clear_response.status_code == 200:
            clear_result = clear_response.json()
            print(f"   清除缓存结果: {json.dumps(clear_result, indent=2, ensure_ascii=False)}")
        else:
            print(f"   清除缓存失败: {clear_response.status_code}")
    except Exception as e:
        print(f"   清除缓存失败: {e}")

def test_post_cache():
    """测试 POST 请求的缓存功能"""
    print("\n=== 测试 POST 请求缓存功能 ===\n")
    
    # 1. 第一次 POST 查询
    print("1. 第一次 POST 查询（缓存未命中）...")
    query_data = {
        "query": "查询杭州市的4A景区",
        "include_sql": True
    }
    start_time = time.time()
    response1 = requests.post(f"{BASE_URL}/query", json=query_data)
    execution_time1 = time.time() - start_time
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"   查询: {query_data['query']}")
        print(f"   执行时间: {execution_time1:.3f}s")
        print(f"   结果数量: {result1.get('count', 0)}")
    else:
        print(f"   查询失败: {response1.status_code}")
        return
    
    # 2. 第二次相同 POST 查询（应该缓存命中）
    print("\n2. 第二次相同 POST 查询（缓存命中）...")
    start_time = time.time()
    response2 = requests.post(f"{BASE_URL}/query", json=query_data)
    execution_time2 = time.time() - start_time
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"   查询: {query_data['query']}")
        print(f"   执行时间: {execution_time2:.3f}s")
        print(f"   结果数量: {result2.get('count', 0)}")
        print(f"   消息: {result2.get('message')}")
        
        if "缓存" in result2.get('message', ''):
            print("   ✅ POST 缓存命中确认")
        else:
            print("   ⚠️ POST 缓存可能未命中")
    else:
        print(f"   查询失败: {response2.status_code}")

if __name__ == "__main__":
    print("确保 Sight Server 正在运行 (http://localhost:8000)")
    print("按 Enter 开始测试...")
    input()
    
    test_cache_functionality()
    test_post_cache()
    
    print("\n=== 测试完成 ===")
