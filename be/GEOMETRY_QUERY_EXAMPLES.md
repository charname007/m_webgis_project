# 几何空间查询功能使用示例

## 功能概述

现在系统支持根据几何对象（点或范围）进行空间查询：

- **如果geom是点**: 查询与该点相交的要素
- **如果geom是范围**: 查询与该范围相交的要素

## 查询参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| `geom` | String | 几何对象（WKT格式），可以是点或范围 |

## 使用示例

### 1. 查询与特定点相交的要素

```java
SpatialTableRequest request = new SpatialTableRequest();
request.setTable("spatial_table");
request.setGeom("POINT(116.3974 39.9093)"); // 北京天安门坐标

String geojson = dynamicTableService.getSpatialTablesGeojson(request);
```

### 2. 查询与特定范围相交的要素

```java
SpatialTableRequest request = new SpatialTableRequest();
request.setTable("spatial_table");
request.setGeom("POLYGON((116.3974 39.9093, 116.4074 39.9093, 116.4074 39.9193, 116.3974 39.9193, 116.3974 39.9093))"); // 矩形范围

String geojson = dynamicTableService.getSpatialTablesGeojson(request);
```

### 3. 查询与线相交的要素

```java
SpatialTableRequest request = new SpatialTableRequest();
request.setTable("spatial_table");
request.setGeom("LINESTRING(116.3974 39.9093, 116.4074 39.9193)"); // 线段

String geojson = dynamicTableService.getSpatialTablesGeojson(request);
```

### 4. 组合查询（空间查询 + 属性过滤）

```java
SpatialTableRequest request = new SpatialTableRequest();
request.setTable("spatial_data");
request.setName("公园"); // 名称包含"公园"
request.setCategories("绿地"); // 分类包含"绿地"
request.setGeom("POLYGON((116.3974 39.9093, 116.4074 39.9093, 116.4074 39.9193, 116.3974 39.9193, 116.3974 39.9093))"); // 特定范围内的要素

String geojson = dynamicTableService.getSpatialTablesGeojson(request);
```

## 支持的几何类型

### 点类型
- `POINT` - 单点
- `MULTIPOINT` - 多点

### 范围类型
- `POLYGON` - 单面
- `MULTIPOLYGON` - 多面
- `LINESTRING` - 单线
- `MULTILINESTRING` - 多线

### 其他类型
- `GEOMETRYCOLLECTION` - 几何集合
- 其他PostGIS支持的几何类型

## 注意事项

1. **坐标系**: 使用WGS84坐标系 (EPSG:4326)
2. **WKT格式**: 几何对象需要使用WKT (Well-Known Text) 格式
3. **空间关系**: 使用ST_Intersects函数判断空间相交关系
4. **查询逻辑**: 
   - 如果geom是点，查询所有包含该点的要素
   - 如果geom是范围，查询所有与该范围相交的要素

## API调用示例

### REST API调用

```bash
# 查询与特定点相交的要素
POST /api/spatial/tables/geojson
Content-Type: application/json

{
  "table": "spatial_table",
  "geom": "POINT(116.3974 39.9093)"
}

# 查询与特定范围相交的要素
POST /api/spatial/tables/geojson
Content-Type: application/json

{
  "table": "spatial_table",
  "geom": "POLYGON((116.3974 39.9093, 116.4074 39.9093, 116.4074 39.9193, 116.3974 39.9193, 116.3974 39.9093))"
}
```

这个功能实现了真正的空间查询，可以根据具体的几何对象进行精确的空间过滤。
