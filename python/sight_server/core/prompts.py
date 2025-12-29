"""
提示词管理模块 - Sight Server
集中管理所有Agent和LLM使用的提示词模板

启发式设计理念：从指令式转向启发式，调动LLM自身的知识和推理能力
"""

from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """提示词类型枚举"""
    SCENIC_QUERY = "scenic_query"  # 景区查询提示词
    SPATIAL_QUERY = "spatial_query"  # 空间查询提示词
    GENERAL_QUERY = "general_query"  # 通用查询提示词
    SUMMARY_QUERY = "summary_query"  # ✅ 新增：统计汇总查询提示词


class QueryIntentType(Enum):
    """查询意图类型枚举"""
    QUERY = "query"      # 查询类：获取具体数据
    SUMMARY = "summary"  # 总结类：统计汇总分析


# ==================== 查询意图分析关键词库 ====================

# 空间查询关键词（扩充版）
SPATIAL_KEYWORDS = [
    # 强空间关键词
    '距离', '附近', '周围', '范围内', '最近', '周边', '临近', '靠近', '邻近',
    '路径', '路线', '附近的', '周围的', '旁边', '边上',
    # PostGIS相关
    '相交', '包含', '在内', '边界', '缓冲', '缓冲区',
    # 英文关键词
    'distance', 'near', 'nearby', 'around', 'within',
    'route', 'path', 'nearest', 'proximity', 'intersect',
    'contain', 'buffer', 'st_', 'dwithin', 'surrounding'
]

# 总结/统计类查询关键词（扩充版）
SUMMARY_KEYWORDS = [
    # 强统计关键词
    '统计', '总结', '汇总', '计数', '总数', '总计', '一共', '总共', '共有', '合计',
    # 数量相关
    '多少', '数量', '个数', '有几个', '有多少', '几个',
    # 聚合函数
    '分布', '平均', '最多', '最少', '排名', '分析',
    '占比', '百分比', '比例',
    # 英文关键词
    'count', 'sum', 'average', 'max', 'min', 'total',
    'statistics', 'summary', 'analyze', 'how many', 'percentage'
]


