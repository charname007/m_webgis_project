#!/usr/bin/env python3
"""
解析失败修复方案
修复LLM响应解析失败的问题，改进输出解析逻辑
"""

import re
import logging
from typing import Dict, Any, Optional, List

class LLMResponseParser:
    """LLM响应解析器，处理各种格式的LLM输出"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_llm_response(self, llm_output: str) -> Dict[str, Any]:
        """
        解析LLM响应，支持多种格式
        
        Args:
            llm_output: LLM原始输出
            
        Returns:
            解析后的结构化结果
        """
        if not llm_output:
            return {"status": "error", "message": "LLM输出为空"}
        
        # 首先检查是否包含完整的Thought/Action链（即使最后有直接答案）
        hybrid_result = self._parse_hybrid_format(llm_output)
        if hybrid_result["status"] == "success":
            return hybrid_result
        
        # 尝试解析标准格式（Thought/Action/Final Answer）
        standard_result = self._parse_standard_format(llm_output)
        if standard_result["status"] == "success":
            return standard_result
        
        # 尝试解析直接答案格式
        direct_result = self._parse_direct_answer_format(llm_output)
        if direct_result["status"] == "success":
            return direct_result
        
        # 尝试解析SQL查询格式
        sql_result = self._parse_sql_format(llm_output)
        if sql_result["status"] == "success":
            return sql_result
        
        # 如果所有解析都失败，返回原始内容
        return {
            "status": "success",
            "type": "raw_response",
            "content": llm_output,
            "thought_chain": [{
                "step": 1,
                "type": "thought",
                "content": llm_output[:500] + "..." if len(llm_output) > 500 else llm_output,
                "timestamp": "single_step"
            }]
        }
    
    def _parse_standard_format(self, llm_output: str) -> Dict[str, Any]:
        """解析标准Thought/Action/Final Answer格式"""
        thought_chain = []
        
        # 提取Thoughts
        thought_pattern = r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)"
        thought_matches = re.findall(thought_pattern, llm_output, re.DOTALL)
        for i, thought in enumerate(thought_matches):
            thought_chain.append({
                "step": i + 1,
                "type": "thought",
                "content": thought.strip(),
                "timestamp": f"step_{i+1}"
            })
        
        # 提取Actions
        action_pattern = r"Action:\s*(\w+)(?:\s+Action Input:\s*(.*?))?(?=Thought:|Final Answer:|$)"
        action_matches = re.findall(action_pattern, llm_output, re.DOTALL)
        for i, (action, action_input) in enumerate(action_matches):
            thought_chain.append({
                "step": len(thought_chain) + 1,
                "type": "action",
                "action": action.strip(),
                "action_input": action_input.strip() if action_input else "",
                "timestamp": f"step_{len(thought_chain)+1}"
            })
        
        # 提取Final Answer
        final_answer_pattern = r"Final Answer:\s*(.*?)(?=Thought:|Action:|$)"
        final_answer_matches = re.findall(final_answer_pattern, llm_output, re.DOTALL)
        
        if thought_chain or final_answer_matches:
            result = {
                "status": "success",
                "type": "standard_format",
                "thought_chain": thought_chain
            }
            
            if final_answer_matches:
                result["final_answer"] = final_answer_matches[0].strip()
                thought_chain.append({
                    "step": len(thought_chain) + 1,
                    "type": "final_answer",
                    "content": final_answer_matches[0].strip(),
                    "timestamp": "final"
                })
            
            return result
        
        return {"status": "failed"}
    
    def _parse_hybrid_format(self, llm_output: str) -> Dict[str, Any]:
        """
        解析混合格式：包含完整Thought/Action链但最后返回直接答案
        
        Args:
            llm_output: LLM原始输出
            
        Returns:
            解析后的结构化结果
        """
        # 首先检查是否包含Thought/Action模式
        thought_pattern = r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)"
        action_pattern = r"Action:\s*(\w+)(?:\s+Action Input:\s*(.*?))?(?=Thought:|Final Answer:|$)"
        
        thought_matches = re.findall(thought_pattern, llm_output, re.DOTALL)
        action_matches = re.findall(action_pattern, llm_output, re.DOTALL)
        
        # 如果包含Thought/Action模式，尝试提取完整的思维链
        if thought_matches or action_matches:
            thought_chain = []
            step_counter = 1
            
            # 提取Thoughts
            for i, thought in enumerate(thought_matches):
                thought_chain.append({
                    "step": step_counter,
                    "type": "thought",
                    "content": thought.strip(),
                    "timestamp": f"step_{step_counter}"
                })
                step_counter += 1
            
            # 提取Actions
            for i, (action, action_input) in enumerate(action_matches):
                thought_chain.append({
                    "step": step_counter,
                    "type": "action",
                    "action": action.strip(),
                    "action_input": action_input.strip() if action_input else "",
                    "timestamp": f"step_{step_counter}"
                })
                step_counter += 1
            
            # 检查是否有直接答案部分（在Thought/Action之后）
            # 查找最后一个Action或Thought之后的内容
            last_marker_pos = 0
            last_marker_type = ""
            for marker in ["Thought:", "Action:", "Final Answer:"]:
                last_pos = llm_output.rfind(marker)
                if last_pos > last_marker_pos:
                    last_marker_pos = last_pos
                    last_marker_type = marker
            
            if last_marker_pos > 0:
                # 提取最后一个标记之后的内容作为直接答案
                # 找到标记的结束位置（包括标记本身和后面的内容）
                marker_end = last_marker_pos + len(last_marker_type)
                
                # 找到标记行的结束位置
                line_end = llm_output.find("\n", marker_end)
                if line_end == -1:
                    line_end = len(llm_output)
                else:
                    line_end += 1  # 包含换行符
                
                # 提取从标记行结束到文本末尾的内容
                direct_answer = llm_output[line_end:].strip()
                
                # 如果直接答案有内容且不是空的，添加到思维链
                if direct_answer and len(direct_answer) > 10:
                    # 检查直接答案是否包含SQL查询或其他有意义的内容
                    # 避免将Action Input误认为直接答案
                    if not any(action_input in direct_answer for action_input in ["SELECT", "INSERT", "UPDATE", "DELETE"]):
                        thought_chain.append({
                            "step": step_counter,
                            "type": "final_answer",
                            "content": direct_answer,
                            "timestamp": "final"
                        })
            
            # 如果成功提取了思维链，返回结果
            if thought_chain:
                return {
                    "status": "success",
                    "type": "hybrid_format",
                    "thought_chain": thought_chain,
                    "final_answer": direct_answer if 'direct_answer' in locals() and direct_answer else None
                }
        
        return {"status": "failed"}
    
    def _parse_direct_answer_format(self, llm_output: str) -> Dict[str, Any]:
        """解析直接答案格式（没有Thought/Action标记）"""
        # 检查是否包含常见的直接答案模式
        direct_patterns = [
            r"查询结果.*?如下：?(.*)",
            r"以下是.*?结果：?(.*)",
            r"我.*?找到.*?结果：?(.*)",
            r"结果.*?如下：?(.*)",
            r"答案.*?如下：?(.*)"
        ]
        
        for pattern in direct_patterns:
            match = re.search(pattern, llm_output, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                return {
                    "status": "success",
                    "type": "direct_answer",
                    "content": content,
                    "thought_chain": [{
                        "step": 1,
                        "type": "final_answer",
                        "content": content,
                        "timestamp": "direct_answer"
                    }]
                }
        
        # 如果没有匹配模式，但内容看起来像直接答案
        if len(llm_output) < 1000 and not any(marker in llm_output for marker in ["Thought:", "Action:", "Final Answer:"]):
            return {
                "status": "success",
                "type": "direct_answer",
                "content": llm_output,
                "thought_chain": [{
                    "step": 1,
                    "type": "final_answer",
                    "content": llm_output,
                    "timestamp": "direct_answer"
                }]
            }
        
        return {"status": "failed"}
    
    def _parse_sql_format(self, llm_output: str) -> Dict[str, Any]:
        """解析包含SQL查询的格式"""
        sql_queries = self._extract_sql_queries(llm_output)
        
        if sql_queries:
            return {
                "status": "success",
                "type": "sql_query",
                "sql_queries": sql_queries,
                "thought_chain": [{
                    "step": 1,
                    "type": "thought",
                    "content": f"生成SQL查询: {sql_queries[0][:100]}...",
                    "timestamp": "sql_generation"
                }]
            }
        
        return {"status": "failed"}
    
    def _extract_sql_queries(self, text: str) -> List[str]:
        """从文本中提取SQL查询"""
        sql_queries = []
        
        # 提取SQL代码块
        if "```sql" in text:
            start_index = text.find("```sql") + 6
            while start_index > 5:
                end_index = text.find("```", start_index)
                if end_index > start_index:
                    sql_content = text[start_index:end_index].strip()
                    if self._is_valid_sql(sql_content):
                        sql_queries.append(sql_content)
                    start_index = text.find("```sql", end_index)
                    if start_index == -1:
                        break
                    start_index += 6
                else:
                    break
        
        # 提取直接的SQL语句
        sql_patterns = [
            r"SELECT\s+.*?\s+FROM\s+.*?(?:\s+WHERE\s+.*?)?(?:\s+LIMIT\s+\d+)?",
            r"SELECT\s+.*?\s+FROM\s+.*"
        ]
        
        for pattern in sql_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if self._is_valid_sql(match):
                    sql_queries.append(match.strip())
        
        return sql_queries
    
    def _is_valid_sql(self, sql: str) -> bool:
        """验证SQL语句的有效性"""
        if "SELECT" not in sql.upper():
            return False
        
        # 检查是否包含危险操作
        dangerous_operations = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER"]
        for operation in dangerous_operations:
            if operation in sql.upper():
                return False
        
        return True

def enhance_spatial_sql_agent_error_handling():
    """增强空间SQL代理的错误处理逻辑"""
    
    # 修改spatial_sql_agent.py中的错误处理部分
    enhanced_error_handling_code = '''
    def run(self, query: str) -> str:
        """
        执行SQL查询，支持空间查询
        
        Args:
            query: 自然语言查询字符串
            
        Returns:
            SQL查询结果字符串
        """
        try:
            if not isinstance(query, str):
                query = str(query)
            
            # 增强查询以包含空间提示
            enhanced_query = self._enhance_spatial_query(query)
            
            self.logger.info(f"处理空间查询: {enhanced_query}")
            
            # SQL agent expects input as a dictionary with 'input' key
            result = self.agent.invoke({"input": enhanced_query})
            
            if not isinstance(result, str):
                # Extract the output from the agent result
                if hasattr(result, 'get') and callable(result.get):
                    result = result.get('output', str(result))
                else:
                    result = str(result)
            
            # 后处理结果，确保包含空间信息
            result = self._postprocess_result(result, query)
            
            return result
            
        except Exception as e:
            self.logger.error(f"空间查询处理失败: {e}")
            
            # 改进的错误处理：使用新的解析器
            error_msg = str(e)
            
            # 检查是否是输出解析错误
            if "output parsing error" in error_msg.lower() or "could not parse llm output" in error_msg.lower():
                # 尝试从错误消息中提取LLM的实际输出
                import re
                llm_output_match = re.search(r"Could not parse LLM output: `(.*?)`", error_msg, re.DOTALL)
                if llm_output_match:
                    llm_output = llm_output_match.group(1)
                    self.logger.info(f"提取到LLM输出: {llm_output[:200]}...")
                    
                    # 使用新的解析器处理LLM输出
                    parser = LLMResponseParser()
                    parsed_result = parser.parse_llm_response(llm_output)
                    
                    if parsed_result["status"] == "success":
                        # 根据解析结果返回适当的内容
                        if "final_answer" in parsed_result:
                            return parsed_result["final_answer"]
                        elif "content" in parsed_result:
                            return parsed_result["content"]
                        elif "sql_queries" in parsed_result and parsed_result["sql_queries"]:
                            return parsed_result["sql_queries"][0]
                        else:
                            return llm_output
                    else:
                        return f"LLM响应: {llm_output[:500]}..."
            
            return f"抱歉，处理您的空间查询时出现了问题：{error_msg}"
    '''
    
    return enhanced_error_handling_code

def enhance_server_thought_chain_extraction():
    """增强服务器中的思维链提取逻辑"""
    
    enhanced_extraction_code = '''
    def extract_thought_chain(result: str) -> List[Dict[str, str]]:
        """
        从代理结果中提取思维链（Thought Chain）
        
        Args:
            result: 代理返回的结果字符串
            
        Returns:
            思维链列表，包含thought、action、action_input等信息
        """
        # 首先尝试使用新的解析器
        parser = LLMResponseParser()
        parsed_result = parser.parse_llm_response(result)
        
        if parsed_result["status"] == "success" and "thought_chain" in parsed_result:
            return parsed_result["thought_chain"]
        
        # 如果新解析器失败，回退到原来的逻辑
        thought_chain = []
        
        # 使用正则表达式提取Thought、Action、Action Input、Final Answer等
        thought_pattern = r"Thought:\s*(.*?)(?=Action:|Final Answer:|$)"
        action_pattern = r"Action:\s*(\w+)(?:\s+Action Input:\s*(.*?))?(?=Thought:|Final Answer:|$)"
        final_answer_pattern = r"Final Answer:\s*(.*?)(?=Thought:|Action:|$)"
        
        import re
        
        # 提取Thoughts
        thought_matches = re.findall(thought_pattern, result, re.DOTALL)
        for i, thought in enumerate(thought_matches):
            thought_chain.append({
                "step": i + 1,
                "type": "thought",
                "content": thought.strip(),
                "timestamp": f"step_{i+1}"
            })
        
        # 提取Actions
        action_matches = re.findall(action_pattern, result, re.DOTALL)
        for i, (action, action_input) in enumerate(action_matches):
            thought_chain.append({
                "step": len(thought_chain) + 1,
                "type": "action",
                "action": action.strip(),
                "action_input": action_input.strip() if action_input else "",
                "timestamp": f"step_{len(thought_chain)+1}"
            })
        
        # 提取Final Answer
        final_answer_matches = re.findall(final_answer_pattern, result, re.DOTALL)
        if final_answer_matches:
            thought_chain.append({
                "step": len(thought_chain) + 1,
                "type": "final_answer",
                "content": final_answer_matches[0].strip(),
                "timestamp": "final"
            })
        
        # 如果没有找到标准的思维链格式，尝试从整个结果中提取关键信息
        if not thought_chain:
            # 查找所有包含"Thought"、"Action"、"Final Answer"的行
            lines = result.split('\\n')
            current_step = 1
            for line in lines:
                line = line.strip()
                if line.startswith('Thought:'):
                    thought_chain.append({
                        "step": current_step,
                        "type": "thought",
                        "content": line.replace('Thought:', '').strip(),
                        "timestamp": f"step_{current_step}"
                    })
                    current_step += 1
                elif line.startswith('Action:'):
                    action_parts = line.replace('Action:', '').strip().split('Action Input:')
                    action = action_parts[0].strip()
                    action_input = action_parts[1].strip() if len(action_parts) > 1 else ""
                    thought_chain.append({
                        "step": current_step,
                        "type": "action",
                        "action": action,
                        "action_input": action_input,
                        "timestamp": f"step_{current_step}"
                    })
                    current_step += 1
                elif line.startswith('Final Answer:'):
                    thought_chain.append({
                        "step": current_step,
                        "type": "final_answer",
                        "content": line.replace('Final Answer:', '').strip(),
                        "timestamp": "final"
                    })
                    current_step += 1
        
        # 如果仍然没有找到思维链，返回整个结果作为单个thought
        if not thought_chain:
            thought_chain.append({
                "step": 1,
                "type": "thought",
                "content": result[:500] + "..." if len(result) > 500 else result,
                "timestamp": "single_step"
            })
        
        logger.info(f"提取到{len(thought_chain)}个思维链步骤")
        return thought_chain
    '''
    
    return enhanced_extraction_code

def main():
    """主函数：演示解析器功能"""
    print("LLM响应解析器演示")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        # 标准格式
        """
        Thought: 我需要先查看数据库中有哪些表
        Action: sql_db_list_tables
        Action Input: ""
        
        Thought: 现在我需要查询whupoi表的结构
        Action: sql_db_schema
        Action Input: "whupoi"
        
        Final Answer: 查询完成，找到了相关的数据
        """,
        
        # 直接答案格式（导致解析失败的例子）
        """
        I've successfully found POIs within 1km of 珞珈门 (Wuhan University Luojiamen) using PostGIS spatial functions. Here are the results:

        **珞珈门附近的POI（1公里范围内）：**

        1. **武汉大学珞珈门** - 距离 0.0 米
        2. **珞珈山站** (公交站) - 距离 32.5 米
        3. **KFC** (快餐店) - 距离 39.1 米
        
        这些POI主要分布在珞珈门周边100米范围内。
        """
    ]
    
    parser = LLMResponseParser()
    
    for i, test_case in enumerate(test_cases):
        print(f"\n测试用例 {i+1}:")
        print("-" * 30)
        result = parser.parse_llm_response(test_case.strip())
        print(f"解析状态: {result['status']}")
        print(f"解析类型: {result.get('type', 'unknown')}")
        if 'thought_chain' in result:
            print(f"思维链步骤数: {len(result['thought_chain'])}")
            for step in result['thought_chain'][:3]:  # 只显示前3个步骤
                if step['type'] == 'thought':
                    print(f"  步骤 {step['step']} ({step['type']}): {step['content'][:50]}...")
                elif step['type'] == 'action':
                    print(f"  步骤 {step['step']} ({step['type']}): {step['action']} - {step['action_input'][:30]}...")
                elif step['type'] == 'final_answer':
                    print(f"  步骤 {step['step']} ({step['type']}): {step['content'][:50]}...")
        
        if 'final_answer' in result and result['final_answer']:
            print(f"最终答案: {result['final_answer'][:100]}...")
        elif 'content' in result and result['content']:
            print(f"内容: {result['content'][:100]}...")
    
    print("\n" + "=" * 50)
    print("解析器演示完成")

if __name__ == "__main__":
    main()
