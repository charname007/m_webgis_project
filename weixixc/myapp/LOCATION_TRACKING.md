# 用户位置实时跟踪功能

本文档说明微信小程序中用户位置实时跟踪功能的实现和使用方法。

## 功能概述

位置实时跟踪功能使用微信小程序的 `wx.onLocationChange` API 来持续监听用户位置变化,并在地图上实时显示用户当前位置。

## 核心组件

### 1. LocationService ([myapp/src/services/locationService.js](myapp/src/services/locationService.js))

位置服务核心模块,提供以下功能:

- **位置监听**: 使用 `uni.startLocationUpdate()` 和 `uni.onLocationChange()` 实现持续位置跟踪
- **权限管理**: 自动检查和请求位置权限
- **位置缓存**: 缓存最近的位置历史记录
- **错误处理**: 内置重试机制和错误处理
- **多监听器支持**: 支持多个组件同时监听位置变化

#### 主要 API

```javascript
import locationService from '@/services/locationService'

// 启动位置跟踪
await locationService.startWatching(callback, options)

// 停止位置跟踪
locationService.stopWatching()

// 获取最新位置
const location = locationService.getCurrentPosition()

// 获取位置历史
const history = locationService.getLocationHistory(10)
```

#### 配置选项

```javascript
const LOCATION_CONFIG = {
  updateInterval: 3000,    // 更新频率(毫秒)
  accuracy: 50,            // 精度要求(米)
  maxCacheSize: 100,       // 最大缓存条数
  maxRetries: 3,           // 最大重试次数
  retryDelay: 1000,        // 重试基础延迟(毫秒)
  timeout: 10000           // 请求超时时间(毫秒)
}
```

### 2. ErrorHandler ([myapp/src/utils/errorHandler.js](myapp/src/utils/errorHandler.js))

统一的错误处理工具,提供:

- 位置错误码映射
- 标准化错误对象
- 用户友好的错误提示

### 3. 地图页面集成 ([myapp/src/pages/map/index.vue](myapp/src/pages/map/index.vue))

在地图页面中集成了位置跟踪功能:

- **控制按钮**: 右侧控制面板中的"跟踪"按钮
- **位置标记**: 在地图上显示用户位置标记(📍图标)
- **自动更新**: 位置变化时自动更新标记位置
- **生命周期管理**: 页面卸载时自动停止跟踪

## 使用方法

### 在地图页面中使用

1. **启动位置跟踪**
   - 点击右侧控制面板中的"跟踪"按钮
   - 首次使用需要授权位置权限
   - 启动成功后按钮变为蓝色,显示"停止"

2. **查看位置**
   - 地图上会显示一个蓝色📍标记表示您的当前位置
   - 点击标记可以查看"我的位置"标注

3. **停止位置跟踪**
   - 再次点击"停止"按钮
   - 位置标记会从地图上移除

### 在其他页面中使用

```javascript
import locationService from '@/services/locationService'

export default {
  data() {
    return {
      userLocation: null,
      isTracking: false
    }
  },

  async onLoad() {
    // 启动位置跟踪
    try {
      await locationService.startWatching(this.onLocationUpdate)
      this.isTracking = true
    } catch (error) {
      console.error('启动位置跟踪失败:', error)
    }
  },

  onUnload() {
    // 停止位置跟踪
    if (this.isTracking) {
      locationService.stopWatching()
    }
  },

  methods: {
    onLocationUpdate(location) {
      this.userLocation = {
        lng: location.longitude,
        lat: location.latitude
      }
      console.log('位置更新:', this.userLocation)
    }
  }
}
```

## 权限要求

### app.json 配置

确保在 `app.json` 中配置了位置权限:

```json
{
  "permission": {
    "scope.userLocation": {
      "desc": "你的位置信息将用于显示附近的景点"
    }
  },
  "requiredPrivateInfos": [
    "getLocation",
    "onLocationChange",
    "startLocationUpdate",
    "stopLocationUpdate"
  ]
}
```

### 用户授权流程

1. 首次使用时会弹出授权提示
2. 如果用户拒绝,可以引导用户到设置页面手动开启
3. Android 平台需要在 manifest.json 中配置权限

## 注意事项

### 1. 性能优化

- 位置更新默认每3秒触发一次
- 使用位置缓存避免重复请求
- 页面卸载时自动停止跟踪以节省电量

### 2. 错误处理

- 内置重试机制(最多3次)
- 指数退避策略避免频繁请求
- 友好的错误提示

### 3. 电量消耗

- 持续的位置跟踪会增加电量消耗
- 建议在不需要时及时停止跟踪
- 可以根据实际需求调整 `updateInterval` 参数

### 4. 精度说明

- 默认精度要求为 50 米
- 实际精度取决于设备和环境
- 室内环境下精度可能较低

## 自定义配置

### 修改更新频率

```javascript
import locationService, { LOCATION_CONFIG } from '@/services/locationService'

// 修改全局配置
locationService.updateConfig({
  updateInterval: 5000,  // 改为5秒更新一次
  accuracy: 20           // 提高精度要求
})
```

### 自定义位置标记图标

1. 在 `myapp/static/icons/` 目录下放置 `user-location.png` 图标文件
2. 推荐尺寸: 36x36 像素(或更高分辨率的等比例图片)
3. 如果没有自定义图标,会使用默认的 📍 emoji 标记

### 添加位置历史轨迹

```javascript
// 获取最近10个位置点
const history = locationService.getLocationHistory(10)

// 在地图上绘制轨迹
this.polyline = [{
  points: history.map(loc => ({
    latitude: loc.latitude,
    longitude: loc.longitude
  })),
  color: '#4a90e2',
  width: 4
}]
```

## 调试技巧

### 1. 查看位置更新日志

打开微信开发者工具的控制台,可以看到:
- "开始接收位置更新"
- "位置更新: {latitude, longitude, ...}"
- 错误信息和重试日志

### 2. 模拟位置

在微信开发者工具中:
- 工具栏 → 位置 → 自定义位置
- 可以模拟不同的位置来测试功能

### 3. 测试权限拒绝场景

- 设置 → 权限管理 → 清除授权
- 重新进入页面测试授权流程

## 常见问题

### Q: 为什么位置不更新?

A: 可能的原因:
1. 未授权位置权限
2. 设备GPS信号弱
3. 微信小程序后台限制
4. 检查控制台是否有错误日志

### Q: 如何提高位置精度?

A:
1. 在配置中降低 `accuracy` 值
2. 确保设备GPS已开启
3. 在室外空旷环境测试

### Q: 位置跟踪耗电多吗?

A:
1. 持续跟踪会增加耗电
2. 建议在不需要时停止跟踪
3. 可以适当增加 `updateInterval` 减少更新频率

### Q: 能同时在多个页面使用吗?

A:
1. 可以,locationService 是单例
2. 使用 `addListener()` 和 `removeListener()` 管理监听器
3. 确保每个页面在 onUnload 时移除监听器

## 未来改进方向

- [ ] 添加地理围栏功能
- [ ] 支持离线位置缓存
- [ ] 添加位置轨迹回放
- [ ] 优化室内定位精度
- [ ] 添加位置分享功能

## 相关文档

- [微信小程序位置API文档](https://developers.weixin.qq.com/miniprogram/dev/api/location/wx.onLocationChange.html)
- [uni-app位置API](https://uniapp.dcloud.net.cn/api/location/location.html)
