"""
SQL生成器模块 - Sight Server
负责将自然语言查询转换为SQL语句
"""

import logging
import re
from typing import Optional, List, Dict, Any
from langchain_core.prompts import PromptTemplate

logger = logging.getLogger(__name__)


class SQLGenerator:
    ALIAS_TABLE_MAP = {
        'a': 'a_sight',
        'a_sight': 'a_sight',
        't': 'tourist_spot',
        'ts': 'tourist_spot',
        'tourist_spot': 'tourist_spot',
    }
    ALIAS_DEFAULT_MAPPING = {
        'a_sight': 'a',
        'tourist_spot': 't',
    }
    SUPPORTED_CTE_ALIASES = {'combined', 'combined_data'}

    """
    SQL生成器

    功能:
    - 将自然语言查询转换为SQL
    - 支持初始查询和后续查询
    - 分析缺失信息并生成补充查询
    """

    def __init__(self, llm, base_prompt: str):
        """
        初始化SQL生成器

        Args:
            llm: LLM实例 (BaseLLM)
            base_prompt: 基础提示词
        """
        self.llm = llm
        self.base_prompt = base_prompt
        self.logger = logger
        self._cached_schema: Optional[str] = None
        self._init_prompt_templates()

    def _build_sql_generation_prompt(self, match_mode: str) -> PromptTemplate:
        # 确保模板已初始化
        if not hasattr(self, 'sql_generation_template') or not self.sql_generation_template:
            self.logger.warning("sql_generation_template not initialized, reinitializing...")
            self._init_prompt_templates()
        
        template = self.sql_generation_template.replace("{match_rules}", self._get_match_rules(match_mode, context="initial"))
        return PromptTemplate(template=template, input_variables=self.sql_generation_inputs)

    def _build_followup_prompt(self, match_mode: str) -> PromptTemplate:
        # 确保模板已初始化
        if not hasattr(self, 'followup_query_template') or not self.followup_query_template:
            self.logger.warning("followup_query_template not initialized, reinitializing...")
            self._init_prompt_templates()
        
        template = self.followup_query_template.replace("{match_rules}", self._get_match_rules(match_mode, context="followup"))
        return PromptTemplate(template=template, input_variables=self.followup_query_inputs)

    def _get_match_rules(self, match_mode: str, context: str = "initial") -> str:
        if match_mode.lower() == "exact":
            rules = [
                "## 🎯 精确匹配策略（按需启用）",
                "",
                "- 根据用户明确要求，使用 `=` 对文本字段进行精确比较。",
                "- 可结合 `LOWER()` / `UPPER()` 统一大小写，避免遗漏。",
                "- 如需匹配多个关键词，可使用 `IN` 或多条件 `OR`。",
                "- 未明确要求时请谨慎使用精确过滤，以免遗漏结果。",
            ]
        else:
            rules = [
                "## 🔍 模糊匹配策略（默认启用）",
                "",
                "- 对涉及用户输入的文本条件，优先使用模糊匹配。",
                "- 推荐书写 `column ILIKE '%' || <value> || '%'` 或 `column ILIKE CONCAT('%', <value>, '%')`。",
                "- 用户明确要求“精确匹配/完全一致”时再使用 `=`。",
                "- 组合多个关键字时可先用 `ILIKE` 然后通过 `AND/OR` 组合。",
            ]
        return "\n".join(rules)

    def _init_prompt_templates(self) -> None:
                # ✅ 启发式 SQL 生成 Prompt（调动 LLM 的 SQL 专业知识和推理能力）
                self.sql_generation_template = """你是一个精通 PostgreSQL 和 PostGIS 的 SQL 专家。

        {base_prompt}

        **数据库Schema信息**（完整字段类型供你参考）:
        {database_schema}

        **用户查询**: {query}

        **查询意图分析**（供你参考）:
        - 查询类型: {intent_type} (query=用户需要具体数据 / summary=用户需要统计结果)
        - 空间特征: {is_spatial} (True=涉及距离/位置计算 / False=普通数据查询)
        - 置信度: {confidence}
        - 相关关键词: {keywords_matched}

        ---

        ## 📋 意图组合决策表（快速决策指南）

        根据 **intent_type** 和 **is_spatial** 的组合，选择对应的 SQL 结构：

        ┌─────────────┬─────────────┬──────────────────────────────┬────────────────────────────┐
        │ intent_type │ is_spatial  │ 查询示例                     │ SQL 结构要求               │
        ├─────────────┼─────────────┼──────────────────────────────┼────────────────────────────┤
        │ query       │ False       │ "查询浙江省的5A景区"         │ json_agg + 完整字段        │
        │ query       │ True        │ "距离西湖10公里内的景区"     │ json_agg + 坐标 + 空间过滤 │
        │ summary     │ False       │ "统计浙江省有多少景区"       │ COUNT/AVG + 可选GROUP BY   │
        │ summary     │ True ⭐     │ "武汉市景区的空间分布"       │ GROUP BY + 空间字段        │
        └─────────────┴─────────────┴──────────────────────────────┴────────────────────────────┘

        **当前查询属于**: {intent_type} + {spatial_type} → 请严格遵守对应的 SQL 结构要求

        ---

        ## ⚠️ CRITICAL RULES（绝对必须遵守）

        {match_rules}
        **根据 intent_type 和 is_spatial 严格选择 SQL 结构：**

        ### 📊 Summary 查询 (intent_type="summary") - 规则：

        #### Summary + Non-Spatial (普通统计查询)
           ✅ **必须使用聚合函数**: COUNT(*), SUM(...), AVG(...), MAX(...), MIN(...)
           ✅ **必须返回简单数值或分组统计**
           ✅ **允许 GROUP BY 分组统计**
           ❌ **禁止使用 json_agg 或 json_build_object**

           **正确示例**：
           ```sql
           -- 简单数量统计
           SELECT COUNT(*) as count FROM a_sight WHERE level = '5A'

           -- 分组统计
           SELECT "所属省份" as province, COUNT(*) as count
           FROM a_sight GROUP BY "所属省份"

           -- 多维度统计
           SELECT level, COUNT(*) as count 
           FROM a_sight GROUP BY level ORDER BY count DESC
           ```

        #### Summary + Spatial (空间统计查询) ⭐ 重要
           ✅ **必须返回空间维度的统计**（不能只有总数）
           ✅ **推荐使用 GROUP BY + 空间字段**（按区域/等级分组）
           ✅ **必须包含空间信息**（中心坐标、边界范围等）
           ❌ **禁止只返回简单的 COUNT(*)**

           **正确示例1：按行政区分组统计**（⭐ 推荐，最常用）
           ```sql
           -- "武汉市景区的空间分布" → 按区域分组 + 空间中心
           SELECT
             COALESCE(a."所属行政区", '未知') as district,
             COUNT(*) as count,
             AVG(a.lng_wgs84) as center_lng,  -- ⭐ 区域中心经度
             AVG(a.lat_wgs84) as center_lat   -- ⭐ 区域中心纬度
           FROM a_sight a
           WHERE a."所属城市" = '武汉市'
             AND a.lng_wgs84 IS NOT NULL
             AND a.lat_wgs84 IS NOT NULL
           GROUP BY a."所属行政区"
           ORDER BY count DESC
           ```

           **正确示例2：按景区等级分组 + 空间中心**
           ```sql
           -- "统计各等级景区的空间分布"
           SELECT
             a.level,
             COUNT(*) as count,
             AVG(a.lng_wgs84) as center_lng,
             AVG(a.lat_wgs84) as center_lat
           FROM a_sight a
           WHERE a."所属城市" = '武汉市'
             AND a.lng_wgs84 IS NOT NULL
           GROUP BY a.level
           ORDER BY a.level
           ```

           **正确示例3：空间范围统计**（边界框）
           ```sql
           -- "武汉市景区的分布范围"
           SELECT
             COUNT(*) as total_count,
             MIN(lng_wgs84) as bbox_min_lng,  -- 西边界
             MAX(lng_wgs84) as bbox_max_lng,  -- 东边界
             MIN(lat_wgs84) as bbox_min_lat,  -- 南边界
             MAX(lat_wgs84) as bbox_max_lat,  -- 北边界
             AVG(lng_wgs84) as center_lng,    -- 中心点经度
             AVG(lat_wgs84) as center_lat     -- 中心点纬度
           FROM a_sight
           WHERE "所属城市" = '武汉市' AND lng_wgs84 IS NOT NULL
           ```

           **正确示例4：高级空间分析**（可选，使用 PostGIS 函数）
           ```sql
           -- 地理网格统计（需要 PostGIS）
           SELECT
             ST_GeoHash(lng_wgs84, lat_wgs84, 4) as grid_id,
             COUNT(*) as count,
             AVG(lng_wgs84) as center_lng,
             AVG(lat_wgs84) as center_lat
           FROM a_sight
           WHERE "所属城市" = '武汉市'
             AND lng_wgs84 IS NOT NULL
           GROUP BY ST_GeoHash(lng_wgs84, lat_wgs84, 4)
           ORDER BY count DESC
           ```

           ❌ **错误示例**（只返回总数，丢失空间维度）：
           ```sql
           -- ❌ 错误："空间分布"查询不能只返回总数
           SELECT COUNT(*) as count
           FROM a_sight
           WHERE "所属城市" = '武汉市'
           ```

        ### 📋 Query 查询 (intent_type="query") - 规则：

        #### Query + Non-Spatial (普通数据查询)
           ✅ **必须使用 json_agg(json_build_object(...))**
           ✅ **必须返回 JSON 数组格式**
           ✅ **必须包含完整的记录信息**

           **正确示例**：
           ```sql
           SELECT json_agg(json_build_object(
               'name', name,
               'level', level,
               'city', city
           )) as result
           FROM a_sight WHERE level = '5A'
           ```

        #### Query + Spatial (空间数据查询)
           ✅ **必须使用 json_agg(json_build_object(...))**
           ✅ **必须包含空间坐标信息**
           ✅ **应该使用空间排序和过滤**
           ✅ **可以包含空间聚类分析**

           **正确示例**：
           ```sql
           -- 空间查询（带坐标）
           SELECT json_agg(json_build_object(
               'name', name,
               'level', level,
               'coordinates', json_build_array(lng_wgs84, lat_wgs84)
           )) as result
           FROM a_sight 
           WHERE "所属城市" = '武汉市'
             AND lng_wgs84 IS NOT NULL 
             AND lat_wgs84 IS NOT NULL

           -- 空间聚类查询
           SELECT json_agg(json_build_object(
               'name', name,
               'level', level,
               'coordinates', json_build_array(lng_wgs84, lat_wgs84),
               'cluster_id', ST_GeoHash(lng_wgs84, lat_wgs84, 3)
           )) as result
           FROM a_sight 
           WHERE "所属城市" = '武汉市'
           ORDER BY ST_GeoHash(lng_wgs84, lat_wgs84, 3)
           ```

        ---

        ## 🤔 请运用你的 SQL 专业知识

        基于以上信息，请思考：

        ### 1. 查询意图理解
           - 用户真正需要什么数据？
           - 是需要统计汇总（数量、平均值等），还是具体记录列表？
           - 是否涉及空间计算（距离、范围等）？

           💡 **关键区分**：
           - **intent_type = "summary"**: 用户只需要统计数字（数量、平均值、总数、分布等），不需要详细记录
           - **intent_type = "query"**: 用户需要具体记录列表或详细信息

        ### 2. 数据获取策略
           - 需要从哪些表获取数据？（参考上方Schema信息中的表结构）
           - 如何确保获取完整的数据（包括只在某个表中存在的记录）？
           - 是否需要表连接？用什么连接方式最合适（INNER JOIN、LEFT JOIN、UNION ALL等）？
           - 对于两表数据只有部分重合的情况，如何设计查询才不会遗漏数据？

        ### 3. SQL 结构设计

           **Summary 查询**（intent_type="summary"）：
           - ✅ 直接使用聚合函数：COUNT、SUM、AVG、MAX、MIN 等
           - ✅ 返回简单的数值或统计结果
           - ❌ **不要使用 json_agg 或 json_build_object**
           - 示例：`SELECT COUNT(*) as count FROM table WHERE condition`
           - 示例：`SELECT level, COUNT(*) as count FROM table GROUP BY level`

           **Query 查询**（intent_type="query"）：
           - ✅ 使用 json_agg(json_build_object(...)) 返回 JSON 数组
           - ✅ 返回完整的记录列表
           - 示例：`SELECT json_agg(json_build_object(...)) as result FROM table WHERE condition`

           **其他注意事项**：
           - WHERE 条件应该放在哪里？（子查询内部、外层、还是两者都有）
           - 如何处理可能的 NULL 值和数据类型问题？（参考Schema中的字段类型）
           - 如何避免表别名作用域错误（子查询内的别名外层无法访问）？

        ### 4. 性能和正确性
           - SQL 语法是否完整（FROM 子句、表别名定义等）？
           - 是否考虑了查询性能（LIMIT、索引利用等）？
           - 对于聚合查询，是否遵守了 GROUP BY 规则？

        ---

        请基于你的专业判断和 PostgreSQL 最佳实践，生成最优的 SQL 查询。

        只返回SQL语句，不要解释。

        SQL:"""
                self.sql_generation_inputs = [
                    "base_prompt",
                    "database_schema",
                    "query",
                    "intent_type",
                    "is_spatial",
                    "spatial_type",
                    "confidence",
                    "keywords_matched",
                ]

                # ✅ 启发式补充查询 Prompt（引导 LLM 思考如何获取完整数据）
                self.followup_query_template = """你是一个擅长优化和补充查询的 SQL 专家。

        {base_prompt}

        **数据库Schema信息**（完整字段类型供你参考）:
        {database_schema}

        **用户原始需求**: {original_query}

        **已执行的查询**:
        ```sql
        {previous_sql}
        ```

        **当前数据状况**:
        - 已获取记录数: {record_count}
        - 发现缺失字段: {missing_fields}

        ---

        {match_rules}

        ## 🤔 请分析并决定如何获取完整数据

        ### 思考框架：

        1. **数据完整性分析**
           - 哪些字段缺失了？
           - 这些字段通常在哪个表中？（参考上方Schema信息中的表结构和字段类型）
           - 是否可以通过补充查询获取？还是数据源本身不完整？

        2. **补充查询策略**
           - 应该查询哪些表？
           - 如何与已有数据关联？（通过名称匹配、ID 关联等）
           - 用什么连接方式最合适？（LEFT JOIN、INNER JOIN、还是其他）

        3. **查询优化**
           - 如何避免重复获取已有数据？
           - 如何确保补充查询的效率？
           - WHERE 条件应该如何设置以精准获取缺失数据？

        4. **SQL 结构设计**
           - 是否使用 json_agg 返回 JSON 数组？
           - 如何确保返回的数据可以与已有数据合并？
           - 如何处理可能的 NULL 值？（参考Schema中的字段类型）

        ---

        请基于你的 SQL 专业知识，生成补充查询的 SQL 语句。

        只返回SQL语句，不要解释。

        SQL:"""
                self.followup_query_inputs = [
                    "base_prompt",
                    "database_schema",
                    "original_query",
                    "previous_sql",
                    "record_count",
                    "missing_fields",
                ]

    def set_database_schema(self, formatted_schema: Optional[str]):
        """缓存数据库schema，避免每次调用时重复传入"""
        if formatted_schema and formatted_schema.strip():
            cleaned_schema = formatted_schema.strip()
            if cleaned_schema != self._cached_schema:
                self._cached_schema = cleaned_schema
                self.logger.info("✅ SQLGenerator schema context updated (length=%s)", len(cleaned_schema))
        else:
            self.logger.debug("set_database_schema called with empty schema; ignoring")

    def _resolve_schema_for_prompt(self, database_schema: Optional[str] = None) -> str:
        """优先使用传入schema，否则使用缓存或LLM上下文"""
        candidates = [
            database_schema,
            self._cached_schema,
        ]

        if hasattr(self.llm, 'system_context'):
            context_schema = getattr(self.llm, 'system_context', {}).get('database_schema')
        else:
            context_schema = None
        candidates.append(context_schema)

        for schema in candidates:
            if isinstance(schema, str) and schema.strip():
                return schema
        return "(Schema信息未加载)"

    def generate_initial_sql(
        self,
        query: str,
        intent_info: Optional[Dict[str, Any]] = None,  # ✅ 意图信息
        database_schema: Optional[str] = None,  # ✅ 新增参数：数据库Schema
        match_mode: str = "fuzzy",
    ) -> str:
        """
        生成初始SQL查询

        Args:
            query: 用户查询
            intent_info: 查询意图信息（可选）
                - intent_type: "query" 或 "summary"
                - is_spatial: bool
                - confidence: float
                - keywords_matched: List[str]
            database_schema: 格式化的数据库Schema字符串（可选）
            match_mode: 匹配模式（fuzzy/ exact），默认使用模糊匹配

        Returns:
            生成的SQL语句
        """
        try:
            # ✅ 提取意图信息（如果提供）
            intent_type = "query"  # 默认值
            is_spatial = False
            confidence = 0.0
            keywords_matched = []

            if intent_info:
                intent_type = intent_info.get("intent_type", "query")
                is_spatial = intent_info.get("is_spatial", False)
                confidence = intent_info.get("confidence", 0.0)
                keywords_matched = intent_info.get("keywords_matched", [])

            # 格式化关键词列表
            keywords_str = ", ".join(keywords_matched) if keywords_matched else "无"

            # ✅ 格式化空间类型文本
            spatial_type = "空间" if is_spatial else "非空间"

            # ✅ 如果没有提供schema，使用空字符串
            schema_str = self._resolve_schema_for_prompt(database_schema)

            # 构建提示词（✅ 传递意图信息和Schema）
            generation_prompt = self._build_sql_generation_prompt(match_mode)
            prompt_text = generation_prompt.format(
                base_prompt=self.base_prompt,
                database_schema=schema_str,
                query=query,
                intent_type=intent_type,
                is_spatial=is_spatial,
                spatial_type=spatial_type,  # ✅ 新增参数
                confidence=f"{confidence:.2f}",
                keywords_matched=keywords_str
            )

            # 调用LLM生成SQL
            self.logger.debug(
                f"Generating initial SQL for query: {query} "
                f"(intent={intent_type}, spatial={is_spatial}, confidence={confidence:.2f}, match_mode={match_mode})"
            )
            response = self.llm.llm.invoke(prompt_text)

            # 提取SQL
            sql = self._extract_sql(response)

            # ✅ 验证SQL结构
            if not self._validate_sql_structure(sql):
                self.logger.warning("Generated SQL missing proper FROM clause, attempting to fix")
                sql = self._add_from_clause_if_missing(sql, query)
                # 再次验证
                if not self._validate_sql_structure(sql):
                    self.logger.error("Unable to fix SQL structure automatically")

            # ✅ 验证 summary 查询的 SQL
            is_valid, warning = self._validate_summary_sql(sql, intent_type, is_spatial)
            if not is_valid:
                self.logger.warning(f"Summary SQL validation failed: {warning}")
                self.logger.info(f"Generated SQL (may be incorrect for summary): {sql[:100]}...")

                # ✅ 尝试自动修复
                sql = self._fix_summary_sql_if_needed(sql, intent_type)

                # ✅ 再次验证修复后的 SQL
                is_valid_after_fix, warning_after_fix = self._validate_summary_sql(sql, intent_type, is_spatial)
                if is_valid_after_fix:
                    self.logger.info("✓ Summary SQL auto-fixed successfully")
                else:
                    self.logger.error(f"✗ Summary SQL fix failed: {warning_after_fix}")
                    # 修复失败，但仍返回（让后续错误处理机制处理）

            self.logger.info(f"Generated initial SQL ({intent_type}, spatial={is_spatial}): {sql[:100]}...")
            return sql

        except Exception as e:
            self.logger.error(f"Initial SQL generation failed: {e}")
            raise

    def generate_followup_sql(
        self,
        original_query: str,
        previous_sql: str,
        record_count: int,
        missing_fields: Optional[List[str]] = None,
        database_schema: Optional[str] = None,  # ✅ 新增参数：数据库Schema
        match_mode: str = "fuzzy",
    ) -> str:
        """
        生成后续补充查询SQL

        Args:
            original_query: 原始查询
            previous_sql: 之前执行的SQL
            record_count: 当前记录数
            missing_fields: 缺失的字段列表（可选）
            database_schema: 格式化的数据库Schema字符串（可选）
            match_mode: 匹配模式（fuzzy/ exact）

        Returns:
            生成的补充SQL语句
        """
        try:
            # ✅ 如果没有提供schema，使用空字符串
            schema_str = self._resolve_schema_for_prompt(database_schema)
            missing_fields = missing_fields or []

            # 构建提示词（包含Schema）
            followup_prompt = self._build_followup_prompt(match_mode)
            prompt_text = followup_prompt.format(
                base_prompt=self.base_prompt,
                database_schema=schema_str,
                original_query=original_query,
                previous_sql=previous_sql,
                record_count=record_count,
                missing_fields=", ".join(missing_fields or [])
            )

            # 调用LLM生成SQL
            self.logger.debug(
                f"Generating followup SQL; previous count={record_count}, missing fields={missing_fields or []}, match_mode={match_mode}"
            )
            response = self.llm.llm.invoke(prompt_text)

            # 提取SQL
            sql = self._extract_sql(response)
            self.logger.info(f"Generated followup SQL: {sql[:100]}...")
            return sql

        except Exception as e:
            self.logger.error(f"Followup SQL generation failed: {e}")
            raise

    def analyze_missing_info(
        self,
        query: str,
        current_data: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        保留兼容接口，直接返回统一结构，避免重复字段分析。
        """
        if not current_data:
            return {
                "has_missing": True,
                "missing_fields": [],
                "data_complete": False,
                "suggestion": "暂无数据，可按需重新查询"
            }

        self.logger.debug("Skipping missing-field analysis; assume full column set returned")
        return {
            "has_missing": False,
            "missing_fields": [],
            "data_complete": True,
            "suggestion": "结果已包含全部字段，可直接生成答案"
        }

    def _extract_sql(self, response) -> str:
        """
        从LLM响应中提取SQL语句

        Args:
            response: LLM响应

        Returns:
            清理后的SQL语句
        """
        # 提取SQL（response可能是字符串或对象）
        if hasattr(response, 'content'):
            sql = response.content.strip()
        else:
            sql = str(response).strip()

        # 移除可能的markdown代码块标记
        sql = re.sub(r'^```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'^```\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)
        sql = sql.strip()

        return sql

    def fix_sql_with_error(
        self,
        sql: str,
        error: str,
        query: str,
        database_schema: Optional[str] = None  # ✅ 新增参数：数据库Schema
    ) -> str:
        """
        根据错误信息修复SQL

        Args:
            sql: 原始SQL
            error: 错误信息
            query: 原始查询
            database_schema: 格式化的数据库Schema字符串（可选）

        Returns:
            修复后的SQL
        """
        try:
            # ✅ 如果没有提供schema，使用空字符串
            schema_str = self._resolve_schema_for_prompt(database_schema)

            # ✅ 启发式修复提示词（调动 LLM 的 SQL 专业知识）
            fix_prompt = f"""你是一个精通 PostgreSQL 和 PostGIS 的 SQL 专家。

**数据库Schema信息**（完整字段类型供你参考）:
{schema_str}

**用户需求**: {query}

**生成的 SQL**:
```sql
{sql}
```

**执行错误**:
```
{error}
```

---

## 🤔 请运用你的 PostgreSQL 专业知识进行诊断和修复

### 思考框架：

1. **错误诊断**
   - 这是什么类型的 PostgreSQL 错误？（语法、约束、聚合、类型转换、作用域等）
   - 错误的根本原因是什么？
   - SQL 的哪个部分违反了 PostgreSQL 规则？

2. **问题分析**
   - 查询的意图是什么？（获取数据、统计、空间查询）
   - 当前的 SQL 结构有什么问题？
   - 哪些 PostgreSQL 特性或规则与此相关？
   - 参考上方Schema信息，字段类型是否正确使用？

3. **修复策略**
   - 如何在保持查询意图的同时修复错误？
   - 是否需要调整：表连接方式、WHERE 位置、聚合函数、子查询结构、字段作用域？
   - 有没有更优雅的 PostgreSQL 解决方案？

4. **最佳实践**
   - 修复后的 SQL 是否符合 PostgreSQL 语法规范？
   - 是否考虑了性能优化？
   - 是否处理了可能的 NULL 值和边界情况？（参考Schema中的字段类型）

---

## 📚 相关背景知识（供参考）

**PostgreSQL 核心规则**:
- 聚合查询时，SELECT/WHERE/HAVING 中引用的非聚合字段必须在 GROUP BY 中
- 子查询的表别名（如 a, t）作用域仅限于该子查询内部，外层无法直接访问
- UNION ALL 要求各子查询返回相同数量、顺序和类型的字段
- FROM 子句必须先定义表和别名，才能在 SELECT/WHERE 中使用

---

请基于你的 SQL 专业知识和对错误的理解，生成修复后的 SQL 语句。

只返回修复后的 SQL，不要解释。

修复后的 SQL:"""

            # 调用LLM生成修复后的SQL
            self.logger.debug(f"Attempting to fix SQL with error: {error[:100]}")
            response = self.llm.llm.invoke(fix_prompt)

            # 提取修复后的SQL
            fixed_sql = self._extract_sql(response)

            # ✅ 验证修复后的SQL是否包含FROM子句
            if not self._validate_sql_structure(fixed_sql):
                self.logger.warning("Fixed SQL still missing FROM clause, adding it manually")
                fixed_sql = self._add_from_clause_if_missing(fixed_sql, query)

            self.logger.info(f"SQL fixed: {fixed_sql[:100]}...")
            return fixed_sql

        except Exception as e:
            self.logger.error(f"Failed to fix SQL: {e}")
            # 如果修复失败，返回原始SQL
            return sql

    def regenerate_with_feedback(
        self,
        query: str,
        previous_sql: str,
        feedback: str,
        intent_info: Optional[Dict[str, Any]] = None,
        database_schema: Optional[str] = None
    ) -> str:
        """
        基于验证反馈重新生成改进的 SQL

        Args:
            query: 用户原始查询
            previous_sql: 之前生成的 SQL
            feedback: 验证反馈信息（包含问题和建议）
            intent_info: 查询意图信息（可选）
            database_schema: 格式化的数据库Schema字符串（可选）

        Returns:
            str: 改进后的 SQL
        """
        try:
            # 如果没有提供schema，使用空字符串
            schema_str = self._resolve_schema_for_prompt(database_schema)

            # 获取意图信息
            intent_type = intent_info.get("intent_type", "query") if intent_info else "query"
            is_spatial = intent_info.get("is_spatial", False) if intent_info else False

            # 构建改进提示词
            improve_prompt = f"""你是 PostgreSQL + PostGIS 专家，需要基于验证反馈改进 SQL 查询。

**数据库Schema信息**:
{schema_str}

**用户问题**: {query}

**查询意图**: {intent_type} (空间查询: {'是' if is_spatial else '否'})

**之前的 SQL**:
```sql
{previous_sql}
```

**验证反馈**:
{feedback}

---

## 🎯 任务

请根据验证反馈中指出的问题，改进 SQL 查询以满足用户需求。

## 🔍 改进方向

1. **分析反馈**:
   - 反馈指出了什么问题？（缺少字段、数据不准确、不相关等）
   - 问题的根本原因是什么？
   - 用户实际需要什么信息？

2. **改进策略**:
   - 如果缺少关键字段：添加必要的字段到 SELECT 子句
   - 如果需要坐标信息：确保包含 ST_X(geom) as longitude, ST_Y(geom) as latitude
   - 如果数据不准确：检查 WHERE 条件和 JOIN 关系
   - 如果结果不相关：重新审视查询逻辑

3. **数据库Schema应用**:
   - 参考上方Schema信息，确保使用正确的表名和字段名
   - 注意字段类型（如 geometry 类型需用 PostGIS 函数）
   - 考虑表之间的关联关系

4. **查询意图考虑**:
   - 如果是 summary 类型：确保包含聚合函数（COUNT, SUM, AVG等）和 GROUP BY
   - 如果是 query 类型：确保返回完整的记录列表
   - 如果是空间查询：确保包含坐标字段和空间函数

## ⚠️ 重要约束

- 必须保留 `json_agg(...) as result` 的输出格式
- 确保包含完整的 FROM 子句
- 使用合适的表别名（a_sight → a, tourist_spot → t）
- 根据需求选择合适的 JOIN 类型（FULL OUTER JOIN / LEFT JOIN）

## 输出

只返回改进后的 SQL，不要解释。

改进后的 SQL:"""

            # 调用LLM生成改进的SQL
            self.logger.debug(f"Regenerating SQL based on feedback: {feedback[:100]}")
            response = self.llm.llm.invoke(improve_prompt)

            # 提取改进后的SQL
            improved_sql = self._extract_sql(response)

            # 验证改进后的SQL是否包含FROM子句
            if not self._validate_sql_structure(improved_sql):
                self.logger.warning("Improved SQL still missing FROM clause, adding it manually")
                improved_sql = self._add_from_clause_if_missing(improved_sql, query)

            self.logger.info(f"SQL improved based on feedback: {improved_sql[:100]}...")
            return improved_sql

        except Exception as e:
            self.logger.error(f"Failed to regenerate SQL with feedback: {e}")
            # 如果重新生成失败，返回原始SQL
            return previous_sql

    def _validate_sql_structure(self, sql: str) -> bool:
        """
        验证SQL是否包含必需的FROM子句和正确的别名定义

        Args:
            sql: SQL语句

        Returns:
            bool: SQL结构是否有效
        """
        sql_lower = sql.lower()

        # 检查是否包含FROM关键字
        if 'from' not in sql_lower:
            self.logger.warning("SQL missing FROM keyword")
            return False

        # 提取所有使用的表别名（模式：别名.字段名）
        alias_pattern = r'\b([a-z_][a-z0-9_]*)\.\w+'
        used_aliases = set(re.findall(alias_pattern, sql_lower))
        
        # 移除系统关键字和常见函数名
        system_keywords = {'select', 'from', 'where', 'group', 'order', 'having', 'limit', 'offset', 'join', 'on', 'as', 'and', 'or', 'not', 'in', 'is', 'null', 'true', 'false'}
        used_aliases = used_aliases - system_keywords

        allowed_aliases = set(self.ALIAS_TABLE_MAP.keys()) | set(self.SUPPORTED_CTE_ALIASES)
        unsupported_aliases = {alias for alias in used_aliases if alias not in allowed_aliases}
        if unsupported_aliases:
            self.logger.warning(f"Unsupported aliases detected during auto-repair: {unsupported_aliases}")
            raise ValueError(f"Unsupported aliases for auto-repair: {', '.join(sorted(unsupported_aliases))}")

        if not used_aliases:
            # 如果没有使用任何别名，则只需检查FROM子句存在即可
            self.logger.debug("No table aliases used in SQL")
            return True

        # 提取FROM子句中定义的别名
        from_pattern = r'from\s+(\w+(?:\s+(?:as\s+)?(\w+))?(?:\s*,\s*\w+(?:\s+(?:as\s+)?(\w+))?)*)'
        from_match = re.search(from_pattern, sql_lower)
        
        if not from_match:
            self.logger.warning("FROM clause found but cannot parse table aliases")
            return False

        # 提取所有定义的别名
        defined_aliases = set()
        
        # 匹配简单的表定义：table alias 或 table AS alias
        simple_table_pattern = r'(\w+)(?:\s+(?:as\s+)?(\w+))?'
        from_content = from_match.group(1)
        
        # 分割多个表定义（处理逗号分隔）
        table_definitions = re.split(r'\s*,\s*', from_content)
        
        for table_def in table_definitions:
            table_match = re.match(simple_table_pattern, table_def.strip())
            if table_match:
                table_name = table_match.group(1)
                alias_name = table_match.group(2)
                
                # 如果没有显式别名，表名本身就是别名
                if alias_name:
                    defined_aliases.add(alias_name)
                else:
                    defined_aliases.add(table_name)

        # 检查JOIN子句中的别名定义
        join_pattern = r'(?:inner|left|right|full|cross)\s+join\s+(\w+)(?:\s+(?:as\s+)?(\w+))?'
        join_matches = re.finditer(join_pattern, sql_lower)
        
        for join_match in join_matches:
            table_name = join_match.group(1)
            alias_name = join_match.group(2)
            
            if alias_name:
                defined_aliases.add(alias_name)
            else:
                defined_aliases.add(table_name)

        # 检查所有使用的别名是否都已定义
        undefined_aliases = (used_aliases - set(self.SUPPORTED_CTE_ALIASES)) - defined_aliases
        
        if undefined_aliases:
            self.logger.warning(f"SQL uses undefined table aliases: {undefined_aliases}")
            for alias in undefined_aliases:
                self.logger.warning(f"  - Alias '{alias}' is used but not defined in FROM clause")
            return False

        self.logger.debug(f"SQL validation passed. Used aliases: {used_aliases}, Defined aliases: {defined_aliases}")
        return True

    def _validate_summary_sql(self, sql: str, intent_type: str, is_spatial: bool = False) -> tuple[bool, str]:
        """
        验证 summary 查询的 SQL 是否正确

        Summary 查询应该：
        1. 使用聚合函数（COUNT、SUM、AVG等）或空间聚合函数
        2. 根据是否空间查询使用不同的规则

        Args:
            sql: 生成的 SQL
            intent_type: 查询意图类型（"query" 或 "summary"）
            is_spatial: 是否空间查询

        Returns:
            (is_valid, warning_message): 验证结果和警告信息
        """
        # 只验证 summary 类型的查询
        if intent_type != "summary":
            return (True, "")

        sql_lower = sql.lower()

        # 空间统计查询的特殊规则
        if is_spatial:
            # 空间统计查询必须包含空间维度的统计，不能只有简单计数

            # 检查是否包含空间字段（经纬度）
            has_spatial_fields = any(keyword in sql_lower for keyword in ['lng_wgs84', 'lat_wgs84', 'lng', 'lat', 'longitude', 'latitude'])

            if not has_spatial_fields:
                return (False, "空间统计查询必须包含空间字段（lng_wgs84、lat_wgs84 等）")

            # 检查是否包含空间聚合或分组
            spatial_aggregation_patterns = [
                r'avg\(.*?lng',           # AVG(lng_wgs84) - 中心点经度
                r'avg\(.*?lat',           # AVG(lat_wgs84) - 中心点纬度
                r'min\(.*?lng',           # MIN(lng_wgs84) - 边界框
                r'max\(.*?lng',           # MAX(lng_wgs84) - 边界框
                r'min\(.*?lat',           # MIN(lat_wgs84) - 边界框
                r'max\(.*?lat',           # MAX(lat_wgs84) - 边界框
                r'round\(.*?lng',         # ROUND(lng_wgs84) - 密度分析
                r'round\(.*?lat',         # ROUND(lat_wgs84) - 密度分析
                r'st_geohash',            # ST_GeoHash - 地理网格
                r'st_collect',            # ST_Collect - 几何聚合
                r'st_centroid',           # ST_Centroid - 中心点
                r'group by.*?行政区',     # GROUP BY 行政区 - 按区域分组
                r'group by.*?level',      # GROUP BY level - 按等级分组
                r'group by.*?province',   # GROUP BY province - 按省份分组
                r'group by.*?city',       # GROUP BY city - 按城市分组
            ]

            has_spatial_aggregation = any(
                re.search(pattern, sql_lower)
                for pattern in spatial_aggregation_patterns
            )

            if not has_spatial_aggregation:
                return (False, "空间统计查询必须包含空间聚合（AVG/MIN/MAX经纬度、GROUP BY区域等）或空间分组")

            # ⚠️ 严格禁止：只有 COUNT(*) 而没有任何空间维度
            # 允许: COUNT(*) + AVG(lng/lat) 或 COUNT(*) + GROUP BY 区域
            # 禁止: 只有 COUNT(*) 而没有其他空间字段
            if 'count(*)' in sql_lower:
                # 检查是否同时包含空间聚合字段（AVG/MIN/MAX经纬度）
                has_spatial_agg_fields = any(
                    re.search(pattern, sql_lower)
                    for pattern in [
                        r'avg\(.*?lng', r'avg\(.*?lat',
                        r'min\(.*?lng', r'max\(.*?lng',
                        r'min\(.*?lat', r'max\(.*?lat'
                    ]
                )

                # 检查是否使用了 GROUP BY
                has_group_by = 'group by' in sql_lower

                if not has_spatial_agg_fields and not has_group_by:
                    return (False, "空间统计查询不能只返回 COUNT(*)，必须包含空间维度（AVG经纬度、边界框、GROUP BY区域等）")

            # 通过验证
            self.logger.debug(f"Spatial summary SQL validation passed for: {sql[:50]}...")
            return (True, "")

        # 普通统计查询的规则
        else:
            # 检查1: 普通统计查询不应该使用 json_agg
            if 'json_agg' in sql_lower:
                return (False, "普通统计查询不应该使用 json_agg，应该直接使用 COUNT/SUM/AVG 等聚合函数")

            # 检查2: 普通统计查询应该包含聚合函数
            aggregation_keywords = ['count(', 'sum(', 'avg(', 'max(', 'min(', 'group by']
            has_aggregation = any(keyword in sql_lower for keyword in aggregation_keywords)

            if not has_aggregation:
                return (False, "普通统计查询应该包含聚合函数（COUNT、SUM、AVG 等）或 GROUP BY 子句")

            # 通过验证
            self.logger.debug(f"Non-spatial summary SQL validation passed for: {sql[:50]}...")
            return (True, "")

    def _fix_summary_sql_if_needed(self, sql: str, intent_type: str) -> str:
        """
        如果 Summary SQL 包含 json_agg，自动转换为 COUNT

        Args:
            sql: 原始 SQL
            intent_type: 查询意图类型

        Returns:
            修复后的 SQL
        """
        if intent_type != "summary":
            return sql

        sql_lower = sql.lower()

        # 检查是否包含 json_agg（错误的 Summary SQL）
        if 'json_agg' not in sql_lower:
            return sql

        self.logger.warning("Detected json_agg in Summary SQL, auto-fixing to COUNT")

        try:
            # 提取 FROM 子句
            from_match = re.search(
                r'FROM\s+(.+?)(?:WHERE|GROUP|ORDER|LIMIT|$)',
                sql,
                re.IGNORECASE | re.DOTALL
            )

            # 提取 WHERE 子句
            where_match = re.search(
                r'WHERE\s+(.+?)(?:GROUP|ORDER|LIMIT|$)',
                sql,
                re.IGNORECASE | re.DOTALL
            )

            # 提取 GROUP BY 子句
            group_match = re.search(
                r'GROUP\s+BY\s+(.+?)(?:ORDER|LIMIT|$)',
                sql,
                re.IGNORECASE | re.DOTALL
            )

            # 提取 ORDER BY 子句
            order_match = re.search(
                r'ORDER\s+BY\s+(.+?)(?:LIMIT|$)',
                sql,
                re.IGNORECASE | re.DOTALL
            )

            # 提取 LIMIT 子句
            limit_match = re.search(
                r'LIMIT\s+(\d+)',
                sql,
                re.IGNORECASE
            )

            # 重建为简单 COUNT SQL
            fixed_sql = "SELECT COUNT(*) as count\n"

            if from_match:
                from_clause = from_match.group(1).strip()
                # 移除可能的子查询别名
                from_clause = re.sub(r'\)\s+\w+\s*$', ')', from_clause)
                fixed_sql += f"FROM {from_clause}\n"

            if where_match:
                where_clause = where_match.group(1).strip()
                fixed_sql += f"WHERE {where_clause}\n"

            if group_match:
                group_clause = group_match.group(1).strip()
                fixed_sql += f"GROUP BY {group_clause}\n"

            if order_match:
                order_clause = order_match.group(1).strip()
                fixed_sql += f"ORDER BY {order_clause}\n"

            if limit_match:
                limit_value = limit_match.group(1)
                fixed_sql += f"LIMIT {limit_value}\n"

            self.logger.info(f"Auto-fixed Summary SQL: removed json_agg, using COUNT")
            self.logger.debug(f"Fixed SQL: {fixed_sql[:100]}...")

            return fixed_sql

        except Exception as e:
            self.logger.error(f"Failed to auto-fix Summary SQL: {e}")
            # 修复失败，返回原 SQL
            return sql

    def _build_default_from_clause(self, uses_a: bool, uses_t: bool) -> str:
        """
        构建缺失 FROM 子句时的默认表关联。
        """
        if uses_a and uses_t:
            lines = [
                "FROM a_sight a",
                "LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'",
                "    OR TRIM(SPLIT_PART(t.name, ' ', 1)) = a.name",
            ]
            return "\n".join(lines) + "\n"

        if uses_a:
            return "FROM a_sight a\n"

        if uses_t:
            return "FROM tourist_spot t\n"

        return "FROM a_sight a\n"




    def _add_from_clause_if_missing(self, sql: str, query: str) -> str:
        """当SQL缺少FROM子句或别名定义时，自动补全。"""
        fixed_sql = sql

        alias_pattern = r"\b([a-z_][a-z0-9_]*)\.\w+"
        used_aliases = {alias for alias in re.findall(alias_pattern, sql.lower())}

        system_keywords = {
            "select", "from", "where", "group", "order", "having", "limit",
            "offset", "join", "on", "as", "and", "or", "not", "in", "is",
            "null", "true", "false",
        }
        used_aliases -= system_keywords

        alias_lookup: dict[str, str] = {}
        unsupported_aliases: list[str] = []
        for alias in used_aliases:
            if alias in self.SUPPORTED_CTE_ALIASES:
                continue
            table = self.ALIAS_TABLE_MAP.get(alias)
            if not table:
                unsupported_aliases.append(alias)
                continue
            alias_lookup.setdefault(table, alias)

        if unsupported_aliases:
            raise ValueError(f"Unsupported aliases for auto-repair: {', '.join(sorted(unsupported_aliases))}")

        if not alias_lookup:
            return fixed_sql

        alias_adjusted = False
        for table_name, alias in alias_lookup.items():
            pattern = rf"\b{table_name}\b(?!\s+(?:as\s+)?{alias}\b)"
            updated_sql, replacements = re.subn(pattern, f"{table_name} {alias}", fixed_sql, count=1, flags=re.IGNORECASE)
            if replacements:
                fixed_sql = updated_sql
                alias_adjusted = True

        sql_lower = fixed_sql.lower()
        needs_default_from = "from" not in sql_lower
        for alias in alias_lookup.values():
            if not re.search(rf"\bfrom\s+.*\b(?:as\s+)?{alias}\b", sql_lower):
                needs_default_from = True
                break

        if needs_default_from:
            from_block = self._build_enhanced_from_clause(alias_lookup)

            from_match = re.search(r"\bfrom\b", fixed_sql, re.IGNORECASE)
            if from_match:
                after_from = fixed_sql[from_match.end():]
                boundary_match = re.search(
                    r"\bWHERE\b|\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|\bHAVING\b|\bUNION\b|\bEXCEPT\b|\bINTERSECT\b",
                    after_from,
                    re.IGNORECASE,
                )
                end_index = from_match.end() + boundary_match.start() if boundary_match else len(fixed_sql)
                original_from_segment = fixed_sql[from_match.start():end_index]
                trailing_clause = fixed_sql[end_index:]

                join_pattern = re.compile(r"\b(?:INNER|LEFT|RIGHT|FULL|CROSS)\s+JOIN\b|\bJOIN\b", re.IGNORECASE)
                join_match = join_pattern.search(original_from_segment)
                trailing_joins = original_from_segment[join_match.start():].strip() if join_match else ""

                rebuilt_from = from_block.rstrip("\n")
                if trailing_joins:
                    rebuilt_from = f"{rebuilt_from}\n{trailing_joins}"
                rebuilt_from = f"{rebuilt_from}\n"

                prefix = fixed_sql[:from_match.start()].rstrip()
                if prefix and not prefix.endswith("\n"):
                    prefix += "\n"
                suffix = trailing_clause.lstrip()
                fixed_sql = f"{prefix}{rebuilt_from}{suffix}"
            else:
                before_where = re.search(r"\bWHERE\b", fixed_sql, re.IGNORECASE)
                if before_where:
                    prefix = fixed_sql[:before_where.start()].rstrip()
                    if prefix and not prefix.endswith("\n"):
                        prefix += "\n"
                    suffix = fixed_sql[before_where.start():]
                    fixed_sql = f"{prefix}{from_block}{suffix}"
                else:
                    trimmed = fixed_sql.rstrip()
                    if trimmed and not trimmed.endswith("\n"):
                        trimmed += "\n"
                    fixed_sql = f"{trimmed}{from_block}"

            self.logger.info(f"Auto-rebuilt FROM clause for aliases: {set(alias_lookup.values())}")
        else:
            if alias_adjusted:
                self.logger.info("Auto-added missing table aliases in FROM clause")
            else:
                self.logger.info("SQL structure appears valid, no changes needed")

        if not self._validate_sql_structure(fixed_sql):
            self.logger.warning("Auto-repair failed, SQL structure still invalid")
            self.logger.debug(f"Failed to repair SQL: {fixed_sql}")

        return fixed_sql

    def _build_enhanced_from_clause(self, alias_lookup: dict[str, str]) -> str:
        """根据使用的别名构建增强的FROM子句"""
        def alias_for_join(table: str, alias: Optional[str]) -> str:
            return alias if alias else self.ALIAS_DEFAULT_MAPPING[table]

        def format_table_clause(table: str, alias: Optional[str]) -> str:
            if alias and alias == table:
                return table
            effective_alias = alias if alias else self.ALIAS_DEFAULT_MAPPING[table]
            if effective_alias == table:
                return table
            return f"{table} {effective_alias}"

        sight_alias = alias_lookup.get('a_sight')
        tourist_alias = alias_lookup.get('tourist_spot')
        sight_join_alias = alias_for_join('a_sight', sight_alias)
        tourist_join_alias = alias_for_join('tourist_spot', tourist_alias)

        if sight_alias and tourist_alias:
            lines = [
                format_table_clause('a_sight', sight_alias),
                f"LEFT JOIN {format_table_clause('tourist_spot', tourist_alias)} ON {tourist_join_alias}.name LIKE {sight_join_alias}.name || '%'",
                f"    OR TRIM(SPLIT_PART({tourist_join_alias}.name, ' ', 1)) = {sight_join_alias}.name",
            ]
        elif sight_alias:
            lines = [format_table_clause('a_sight', sight_alias)]
        elif tourist_alias:
            lines = [format_table_clause('tourist_spot', tourist_alias)]
        else:
            default_alias = self.ALIAS_DEFAULT_MAPPING['a_sight']
            lines = [format_table_clause('a_sight', default_alias)]

        return "\n".join(lines) + "\n"

    def fix_sql_with_context(
        self,
        sql: str,
        error_context: Dict[str, Any],
        query: str,
        database_schema: Optional[str] = None
    ) -> str:
        """
        使用错误上下文增强修复SQL

        Args:
            sql: 原始SQL
            error_context: 错误上下文信息
                - failed_sql: 失败的SQL
                - error_message: 错误信息
                - error_code: PostgreSQL错误码
                - error_position: 错误位置
                - failed_at_step: 失败步骤
                - query_context: 查询上下文
                - database_context: 数据库上下文
                - execution_context: 执行上下文
            query: 原始查询
            database_schema: 格式化的数据库Schema字符串（可选）

        Returns:
            修复后的SQL
        """
        try:
            # ✅ 如果没有提供schema，使用空字符串
            schema_str = self._resolve_schema_for_prompt(database_schema)

            # ✅ 提取错误上下文信息
            error_message = error_context.get("error_message", "")
            error_code = error_context.get("error_code", "")
            error_position = error_context.get("error_position")
            failed_at_step = error_context.get("failed_at_step", 0)
            
            # ✅ 提取查询上下文
            query_context = error_context.get("query_context", {})
            original_query = query_context.get("original_query", query)
            enhanced_query = query_context.get("enhanced_query", query)
            intent_type = query_context.get("intent_type", "query")
            requires_spatial = query_context.get("requires_spatial", False)
            
            # ✅ 提取数据库上下文
            database_context = error_context.get("database_context", {})
            schema_used = database_context.get("schema_used", {})
            tables_accessed = database_context.get("tables_accessed", [])
            
            # ✅ 提取执行上下文
            execution_context = error_context.get("execution_context", {})
            execution_time_ms = execution_context.get("execution_time_ms", 0)
            rows_affected = execution_context.get("rows_affected", 0)

            # ✅ 增强修复提示词（利用完整的错误上下文）
            fix_prompt = f"""你是一个精通 PostgreSQL 和 PostGIS 的 SQL 专家。

**数据库Schema信息**（完整字段类型供你参考）:
{schema_str}

**用户需求**: {original_query}
**增强查询**: {enhanced_query}
**查询意图**: {intent_type} (query=具体数据 / summary=统计结果)
**空间查询**: {requires_spatial}

**失败的 SQL**:
```sql
{sql}
```

**执行错误详情**:
- 错误信息: {error_message}
- PostgreSQL 错误码: {error_code}
- 错误位置: {error_position}
- 失败步骤: {failed_at_step}
- 执行耗时: {execution_time_ms:.0f}ms
- 影响行数: {rows_affected}

**数据库上下文**:
- 使用的表: {', '.join(tables_accessed) if tables_accessed else '未知'}
- Schema 状态: {'已加载' if schema_used else '未加载'}

---

## 🤔 请运用你的 PostgreSQL 专业知识进行深度诊断和修复

### 思考框架：

1. **错误深度分析**
   - 根据 PostgreSQL 错误码 {error_code}，这是什么类型的错误？
   - 错误位置 {error_position} 指向 SQL 的哪个部分？
   - 结合查询意图 {intent_type} 和空间需求 {requires_spatial}，分析根本原因

2. **上下文关联分析**
   - 用户真正需要什么数据？（参考原始需求: {original_query}）
   - 当前 SQL 结构是否匹配查询意图？
   - 使用的表 {tables_accessed} 是否合适？
   - 执行耗时 {execution_time_ms:.0f}ms 是否暗示性能问题？

3. **修复策略制定**
   - 如何保持查询意图 {intent_type} 的同时修复错误？
   - 是否需要调整：表连接策略、聚合函数使用、子查询结构、字段作用域？
   - 对于空间查询 {requires_spatial}，PostGIS 函数使用是否正确？
   - 如何优化性能避免超时？

4. **最佳实践验证**
   - 修复后的 SQL 是否符合 PostgreSQL 语法规范？
   - 是否考虑了数据类型匹配？（参考上方Schema信息）
   - 是否处理了可能的 NULL 值和边界情况？
   - 是否利用了适当的索引和查询优化？

---

## 📚 相关背景知识（供参考）

**PostgreSQL 核心规则**:
- 聚合查询时，SELECT/WHERE/HAVING 中引用的非聚合字段必须在 GROUP BY 中
- 子查询的表别名作用域仅限于该子查询内部，外层无法直接访问
- UNION ALL 要求各子查询返回相同数量、顺序和类型的字段
- FROM 子句必须先定义表和别名，才能在 SELECT/WHERE 中使用
- 对于空间查询，确保 PostGIS 函数参数类型正确

**常见错误码解读**:
- 42P01: 表不存在
- 42703: 列不存在
- 42601: 语法错误
- 42883: 函数不存在（常见于 PostGIS 函数）

---

请基于完整的错误上下文和你的 SQL 专业知识，生成修复后的 SQL 语句。

只返回修复后的 SQL，不要解释。

修复后的 SQL:"""

            # 调用LLM生成修复后的SQL
            self.logger.debug(f"Attempting to fix SQL with enhanced context, error_code: {error_code}")
            response = self.llm.llm.invoke(fix_prompt)

            # 提取修复后的SQL
            fixed_sql = self._extract_sql(response)

            # ✅ 验证修复后的SQL是否包含FROM子句
            if not self._validate_sql_structure(fixed_sql):
                self.logger.warning("Fixed SQL still missing FROM clause, adding it manually")
                fixed_sql = self._add_from_clause_if_missing(fixed_sql, query)

            self.logger.info(f"SQL fixed with enhanced context: {fixed_sql[:100]}...")
            return fixed_sql

        except Exception as e:
            self.logger.error(f"Failed to fix SQL with context: {e}")
            # 如果修复失败，回退到基本修复方法
            return self.fix_sql_with_error(sql, error_context.get("error_message", ""), query, database_schema)

    def simplify_sql(self, sql: str, max_limit: int = 100) -> str:
        """
        简化SQL查询以避免超时

        策略:
        1. 添加LIMIT限制
        2. 移除复杂的子查询（如果有）
        3. 保留核心字段

        Args:
            sql: 原始SQL
            max_limit: 最大记录数（默认100）

        Returns:
            简化后的SQL
        """
        try:
            import re
            self.logger.info(f"Simplifying SQL, adding LIMIT {max_limit}")

            # 先移除末尾的分号
            sql = sql.rstrip().rstrip(';')

            # 检查是否已经有LIMIT（不区分大小写）
            if re.search(r'\bLIMIT\s+\d+', sql, flags=re.IGNORECASE):
                # 替换现有的LIMIT
                sql = re.sub(r'\bLIMIT\s+\d+', f'LIMIT {max_limit}', sql, flags=re.IGNORECASE)
                self.logger.debug("Replaced existing LIMIT")
            else:
                # 添加LIMIT
                sql = f"{sql}\nLIMIT {max_limit}"
                self.logger.debug("Added LIMIT clause")

            return sql

        except Exception as e:
            self.logger.error(f"Failed to simplify SQL: {e}")
            # 简化失败，直接在末尾添加LIMIT
            return f"{sql.rstrip().rstrip(';')}\nLIMIT {max_limit}"


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== SQLGenerator 测试 ===\n")

    # 测试分析缺失信息
    print("--- 测试1: 分析缺失信息 ---")
    generator = SQLGenerator(None, "测试提示词")

    test_data = [
        {
            "name": "西湖",
            "level": "5A",
            "coordinates": [120.15, 30.28]
            # 缺少: address, 评分, 门票, 介绍, 图片链接
        }
    ]

    analysis = generator.analyze_missing_info("查询西湖", test_data)
    print(f"Has missing: {analysis['has_missing']}")
    print(f"Missing fields: {analysis['missing_fields']}")
    print(f"Data complete: {analysis['data_complete']}")
    print(f"Suggestion: {analysis['suggestion']}")
