# 数据库更新问题修复总结

## 问题描述
当更新"武汉大学Wuhan University"时出现以下问题：
1. tourist_spot表更新成功（影响行数=1）
2. a_sight表更新失败（影响行数=0）
3. 没有在a_sight表无记录时创建新记录

## 解决方案

### 1. 添加upsert功能
- **ASightService接口**：添加`upsertByName`方法
- **ASightServiceImpl实现**：实现upsert逻辑（先尝试更新，失败则插入）

### 2. 修改业务逻辑
- **TouristSpotServiceImpl**：将a_sight表的更新逻辑改为使用`upsertByName`
- 确保在记录不存在时自动创建新记录

### 3. 名称处理优化
- **TouristSpotController**：添加`extractChineseName`方法
- 从混合名称中提取中文部分（如"武汉大学Wuhan University" -> "武汉大学"）
- 确保新记录只使用中文名称

## 修改的文件
1. `be/src/main/java/com/backend/be/service/ASightService.java`
2. `be/src/main/java/com/backend/be/service/impl/ASightServiceImpl.java`
3. `be/src/main/java/com/backend/be/service/impl/TouristSpotServiceImpl.java`
4. `be/src/main/java/com/backend/be/controller/TouristSpotController.java`

## 预期效果
- 当a_sight表没有记录时，自动创建新记录
- 确保名称一致性，只使用中文部分
- 提高数据更新的可靠性