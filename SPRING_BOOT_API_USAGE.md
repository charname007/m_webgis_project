# Spring Boot 后端 API 端点使用指南

本文档详细介绍了如何在前端项目中使用 Spring Boot 后端提供的各种 API 端点。

## 基础配置

### API 配置
所有 Spring Boot 后端 API 端点都配置在 `m_WGP_vue3/src/config/api.js` 文件中，通过 `API_CONFIG.endpoints.springBoot` 对象访问。

```javascript
import API_CONFIG from '@/config/api.js'

// 构建完整的 Spring Boot API URL
const fullURL = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.spatialTables.list)
// 结果: http://localhost:8082/postgis/WGP_db/tables/SpatialTables
```

### 环境变量
- `VITE_API_BASE_URL`: Spring Boot 后端服务地址，默认 `http://localhost:8082`
- `VITE_SIGHT_SERVER_URL`: Sight Server 服务地址，默认 `http://localhost:8001`

## API 端点分类

### 1. 空间表相关 (Spatial Tables)

#### 获取所有空间表
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.spatialTables.allTables)
// GET /postgis/WGP_db/tables
```

#### 获取空间表列表
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.spatialTables.list)
// GET /postgis/WGP_db/tables/SpatialTables
```

#### 获取指定表的 GeoJSON 数据
```javascript
const tableName = 'a_sight'
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.spatialTables.tableGeojson(tableName))
// GET /postgis/WGP_db/tables/SpatialTables/a_sight/geojson
```

#### 根据坐标范围查询表数据
```javascript
const tableName = 'a_sight'
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.spatialTables.tableGeojsonByExtent(tableName))
// POST /postgis/WGP_db/tables/SpatialTables/a_sight/geojson/extent

// 请求体示例
const requestBody = {
  minLng: 114.0,
  minLat: 30.0,
  maxLng: 115.0,
  maxLat: 31.0
}
```

#### 根据字段条件查询
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.spatialTables.tableGeojsonByFields)
// POST /postgis/WGP_db/tables/SpatialTables/geojson/fields

// 请求体示例
const requestBody = {
  tableName: 'a_sight',
  fields: [
    { fieldName: 'name', fieldValue: '武汉大学', operator: '=' }
  ]
}
```

#### 获取表数据
```javascript
const tableName = 'a_sight'
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.spatialTables.tableData(tableName))
// GET /postgis/WGP_db/tables/a_sight/data
```

#### 获取表结构
```javascript
const tableName = 'a_sight'
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.spatialTables.tableSchema(tableName))
// GET /postgis/WGP_db/tables/a_sight/schema
```

### 2. 地图元素相关 (Map Elements)

#### 获取所有地图元素
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.list)
// GET /postgis2/WGP_db/list
```

#### 分页查询地图元素
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.byPage)
// GET /postgis2/WGP_db?currentPage=1&pageSize=10
```

#### 条件查询地图元素
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.byCondition)
// GET /postgis2/WGP_db/condition?name=武汉大学
```

#### 圆形区域查询
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.byCircle)
// GET /postgis2/WGP_db/circle?longitude=114.0&latitude=30.0&radius=5.0
```

#### 多边形区域查询
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.byPolygon)
// GET /postgis2/WGP_db/polygon?geometry=POLYGON((114 30, 115 30, 115 31, 114 31, 114 30))
```

#### 添加地图元素
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.add)
// POST /postgis2/WGP_db

// 请求体示例
const mapElement = {
  name: '测试点',
  longitude: 114.0,
  latitude: 30.0,
  type: 'point'
}
```

#### 更新地图元素
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.update)
// PUT /postgis2/WGP_db
```

#### 删除地图元素
```javascript
const elementId = 123
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.delete(elementId))
// DELETE /postgis2/WGP_db/123
```

#### 获取地图元素 GeoJSON
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.geojson)
// GET /postgis/WGP_db/tables/map_elements/geojson
```

#### 根据坐标范围查询地图元素
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.geojsonByExtent)
// POST /postgis/WGP_db/tables/map_elements/geojson/extent
```

### 3. 动态表相关 (Dynamic Tables)

动态表相关的 API 与空间表类似，但使用不同的路径前缀：

```javascript
// 获取动态表列表
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.dynamicTables.list)
// GET /postgis/WGP_db/dynamic-tables/tables/SpatialTables

// 获取动态表 GeoJSON
const tableName = 'dynamic_table'
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.dynamicTables.tableGeojson(tableName))
// GET /postgis/WGP_db/dynamic-tables/tables/SpatialTables/dynamic_table/geojson
```

