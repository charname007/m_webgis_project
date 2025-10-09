#!/usr/bin/env python3
"""
测试缓存命中时 answer 字段修复效果
"""

import requests
import json
import time

# 服务器地址
BASE_URL = "http://localhost:8000"

def test_cache_hit_with_answer():
    """测试缓存命中时的 answer 字段修复"""
    print("=== 测试缓存命中时的 answer 字段修复 ===\n")
    
    # 测试查询
    test_query = "查询故宫"
    
    print(f"测试查询: {test_query}")
    
    # 第一次查询（创建缓存）
    print("\n1. 第一次查询（创建缓存）...")
    start_time = time.time()
    response1 = requests.get(f"{BASE_URL}/query", params={"q": test_query})
    first_time = time.time() - start_time
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"   - 状态: {result1.get('status')}")
        print(f"   - 回答: {result1.get('answer')}")
        print(f"   - 数据数量: {result1.get('count')}")
        print(f"   - 执行时间: {result1.get('execution_time')}s")
        print(f"   - 实际时间: {first_time:.3f}s")
    else:
        print(f"   - 第一次查询失败: {response1.status_code}")
        return
    
    # 等待一下，确保缓存保存完成
    time.sleep(0.5)
    
    # 第二次查询（缓存命中）
    print("\n2. 第二次查询（缓存命中）...")
    start_time = time.time()
    response2 = requests.get(f"{BASE_URL}/query", params={"q": test_query})
    cache_time = time.time() - start_time
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"   - 状态: {result2.get('status')}")
        print(f"   - 回答: {result2.get('answer')}")
        print(f"   - 数据数量: {result2.get('count')}")
        print(f"   - 执行时间: {result2.get('execution_time')}s")
        print(f"   - 实际时间: {cache_time:.3f}s")
        
        # 检查缓存命中效果
        if cache_time < first_time * 0.5:  # 缓存应该快很多
            print("   - ✅ 缓存命中成功（响应时间显著减少）")
        else:
            print("   - ⚠️ 缓存命中但响应时间未显著减少")
            
        # 检查 answer 字段
        if result2.get('answer') and len(result2.get('answer', '')) > 0:
            print("   - ✅ answer 字段修复成功（包含有效内容）")
        else:
            print("   - ❌ answer 字段仍然为空")
            
        # 检查数据完整性
        if result2.get('count') == result1.get('count'):
            print("   - ✅ 数据完整性验证通过")
        else:
            print("   - ❌ 数据完整性验证失败")
            
    else:
        print(f"   - 第二次查询失败: {response2.status_code}")
        return
    
    # 测试 POST 查询
    print("\n3. 测试 POST 查询缓存...")
    post_data = {
        "query": test_query,
        "include_sql": True
    }
    
    start_time = time.time()
    response3 = requests.post(f"{BASE_URL}/query", json=post_data)
    post_cache_time = time.time() - start_time
    
    if response3.status_code == 200:
        result3 = response3.json()
        print(f"   - 状态: {result3.get('status')}")
        print(f"   - 回答: {result3.get('answer')}")
        print(f"   - 数据数量: {result3.get('count')}")
        print(f"   - 执行时间: {result3.get('execution_time')}s")
        print(f"   - 实际时间: {post_cache_time:.3f}s")
        
        if result3.get('answer') and len(result3.get('answer', '')) > 0:
            print("   - ✅ POST 查询 answer 字段修复成功")
        else:
            print("   - ❌ POST 查询 answer 字段仍然为空")
            
    else:
        print(f"   - POST 查询失败: {response3.status_code}")
    
    # 获取缓存统计
    print("\n4. 获取缓存统计...")
    stats_response = requests.get(f"{BASE_URL}/cache/stats")
    if stats_response.status_code == 200:
        stats = stats_response.json()
        cache_stats = stats.get('cache_stats', {})
        print(f"   - 缓存条目数: {cache_stats.get('total_entries', 0)}")
        print(f"   - 缓存命中数: {cache_stats.get('total_hits', 0)}")
        print(f"   - 缓存未命中数: {cache_stats.get('total_misses', 0)}")
        print(f"   - 命中率: {cache_stats.get('hit_rate_percent', 0)}%")
    else:
        print(f"   - 获取缓存统计失败: {stats_response.status_code}")

def test_multiple_queries():
    """测试多个查询的缓存效果"""
    print("\n=== 测试多个查询的缓存效果 ===\n")
    
    test_queries = [
        "查询故宫",
        "查询武汉大学",
        "统计5A景区数量",
        "查找北京的景区"
    ]
    
    for query in test_queries:
        print(f"测试查询: {query}")
        
        # 第一次查询
        start_time = time.time()
        response1 = requests.get(f"{BASE_URL}/query", params={"q": query})
        first_time = time.time() - start_time
        
        if response1.status_code == 200:
            result1 = response1.json()
            answer1 = result1.get('answer', '')
            count1 = result1.get('count', 0)
            
            # 等待缓存保存
            time.sleep(0.3)
            
            # 第二次查询（缓存命中）
            start_time = time.time()
            response2 = requests.get(f"{BASE_URL}/query", params={"q": query})
            cache_time = time.time() - start_time
            
            if response2.status_code == 200:
                result2 = response2.json()
                answer2 = result2.get('answer', '')
                count2 = result2.get('count', 0)
                
                # 检查结果
                if answer2 and len(answer2) > 0:
                    status = "✅"
                else:
                    status = "❌"
                    
                print(f"   - {status} 缓存命中: 回答='{answer2[:50]}...', 数量={count2}, 时间={cache_time:.3f}s")
                
            else:
                print(f"   - ❌ 缓存查询失败: {response2.status_code}")
        else:
            print(f"   - ❌ 首次查询失败: {response1.status_code}")

if __name__ == "__main__":
    try:
        # 检查服务器是否运行
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ 服务器未运行，请先启动服务器")
            print("启动命令: cd python/sight_server && python main.py")
            exit(1)
            
        print("✅ 服务器运行正常，开始测试...\n")
        
        # 运行测试
        test_cache_hit_with_answer()
        test_multiple_queries()
        
        print("\n=== 测试完成 ===")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
        print("启动命令: cd python/sight_server && python main.py")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
