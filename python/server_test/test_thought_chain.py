#!/usr/bin/env python3
"""
测试思维链提取功能
"""

import requests
import json
import time

def test_thought_chain():
    """测试思维链提取功能"""
    base_url = "http://localhost:8010"
    
    # 测试查询
    test_queries = [
        "查找距离珞珈山5公里内的所有点",
        "统计whupoi表中的数据",
        "查询所有包含名称的点"
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n{'='*60}")
        print(f"测试 {i+1}: {query}")
        print('='*60)
        
        try:
            # 使用POST方式测试智能代理查询
            response = requests.post(
                f"{base_url}/agent/query",
                json={
                    "question": query,
                    "execute_sql": True,
                    "return_geojson": True
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"状态: {result.get('status', 'unknown')}")
                
                # 检查思维链是否存在
                if 'answer' in result and 'thought_chain' in result['answer']:
                    thought_chain = result['answer']['thought_chain']
                    print(f"思维链步骤数: {len(thought_chain)}")
                    
                    # 显示思维链详情
                    for step in thought_chain:
                        print(f"\n步骤 {step['step']} ({step['type']}):")
                        if step['type'] == 'thought':
                            print(f"  思考: {step['content'][:200]}...")
                        elif step['type'] == 'action':
                            print(f"  动作: {step['action']}")
                            if step['action_input']:
                                print(f"  输入: {step['action_input'][:100]}...")
                        elif step['type'] == 'final_answer':
                            print(f"  最终答案: {step['content'][:200]}...")
                
                # 检查SQL查询
                if 'sql' in result and result['sql']:
                    print(f"\nSQL查询数量: {len(result['sql'])}")
                    for j, sql in enumerate(result['sql'][:3]):  # 只显示前3个
                        print(f"  SQL {j+1}: {sql[:100]}...")
                
                # 检查GeoJSON
                if 'geojson' in result and result['geojson']:
                    feature_count = len(result['geojson'].get('features', []))
                    print(f"GeoJSON要素数量: {feature_count}")
                
            else:
                print(f"请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
        except Exception as e:
            print(f"处理异常: {e}")
        
        # 等待一下避免请求过快
        time.sleep(2)

def test_thought_chain_detailed():
    """详细测试思维链提取功能"""
    base_url = "http://localhost:8010"
    
    # 测试一个具体的查询来详细分析思维链
    query = "查找距离珞珈山5公里内的所有点，并统计数量"
    
    print(f"\n{'='*60}")
    print(f"详细测试: {query}")
    print('='*60)
    
    try:
        response = requests.post(
            f"{base_url}/agent/query",
            json={
                "question": query,
                "execute_sql": True,
                "return_geojson": True
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 保存完整结果到文件以便分析
            with open('thought_chain_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print("完整结果已保存到 thought_chain_result.json")
            
            # 详细分析思维链
            if 'answer' in result and 'thought_chain' in result['answer']:
                thought_chain = result['answer']['thought_chain']
                
                print(f"\n思维链分析:")
                print(f"总步骤数: {len(thought_chain)}")
                
                # 统计不同类型的步骤
                thought_count = sum(1 for step in thought_chain if step['type'] == 'thought')
                action_count = sum(1 for step in thought_chain if step['type'] == 'action')
                final_answer_count = sum(1 for step in thought_chain if step['type'] == 'final_answer')
                
                print(f"思考步骤: {thought_count}")
                print(f"动作步骤: {action_count}")
                print(f"最终答案: {final_answer_count}")
                
                # 显示每个步骤的详细信息
                for step in thought_chain:
                    print(f"\n{'─'*40}")
                    print(f"步骤 {step['step']} - {step['type'].upper()} ({step['timestamp']})")
                    print(f"{'─'*40}")
                    
                    if step['type'] == 'thought':
                        print(f"思考内容:\n{step['content']}")
                    elif step['type'] == 'action':
                        print(f"动作类型: {step['action']}")
                        if step['action_input']:
                            print(f"动作输入:\n{step['action_input']}")
                    elif step['type'] == 'final_answer':
                        print(f"最终答案:\n{step['content']}")
            
            # 显示查询分析结果
            if 'question' in result and 'analysis' in result['question']:
                analysis = result['question']['analysis']
                print(f"\n查询类型分析:")
                print(f"  查询类型: {analysis.get('query_type', 'unknown')}")
                print(f"  优先级: {analysis.get('priority', 'unknown')}")
                print(f"  是否空间查询: {analysis.get('is_spatial', False)}")
                print(f"  是否总结查询: {analysis.get('is_summary', False)}")
                print(f"  是否SQL查询: {analysis.get('is_sql', False)}")
                
                if analysis.get('spatial_keywords_found'):
                    print(f"  发现的空间关键词: {analysis['spatial_keywords_found']}")
                
        else:
            print(f"请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"测试异常: {e}")

if __name__ == "__main__":
    print("开始测试思维链提取功能...")
    
    # 先测试健康检查
    try:
        response = requests.get("http://localhost:8010/", timeout=10)
        if response.status_code == 200:
            print("服务健康检查通过")
        else:
            print("服务可能未启动，请先启动服务器")
            exit(1)
    except:
        print("服务未启动，请先运行: cd python && python server.py --port 8010")
        exit(1)
    
    # 运行测试
    test_thought_chain()
    test_thought_chain_detailed()
    
    print("\n测试完成！")
