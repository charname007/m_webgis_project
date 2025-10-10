# 建议命令列表

## 开发环境设置

### 后端开发
```bash
# 进入后端目录
cd python/sight_server

# 安装Python依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --reload

# 运行测试
pytest

# 代码格式化
black .

# 代码检查
flake8 .
```

### 前端开发
```bash
# 进入前端目录
cd m_WGP_vue3

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 系统工具命令 (Windows)

### 文件和目录操作
```cmd
# 列出文件
ls 或 dir

# 切换目录
cd <目录路径>

# 创建目录
mkdir <目录名>

# 删除文件
del <文件名>

# 删除目录
rmdir /s <目录名>
```

### Git操作
```cmd
# 查看状态
git status

# 添加文件
git add .

# 提交更改
git commit -m "提交信息"

# 推送更改
git push

# 拉取更新
git pull
```

### 搜索和查找
```cmd
# 在文件中搜索内容
grep -r "搜索内容" .

# 查找文件
find . -name "*.py"
```

## 项目特定命令

### 缓存管理
```bash
# 清理缓存
python cleanup_bad_cache.py

# 测试缓存功能
python test_cache_functionality.py
```

### 数据库操作
```bash
# 创建缓存表
psql -f create_separate_cache_tables.sql
```

### 测试和验证
```bash
# 运行特定测试
python test_intent_analysis.py
python test_enhanced_error_handling.py
python test_cache_fix_final.py
```

## 开发工作流

1. **启动后端**: `cd python/sight_server && uvicorn main:app --reload`
2. **启动前端**: `cd m_WGP_vue3 && npm run dev`
3. **测试功能**: 运行相关测试文件
4. **代码检查**: 使用black和flake8
5. **提交更改**: 使用git工作流