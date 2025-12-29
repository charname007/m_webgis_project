#!/usr/bin/env python3
"""
测试思维链捕获功能，特别是SQL查询结果的捕获
"""

import sys
import os
import json
import logging

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from spatial_sql_agent import SpatialSQLQueryAgent

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_thought_chain_capture():
    """测试思维链捕获功能"""
    logger.info("开始测试思维链捕获功能...")
    
    try:
        # 创建空间查询代理
        spatial_agent = SpatialSQLQueryAgent()
        logger.info("空间查询代理创建成功")
        
        # 测试查询列表
        test_queries = [
            "查看数据库中有哪些表",
            "查询whupoi表的前5条记录",
            "查找包含'珞珈'名称的点",
            "统计whupoi表中不同类型的几何要素数量"
        ]
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"测试 {i}/{len(test_queries)}: {query}")
            logger.info(f"{'='*50}")
            
            try:
                # 使用思维链捕获功能
                result = spatial_agent.run_with_thought_chain(query)
                
                # 检查结果状态
                if result["status"] == "success":
                    logger.info(f"✅ 查询处理成功")
                    logger.info(f"思维链步骤数: {result['step_count']}")
                    logger.info(f"最终答案长度: {len(result['final_answer'])}")
                    
                    # 检查SQL查询结果捕获
                    sql_queries_with_results = result.get("sql_queries_with_results", [])
                    logger.info(f"捕获到的SQL查询数量: {len(sql_queries_with_results)}")
                    
                    # 显示每个SQL查询及其结果
                    for j, sql_info in enumerate(sql_queries_with_results, 1):
                        logger.info(f"\n--- SQL查询 {j} ---")
                        logger.info(f"SQL: {sql_info.get('sql', 'N/A')}")
                        logger.info(f"状态: {sql_info.get('status', 'N/A')}")
                        logger.info(f"步骤: {sql_info.get('step', 'N/A')}")
                        
                        # 显示查询结果（截断显示）
                        result_data = sql_info.get('result', '')
                        if result_data:
                            result_preview = str(result_data)[:200] + "..." if len(str(result_data)) > 200 else str(result_data)
                            logger.info(f"结果预览: {result_preview}")
                        else:
                            logger.info("结果: 无结果或结果为空")
                    
                    # 显示思维链摘要
                    thought_chain = result.get("thought_chain", [])
                    logger.info(f"\n思维链摘要:")
                    for k, step in enumerate(thought_chain, 1):
                        step_type = step.get("type", "unknown")
                        if step_type == "action":
                            logger.info(f"  {k}. [Action] {step.get('action', 'N/A')}")
                        elif step_type == "final_answer":
                            logger.info(f"  {k}. [Final Answer] 长度: {len(step.get('content', ''))}")
                        else:
                            logger.info(f"  {k}. [{step_type}]")
                
                else:
                    logger.error(f"❌ 查询处理失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                logger.error(f"❌ 测试查询失败: {str(e)}")
                continue
        
        # 测试完成
        logger.info(f"\n{'='*50}")
        logger.info("思维链捕获功能测试完成")
        logger.info(f"{'='*50}")
        
        # 清理资源
        spatial_agent.close()
        
    except Exception as e:
        logger.error(f"❌ 测试初始化失败: {str(e)}")
        return False
    
    return True

def test_specific_query():
    """测试特定查询的思维链捕获"""
    logger.info("\n开始测试特定查询...")
    
    try:
        # 创建空间查询代理
        spatial_agent = SpatialSQLQueryAgent()
        
        # 测试一个具体的查询
        query = "查询whupoi表中名称包含'珞珈'的点要素"
        logger.info(f"测试查询: {query}")
        
        # 使用思维链捕获功能
        result = spatial_agent.run_with_thought_chain(query)
        
        # 保存详细结果到文件
        output_file = "test_thought_chain_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"详细结果已保存到: {output_file}")
        
        # 显示关键信息
        if result["status"] == "success":
            logger.info("✅ 查询处理成功")
            
            # 显示思维链步骤
            thought_chain = result.get("thought_chain", [])
            logger.info(f"思维链步骤数: {len(thought_chain)}")
            
            for i, step in enumerate(thought_chain, 1):
                step_type = step.get("type", "unknown")
                logger.info(f"\n步骤 {i}: {step_type}")
                
                if step_type == "action":
                    logger.info(f"  动作: {step.get('action', 'N/A')}")
                    logger.info(f"  输入: {step.get('action_input', 'N/A')}")
                    logger.info(f"  状态: {step.get('status', 'N/A')}")
                    
                    # 显示观察结果（SQL查询结果）
                    observation = step.get('observation', '')
                    if observation:
                        obs_preview = str(observation)[:300] + "..." if len(str(observation)) > 300 else str(observation)
                        logger.info(f"  观察结果: {obs_preview}")
                
                elif step_type == "final_answer":
                    content = step.get('content', '')
                    logger.info(f"  最终答案长度: {len(content)}")
                    logger.info(f"  最终答案预览: {content[:200]}...")
            
            # 显示SQL查询结果统计
            sql_queries_with_results = result.get("sql_queries_with_results", [])
            logger.info(f"\n捕获到的SQL查询数量: {len(sql_queries_with_results)}")
            
            for j, sql_info in enumerate(sql_queries_with_results, 1):
                logger.info(f"\nSQL查询 {j}:")
                logger.info(f"  SQL: {sql_info.get('sql', 'N/A')}")
                logger.info(f"  状态: {sql_info.get('status', 'N/A')}")
                
                result_data = sql_info.get('result', '')
                if result_data:
                    logger.info(f"  结果类型: {type(result_data)}")
                    if isinstance(result_data, list):
                        logger.info(f"  结果记录数: {len(result_data)}")
                        if result_data:
                            logger.info(f"  第一条记录预览: {str(result_data[0])[:100]}...")
                    else:
                        logger.info(f"  结果预览: {str(result_data)[:200]}...")
        
        else:
            logger.error(f"❌ 查询处理失败: {result.get('error', '未知错误')}")
        
        # 清理资源
        spatial_agent.close()
        
    except Exception as e:
        logger.error(f"❌ 特定查询测试失败: {str(e)}")

if __name__ == "__main__":
    logger.info("思维链捕获功能测试开始")
    
    # 运行基本测试
    basic_test_success = test_thought_chain_capture()
    
    # 运行特定查询测试
    test_specific_query()
    
    logger.info("思维链捕获功能测试结束")
    
    if basic_test_success:
        logger.info("✅ 基本测试通过")
    else:
        logger.error("❌ 基本测试失败")
