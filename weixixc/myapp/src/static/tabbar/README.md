# 静态资源说明

## tabbar 图标

在 `static/tabbar/` 目录下需要添加以下图标文件：

### 地图图标
- **map.png** - 地图图标（未选中状态）
  - 尺寸：81x81 像素（推荐）
  - 格式：PNG，支持透明
  - 颜色：灰色 (#7A7E83)

- **map-active.png** - 地图图标（选中状态）
  - 尺寸：81x81 像素（推荐）
  - 格式：PNG，支持透明
  - 颜色：蓝色 (#4a90e2)

## 图标设计建议

### 地图图标设计
可以使用以下元素：
- 📍 地图标记
- 🗺️ 地图轮廓
- 📌 定位针

### 在线图标资源
- [iconfont](https://www.iconfont.cn/) - 阿里巴巴矢量图标库
- [IconPark](https://iconpark.oceanengine.com/) - 字节跳动图标库
- [icons8](https://icons8.com/) - 免费图标库

## 如何添加图标

1. 下载或设计符合要求的图标
2. 将图标文件放置在对应目录：
   ```
   static/
   └── tabbar/
       ├── map.png
       └── map-active.png
   ```
3. 确保文件名与 `pages.json` 中的配置一致

## 临时方案

如果暂时没有图标，可以：
1. 在 `pages.json` 中暂时注释掉 `tabBar` 配置
2. 或使用文字代替图标（在 `pages.json` 中只保留 `text` 字段）
