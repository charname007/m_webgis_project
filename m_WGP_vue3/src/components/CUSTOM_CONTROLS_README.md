# 自定义 OpenLayers Control 类使用指南

本文档介绍如何在项目中使用自定义的 OpenLayers Control 类，包括测量工具和定位工具。

## 控件概述

### 1. MeasureControl - 测量工具控件
- **功能**: 距离测量、面积测量
- **类型**: 按钮式控件
- **状态**: 激活/取消测量模式
- **特性**: 实时测量结果显示、测量提示框

### 2. LocationControl - 定位工具控件
- **功能**: 获取当前位置、自动居中并缩放到合适级别
- **类型**: 按钮式控件
- **状态**: 定位中、定位成功、定位失败
- **特性**: 定位标记显示、精度圆圈、动画效果

## 安装和导入

### 1. 导入控件类
```javascript
import { MeasureControl, LocationControl } from './m_controls.js';
```

### 2. 导入样式文件
在项目的入口文件（如 main.js）中导入 CSS：
```javascript
import './assets/custom-controls.css';
```

## 使用方法

### 基本使用示例

```javascript
import { MeasureControl, LocationControl } from './m_controls.js';

// 创建测量控件
const measureControl = new MeasureControl({
  className: 'ol-measure-control',
  title: '测量工具',
  activeClassName: 'active'
});

// 创建定位控件
const locationControl = new LocationControl({
  className: 'ol-location-control',
  title: '定位',
  targetZoom: 16,
  animationDuration: 800
});

// 将控件添加到地图
const map = new Map({
  target: 'map',
  controls: defaultControls().extend([
    measureControl,
    locationControl
  ]),
  // ... 其他配置
});
```

### 在 Vue 组件中使用

```vue
<template>
  <div id="map-container">
    <div id="map"></div>
  </div>
</template>

<script>
import { Map, View } from 'ol';
import { defaults as defaultControls } from 'ol/control';
import { MeasureControl, LocationControl } from './m_controls.js';
import './assets/custom-controls.css';

export default {
  name: 'MapWithCustomControls',
  mounted() {
    this.initMap();
  },
  methods: {
    initMap() {
      // 创建自定义控件
      const measureControl = new MeasureControl();
      const locationControl = new LocationControl();

      // 创建地图
      this.map = new Map({
        target: 'map',
        controls: defaultControls().extend([
          measureControl,
          locationControl
        ]),
        view: new View({
          center: [114.305, 30.5928],
          zoom: 12,
          projection: 'EPSG:4326'
        }),
        layers: [
          // 添加图层...
        ]
      });
    }
  }
}
</script>

<style scoped>
#map-container {
  width: 100%;
  height: 100vh;
}

#map {
  width: 100%;
  height: 100%;
}
</style>
```

## 配置选项

### MeasureControl 配置选项

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| className | string | 'ol-measure-control' | CSS 类名 |
| title | string | '测量工具' | 按钮标题 |
| activeClassName | string | 'active' | 激活状态类名 |
| eventsToSuspend | string[] | ['singleclick', 'moveend'] | 测量激活时暂时移除的地图事件类型 |
| cursorWhenActive | string | 'crosshair' | 测量激活时应用的鼠标指针样式 |
| measureModes | (string \| object)[] | ['LineString', 'Polygon', 'angle'] | 可通过长按切换的测量模式集合（支持字符串或 { type, label, icon }） |
| defaultMeasureMode | string | null | 初始化时选中的测量模式（匹配 measureModes 内的 type） |
| longPressDuration | number | 600 | 触发长按切换模式所需的持续时间（毫秒） |

> **提示**：单击按钮即可开始/结束测量，长按按钮会在 `measureModes` 配置的模式之间循环切换。测量激活时会暂时移除 `eventsToSuspend` 指定的地图事件监听（默认包含 `singleclick` 和 `moveend`），结束后自动恢复，避免与自定义行为冲突。

### LocationControl 配置选项

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| className | string | 'ol-location-control' | CSS 类名 |
| title | string | '定位' | 按钮标题 |
| targetZoom | number | 16 | 定位后的缩放级别 |
| animationDuration | number | 800 | 动画持续时间（毫秒） |

## API 方法

### MeasureControl 方法

```javascript
// 激活测量模式
measureControl.activate();

// 取消测量模式
measureControl.deactivate();

// 设置测量类型
measureControl.setMeasureType('LineString'); // 距离测量
measureControl.setMeasureType('Polygon');    // 面积测量
measureControl.setMeasureType('angle');      // 角度测量
measureControl.cycleMeasureMode();           // 顺序切换到下一个测量模式

// 清理测量工具
measureControl.cleanupMeasureTool();
```

### LocationControl 方法

```javascript
// 开始定位
await locationControl.startLocating();

// 停止定位
locationControl.stopLocating();

// 获取当前位置（返回 Promise）
const position = await locationControl.getCurrentPosition();

// 将地图居中到指定位置
await locationControl.centerToPosition(position);

// 显示位置标记
locationControl.showLocationMarker(position);

// 隐藏位置标记
locationControl.hideLocationMarker();
```

## 事件处理

### MeasureControl 事件

控件内部处理了所有交互事件，无需额外的事件监听。

### LocationControl 事件

可以通过 Promise 处理定位结果：

```javascript
try {
  await locationControl.startLocating();
  console.log('定位成功');
} catch (error) {
  console.error('定位失败:', error.message);
}
```

## 样式自定义

### 修改控件位置

在 CSS 中调整控件位置：

```css
.ol-measure-control {
  top: 20px;
  left: 20px;
}

.ol-location-control {
  top: 20px;
  left: 62px; /* 测量控件宽度 + 间距 */
}
```

### 自定义颜色主题

```css
.ol-measure-control-button.active {
  background-color: #your-color;
  border-color: #your-border-color;
}

.ol-location-control-button.success {
  background-color: #your-success-color;
}
```

## 浏览器兼容性

- 支持所有现代浏览器（Chrome, Firefox, Safari, Edge）
- 需要浏览器支持 Geolocation API（定位功能）
- 支持响应式设计
- 支持高对比度模式和减少动画模式

## 注意事项

1. **定位权限**: 定位功能需要用户授权地理位置权限
2. **HTTPS**: 在生产环境中，定位功能需要 HTTPS 协议
3. **性能**: 测量工具会创建额外的图层和交互，使用后及时清理
4. **移动端**: 控件已针对移动端进行优化，支持触摸操作

## 故障排除

### 定位失败常见原因

1. **权限被拒绝**: 用户拒绝了地理位置权限
2. **浏览器不支持**: 旧版本浏览器不支持 Geolocation API
3. **HTTPS 要求**: 非 HTTPS 环境下定位可能受限
4. **设备问题**: 设备 GPS 功能未开启或故障

### 测量工具问题

1. **图层重叠**: 确保测量图层 z-index 足够高
2. **交互冲突**: 避免同时激活多个绘制交互
3. **内存泄漏**: 使用后调用 cleanupMeasureTool() 清理资源

## 更新日志

### v1.0.0
- 初始版本发布
- 实现测量工具控件
- 实现定位工具控件
- 完整的样式和交互优化
