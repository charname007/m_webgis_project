import logging
from typing import Dict, Any, List
from base_llm import BaseLLM
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
# import json  # 未使用，已注释
# import re  # 未使用，已注释

# 定义意图分析结果的Pydantic模型
class QueryIntentResult(BaseModel):
    """查询意图分析结果模型"""
    query_type: str = Field(description="查询类型 (spatial/summary/sql/general)")
    confidence: float = Field(description="置信度 (0.0-1.0)", ge=0.0, le=1.0)
    priority: int = Field(description="优先级 (1-4)", ge=1, le=4)
    intent_description: str = Field(description="对查询意图的详细描述")
    keywords_found: List[str] = Field(default_factory=list, description="找到的关键词列表")
    suggested_processing: str = Field(description="建议的处理方式")
    is_spatial: bool = Field(description="是否是空间查询")
    is_summary: bool = Field(description="是否是数据总结查询")
    is_sql: bool = Field(description="是否是SQL查询")

class QueryIntentAnalyzer:
    """
    使用LLM分析查询意图的专门类
    替代原有的基于关键词的analyze_query_type函数
    """
    
    def __init__(self, temperature: float = 0.3, model: str = "deepseek-chat"):
        """
        初始化意图分析器 - 优化版本

        Args:
            temperature: 控制随机性 (0.0到2.0)
            model: 使用的模型名称
        """
        self.logger = self._setup_logger()
        self.logger.info("开始初始化QueryIntentAnalyzer...")

        # 创建Pydantic输出解析器
        self.parser = PydanticOutputParser(pydantic_object=QueryIntentResult)
        self.logger.debug("✓ Pydantic解析器创建成功")

        # 创建专门的意图分析提示词
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_intent_analysis_prompt()),
            ("human", "{input}")
        ])

        # 创建专门的LLM实例用于意图分析
        try:
            self.llm = BaseLLM(
                temperature=temperature,
                model=model,
                prompt=self.intent_prompt,
                outparser=self.parser
            )
            self.logger.info(f"✓ BaseLLM初始化成功 (model={model}, temperature={temperature})")
        except Exception as e:
            self.logger.error(f"✗ BaseLLM初始化失败: {e}")
            raise

        self.logger.info("✓ QueryIntentAnalyzer初始化完成")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _get_intent_analysis_prompt(self) -> str:
        """
        获取意图分析的系统提示词
        """
        return """
你是一个专门分析自然语言查询意图的AI助手。你的任务是准确识别用户查询的类型和意图。

请根据用户的查询内容，分析其意图并返回标准化的JSON格式结果。

查询类型定义：
- 空间查询 (spatial): 涉及地理位置、距离、范围、路径、几何关系等
- 数据总结查询 (summary): 涉及统计、汇总、分析、报告等  
- SQL查询 (sql): 明确的数据库查询请求
- 一般查询 (general): 不涉及具体数据操作的一般性问题

优先级规则：空间查询 > 数据总结查询 > SQL查询 > 一般查询

输出格式要求：返回严格的JSON格式，包含以下字段：
- query_type: 查询类型 (spatial/summary/sql/general)
- confidence: 置信度 (0.0-1.0)
- priority: 优先级 (1-4)
- intent_description: 对查询意图的详细描述
- keywords_found: 找到的关键词列表
- suggested_processing: 建议的处理方式
- is_spatial: 是否是空间查询
- is_summary: 是否是数据总结查询  
- is_sql: 是否是SQL查询

请确保你的分析准确且全面。
"""
    
    def analyze_intent(self, query_text: str) -> Dict[str, Any]:
        """
        分析查询意图 - 优化版本

        Args:
            query_text: 自然语言查询文本

        Returns:
            意图分析结果字典
        """
        try:
            self.logger.info(f"开始分析查询意图: {query_text[:50]}...")

            # 使用LLM分析意图 - PydanticOutputParser会返回QueryIntentResult对象
            intent_result = self.llm.invoke(query_text, session_id="intent_analysis")

            # 将Pydantic对象转换为字典
            if isinstance(intent_result, QueryIntentResult):
                result_dict = intent_result.model_dump()
                self.logger.info(
                    f"✓ 意图分析完成: type={result_dict['query_type']}, "
                    f"confidence={result_dict['confidence']:.2f}"
                )
                return result_dict

            # 如果返回的不是Pydantic对象，尝试转换
            if hasattr(intent_result, '__dict__'):
                result_dict = dict(intent_result)
            else:
                result_dict = intent_result

            self.logger.info(f"✓ 意图分析完成: {result_dict.get('query_type', 'unknown')}")
            return result_dict

        except Exception as e:
            self.logger.error(f"✗ 意图分析失败: {e}", exc_info=False)
            # 返回回退结果
            return self._get_fallback_result(query_text)
    
    def _extract_from_text(self, text: str, original_query: str) -> Dict[str, Any]:
        """
        从文本中提取意图信息
        
        Args:
            text: LLM响应文本
            original_query: 原始查询
            
        Returns:
            提取的意图信息
        """
        # 默认结果
        result = {
            "query_type": "general",
            "confidence": 0.5,
            "priority": 4,
            "intent_description": "无法准确识别意图",
            "keywords_found": [],
            "suggested_processing": "使用通用查询处理",
            "is_spatial": False,
            "is_summary": False,
            "is_sql": False
        }
        
        # 尝试从文本中提取类型信息
        text_lower = text.lower()
        original_lower = original_query.lower()
        
        # 检查空间相关关键词
        spatial_keywords = [
            '距离', '附近', '周围', '范围内', '路径', '路线', '最短', '最近',
            '相交', '包含', '在内', '边界', '面积', '长度', '周长',
            '点', '线', '面', '多边形', '几何', '空间', '地理',
            'buffer', 'intersect', 'contain', 'within', 'distance',
            'route', 'path', 'shortest', 'nearest', 'proximity',
            'st_', 'geom', 'geometry', '坐标', '经纬度'
        ]
        
        # 检查总结相关关键词
        summary_keywords = [
            '总结', '统计', '汇总', '分析', '报告', '概况', '总数',
            '平均', '最大', '最小', '分布', '趋势', '比例',
            'summary', 'statistics', 'analyze', 'report', 'overview',
            'count', 'average', 'max', 'min', 'distribution'
        ]
        
        # 检查SQL相关关键词
        sql_keywords = [
            '查询', '查找', '搜索', '获取', '显示', '列出',
            'select', 'find', 'search', 'get', 'show', 'list',
            'where', 'from', 'table', 'column'
        ]
        
        # 查找关键词
        found_spatial = [kw for kw in spatial_keywords if kw in original_lower]
        found_summary = [kw for kw in summary_keywords if kw in original_lower]
        found_sql = [kw for kw in sql_keywords if kw in original_lower]
        
        # 根据关键词确定类型
        if found_spatial:
            result.update({
                "query_type": "spatial",
                "confidence": 0.8,
                "priority": 1,
                "intent_description": "检测到空间查询意图",
                "keywords_found": found_spatial,
                "suggested_processing": "使用空间查询处理",
                "is_spatial": True
            })
        elif found_summary:
            result.update({
                "query_type": "summary",
                "confidence": 0.8,
                "priority": 2,
                "intent_description": "检测到数据总结意图",
                "keywords_found": found_summary,
                "suggested_processing": "使用数据总结处理",
                "is_summary": True
            })
        elif found_sql:
            result.update({
                "query_type": "sql",
                "confidence": 0.8,
                "priority": 3,
                "intent_description": "检测到SQL查询意图",
                "keywords_found": found_sql,
                "suggested_processing": "使用SQL查询处理",
                "is_sql": True
            })
        
        return result
    
    def _get_fallback_result(self, query_text: str) -> Dict[str, Any]:
        """
        获取回退结果（当LLM分析失败时使用）
        
        Args:
            query_text: 查询文本
            
        Returns:
            回退分析结果
        """
        query_lower = query_text.lower()
        
        # 简单的关键词匹配（类似于原来的analyze_query_type函数）
        spatial_keywords = ['距离', '附近', '路径', '相交', '包含', '点', '线', '面', '空间', '地理']
        summary_keywords = ['总结', '统计', '汇总', '分析', '报告', '总数', '平均']
        sql_keywords = ['查询', '查找', '搜索', '获取', '显示', '列出']
        
        is_spatial = any(keyword in query_lower for keyword in spatial_keywords)
        is_summary = any(keyword in query_lower for keyword in summary_keywords)
        is_sql = any(keyword in query_lower for keyword in sql_keywords)
        
        # 优先级：空间查询 > 数据总结 > 普通SQL查询
        if is_spatial:
            query_type = "spatial"
            priority = 1
        elif is_summary:
            query_type = "summary"
            priority = 2
        elif is_sql:
            query_type = "sql"
            priority = 3
        else:
            query_type = "general"
            priority = 4
        
        return {
            "query_type": query_type,
            "confidence": 0.6,  # 回退结果的置信度较低
            "priority": priority,
            "intent_description": "使用关键词匹配分析意图",
            "keywords_found": [],
            "suggested_processing": "使用通用查询处理",
            "is_spatial": is_spatial,
            "is_summary": is_summary,
            "is_sql": is_sql
        }
    
    def batch_analyze(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        批量分析查询意图
        
        Args:
            queries: 查询文本列表
            
        Returns:
            意图分析结果列表
        """
        results = []
        for query in queries:
            result = self.analyze_intent(query)
            results.append(result)
        
        return results
    
    def get_statistics(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取意图分析统计信息
        
        Args:
            analysis_results: 分析结果列表
            
        Returns:
            统计信息
        """
        if not analysis_results:
            return {}
        
        type_counts = {}
        total_confidence = 0
        
        for result in analysis_results:
            query_type = result["query_type"]
            type_counts[query_type] = type_counts.get(query_type, 0) + 1
            total_confidence += result["confidence"]
        
        avg_confidence = total_confidence / len(analysis_results)
        
        return {
            "total_queries": len(analysis_results),
            "type_distribution": type_counts,
            "average_confidence": round(avg_confidence, 3),
            "most_common_type": max(type_counts, key=lambda k: type_counts[k]) if type_counts and len(type_counts) > 0 else "none"
        }


# 测试函数
def test_intent_analyzer():
    """测试意图分析器"""
    analyzer = QueryIntentAnalyzer()
    
    test_queries = [
        "查找距离武汉大学5公里内的所有建筑",
        "统计数据库中所有道路的总长度",
        "查询名称包含'医院'的所有点",
        "这个系统能做什么？",
        "计算从A点到B点的最短路径，并分析路径上的设施分布"
    ]
    
    print("=== 查询意图分析测试 ===")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. 查询: {query}")
        result = analyzer.analyze_intent(query)
        
        print(f"   类型: {result['query_type']}")
        print(f"   置信度: {result['confidence']}")
        print(f"   优先级: {result['priority']}")
        print(f"   描述: {result['intent_description']}")
        print(f"   建议处理: {result['suggested_processing']}")
    
    # 批量分析统计
    batch_results = analyzer.batch_analyze(test_queries)
    stats = analyzer.get_statistics(batch_results)
    
    print(f"\n=== 批量分析统计 ===")
    print(f"总查询数: {stats['total_queries']}")
    print(f"类型分布: {stats['type_distribution']}")
    print(f"平均置信度: {stats['average_confidence']}")
    print(f"最常见类型: {stats['most_common_type']}")


if __name__ == "__main__":
    test_intent_analyzer()
