# 驾车路线规划功能使用说明

## 功能概述

本功能提供了基于高德地图API的驾车路线规划服务，支持：
- 多路径路线规划
- WGS84与GCJ02坐标系自动转换
- GeoJSON格式返回路线数据
- 多种驾车策略选择
- 途经点、避让区域等高级功能

## API接口

### 1. POST方式路线规划

**接口地址**: `POST /route/driving`

**请求示例**:
```json
{
  "origin": "116.397428,39.90923",
  "destination": "116.397428,39.90923", 
  "strategy": 32,
  "waypoints": "116.397428,39.90923;116.397428,39.90923",
  "avoidroad": "长安街",
  "plate": "京A12345",
  "cartype": 0,
  "ferry": 0
}
```

**参数说明**:
- `origin`: 起点坐标 (WGS84坐标系，格式："经度,纬度")
- `destination`: 终点坐标 (WGS84坐标系，格式："经度,纬度")
- `strategy`: 驾车策略 (默认32：高德推荐)
- `waypoints`: 途经点 (多个坐标用分号分隔)
- `avoidroad`: 避让道路
- `plate`: 车牌号码 (用于限行判断)
- `cartype`: 车辆类型 (0:燃油车, 1:纯电动, 2:插电混动)
- `ferry`: 是否使用轮渡 (0:使用, 1:不使用)

### 2. GET方式路线规划

**接口地址**: `GET /route/driving?origin=经度,纬度&destination=经度,纬度&strategy=32`

**请求示例**:
```
GET /route/driving?origin=116.397428,39.90923&destination=116.397428,39.90923&strategy=32
```

## 响应格式

### 成功响应示例
```json
{
  "count": 3,
  "paths": [
    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "type": "LineString",
            "coordinates": [[116.397428, 39.90923], [116.397428, 39.90923]]
          },
          "properties": {
            "instruction": "沿长安街行驶",
            "roadName": "长安街",
            "stepDistance": 1500.0,
            "duration": 120.0,
            "tmcStatus": "畅通",
            "stepIndex": 0
          }
        }
      ],
      "properties": {
        "pathIndex": 0,
        "totalDistance": 5000.0,
        "totalDuration": 600.0,
        "totalTolls": 10.0,
        "taxiFee": 25.0,
        "trafficLights": 5,
        "restriction": false
      }
    }
  ],
  "status": 1,
  "info": "ok",
  "infocode": "10000"
}
```

### 错误响应示例
```json
{
  "status": 0,
  "info": "参数验证失败",
  "infocode": "40000",
  "count": 0,
  "paths": []
}
```

## 驾车策略说明

| 策略值 | 说明 |
|--------|------|
| 32 | 默认，高德推荐，同高德地图APP默认 |
| 33 | 躲避拥堵 |
| 34 | 高速优先 |
| 35 | 不走高速 |
| 36 | 少收费 |
| 37 | 大路优先 |
| 38 | 速度最快 |
| 39 | 躲避拥堵＋高速优先 |
| 40 | 躲避拥堵＋不走高速 |
| 41 | 躲避拥堵＋少收费 |
| 42 | 少收费＋不走高速 |
| 43 | 躲避拥堵＋少收费＋不走高速 |
| 44 | 躲避拥堵＋大路优先 |
| 45 | 躲避拥堵＋速度最快 |

## 配置说明

### 1. 高德地图API密钥配置

在 `application.properties` 中配置您的高德地图API密钥：
```properties
amap.api.key=your_amap_api_key_here
amap.api.base-url=https://restapi.amap.com
```

### 2. 获取高德地图API密钥

1. 访问 [高德开放平台](https://lbs.amap.com/)
2. 注册开发者账号
3. 创建应用并获取API密钥
4. 将密钥配置到 `application.properties` 文件中

## 坐标系说明

- **输入坐标**: WGS84坐标系 (GPS标准坐标系)
- **内部处理**: 自动转换为GCJ02坐标系 (高德地图坐标系)
- **输出坐标**: WGS84坐标系

## 技术特性

1. **多路径支持**: 返回多条路线规划方案
2. **GeoJSON格式**: 使用标准GeoJSON格式返回路线数据
3. **坐标自动转换**: 自动处理WGS84与GCJ02坐标系转换
4. **详细分段信息**: 每条路线包含详细的分段信息和属性
5. **错误处理**: 完善的参数验证和异常处理机制
6. **日志记录**: 详细的请求和响应日志记录

## 使用示例

### Java代码示例
```java
@Autowired
private RouteService routeService;

// 创建路线规划请求
RouteRequest request = new RouteRequest();
request.setOrigin("116.397428,39.90923");
request.setDestination("116.397428,39.90923");
request.setStrategy(32);

// 调用路线规划服务
RouteResponse response = routeService.getDrivingRoute(request);

// 处理响应
if (response.getStatus() == 1) {
    List<RoutePath> paths = response.getPaths();
    for (RoutePath path : paths) {
        System.out.println("路径距离: " + path.getProperties().getTotalDistance());
        System.out.println("路径时间: " + path.getProperties().getTotalDuration());
    }
}
```

## 注意事项

1. **API密钥**: 请确保配置正确的高德地图API密钥
2. **坐标格式**: 输入坐标必须为WGS84坐标系，格式为"经度,纬度"
3. **精度限制**: 经纬度小数点后不得超过6位
4. **频率限制**: 注意高德地图API的调用频率限制
5. **错误处理**: 建议在生产环境中添加重试机制和降级策略