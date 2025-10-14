# ID字段缺失问题修复总结

## 问题描述
- 景点数据在搜索结果中缺少ID字段，导致无法编辑
- 问题出现在从a_sight表查询得到的基本信息景点中

## 解决方案

### 1. 前端修改
- **TouristSpotSearch.vue**: 修改`handleEditSpot`方法，允许通过name字段进行修改
  - 为没有ID的景点添加虚拟ID：`name_${spot.name}`
  - 移除ID检查限制

- **TouristSpotEditModal.vue**: 修改更新逻辑
  - 根据是否有真实ID或虚拟ID选择不同的更新端点
  - 支持通过名称更新：`/api/tourist-spots/by-name/{name}/with-sight`

- **api.js**: 添加新的API端点
  - `updateByName: (name) => "/api/tourist-spots/by-name/${name}/with-sight"`

### 2. 后端修改
- **TouristSpotController.java**: 
  - 修改现有端点支持ID为0的情况（通过名称更新）
  - 添加新的端点：`updateTouristSpotByNameWithSight`

- **TouristSpotService.java**: 添加新方法
  - `updateTouristSpotByNameWithSight`

- **TouristSpotServiceImpl.java**: 实现通过名称更新的逻辑
  - 通过名称更新tourist_spot表
  - 通过名称更新a_sight表

- **TouristSpotMapper.java**: 添加通过名称更新的SQL
  - `updateByName`方法

## 匹配规则
- **a_sight表**: 全字匹配
- **tourist_spot表**: 中文部分匹配

## 效果
- 现在所有搜索结果中的景点都可以进行编辑
- 有详细信息的景点通过ID更新
- 只有基本信息的景点通过名称更新
- 双表同步更新确保数据一致性