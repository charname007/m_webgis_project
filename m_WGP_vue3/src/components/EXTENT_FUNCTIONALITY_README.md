# GeoJSON图层Extent功能说明

## 功能概述

在 `loadGeoJsonLayer` 方法中添加了设置extent和跳转到extent的功能，包括自动调整视图、存储图层范围、手动跳转等功能。

## 新增功能

### 1. 修改的 `loadGeoJsonLayer` 方法

```javascript
loadGeoJsonLayer(geoJson, styleOptions = {}, layerName = "GeoJSON Layer", options = {})
```

**新增参数：**
- `options` - 配置选项对象，包含以下属性：
  - `autoFitExtent` (boolean, 默认true): 是否自动调整视图到图层范围
  - `fitPadding` (number, 默认50): 调整视图时的边距
  - `storeExtent` (boolean, 默认true): 是否存储图层范围到图层属性中

**使用示例：**
```javascript
// 自动调整视图到图层范围
const layer1 = mapUtils.loadGeoJsonLayer(geoJsonData, {}, '图层1', {
    autoFitExtent: true,
    fitPadding: 50,
    storeExtent: true
});

// 不自动调整视图，仅存储范围
const layer2 = mapUtils.loadGeoJsonLayer(geoJsonData, {}, '图层2', {
    autoFitExtent: false,
    storeExtent: true
});
```

### 2. 新增方法

#### `getLayerExtent(layer)`
获取图层的实时范围。

```javascript
const extent = mapUtils.getLayerExtent(layer);
console.log('图层范围:', extent); // [minX, minY, maxX, maxY]
```

#### `getStoredLayerExtent(layer)`
获取存储的图层范围（如果存在）。

```javascript
const storedExtent = mapUtils.getStoredLayerExtent(layer);
console.log('存储的范围:', storedExtent);
```

#### `zoomToLayerExtent(layer, padding = 50)`
手动跳转到图层范围。

```javascript
const success = mapUtils.zoomToLayerExtent(layer, 30);
if (success) {
    console.log('跳转成功');
} else {
    console.log('跳转失败');
}
```

#### `getLayerCenter(layer)`
获取图层中心点。

```javascript
const center = mapUtils.getLayerCenter(layer);
console.log('图层中心:', center); // [centerX, centerY]
```

#### `fitToLayerExtent(layer, padding = 50)`
调整视图到图层范围（已存在的方法，现在与extent功能集成）。

```javascript
mapUtils.fitToLayerExtent(layer, 50);
```

## 功能特点

### 1. 智能范围计算
- 自动计算GeoJSON图层的边界范围
- 支持点、线、面等多种几何类型
- 范围计算包含所有要素的集合范围

### 2. 范围存储机制
- 可选择是否将范围存储到图层属性中
- 存储的范围可以快速访问，无需重新计算
- 支持实时计算和存储范围的双重机制

### 3. 灵活的视图调整
- 支持自动调整和手动调整两种模式
- 可自定义边距大小
- 包含平滑的动画效果

### 4. 错误处理
- 对空图层和无效范围进行检测
- 提供详细的错误信息和警告
- 防止因无效范围导致的视图异常

## 使用场景

### 场景1：加载数据时自动定位
```javascript
// 加载GeoJSON数据时自动调整到合适视图
const layer = mapUtils.loadGeoJsonLayer(geoJsonData, {}, '数据图层', {
    autoFitExtent: true,
    fitPadding: 50
});
```

### 场景2：手动控制视图跳转
```javascript
// 先加载数据但不调整视图
const layer = mapUtils.loadGeoJsonLayer(geoJsonData, {}, '数据图层', {
    autoFitExtent: false,
    storeExtent: true
});

// 在需要时手动跳转
mapUtils.zoomToLayerExtent(layer, 30);
```

### 场景3：获取范围信息用于分析
```javascript
const extent = mapUtils.getLayerExtent(layer);
const center = mapUtils.getLayerCenter(layer);

console.log('数据范围:', extent);
console.log('数据中心:', center);
```

## 测试方法

已创建测试文件 `test-extent-functionality.html`，可以通过以下方式测试：

1. 在浏览器中打开测试文件
2. 点击不同按钮测试各种功能
3. 观察控制台输出和地图行为

## 注意事项

1. **数据加载时机**: 范围计算依赖于数据加载完成，对于URL加载的GeoJSON，需要等待数据加载完成
2. **投影系统**: 范围计算基于地图的当前投影系统（EPSG:4326）
3. **性能考虑**: 对于大数据量的图层，实时计算范围可能会有性能影响，建议使用存储范围
4. **边界情况**: 对空图层和无效几何进行了处理，返回null值

## 向后兼容性

新功能完全向后兼容，原有的 `loadGeoJsonLayer` 调用方式不受影响：

```javascript
// 原有调用方式仍然有效
const layer = mapUtils.loadGeoJsonLayer(geoJsonData, {}, '图层名称');
```

## 更新日志

- **v1.0**: 添加extent相关功能
  - 修改 `loadGeoJsonLayer` 方法，添加options参数
  - 新增 `getLayerExtent`、`getStoredLayerExtent`、`zoomToLayerExtent` 方法
  - 完善错误处理和边界情况处理
  - 创建测试文件和说明文档
