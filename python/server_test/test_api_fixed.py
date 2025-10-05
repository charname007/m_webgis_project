import requests
import json

def test_agent_query():
    """测试智能代理查询接口"""
    url = "http://localhost:8010/agent/query"
    
    # 测试数据
    test_queries = [
        "查找距离珞珈山最近的点",
        "统计whupoi表中的数据",
        "显示所有POI点"
    ]
    
    for query in test_queries:
        print(f"\n=== 测试查询: {query} ===")
        
        try:
            # 准备请求数据
            data = {
                "question": query,
                "execute_sql": True,
                "return_geojson": True
            }
            
            # 发送请求
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"状态: {result.get('status')}")
                print(f"查询类型: {result.get('question', {}).get('type')}")
                print(f"SQL查询: {result.get('sql')}")
                print(f"GeoJSON要素数量: {result.get('answer', {}).get('feature_count', 'N/A')}")
                print(f"错误信息: {result.get('error', '无')}")
                
                # 检查是否有输出解析错误
                if "LLM响应（解析失败）" in str(result):
                    print("⚠️ 检测到输出解析错误，但已成功处理")
                else:
                    print("✅ 查询处理成功")
                    
            else:
                print(f"请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
        except Exception as e:
            print(f"请求异常: {e}")

def test_health_check():
    """测试健康检查接口"""
    url = "http://localhost:8010/"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            print(f"健康检查: {result}")
        else:
            print(f"健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"健康检查异常: {e}")

if __name__ == "__main__":
    print("开始测试API接口...")
    
    # 测试健康检查
    print("\n=== 健康检查 ===")
    test_health_check()
    
    # 测试智能查询
    test_agent_query()