### 4. 景区相关 (Sights)

#### 根据坐标范围和级别查询景区
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.sights.geojsonByExtentAndLevel)
// POST /postgis/WGP_db/tables/a_sight/geojson/extent-level

// 请求体示例
const requestBody = {
  minLng: 114.0,
  minLat: 30.0,
  maxLng: 115.0,
  maxLat: 31.0,
  level: 3
}
```

### 5. 路线规划相关 (Routes)

#### 驾车路线规划
```javascript
// POST 方式
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.routes.driving.post)
// POST /route/driving

// GET 方式
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.routes.driving.get)
// GET /route/driving?origin=114.0,30.0&destination=115.0,31.0&strategy=32

// 请求体示例 (POST)
const requestBody = {
  origin: "114.0,30.0",
  destination: "115.0,31.0",
  strategy: 32,
  cartype: 0,
  ferry: 0
}
```

#### 步行路线规划
```javascript
// POST 方式
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.routes.walking.post)
// POST /route/walking

// GET 方式
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.routes.walking.get)
// GET /route/walking?origin=114.0,30.0&destination=115.0,31.0
```

#### 骑行路线规划
```javascript
// POST 方式
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.routes.bicycling.post)
// POST /route/bicycling

// GET 方式
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.routes.bicycling.get)
// GET /route/bicycling?origin=114.0,30.0&destination=115.0,31.0
```

### 6. 特征详情相关 (Feature Details)

#### 获取特征详情
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.featureDetails.get)
// GET /feature-details
```

### 7. 查询相关 (Queries)

#### 执行查询
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.queries.execute)
// POST /query
```

### 8. 用户相关 (Users)

#### 用户登录
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.users.login)
// POST /users/login

// 请求体示例
const loginData = {
  username: 'admin',
  password: 'password'
}
```

#### 用户注册
```javascript
const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.users.register)
// POST /users/register
```

## 使用示例

### 在 Vue 组件中使用

```javascript
import { ref } from 'vue'
import API_CONFIG from '@/config/api.js'

export default {
  setup() {
    const spatialTables = ref([])
    
    // 获取空间表列表
    const fetchSpatialTables = async () => {
      try {
        const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.spatialTables.list)
        const response = await fetch(url)
        const data = await response.json()
        spatialTables.value = data
      } catch (error) {
        console.error('获取空间表失败:', error)
      }
    }
    
    // 路线规划
    const planRoute = async (origin, destination) => {
      try {
        const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.routes.driving.post)
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            origin: origin,
            destination: destination,
            strategy: 32
          })
        })
        const routeData = await response.json()
        return routeData
      } catch (error) {
        console.error('路线规划失败:', error)
      }
    }
    
    return {
      spatialTables,
      fetchSpatialTables,
      planRoute
    }
  }
}
```

### 在服务层中使用

```javascript
// services/apiService.js
import API_CONFIG from '@/config/api.js'

export class ApiService {
  // 获取地图元素
  static async getMapElements() {
    const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.list)
    const response = await fetch(url)
    return await response.json()
  }
  
  // 添加地图元素
  static async addMapElement(element) {
    const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.mapElements.add)
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(element)
    })
    return await response.json()
  }
  
  // 路线规划
  static async getDrivingRoute(origin, destination) {
    const url = API_CONFIG.buildURL(API_CONFIG.endpoints.springBoot.routes.driving.post)
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        origin: origin,
        destination: destination,
        strategy: 32
      })
    })
    return await response.json()
  }
}
```

## 注意事项

1. **跨域问题**: 确保 Spring Boot 后端已配置 CORS，允许前端域名访问
2. **错误处理**: 所有 API 调用都应包含适当的错误处理
3. **响应格式**: 大多数 API 返回 JSON 格式数据，部分空间数据接口返回 GeoJSON
4. **参数验证**: 调用 API 时确保参数格式正确，特别是坐标格式
5. **环境配置**: 生产环境记得更新 `VITE_API_BASE_URL` 环境变量

## 故障排除

- **404 错误**: 检查 API 路径是否正确，确保后端服务正在运行
- **CORS 错误**: 检查后端 CORS 配置
- **参数错误**: 查看 API 文档确保参数格式正确
- **网络错误**: 检查网络连接和后端服务状态