class PromptManager:
    """
    提示词管理器

    功能:
    - 集中管理所有提示词模板
    - 支持动态提示词生成
    - 提供提示词自定义接口
    - 模板变量替换
    """

    # ==================== 启发式景区查询提示词 ====================
    SCENIC_QUERY_PROMPT = """
你是一个精通PostgreSQL和PostGIS的空间数据查询专家，专门处理全国景区旅游数据查询。

## 🎯 启发式思考框架

**请运用你的专业知识和推理能力，自主分析查询需求并生成最优SQL：**

### 核心思考原则：
1. **理解查询本质** - 分析用户真正需要什么数据
2. **评估数据需求** - 考虑是否需要坐标、详细信息、统计数据
3. **选择最佳策略** - 基于查询意图选择最合适的表连接方式
4. **确保数据完整** - 考虑如何获取最全面的景区信息

### 数据表结构（供你参考）：
- **a_sight**：基础景区信息（含坐标，纯中文名称）
- **tourist_spot**：详细旅游信息（含评分(类型为text，所以在查询时需要使用正则表达式)、门票、介绍，中英文名称）
- **关键关系**：两表通过名称模糊匹配（a_sight.name ≈ tourist_spot.name的中文部分）
- **注意**：两表数据只有一部分重合，若没有特别指明需要详细数据或设计坐标，空间，则两个表都要查询记录


### 查询策略思考指南：

**当你分析用户查询时，请考虑：**

1. **查询类型分析**
   - 用户需要具体数据还是统计结果？

   💡 **SQL 结构选择指南**：
   - **Summary 类型**（统计、汇总、数量）：
     * 直接使用 COUNT、SUM、AVG 等聚合函数
     * 返回数值结果：`SELECT COUNT(*) as count FROM ...`

   - **Query 类型**（列表、查询、详情）：
     * 使用 `SELECT json_agg(json_build_object(...)) as result FROM ...
       例如（仅供参考）：
    SELECT json_agg(
     json_build_object(
    'name', a.name,
    'level', a.level,
    'province', a."所属省份"
      )
      ) AS result
     FROM a_sight a;`
     * 返回完整的 JSON 数组

2. **数据完整性考虑**
   - 是否需要获取所有景区数据（包括两表独有的记录）？
   - 是否需要详细信息（评分、门票、介绍）？
   - 是否需要坐标信息？

3. **空间查询判断**
   - 是否涉及距离、附近、范围内等空间概念？
   - 是否需要使用PostGIS函数（ST_DWithin、ST_Distance等）？

4. **表连接策略选择**
   - 完整数据获取：考虑使用UNION ALL策略组合三个查询
   - 空间查询：使用LEFT JOIN确保有坐标数据
   - 详细信息优先：考虑从tourist_spot表开始连接

### 技术约束提醒：
- 必须包含完整的FROM子句定义表别名
- 优先使用精确匹配，若非指出精确地名且没有得到返回结果，则改为模糊匹配：例如
  `FROM a_sight a
  LEFT JOIN tourist_spot t
  t.name LIKE a.name || '%' OR TRIM(SPLIT_PART(t.name, ' ', 1)) = a.name`
- 评分字段需要安全处理（CASE语句处理无效值）
- 坐标使用WGS84标准：`ARRAY[lng_wgs84, lat_wgs84]` 或 `ARRAY[ST_X(ST_Transform(geom, 4326)), ST_Y(ST_Transform(geom, 4326))]`

### 输出要求：
- 确保SQL语法正确且可执行
- 考虑查询性能，适当使用LIMIT

现在，请基于以上思考框架，运用你的PostGIS和SQL专业知识，为用户的查询生成最优的SQL语句。
"""

    # ==================== 启发式空间查询提示词 ====================
    SPATIAL_ENHANCEMENT_PROMPT = """
## 🗺️ 空间查询思考指南

你正在处理一个空间查询，请运用你的PostGIS专业知识：

**空间思维要点：**
- 分析空间关系：距离、包含、相交等
- 选择合适的PostGIS函数：ST_DWithin、ST_Distance、ST_Intersects等
- 考虑坐标系转换：确保使用WGS84 (EPSG:4326)
- 评估性能：空间查询可能较慢，考虑使用索引

**空间查询策略：**
- 距离查询：优先使用ST_DWithin（效率更高）
- 范围查询：考虑ST_Intersects或ST_Within
- 坐标转换：使用ST_Transform确保坐标系一致

请基于空间分析原理生成最优的空间查询SQL。
"""

    # ==================== 启发式统计查询提示词 ====================
    SUMMARY_QUERY_PROMPT = """
你是一个精通PostgreSQL聚合查询和统计分析的专家，专门处理景区旅游数据的统计汇总与**分析任务**查询。

## 📊 启发式统计思维框架

**请运用你的统计知识，聚合查询和数据分析的经验，自主分析需求并生成最优SQL，并且对此做出解释：**

### 核心统计原则：
1. **理解统计本质** - 分析用户需要什么维度的统计数据
2. **选择聚合函数** - 基于需求选择合适的COUNT、SUM、AVG、GROUP BY等
3. **优化查询性能** - 统计查询通常需要高效执行
4. **确保结果准确** - 避免数据重复和统计偏差

### 统计查询策略思考指南：

**当你分析统计查询时，请考虑：**

1. **统计维度分析**
   - 是否需要按省份、城市、景区等级,地理坐标分组？
   - 是否需要多维度交叉统计？
   - 是否需要排序和限制结果？

2. **聚合函数选择**
   - **计数统计**：使用 COUNT(*) 或 COUNT(DISTINCT ...)
   - **求和统计**：使用 SUM() 计算总和
   - **平均值统计**：使用 AVG() 计算平均值
   - **极值统计**：使用 MAX()/MIN() 获取最值
   - **等等**

3. **表连接策略**
   - 统计查询通常不需要复杂表连接
   - 优先使用单一表进行统计以提高性能
   - 必要时使用简单的JOIN获取必要字段

4. **输出格式要求**
   - 使用有意义的列名：COUNT(*) as count, AVG(score) as avg_score
   - 考虑使用GROUP BY进行分组统计

### 技术约束提醒：
- 使用明确的列别名便于结果解析
- 考虑使用DISTINCT避免重复计数
- 使用WHERE条件过滤无效数据

### 常见统计场景示例：

**场景1：简单计数**
```sql
-- 统计浙江省5A景区数量
SELECT COUNT(*) as count 
FROM a_sight 
WHERE "所属省份" = '浙江省' AND level = '5A'
```

**场景2：分组统计**
```sql
-- 按省份统计景区数量
SELECT "所属省份" as province, COUNT(*) as count 
FROM a_sight 
GROUP BY "所属省份" 
ORDER BY count DESC
```

**场景3：多维度统计**
```sql
-- 按省份和等级统计景区分布
SELECT "所属省份" as province, level, COUNT(*) as count 
FROM a_sight 
GROUP BY "所属省份", level 
ORDER BY province, level
```

**场景4：复杂聚合**
```sql
-- 统计各省份景区平均评分（需要JOIN）
SELECT 
    a."所属省份" as province, 
    COUNT(*) as total_count,
    AVG(CASE 
        WHEN t."评分" ~ '^[0-9.]+$' THEN t."评分"::numeric 
        ELSE NULL 
    END) as avg_rating
FROM a_sight as  a
LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'
GROUP BY a."所属省份"
ORDER BY avg_rating DESC NULLS LAST
```

### 输出要求：
- 能够解释SQL查询的结果，并且分析意义
- 确保SQL语法正确且可执行
- 考虑查询性能，适当使用索引和优化
- 使用有意义的列名便于结果解析

现在，请基于以上统计思维框架，运用你的SQL聚合查询专业知识，为用户的统计查询生成最优的SQL语句。
"""

    # ==================== 通用查询提示词 ====================
    GENERAL_QUERY_PROMPT = """
你是一个专业的SQL查询助手，精通PostgreSQL数据库查询。

请运用你的SQL专业知识，分析用户需求并生成准确、高效的查询语句。

思考要点：
- 理解查询意图和数据需求
- 选择最优的查询策略和表连接方式
- 确保SQL语法正确和性能优化
- 考虑数据完整性和准确性

只返回SQL语句，不要任何解释。
"""

    @classmethod
    def get_prompt(cls, prompt_type: PromptType = PromptType.SCENIC_QUERY) -> str:
        """
        获取指定类型的提示词

        Args:
            prompt_type: 提示词类型

        Returns:
            提示词文本
        """
        prompt_map = {
            PromptType.SCENIC_QUERY: cls.SCENIC_QUERY_PROMPT,
            PromptType.SPATIAL_QUERY: cls.SPATIAL_ENHANCEMENT_PROMPT,
            PromptType.GENERAL_QUERY: cls.GENERAL_QUERY_PROMPT,
            PromptType.SUMMARY_QUERY: cls.SUMMARY_QUERY_PROMPT,  # ✅ 新增summary提示词
        }
        return prompt_map.get(prompt_type, cls.GENERAL_QUERY_PROMPT)

    @classmethod
    def get_scenic_query_prompt(cls) -> str:
        """获取景区查询提示词"""
        return cls.SCENIC_QUERY_PROMPT

    @classmethod
    def get_spatial_enhancement_prompt(cls) -> str:
        """获取空间查询增强提示词"""
        return cls.SPATIAL_ENHANCEMENT_PROMPT

    @classmethod
    def get_general_query_prompt(cls) -> str:
        """获取通用查询提示词"""
        return cls.GENERAL_QUERY_PROMPT

    @classmethod
    def get_summary_query_prompt(cls) -> str:
        """获取统计查询提示词"""
        return cls.SUMMARY_QUERY_PROMPT

    @classmethod
    def build_system_prompt_with_schema(cls, database_schema: str) -> str:
        """
        构建包含数据库schema的system prompt

        Args:
            database_schema: 格式化的数据库schema信息

        Returns:
            专业的system prompt文本
        """
        return f"""
你是一个精通PostgreSQL和PostGIS的SQL专家，专门处理全国景区旅游数据查询。

**数据库Schema信息**:
{database_schema}

**核心职责**:
- 将自然语言查询转换为准确的SQL语句
- 运用PostGIS专业知识处理空间查询
- 确保查询性能和结果准确性
- 遵循最佳SQL实践

请基于以上信息，为用户查询生成最优的SQL语句。
"""

    @classmethod
    def build_enhanced_query(
        cls,
        query: str,
        add_spatial_hint: bool = False,
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        构建增强的查询文本

        Args:
            query: 原始查询文本
            add_spatial_hint: 是否添加空间查询提示
            custom_instructions: 自定义指令

        Returns:
            增强后的查询文本
        """
        enhanced = query

        if add_spatial_hint:
            enhanced = f"{enhanced}\n\n{cls.SPATIAL_ENHANCEMENT_PROMPT}"

        if custom_instructions:
            enhanced = f"{enhanced}\n\n{custom_instructions}"

        return enhanced

    @classmethod
    def detect_query_type(cls, query: str) -> PromptType:
        """
        自动检测查询类型

        Args:
            query: 查询文本

        Returns:
            检测到的提示词类型
        """
        query_lower = query.lower()

        # 检测空间查询关键词
        spatial_keywords = [
            '距离', '附近', '周围', '范围内', '路径', '最近',
            'distance', 'near', 'nearby', 'around', 'within'
        ]

        if any(keyword in query_lower for keyword in spatial_keywords):
            return PromptType.SPATIAL_QUERY

        # 检测景区查询关键词
        scenic_keywords = [
            '景区', '景点', '旅游', '5a', '4a', '评级',
            'scenic', 'tourist', 'spot', 'attraction'
        ]

        if any(keyword in query_lower for keyword in scenic_keywords):
            return PromptType.SCENIC_QUERY

        return PromptType.GENERAL_QUERY

    @classmethod
    def analyze_query_intent(
        cls,
        query: str,
        llm: Optional[Any] = None,  # ✅ 新增 LLM 参数
        use_llm_analysis: bool = True  # ✅ 新增开关
    ) -> Dict[str, Any]:
        """
        分析查询意图

        优先使用 LLM 进行语义分析，失败时 fallback 到关键词分析

        Args:
            query: 查询文本
            llm: BaseLLM 实例（可选）
            use_llm_analysis: 是否使用 LLM 分析（默认 True）

        Returns:
            意图分析结果字典：
            {
                "intent_type": "query" | "summary",
                "is_spatial": bool,
                "prompt_type": PromptType,
                "keywords_matched": List[str],
                "description": str,
                "confidence": float,
                "analysis_details": Dict[str, Any],
                "semantic_enhanced": bool,
                "reasoning": str
            }
        """
        # ✅ 优先使用 LLM 分析
        if use_llm_analysis and llm:
            try:
                from .processors.intent_analyzer import IntentAnalyzer
                analyzer = IntentAnalyzer(llm)
                result = analyzer.analyze_intent(query)
                logger.info(
                    f"LLM intent analysis succeeded: {result['intent_type']}")
                return result
            except Exception as e:
                logger.warning(
                    f"LLM analysis failed, fallback to keywords: {e}")

        # ✅ Fallback: 使用原有的关键词分析
        logger.info("Using keyword-based intent analysis")
        return cls._analyze_intent_by_keywords(query)

    @classmethod
    def _analyze_intent_by_keywords(cls, query: str, use_semantic_enhancement: bool = True) -> Dict[str, Any]:
        """
        基于关键词的意图分析（保留作为 Fallback）

        原 analyze_query_intent() 的实现移到这里

        Args:
            query: 查询文本
            use_semantic_enhancement: 是否使用语义增强

        Returns:
            意图分析结果字典
        """
        query_lower = query.lower()

        # 初始化分析结果
        analysis_details = {
            "summary_score": 0.0,
            "spatial_score": 0.0,
            "scenic_score": 0.0,
            "matched_patterns": []
        }

        import re

        # ==================== 统计意图分析（优化版）====================
        summary_score = 0.0

        # 强统计关键词（权重 0.4）
        strong_summary_keywords = [
            '统计', '计数', '总数', '总计', '一共', '总共', '共有', '合计'
        ]
        for keyword in strong_summary_keywords:
            if keyword in query_lower:
                summary_score += 0.4
                analysis_details["matched_patterns"].append(
                    f"强统计关键词: {keyword}")

        # 中等统计关键词（权重 0.25）
        medium_summary_keywords = [
            '汇总', '总结', '分布', '平均', '最多', '最少',
            '个数', 'count', 'sum', 'total'
        ]
        for keyword in medium_summary_keywords:
            if keyword in query_lower:
                summary_score += 0.25
                analysis_details["matched_patterns"].append(
                    f"中等统计关键词: {keyword}")

        # 弱统计关键词（权重 0.15）
        weak_summary_keywords = [
            '占比', '百分比', '比例', 'average', 'max', 'min', 'percentage'
        ]
        for keyword in weak_summary_keywords:
            if keyword in query_lower:
                summary_score += 0.15
                analysis_details["matched_patterns"].append(
                    f"弱统计关键词: {keyword}")

        # ✅ 统计模式识别（优化正则）
        summary_patterns = [
            (r'有多少个?\b', 0.5),        # "有多少个"、"有多少"
            (r'一共.*?多少', 0.5),         # "一共有多少"
            (r'总共.*?多少', 0.5),         # "总共有多少"
            (r'多少.*?个', 0.4),           # "多少个景区"
            (r'(多少|几).{0,5}?个', 0.35),  # "多少/几XX个"
            (r'排名', 0.25),
            (r'分布情况', 0.3)
        ]

        # ✅ 排除模式（不是统计查询的特征）
        exclusion_patterns = [
            r'这几个',        # "这几个景区"是指代
            r'那几个',        # "那几个景区"是指代
            r'哪几个',        # "哪几个景区"是疑问
            r'前\d+个',       # "前10个"是排序
            r'后\d+个',       # "后10个"是排序
        ]

        # 检查排除模式
        has_exclusion = any(re.search(pattern, query_lower)
                            for pattern in exclusion_patterns)

        if not has_exclusion:
            # 只有在没有排除模式时才进行统计模式匹配
            for pattern, weight in summary_patterns:
                if re.search(pattern, query_lower):
                    summary_score += weight
                    analysis_details["matched_patterns"].append(
                        f"统计模式: {pattern}")

        # ✅ 意图动词检测 - Summary 加成
        summary_verbs = ['统计', '计算', '汇总', '总结']
        for verb in summary_verbs:
            if verb in query_lower:
                summary_score += 0.3
                analysis_details["matched_patterns"].append(f"统计动词: {verb}")
                break  # 只加一次

        analysis_details["summary_score"] = min(summary_score, 1.0)

        # ==================== 空间意图分析（优化版）====================
        spatial_score = 0.0

        # 强空间关键词（权重 0.3）
        strong_spatial_keywords = [
            '距离', '附近', '周围', '范围内', '最近', '周边', '临近', '靠近', '邻近', '分布'
        ]
        for keyword in strong_spatial_keywords:
            if keyword in query_lower:
                spatial_score += 0.3
                analysis_details["matched_patterns"].append(
                    f"强空间关键词: {keyword}")

        # 中等空间关键词（权重 0.2）
        medium_spatial_keywords = [
            '路径', '路线', '附近的', '周围的', '旁边', '边上',
            'near', 'nearby', 'around', 'within', 'surrounding'
        ]
        for keyword in medium_spatial_keywords:
            if keyword in query_lower:
                spatial_score += 0.2
                analysis_details["matched_patterns"].append(
                    f"中等空间关键词: {keyword}")

        # 弱空间关键词（权重 0.1）
        weak_spatial_keywords = [
            '相交', '包含', '边界', '缓冲', 'buffer', 'st_', 'dwithin'
        ]
        for keyword in weak_spatial_keywords:
            if keyword in query_lower:
                spatial_score += 0.1
                analysis_details["matched_patterns"].append(
                    f"弱空间关键词: {keyword}")

        # ✅ 空间模式识别（优化正则）
        spatial_patterns = [
            (r'距离.{0,10}?[公里|千米|米|km]', 0.5),      # "距离XX 10公里"
            (r'附近.{0,20}?[景区|景点]', 0.4),            # "附近的景区"
            (r'周边.{0,20}?[景区|景点]', 0.4),            # "周边的景区"
            (r'[东南西北].{0,5}?公里', 0.3),              # "东边5公里"
            (r'经纬度', 0.25),
            (r'坐标', 0.2)
        ]

        for pattern, weight in spatial_patterns:
            if re.search(pattern, query_lower):
                spatial_score += weight
                analysis_details["matched_patterns"].append(f"空间模式: {pattern}")

        analysis_details["spatial_score"] = min(spatial_score, 1.0)

        # ==================== 景区意图分析 ====================
        scenic_score = 0.0

        # 景区相关关键词
        scenic_keywords = ['景区', '景点', '旅游', '5a', '4a',
                           '3a', '2a', '1a', 'scenic', 'tourist', 'spot']
        for keyword in scenic_keywords:
            if keyword in query_lower:
                scenic_score += 0.1
                analysis_details["matched_patterns"].append(
                    f"景区关键词: {keyword}")

        # 景区等级模式
        level_patterns = [
            (r'[1-5]a景区', 0.3),
            (r'[1-5]a级', 0.3),
            (r'[1-5]a景点', 0.3)
        ]

        for pattern, weight in level_patterns:
            if re.search(pattern, query_lower):
                scenic_score += weight
                analysis_details["matched_patterns"].append(
                    f"景区等级模式: {pattern}")

        analysis_details["scenic_score"] = min(scenic_score, 1.0)

        # ==================== 意图动词折扣（优化）====================

        # ✅ Query 动词检测 - 降低 Summary 分数
        query_verbs = ['查询', '查找', '列出', '显示', '给我', '找', '搜索', '看看', '获取']
        has_query_verb = any(verb in query_lower for verb in query_verbs)
        if has_query_verb and summary_score > 0:
            # ✅ 更强的折扣：如果有明确的查询动词，打更大折扣
            original_score = summary_score
            summary_score *= 0.4  # 0.6 → 0.4（更强的折扣）
            analysis_details["matched_patterns"].append(
                f"Query动词折扣: {original_score:.2f} → {summary_score:.2f}")
            # 更新到 analysis_details
            analysis_details["summary_score"] = summary_score

        # ==================== 意图决策（优化阈值）====================

        # ✅ 降低阈值以减少漏判
        is_summary = analysis_details["summary_score"] >= 0.25  # 0.4 → 0.25
        is_spatial = analysis_details["spatial_score"] >= 0.2   # 0.3 → 0.2

        # 确定意图类型
        intent_type = QueryIntentType.SUMMARY.value if is_summary else QueryIntentType.QUERY.value

        # 确定提示词类型
        prompt_type = cls.detect_query_type(query)

        # ✅ 优化置信度计算（加权平均）
        if is_summary:
            confidence = analysis_details["summary_score"] * \
                0.7 + analysis_details["scenic_score"] * 0.3
        elif is_spatial:
            confidence = analysis_details["spatial_score"] * \
                0.7 + analysis_details["scenic_score"] * 0.3
        else:
            confidence = analysis_details["scenic_score"] if analysis_details["scenic_score"] > 0 else 0.5

        # 构建描述
        description_parts = []
        if is_summary:
            description_parts.append(
                f"统计汇总查询(置信度:{analysis_details['summary_score']:.2f})")
        else:
            description_parts.append(f"数据查询")

        if is_spatial:
            description_parts.append(
                f"空间查询(置信度:{analysis_details['spatial_score']:.2f})")

        if scenic_score > 0.2:
            description_parts.append(
                f"景区查询(置信度:{analysis_details['scenic_score']:.2f})")

        description = " - ".join(description_parts)

        # 收集匹配的关键词
        spatial_matched = [kw for kw in SPATIAL_KEYWORDS if kw in query_lower]
        summary_matched = [kw for kw in SUMMARY_KEYWORDS if kw in query_lower]

        # ==================== 语义推断增强（启发式）====================
        semantic_enhanced = False
        reasoning = "基于关键词分析"

        # 检查是否需要语义增强
        if use_semantic_enhancement:
            # 低置信度或模糊查询时使用语义增强
            needs_enhancement = (
                confidence < 0.3 or  # 置信度低
                # 无明确查询动词
                (intent_type == "query" and not any(keyword in query_lower for keyword in ['查询', '查找', '列出'])) or
                # 无明确统计动词
                (intent_type == "summary" and not any(keyword in query_lower for keyword in ['统计', '计数', '多少'])) or
                (is_spatial and not any(
                    keyword in query_lower for keyword in ['距离', '附近', '周边']))  # 无明确空间关键词
            )

            if needs_enhancement:
                semantic_enhanced = True
                reasoning = "语义推断增强：基于查询上下文理解意图"

                # 启发式语义推断规则
                if "排名" in query_lower and "前" in query_lower:
                    # "排名前十的景区" → 统计查询
                    intent_type = QueryIntentType.SUMMARY.value
                    confidence = max(confidence, 0.6)
                    reasoning += " → 排名查询识别为统计意图"

                elif "推荐" in query_lower or "热门" in query_lower:
                    # "推荐景区" → 详细信息查询
                    intent_type = QueryIntentType.QUERY.value
                    reasoning += " → 推荐查询识别为详细信息意图"

                elif "分布" in query_lower and "地图" not in query_lower:
                    # "景区分布" → 统计查询
                    intent_type = QueryIntentType.SUMMARY.value
                    confidence = max(confidence, 0.7)
                    reasoning += " → 分布查询识别为统计意图"

                # 空间意图的语义推断
                if not is_spatial and any(word in query_lower for word in ['周边', '附近', '距离']):
                    is_spatial = True
                    reasoning += " → 空间意图语义推断"

        return {
            "intent_type": intent_type,
            "is_spatial": is_spatial,
            "prompt_type": prompt_type,
            "keywords_matched": spatial_matched + summary_matched,
            "description": description,
            "confidence": confidence,
            "analysis_details": analysis_details,
            "semantic_enhanced": semantic_enhanced,
            "reasoning": reasoning
        }


# 测试代码
if __name__ == "__main__":
    print("=== 提示词管理器测试 ===\n")

    # 测试1：获取景区查询提示词
    print("--- 测试1: 获取景区查询提示词 ---")
    scenic_prompt = PromptManager.get_scenic_query_prompt()
    print(f"景区提示词长度: {len(scenic_prompt)} 字符")
    print(f"前200字符: {scenic_prompt[:200]}...\n")

    # 测试2：自动检测查询类型
    print("--- 测试2: 自动检测查询类型 ---")
    test_queries = [
        "查询浙江省的5A景区",
        "查找距离杭州10公里内的景点",
        "统计所有表的记录数"
    ]
    for query in test_queries:
        query_type = PromptManager.detect_query_type(query)
        print(f"查询: {query}")
        print(f"类型: {query_type.value}\n")

    # 测试3：构建增强查询
    print("--- 测试3: 构建增强查询 ---")
    original_query = "查询杭州市的景区"
    enhanced_query = PromptManager.build_enhanced_query(
        original_query,
        add_spatial_hint=True,
        custom_instructions="请返回前5条记录"
    )
    print(f"原始查询: {original_query}")
    print(f"增强查询长度: {len(enhanced_query)} 字符\n")

    # 测试4：查询意图分析
    print("--- 测试4: 查询意图分析 ---")
    intent_test_queries = [
        "查询浙江省的5A景区",
        "查找距离杭州10公里内的景区",
        "统计浙江省有多少个4A景区",
        "统计西湖周围5公里的景点分布"
    ]

    for query in intent_test_queries:
        intent = PromptManager.analyze_query_intent(query)
        print(f"查询: {query}")
        print(f"  意图类型: {intent['intent_type']}")
        print(f"  空间查询: {intent['is_spatial']}")
        print(f"  提示词类型: {intent['prompt_type'].value}")
        print(f"  匹配关键词: {intent['keywords_matched']}")
        print(f"  描述: {intent['description']}")
        print()
