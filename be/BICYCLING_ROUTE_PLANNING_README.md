# 骑行路线规划功能实现文档

## 概述

本功能扩展了现有的路线规划系统，新增了骑行路线规划能力，使用高德地图v4/direction/bicycling API，支持500KM以内的骑行路线规划。

## 功能特性

- **支持距离**: 最大500KM的骑行路线规划
- **详细分段**: 提供详细的骑行动作、道路类型、步行类型等信息
- **坐标转换**: 自动处理WGS84到GCJ02坐标系的转换
- **RESTful API**: 提供POST和GET两种方式的API接口
- **完整验证**: 包含参数验证、异常处理和日志记录

## API 端点

### POST /route/bicycling

**请求体**:
```json
{
    "origin": "116.397428,39.90923",
    "destination": "116.397428,39.90923",
    "originId": "optional_origin_id",
    "destinationId": "optional_destination_id",
    "sig": "optional_signature",
    "output": "JSON",
    "callback": "optional_callback"
}
```

### GET /route/bicycling

**参数**:
- `origin`: 起点坐标，格式："经度,纬度"
- `destination`: 终点坐标，格式："经度,纬度"

## 响应数据结构

### BicyclingRouteResponse
```java
@Data
public class BicyclingRouteResponse {
    private Integer status;      // 状态值
    private String info;         // 状态说明
    private String infocode;     // 状态码
    private Integer count;       // 路径数量
    private List<BicyclingPath> route; // 路径列表
}
```

### BicyclingPath
```java
@Data
public class BicyclingPath {
    private Double distance;     // 骑行距离
    private Double duration;     // 骑行时间
    private List<BicyclingStep> steps; // 骑行分段列表
}
```

### BicyclingStep
```java
@Data
public class BicyclingStep {
    private String instruction;      // 路段骑行指示
    private String road;             // 道路名称
    private Double distance;         // 骑行距离
    private String orientation;      // 骑行方向
    private Double duration;         // 骑行耗时
    private String polyline;         // 坐标点
    private String action;           // 主要动作
    private String assistantAction;  // 辅助动作
    private Integer walkType;        // 步行类型
}
```

## 骑行动作映射

骑行API返回的动作类型包括：
- `start`: 开始骑行
- `end`: 结束骑行
- `turn`: 转弯
- `straight`: 直行
- `arrive`: 到达
- `via_waypoint`: 途经点
- `ferry`: 轮渡

## 道路类型分类

- `main_road`: 主干道
- `side_road`: 辅路
- `bicycle_road`: 自行车道
- `pedestrian_road`: 人行道
- `mixed_road`: 混合道路

## 步行类型

- `0`: 无需步行
- `1`: 需要步行

## 实现文件

1. **模型类**:
   - `BicyclingRouteResponse.java` - 骑行路线规划响应模型
   - `BicyclingPath.java` - 骑行路径模型
   - `BicyclingStep.java` - 骑行分段模型

2. **服务接口**:
   - `RouteService.java` - 扩展骑行路线规划方法

3. **服务实现**:
   - `RouteServiceImpl.java` - 实现骑行路线规划业务逻辑

4. **控制器**:
   - `RouteController.java` - 添加骑行路线规划端点

## 技术细节

### 坐标转换
骑行路线规划使用与驾车和步行相同的坐标转换机制，通过`CoordinateUtils`工具类实现WGS84到GCJ02的转换。

### API调用
使用高德地图v4/direction/bicycling端点，支持以下参数：
- `origin`: 起点坐标（GCJ02）
- `destination`: 终点坐标（GCJ02）
- `key`: 高德地图API密钥

### 错误处理
- 参数验证失败返回400状态码
- API调用失败返回500状态码
- 详细的错误信息和错误码

## 使用示例

### POST请求示例
```bash
curl -X POST "http://localhost:8080/route/bicycling" \
     -H "Content-Type: application/json" \
     -d '{
         "origin": "116.397428,39.90923",
         "destination": "116.397428,39.90923"
     }'
```

### GET请求示例
```bash
curl "http://localhost:8080/route/bicycling?origin=116.397428,39.90923&destination=116.397428,39.90923"
```

## 与其他路线规划功能的对比

| 功能 | API端点 | 距离限制 | 返回格式 | 特有特性 |
|------|---------|----------|----------|----------|
| 驾车 | v5/direction/driving | 无限制 | GeoJSON | 多条路径、策略选择 |
| 步行 | v3/direction/walking | 100KM | 结构化数据 | 步行指示 |
| 骑行 | v4/direction/bicycling | 500KM | 结构化数据 | 骑行动作、道路类型 |

## 注意事项

1. 骑行API支持最大500KM的路线规划
2. 骑行路线包含详细的骑行动作和道路类型信息
3. 需要配置高德地图API密钥才能正常使用
4. 骑行路线规划不包含实时交通信息
5. 建议在客户端显示骑行特有的指示信息

## 后续优化建议

1. 添加骑行路线缓存机制
2. 支持骑行偏好设置（避开陡坡、选择自行车道等）
3. 集成实时天气信息
4. 添加骑行时间预估优化
5. 支持骑行路线分享功能