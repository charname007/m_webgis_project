# 文件名大小写冲突修复指南

## 错误信息
```
Error: Prevent writing to file that only differs in casing
E:\...\dist\dev\mp-weixin\App.json
E:\...\dist\dev\mp-weixin\app.json
```

## 原因
Windows文件系统不区分大小写，但uni-app构建时生成了两个仅大小写不同的文件。

## 解决方法

### 方法1: 清理构建目录 (推荐) ⭐

```bash
cd myapp

# 删除构建目录
rm -rf dist

# 清理缓存
rm -rf node_modules/.cache

# 重新构建
npm run dev:mp-weixin
```

### 方法2: 使用npm脚本

```bash
cd myapp

# 停止当前服务 (Ctrl+C)

# 清理并重新构建
npm run clean  # 如果有这个脚本
npm run dev:mp-weixin
```

### 方法3: 手动删除dist目录

1. 关闭微信开发者工具
2. 手动删除 `myapp/dist` 文件夹
3. 重新运行 `npm run dev:mp-weixin`
4. 重新用微信开发者工具打开项目

## 预防措施

### 1. 统一文件命名规范
确保项目中的文件名大小写一致：
- `App.vue` (推荐，首字母大写)
- `app.json` (配置文件，全小写)
- 页面组件: `pages/map/index.vue`

### 2. 检查pages.json
确认 `src/pages.json` 中路径大小写正确：
```json
{
  "pages": [
    {
      "path": "pages/map/index"  // 全小写
    }
  ]
}
```

### 3. 检查manifest.json
确认 `src/manifest.json` 配置正确。

## 验证步骤

构建完成后检查:
```bash
# 查看生成的文件
ls -la myapp/dist/dev/mp-weixin/ | grep -i app
```

应该只看到:
- `app.js`
- `app.json`
- `app.wxss`

(都是小写的 `app`)

## 如果问题持续

1. **检查是否有多个App.vue文件**
   ```bash
   find myapp/src -iname "app.vue"
   ```
   应该只有一个: `src/App.vue`

2. **检查git配置**
   ```bash
   git config core.ignorecase false
   ```

3. **重新安装依赖**
   ```bash
   cd myapp
   rm -rf node_modules package-lock.json
   npm install
   npm run dev:mp-weixin
   ```

4. **使用最新的uni-app CLI**
   ```bash
   npm install -g @dcloudio/uvm
   uvm
   # 选择最新版本
   ```

## 常见情况

### 情况1: Git仓库中有大小写冲突
```bash
# 查看git中的文件
git ls-files | grep -i app.vue
```

如果看到多个版本(App.vue 和 app.vue)，需要清理：
```bash
git rm --cached src/app.vue  # 删除小写版本
git commit -m "fix: remove lowercase app.vue"
```

### 情况2: 不同系统间切换
如果在Mac/Linux开发后切换到Windows:
1. 删除整个项目
2. 重新从git克隆
3. 重新安装依赖

## 我们的项目状态

✅ 源文件正确: `src/App.vue` (大写A)
✅ pages.json 配置正确
✅ 已清理 dist 目录

现在可以重新构建:
```bash
cd myapp
npm run dev:mp-weixin
```

应该不会再出现这个错误。
