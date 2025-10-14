# 更新接口行为分析

## @PutMapping("/by-name/{name}/with-sight") 更新机制

### 当前行为
1. **只更新不创建**：如果对应的name在表中不存在，更新操作会失败
2. **双表更新**：同时更新 tourist_spot 和 a_sight 两个表
3. **全字段更新**：更新所有传入的字段，不是部分更新

### 具体逻辑
- **tourist_spot 表**：使用 `touristSpotMapper.updateByName()` 通过名称更新
- **a_sight 表**：使用 `aSightService.updateByName()` 通过名称更新
- **返回值**：如果任一表更新失败，整个操作返回 null

### 问题分析
- **没有插入逻辑**：代码中只有 `update` 方法，没有 `insert` 或 `upsert` 逻辑
- **ASight 表缺少插入方法**：`ASightMapper` 只有 `updateByName`，没有 `insert` 方法
- **错误处理**：如果name不存在，更新操作返回0行，整个操作失败

### 建议改进
1. 添加 `upsert` 逻辑：如果name不存在则插入新记录
2. 为 ASight 表添加 `insert` 方法
3. 在更新前检查记录是否存在，不存在则插入
4. 或者使用数据库的 `ON CONFLICT` 语法实现 upsert