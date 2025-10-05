# FULL OUTER JOIN 错误修复计划

## 问题描述
PostgreSQL在某些配置下不支持FULL OUTER JOIN的某些用法，错误信息：
"错误: 只有在合并连接或哈希连接的查询条件中才支持FULL JOIN"

## 根本原因
当前提示词系统强制要求使用 `FULL OUTER JOIN` 来联合查询 `a_sight` 和 `tourist_spot` 两个表，但PostgreSQL在某些优化器设置下对此有限制。

## 解决方案
采用多策略查询方案替代单一的FULL OUTER JOIN：

### 策略1: UNION ALL + 去重
```sql
-- 组合三个查询结果
SELECT json_agg(...) as result
FROM (
    -- 查询1：只在a_sight中的数据
    SELECT ... FROM a_sight a 
    LEFT JOIN tourist_spot t ON ... 
    WHERE t.id IS NULL
    
    UNION ALL
    
    -- 查询2：只在tourist_spot中的数据  
    SELECT ... FROM tourist_spot t
    LEFT JOIN a_sight a ON ...
    WHERE a.gid IS NULL
    
    UNION ALL
    
    -- 查询3：两表都有的数据
    SELECT ... FROM a_sight a
    INNER JOIN tourist_spot t ON ...
) combined_data
```

### 策略2: 条件查询策略
根据查询意图动态选择连接方式：
- 需要完整数据 → 使用UNION ALL策略
- 只需要有坐标的数据 → 使用LEFT JOIN
- 只需要详细信息 → 使用RIGHT JOIN

## 实施步骤
1. 修改提示词模板，移除强制使用FULL OUTER JOIN的要求
2. 实现多策略查询逻辑
3. 更新查询决策树
4. 测试验证修复效果
