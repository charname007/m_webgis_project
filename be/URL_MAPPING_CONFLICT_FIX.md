# URL映射冲突修复文档

## 问题描述
后端启动失败，原因是 `SpatialTableController` 和 `DynamicTableController` 之间存在URL映射冲突。

## 冲突详情
两个控制器使用了相同的根路径：
- `SpatialTableController`: `@RequestMapping("/postgis/WGP_db")`
- `DynamicTableController`: `@RequestMapping("/postgis/WGP_db")`

冲突的具体URL包括：
- `POST /tables/SpatialTables/{tableName}/geojson/extent`
- `GET /tables/SpatialTables`
- `GET /tables/SpatialTables/{tableName}/geojson`
- `POST /tables/SpatialTables/geojson`
- `POST /tables/SpatialTables/geojson/fields`

## 修复方案
修改 `DynamicTableController` 的路径前缀为：
```java
@RequestMapping("/postgis/WGP_db/dynamic-tables")
```

## 修复结果
✅ 后端服务成功启动，无URL映射冲突错误
✅ 服务运行在端口8081
✅ 所有API端点正常可用

## 新的URL结构

### SpatialTableController (保持不变)
- `GET /postgis/WGP_db/tables/SpatialTables`
- `GET /postgis/WGP_db/tables/SpatialTables/{tableName}/geojson`
- `POST /postgis/WGP_db/tables/SpatialTables/{tableName}/geojson/extent`
- `POST /postgis/WGP_db/tables/SpatialTables/geojson/fields`

### DynamicTableController (已修改)
- `GET /postgis/WGP_db/dynamic-tables/tables`
- `GET /postgis/WGP_db/dynamic-tables/tables/{tableName}/data`
- `GET /postgis/WGP_db/dynamic-tables/tables/{tableName}/schema`
- `GET /postgis/WGP_db/dynamic-tables/tables/SpatialTables`
- `GET /postgis/WGP_db/dynamic-tables/tables/SpatialTables/{tableName}/geojson`
- `POST /postgis/WGP_db/dynamic-tables/tables/SpatialTables/{tableName}/geojson/extent`
- `POST /postgis/WGP_db/dynamic-tables/tables/SpatialTables/geojson/fields`

## 前端API配置更新
如果需要使用DynamicTableController的API，前端需要更新相应的API配置，将路径前缀从 `/postgis/WGP_db` 改为 `/postgis/WGP_db/dynamic-tables`。

## 验证
后端服务已成功启动，可以正常访问所有API端点。
