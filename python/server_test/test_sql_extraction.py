import requests
import json

def test_sql_extraction():
    """测试SQL查询提取逻辑"""
    url = "http://localhost:8010/agent/query"
    
    # 测试数据 - 包含多个SQL查询的复杂查询
    test_queries = [
        "统计whupoi表中的数据",
        "查找距离珞珈山最近的点",
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
                
                # 检查SQL查询列表
                sql_queries = result.get('sql', [])
                print(f"提取到的SQL查询数量: {len(sql_queries)}")
                
                # 显示每个SQL查询
                for i, sql_query in enumerate(sql_queries, 1):
                    print(f"\nSQL查询 {i}:")
                    print("-" * 50)
                    print(sql_query[:200] + "..." if len(sql_query) > 200 else sql_query)
                    print(f"查询长度: {len(sql_query)} 字符")
                    print(f"是否完整: {'SELECT' in sql_query.upper() and 'FROM' in sql_query.upper()}")
                
                # 检查GeoJSON数据
                geojson = result.get('geojson')
                if geojson:
                    feature_count = len(geojson.get('features', []))
                    print(f"\nGeoJSON要素数量: {feature_count}")
                else:
                    print(f"\nGeoJSON: 无")
                    
                print(f"错误信息: {result.get('error', '无')}")
                
            else:
                print(f"请求失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                
        except Exception as e:
            print(f"请求异常: {e}")

def test_query_analysis():
    """测试查询类型分析功能"""
    url = "http://localhost:8010/agent/analyze"
    
    test_questions = [
        "查找距离珞珈山最近的点",
        "统计whupoi表中的数据",
        "显示所有POI点",
        "这是什么意思"
    ]
    
    for question in test_questions:
        print(f"\n=== 分析查询: {question} ===")
        
        try:
            data = {"question": question}
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('analysis', {})
                print(f"查询类型: {analysis.get('query_type')}")
                print(f"优先级: {analysis.get('priority')}")
                print(f"空间关键词: {analysis.get('spatial_keywords_found')}")
                print(f"总结关键词: {analysis.get('summary_keywords_found')}")
                print(f"SQL关键词: {analysis.get('sql_keywords_found')}")
            else:
                print(f"分析失败: {response.status_code}")
                
        except Exception as e:
            print(f"分析异常: {e}")

if __name__ == "__main__":
    print("开始测试SQL查询提取逻辑...")
    
    # 测试查询类型分析
    print("\n=== 查询类型分析测试 ===")
    test_query_analysis()
    
    # 测试SQL查询提取
    print("\n=== SQL查询提取测试 ===")
    test_sql_extraction()
