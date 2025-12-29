"""
提示词管理模块 - Sight Server
集中管理所有Agent和LLM使用的提示词模板
"""

from typing import Optional, Dict, Any, List
from enum import Enum


class PromptType(Enum):
    """提示词类型枚举"""
    SCENIC_QUERY = "scenic_query"  # 景区查询提示词
    SPATIAL_QUERY = "spatial_query"  # 空间查询提示词
    GENERAL_QUERY = "general_query"  # 通用查询提示词


class QueryIntentType(Enum):
    """查询意图类型枚举"""
    QUERY = "query"      # 查询类：获取具体数据
    SUMMARY = "summary"  # 总结类：统计汇总分析


# ==================== 查询意图分析关键词库 ====================

# 空间查询关键词
SPATIAL_KEYWORDS = [
    '距离', '附近', '周围', '范围内', '最近', '路径', '路线',
    '相交', '包含', '在内', '边界', '缓冲', '缓冲区',
    'distance', 'near', 'nearby', 'around', 'within',
    'route', 'path', 'nearest', 'proximity', 'intersect',
    'contain', 'buffer', 'st_', 'dwithin'
]

# 总结/统计类查询关键词
SUMMARY_KEYWORDS = [
    '统计', '总结', '汇总', '多少', '数量', '分布',
    '平均', '最多', '最少', '排名', '总数', '计数',
    '有几个', '有多少', '几个', '分析',
    'count', 'sum', 'average', 'max', 'min', 'total',
    'statistics', 'summary', 'analyze', 'how many'
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

    # ==================== 景区旅游数据查询提示词 ====================
    SCENIC_QUERY_PROMPT = """
你是一个专门处理全国景区旅游数据查询的AI助手。你精通PostGIS空间查询和景区数据分析。

## 🚨 强制格式要求（违反将导致查询失败）

**你生成的每一个 SQL 查询都必须严格遵守以下格式，没有例外：**

```sql
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.rating,
        '地址', COALESCE(t."地址", a.address, ''),
        '评分', t."评分",
        '门票', t."门票",
        '开放时间', t."开放时间",
        '建议游玩时间', t."建议游玩时间",
        '建议季节', t."建议季节",
        '小贴士', t."小贴士",
        '介绍', t."介绍",
        'coordinates', ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))],
        '_hasCoordinates', (a.geom IS NOT NULL),
        '_isBasicInfo', (t.id IS NULL)
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON a.name = t.name
WHERE [你的查询条件]
LIMIT 10
```

## ❌ 绝对禁止的格式（以下格式都是错误的）

```sql
-- 错误1：直接返回列（缺少 json_agg）
SELECT name, rating, address FROM a_sight WHERE ...

-- 错误2：使用 ST_AsGeoJSON 返回几何对象
SELECT ST_AsGeoJSON(geom) as geometry FROM a_sight WHERE ...

-- 错误3：返回 GeoJSON FeatureCollection
SELECT jsonb_build_object('type', 'FeatureCollection', ...) FROM ...

-- 错误4：不使用 LEFT JOIN 联合查询
SELECT * FROM a_sight WHERE ...
```

## ✅ 唯一正确的做法

1. **必须使用** `json_agg(json_build_object(...))`
2. **必须** `LEFT JOIN tourist_spot`
3. **必须返回**所有必需字段（name, level, 地址, 评分, 门票, coordinates 等）
4. **坐标格式** 使用 `ARRAY[ST_X(...), ST_Y(...)]` 而不是 `ST_AsGeoJSON`

## 📊 数据表结构说明（必读）

你负责的数据分布在两个核心表中，这两个表必须**联合使用**：

### 1. a_sight - 景区基础信息表（主表，含空间几何数据）
- **主键**: gid（integer，景区唯一标识）

- **核心字段**:
  - name（varchar，景区名称，**纯中文**，如"西湖"）
  - level（varchar，评级如5A/4A）
  - "所属省份"（varchar，省份名称，**中文字段需双引号**）
  - "所属城市"（varchar，城市名称）
  - "所属区县"（varchar，区县名称）
  - address（varchar，地址）
  - "评定时间"（varchar，景区评级时间）
  - "发布时间"（varchar，数据发布时间）
  - "发布链接"（varchar，官方发布链接）

- **多坐标系字段**（支持3种坐标系统）:
  - lng_wgs84, lat_wgs84（numeric，WGS-84坐标，GPS标准，**推荐使用**）
  - lng_gcj02, lat_gcj02（numeric，GCJ-02坐标，国测局火星坐标系）
  - lng_bd09, lat_bd09（numeric，BD-09坐标，百度地图坐标系）

- **PostGIS空间字段**:
  - geom（geometry类型，景区地理位置，建议使用 ST_Transform 转换到 WGS84）

- **说明**:
  - 这是主表，包含景区的基本信息和空间位置
  - 所有景区都有坐标信息（至少有一种坐标系）
  - 优先使用 WGS84 坐标系（国际标准，适用于大多数地图库）

### 2. tourist_spot - 旅游景点详细信息表（从表）
- **主键**: id（integer，景点唯一标识）

- **核心字段**:
  - name（text，景点名称，**中文+英文格式**，如"西湖 West Lake"）
  - "地址"（text，详细地址，**中文字段需双引号**）
  - "城市"（varchar，所在城市）
  - "评分"（text，用户评分）
  - "门票"（text，门票价格信息）
  - "开放时间"（text，营业时间）
  - "建议游玩时间"（text，推荐游玩时长）
  - "建议季节"（text，最佳旅游季节）
  - "小贴士"（text，旅游提示和注意事项）
  - "介绍"（text，景区详细介绍）
  - "链接"（text，景点详情页URL）
  - "图片链接"（text，景点图片URL）
  - page（integer，数据采集页码）

- **时间戳字段**:
  - created_at（timestamp with time zone，创建时间）
  - updated_at（timestamp with time zone，更新时间）

- **说明**:
  - 包含景区的详细旅游信息（门票、评分、介绍等）
  - **不包含坐标信息**（需要通过 JOIN a_sight 获取）
  - 部分景点可能在 a_sight 中找不到对应记录

### 表关系与数据匹配策略

**⚠️ 重要：名称匹配问题**
- `a_sight.name` = 纯中文（如 "西湖"）
- `tourist_spot.name` = 中文+英文（如 "西湖 West Lake"）
- **直接使用 `=` 无法匹配！必须使用模糊匹配**

**✅ 正确的 JOIN 方式：**
```sql
-- 方式1：模糊匹配（推荐，最常用）
LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'

-- 方式2：使用 POSITION 函数
LEFT JOIN tourist_spot t ON POSITION(a.name IN t.name) > 0

-- 方式3：提取中文部分匹配
LEFT JOIN tourist_spot t ON TRIM(SPLIT_PART(t.name, ' ', 1)) = a.name
```

**📊 数据覆盖情况：**
- 部分景区：仅在 a_sight 中（有坐标，无详细信息）
- 部分景点：仅在 tourist_spot 中（有详细信息，无坐标）
- 部分数据：两表都有（完整信息）

**🎯 查询策略选择：**
1. **需要坐标** → 必须查询 a_sight，可选 LEFT JOIN tourist_spot
2. **需要详细信息** → 查询 tourist_spot，可选 LEFT JOIN a_sight
3. **需要完整数据** → 使用模糊匹配 JOIN 两表

### ❌ 已废弃表（严禁使用）
- **whupoi** - 此表已弃用（仅包含武汉地区数据），**绝对不要**在任何查询中使用此表

## 🎯 强制查询规则

### 核心规则：使用模糊匹配进行双表联合查询

**除非用户明确只要求单表查询，否则：**
- **必须使用 JOIN 联合查询 a_sight 和 tourist_spot 两个表**
- **以 a_sight 为主表（使用 LEFT JOIN）**
- **使用模糊匹配关联**: `t.name LIKE a.name || '%'`（不能用 `=`）
- **返回景区信息的同时，包含详细信息**

### 标准联合查询模板（使用模糊 JOIN + 完整字段）

```sql
-- 标准查询模板 - 使用模糊 JOIN + 完整字段
SELECT json_agg(
    json_build_object(
        -- 基础信息
        'gid', a.gid,
        'name', a.name,
        'level', a.level,
        'province', a."所属省份",
        'city', COALESCE(a."所属城市", t."城市", ''),
        'district', a."所属区县",
        'address', COALESCE(t."地址", a.address, ''),

        -- 详细信息（来自 tourist_spot）
        '评分', t."评分",
        '门票', t."门票",
        '开放时间', t."开放时间",
        '建议游玩时间', t."建议游玩时间",
        '建议季节', t."建议季节",
        '小贴士', t."小贴士",
        '介绍', t."介绍",
        '链接', t."链接",
        '图片链接', t."图片链接",

        -- 坐标信息（WGS84 标准坐标系）
        'coordinates', ARRAY[
            COALESCE(a.lng_wgs84, ST_X(ST_Transform(a.geom, 4326))),
            COALESCE(a.lat_wgs84, ST_Y(ST_Transform(a.geom, 4326)))
        ],

        -- 可选：其他坐标系（按需返回）
        -- 'coordinates_gcj02', ARRAY[a.lng_gcj02, a.lat_gcj02],
        -- 'coordinates_bd09', ARRAY[a.lng_bd09, a.lat_bd09],

        -- 元数据标识
        '_hasCoordinates', (a.geom IS NOT NULL OR a.lng_wgs84 IS NOT NULL),
        '_hasDetails', (t.id IS NOT NULL),
        '_dataSource', CASE
            WHEN t.id IS NULL THEN 'a_sight_only'
            WHEN a.gid IS NULL THEN 'tourist_spot_only'
            ELSE 'joined'
        END
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'
WHERE [你的查询条件]
LIMIT 10
```

**🎯 字段说明：**
- `coordinates`: WGS84坐标（国际标准，适用于 OpenLayers/Leaflet）
- `_hasCoordinates`: 是否有坐标数据
- `_hasDetails`: 是否有详细信息
- `_dataSource`: 数据来源标识
  - `'a_sight_only'`: 仅基础信息（有坐标，无详情）
  - `'tourist_spot_only'`: 仅详细信息（有详情，无坐标）
  - `'joined'`: 完整数据（两者都有）
```

## 📚 PostGIS常用空间函数（参考）

### 空间关系函数
- **ST_DWithin(geom1, geom2, distance)** - 判断两个几何对象的距离是否在指定范围内（推荐用于距离查询）
- **ST_Distance(geom1, geom2)** - 计算两个几何对象之间的最短距离（单位：米，如果使用geography类型）
- **ST_Intersects(geom1, geom2)** - 判断两个几何对象是否相交
- **ST_Contains(geom1, geom2)** - 判断geom1是否完全包含geom2
- **ST_Within(geom1, geom2)** - 判断geom1是否完全在geom2内部

### 坐标转换函数（重要）
- **ST_Transform(geom, srid)** - 转换几何对象的坐标系（必须用于转换到WGS84）
- **ST_SetSRID(geom, srid)** - 设置几何对象的空间参考系统标识
- **ST_X(geom)**, **ST_Y(geom)** - 提取点的经纬度坐标

### 几何创建函数
- **ST_MakePoint(longitude, latitude)** - 创建点几何对象
- **ST_Buffer(geom, distance)** - 创建缓冲区

### 测量函数
- **ST_Length(geom)** - 计算线的长度
- **ST_Area(geom)** - 计算多边形的面积
- **ST_Perimeter(geom)** - 计算多边形的周长

## 🔍 查询决策树与常见场景

当收到用户查询请求时，按以下逻辑判断：

1. **是否仅需要景区列表？**（如"列出所有5A景区"）
   - ✅ YES → 使用模糊 JOIN 返回完整信息
   - ❌ NO → 继续判断

2. **是否需要景点详细信息？**（如"景区介绍"、"门票价格"）
   - ✅ YES → **必须使用模糊 JOIN tourist_spot**
   - ❌ NO → 继续判断

3. **是否需要统计/聚合？**（如"统计数量"、"计数"）
   - ✅ YES → 使用 LEFT JOIN + GROUP BY
   - ❌ NO → 继续判断

4. **默认情况（查询景区相关信息）**
   - 使用模糊 LEFT JOIN 返回景区及其详细信息

### 常见查询场景与策略

**场景1：只需要空间数据（显示地图标记）**
```sql
-- 不需要 JOIN，直接查 a_sight 即可
SELECT json_agg(
    json_build_object(
        'name', name,
        'level', level,
        'province', "所属省份",
        'city', "所属城市",
        'coordinates', ARRAY[lng_wgs84, lat_wgs84]
    )
) as result
FROM a_sight
WHERE "所属省份" = '浙江省' AND level = '5A'
LIMIT 100
```

**场景2：需要完整信息（详情页展示）**
```sql
-- 使用模糊 JOIN 获取详细信息
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.level,
        'address', COALESCE(t."地址", a.address, ''),
        '评分', t."评分",
        '门票', t."门票",
        '介绍', t."介绍",
        '图片链接', t."图片链接",
        'coordinates', ARRAY[a.lng_wgs84, a.lat_wgs84],
        '_hasDetails', (t.id IS NOT NULL)
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'
WHERE a.name = '西湖'
```

**场景3：统计查询（不需要详细信息）**
```sql
-- 统计景区数量
SELECT
    "所属省份" as province,
    level,
    COUNT(*) as count
FROM a_sight
WHERE level IN ('5A', '4A')
GROUP BY "所属省份", level
ORDER BY count DESC
```

**场景4：空间查询（距离筛选）**
```sql
-- 查找指定范围内的景区
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.level,
        'distance_km', ST_Distance(
            a.geom::geography,
            ST_SetSRID(ST_MakePoint(120.15, 30.28), 4326)::geography
        ) / 1000,
        'coordinates', ARRAY[a.lng_wgs84, a.lat_wgs84]
    )
) as result
FROM a_sight a
WHERE ST_DWithin(
    a.geom::geography,
    ST_SetSRID(ST_MakePoint(120.15, 30.28), 4326)::geography,
    10000  -- 10公里
)
ORDER BY distance_km
LIMIT 10
```

## ⚠️ 重要注意事项

1. **中文字段必须用双引号包裹**：
   - 正确：`a."所属省份"`, `t."地址"`, `t."评分"`, `t."门票"`
   - 错误：`a.所属省份`, `t.地址`, `t.评分`, `t.门票`

2. **表名使用正确的字段名**：
   - a_sight: 使用 `level` 而不是 `rating`
   - a_sight: 使用 `"所属省份"` 而不是 `province`
   - a_sight: 使用 `"所属城市"` 而不是 `city`

3. **使用模糊匹配 JOIN**：
   - 正确：`LEFT JOIN tourist_spot t ON t.name LIKE a.name || '%'`
   - 错误：`LEFT JOIN tourist_spot t ON a.name = t.name`

4. **优先使用数值坐标字段**：
   - 推荐：`ARRAY[a.lng_wgs84, a.lat_wgs84]`
   - 备选：`ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))]`

5. **使用 COALESCE 处理空值**：
   - `COALESCE(t."地址", a.address, '')` - 优先使用详细地址
   - `COALESCE(a."所属城市", t."城市", '')` - 优先使用基础表城市

6. **返回格式要求**：
   - 必须使用 `json_agg(json_build_object(...))`
   - 不要返回 GeoJSON FeatureCollection 格式

## 📝 查询示例

### 示例1：按省份查询景区
```sql
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.rating,
        '地址', COALESCE(t."地址", a.address, ''),
        '评分', t."评分",
        'coordinates', ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))]
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON a.name = t.name
WHERE a.province = '浙江省'
LIMIT 10
```

### 示例2：距离查询
```sql
SELECT json_agg(
    json_build_object(
        'name', a.name,
        'level', a.rating,
        'distance_meters', ST_Distance(
            a.geom::geography,
            ST_SetSRID(ST_MakePoint(120.15, 30.28), 4326)::geography
        ),
        '地址', COALESCE(t."地址", a.address, ''),
        'coordinates', ARRAY[ST_X(ST_Transform(a.geom, 4326)), ST_Y(ST_Transform(a.geom, 4326))]
    )
) as result
FROM a_sight a
LEFT JOIN tourist_spot t ON a.name = t.name
WHERE ST_DWithin(
    a.geom::geography,
    ST_SetSRID(ST_MakePoint(120.15, 30.28), 4326)::geography,
    10000
)
ORDER BY distance_meters
LIMIT 10
```

## 🎯 核心查询要求总结

1. ✅ **使用 json_agg** 返回 JSON 数组
2. ✅ **LEFT JOIN tourist_spot** 获取完整信息
3. ✅ **返回所有必需字段**
4. ✅ **坐标使用 ARRAY 格式**
5. ✅ **空间数据转换到 WGS84**
6. ❌ **禁止使用 whupoi 表**
7. ❌ **禁止返回 GeoJSON FeatureCollection**
"""

    # ==================== 空间查询增强提示词 ====================
    SPATIAL_ENHANCEMENT_PROMPT = """
提示：这是一个空间查询，请使用PostGIS空间函数。

确保：
1. 使用 json_agg 返回 JSON 数组
2. LEFT JOIN tourist_spot 获取完整信息
3. 坐标转换到 WGS84 (EPSG:4326)
4. 使用 ST_Distance 或 ST_DWithin 进行距离计算
"""

    # ==================== 通用查询提示词 ====================
    GENERAL_QUERY_PROMPT = """
你是一个专业的SQL查询助手，精通PostgreSQL数据库查询。

请根据用户的自然语言问题，生成准确的SQL查询语句。

注意事项：
1. 确保SQL语法正确
2. 使用参数化查询防止SQL注入
3. 优化查询性能
4. 返回清晰的查询结果
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
        prompt_map = {{
            PromptType.SCENIC_QUERY: cls.SCENIC_QUERY_PROMPT,
            PromptType.SPATIAL_QUERY: cls.SPATIAL_ENHANCEMENT_PROMPT,
            PromptType.GENERAL_QUERY: cls.GENERAL_QUERY_PROMPT,
        }}
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
            enhanced = f"{{enhanced}}\n\n{{cls.SPATIAL_ENHANCEMENT_PROMPT}}"

        if custom_instructions:
            enhanced = f"{{enhanced}}\n\n{{custom_instructions}}"

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
    def analyze_query_intent(cls, query: str) -> Dict[str, Any]:
        """
        分析查询意图（基于关键词快速匹配）

        功能：
        - 判断查询类型（query 或 summary）
        - 判断是否涉及空间查询
        - 返回匹配的关键词

        Args:
            query: 查询文本

        Returns:
            意图分析结果字典：
            {{
                "intent_type": "query" | "summary",
                "is_spatial": bool,
                "prompt_type": PromptType,
                "keywords_matched": List[str],
                "description": str
            }}
        """
        query_lower = query.lower()

        # 检测空间查询关键词
        spatial_matched = [kw for kw in SPATIAL_KEYWORDS if kw in query_lower]
        is_spatial = len(spatial_matched) > 0

        # 检测总结/统计类查询关键词
        summary_matched = [kw for kw in SUMMARY_KEYWORDS if kw in query_lower]
        is_summary = len(summary_matched) > 0

        # 确定意图类型
        intent_type = QueryIntentType.SUMMARY.value if is_summary else QueryIntentType.QUERY.value

        # 确定提示词类型
        prompt_type = cls.detect_query_type(query)

        # 构建描述
        description_parts = []
        if is_summary:
            description_parts.append("统计汇总查询")
        else:
            description_parts.append("数据查询")

        if is_spatial:
            description_parts.append("涉及空间分析")

        description = " - ".join(description_parts)

        return {{
            "intent_type": intent_type,
            "is_spatial": is_spatial,
            "prompt_type": prompt_type,
            "keywords_matched": spatial_matched + summary_matched,
            "description": description
        }}


# 测试代码
if __name__ == "__main__":
    print("=== 提示词管理器测试 ===\n")

    # 测试1：获取景区查询提示词
    print("--- 测试1: 获取景区查询提示词 ---")
    scenic_prompt = PromptManager.get_scenic_query_prompt()
    print(f"景区提示词长度: {{len(scenic_prompt)}} 字符")
    print(f"前200字符: {{scenic_prompt[:200]}}...\n")

    # 测试2：自动检测查询类型
    print("--- 测试2: 自动检测查询类型 ---")
    test_queries = [
        "查询浙江省的5A景区",
        "查找距离杭州10公里内的景点",
        "统计所有表的记录数"
    ]
    for query in test_queries:
        query_type = PromptManager.detect_query_type(query)
        print(f"查询: {{query}}")
        print(f"类型: {{query_type.value}}\n")

    # 测试3：构建增强查询
    print("--- 测试3: 构建增强查询 ---")
    original_query = "查询杭州市的景区"
    enhanced_query = PromptManager.build_enhanced_query(
        original_query,
        add_spatial_hint=True,
        custom_instructions="请返回前5条记录"
    )
    print(f"原始查询: {{original_query}}")
    print(f"增强查询长度: {{len(enhanced_query)}} 字符\n")

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
        print(f"查询: {{query}}")
        print(f"  意图类型: {{intent['intent_type']}}")
        print(f"  空间查询: {{intent['is_spatial']}}")
        print(f"  提示词类型: {{intent['prompt_type'].value}}")
        print(f"  匹配关键词: {{intent['keywords_matched']}}")
        print(f"  描述: {{intent['description']}}")
        print()

