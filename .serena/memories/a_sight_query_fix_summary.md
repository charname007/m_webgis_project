# a_sight 表查询 SQL 逻辑问题修复总结

## 问题分析
在 a_sight 表查询中存在 SQL 逻辑问题，导致无坐标的景区无法正确显示：

### 根本原因
- 在 `ASightMapper.xml` 的 `getSightGeojsonByExtentAndLevel` 方法中使用了 `ST_Intersects` 条件
- `ST_Intersects` 函数要求几何对象不为空才能计算相交关系
- 因此无坐标的景区（geom 为 null）被过滤掉了

### 具体表现
- "厦门大学芙蓉湖" 在 a_sight 表中没有坐标（geom 为空）
- 所以它被 ST_Intersects 条件过滤掉了
- 后端查询返回了 1 条记录，但前端没有收到数据

## 解决方案
修改 `ASightMapper.xml` 中的查询逻辑，使其能够返回无坐标的景区：

### 修改内容
将原有的 `ST_Intersects` 条件替换为：
```sql
WHERE (
    -- 有坐标的景区：检查是否在范围内
    (geom IS NOT NULL AND ST_Intersects(
        ST_Transform(geom, 4326),
        ST_MakeEnvelope(#{minLon}, #{minLat}, #{maxLon}, #{maxLat}, 4326)
    ))
    OR
    -- 无坐标的景区：直接返回
    geom IS NULL
)
```

## 修改的文件
- `be/src/main/resources/mapper/ASightMapper.xml`

## 预期效果
- 有坐标的景区：根据空间范围过滤
- 无坐标的景区：直接返回，不受空间范围限制
- 所有景区数据都能正确显示在前端地图上

## 重要说明
这种修改确保了系统能够正确处理既有坐标数据又有无坐标数据的混合情况，提高了系统的健壮性和用户体验。