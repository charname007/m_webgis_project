-- 分离缓存存储方案 - 创建新表结构
-- 将模式缓存和查询结果缓存完全分离存储

-- 1. 创建查询结果缓存表
CREATE TABLE IF NOT EXISTS query_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    result_data JSONB NOT NULL,
    response_time FLOAT,
    hit_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 为查询结果缓存表创建索引
CREATE INDEX IF NOT EXISTS idx_query_cache_key ON query_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_query_cache_expires ON query_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_query_cache_created ON query_cache(created_at);

-- 2. 创建模式学习缓存表
CREATE TABLE IF NOT EXISTS pattern_cache (
    id SERIAL PRIMARY KEY,
    pattern_key VARCHAR(255) UNIQUE NOT NULL,
    query_template TEXT NOT NULL,
    sql_template TEXT NOT NULL,
    success_count INTEGER DEFAULT 1,
    total_response_time FLOAT DEFAULT 0,
    avg_response_time FLOAT,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 为模式学习缓存表创建索引
CREATE INDEX IF NOT EXISTS idx_pattern_cache_key ON pattern_cache(pattern_key);
CREATE INDEX IF NOT EXISTS idx_pattern_cache_template ON pattern_cache(query_template);
CREATE INDEX IF NOT EXISTS idx_pattern_cache_last_used ON pattern_cache(last_used);

-- 3. 数据迁移：将现有数据从 cache_data 表迁移到新表

-- 迁移查询结果缓存数据
INSERT INTO query_cache (cache_key, query_text, result_data, response_time, hit_count, expires_at, created_at, updated_at)
SELECT 
    cache_key,
    COALESCE((cache_value::json->>'query'), '') as query_text,
    COALESCE((cache_value::json->>'result'), '{}')::jsonb as result_data,
    NULL as response_time, -- 响应时间需要从其他地方获取
    1 as hit_count, -- 默认命中次数
    expires_at,
    created_at,
    updated_at
FROM cache_data 
WHERE cache_key NOT LIKE 'success_pattern:%'
AND cache_type = 'query_result';

-- 迁移模式学习缓存数据
INSERT INTO pattern_cache (pattern_key, query_template, sql_template, success_count, total_response_time, avg_response_time, last_used, created_at, updated_at)
SELECT 
    cache_key as pattern_key,
    COALESCE((cache_value::json->>'query_template'), '') as query_template,
    COALESCE((cache_value::json->>'sql_template'), '') as sql_template,
    COALESCE((cache_value::json->>'result_count')::integer, 1) as success_count,
    COALESCE((cache_value::json->>'response_time')::float, 0) as total_response_time,
    COALESCE((cache_value::json->>'response_time')::float, 0) as avg_response_time,
    created_at as last_used,
    created_at,
    updated_at
FROM cache_data 
WHERE cache_key LIKE 'success_pattern:%'
OR cache_type = 'success_pattern';

-- 4. 验证迁移结果
SELECT '查询结果缓存迁移数量: ' || COUNT(*) FROM query_cache;
SELECT '模式学习缓存迁移数量: ' || COUNT(*) FROM pattern_cache;

-- 5. 可选：删除旧的 cache_data 表（谨慎操作）
-- DROP TABLE IF EXISTS cache_data;

-- 6. 创建更新触发器（可选）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_query_cache_updated_at BEFORE UPDATE ON query_cache FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pattern_cache_updated_at BEFORE UPDATE ON pattern_cache FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
