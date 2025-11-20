# 景区地图小程序 (uni-app版本)

基于 uni-app 开发的景区地图小程序，支持地图浏览、景点搜索、AI智能查询等功能。

## 项目结构

```
weixixc/
├── pages/              # 页面目录
│   └── map/
│       └── index.vue   # 地图页面
├── utils/              # 工具类
│   ├── config.js       # API配置
│   └── request.js      # 网络请求封装
├── static/             # 静态资源
│   └── tabbar/         # 底部标签栏图标
├── App.vue             # 应用入口
├── main.js             # 入口文件
├── uni.scss            # 全局样式变量
├── pages.json          # 页面路由配置
├── manifest.json       # 应用配置
└── package.json        # 项目依赖
```

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 开发运行

#### 微信小程序
```bash
npm run dev:mp-weixin
```

然后使用微信开发者工具打开 `dist/dev/mp-weixin` 目录。

### 3. 生产构建

```bash
npm run build:mp-weixin
```

## 配置说明

### 修改 API 地址

编辑 `utils/config.js`：

```javascript
const API_BASE_URL = 'https://your-domain.com:8082'
const SIGHT_SERVER_URL = 'https://your-domain.com:8001'
```

### 修改小程序 AppID

编辑 `manifest.json`：

```json
{
  "mp-weixin": {
    "appid": "your-weixin-appid"
  }
}
```

### 添加 tabbar 图标

请参考 `static/tabbar/README.md` 文件说明。

## 功能特性

### 已实现功能 ✅
- [x] 基础地图显示
- [x] 地图拖拽、缩放
- [x] 缩放控件
- [x] 定位到当前位置
- [x] 地图信息显示

### 待实现功能 🚧
- [ ] 景点标记显示
- [ ] 标记点聚类
- [ ] 景点搜索
- [ ] 景点详情
- [ ] AI智能查询
- [ ] 景点增删改

## 开发工具

- **HBuilderX** - 官方推荐IDE
- **微信开发者工具** - 用于调试微信小程序
- **VS Code** - 也可以使用（需安装uni-app插件）

## 注意事项

### 微信小程序域名配置

在微信小程序后台配置以下合法域名：
- request合法域名：添加后端API服务器域名
- socket合法域名：如需WebSocket功能
- uploadFile合法域名：如需上传图片
- downloadFile合法域名：如需下载文件

### 地图组件说明

小程序的 `<map>` 组件层级最高，如需在地图上方显示内容，必须使用：
- `<cover-view>` - 覆盖层容器
- `<cover-image>` - 覆盖层图片

## 相关文档

- [uni-app 官方文档](https://uniapp.dcloud.net.cn/)
- [微信小程序 map 组件](https://developers.weixin.qq.com/miniprogram/dev/component/map.html)
- [Vue 3 文档](https://cn.vuejs.org/)

## 问题反馈

如遇到问题，请检查：
1. 是否正确安装依赖
2. API地址是否正确配置
3. 小程序AppID是否配置
4. 是否授予了位置权限

## License

MIT
