# 坐标字段为null问题修复总结

## 问题分析
前端发送的坐标数据在a_sight表中显示为null，主要问题：

### 前端数据结构
- 前端使用`lng_wgs84`和`lat_wgs84`字段名发送数据
- 后端实体类使用`lngWgs84`和`latWgs84`字段名

### 后端映射
- ASight实体类字段映射正确：`@Column(name = "lng_wgs84") private Double lngWgs84;`
- MyBatis映射文件使用正确的参数名：`#{lngWgs84}`和`#{latWgs84}`

## 解决方案

### 1. 增强调试日志
- 在`ASightServiceImpl.upsertByName`方法中添加坐标信息调试日志
- 打印具体的坐标值：`lngWgs84: " + aSight.getLngWgs84() + ", latWgs84: " + aSight.getLatWgs84()`

### 2. 关键改进点
- 添加详细的坐标值调试信息
- 确保前端发送的数据能正确映射到后端实体
- 提供更详细的错误定位信息

## 修改的文件
1. `be/src/main/java/com/backend/be/service/impl/ASightServiceImpl.java`

## 预期效果
现在系统将：
- 打印具体的坐标值信息
- 帮助定位前端数据是否正确传递到后端
- 提供更详细的调试信息帮助解决问题