# Upsert 功能实现总结

## 改进内容

### 1. ASight 表支持
- **添加 insert 方法**：在 `ASightMapper` 接口中添加 `insert` 方法
- **XML 映射**：在 `ASightMapper.xml` 中添加插入语句，包含 geom 字段
- **服务层**：在 `ASightService` 和 `ASightServiceImpl` 中添加 `insert` 方法

### 2. TouristSpot 表支持
- **已有 insert 方法**：`TouristSpotMapper` 已有 `insert` 方法
- **upsert 逻辑**：在 `updateTouristSpotByNameWithSight` 中实现 upsert

### 3. Upsert 逻辑实现
- **检查存在性**：先查询记录是否存在
- **更新或插入**：存在则更新，不存在则插入
- **双表同步**：同时处理 tourist_spot 和 a_sight 两个表

## 核心逻辑

```java
// tourist_spot 表 upsert
List<TouristSpot> existingSpots = touristSpotMapper.findByName(touristSpot.getName());
if (existingSpots != null && !existingSpots.isEmpty()) {
    spotResult = touristSpotMapper.updateByName(touristSpot); // 更新
} else {
    spotResult = touristSpotMapper.insert(touristSpot); // 插入
}

// a_sight 表 upsert
boolean sightResult = aSightService.updateByName(aSight); // 先尝试更新
if (!sightResult) {
    sightResult = aSightService.insert(aSight); // 更新失败则插入
}
```

## 效果

现在 `@PutMapping("/by-name/{name}/with-sight")` 支持：
- **更新现有记录**：如果name存在
- **创建新记录**：如果name不存在
- **双表同步**：同时处理两个表的数据
- **错误恢复**：如果更新失败会自动尝试插入