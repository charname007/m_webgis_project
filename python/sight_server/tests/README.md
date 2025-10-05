# 测试说明

本目录包含 Sight Server 的测试文件。

## 测试结构

```
tests/
├── __init__.py           # 测试模块初始化
├── conftest.py          # pytest 配置和 fixtures
├── test_geojson.py      # GeoJSON 工具类测试
└── test_api.py          # API 端点测试
```

## 运行测试

### 安装测试依赖

```bash
pip install pytest pytest-cov
```

### 运行所有测试

```bash
# 在项目根目录
pytest tests/ -v
```

### 运行特定测试文件

```bash
pytest tests/test_geojson.py -v
pytest tests/test_api.py -v
```

### 运行特定测试类或测试函数

```bash
# 运行特定测试类
pytest tests/test_geojson.py::TestCoordinateConverter -v

# 运行特定测试函数
pytest tests/test_geojson.py::TestCoordinateConverter::test_wgs84_to_gcj02 -v
```

### 生成覆盖率报告

```bash
pytest tests/ --cov=. --cov-report=html
```

## 测试说明

### test_geojson.py

测试 GeoJSON 工具类的功能：
- ✅ 坐标系转换（WGS84, GCJ02, BD09）
- ✅ GeoJSON Feature 创建
- ✅ GeoJSON FeatureCollection 创建
- ✅ 从查询结果生成 GeoJSON
- ✅ 自动检测坐标字段
- ✅ 无效数据处理

### test_api.py

测试 FastAPI 端点功能：

**注意**: 这些测试需要服务器运行，运行前请确保：
1. 启动 Sight Server: `python main.py`
2. 配置正确的 `TEST_DATABASE_URL`

测试内容：
- ✅ 健康检查端点
- ✅ 标准查询端点
- ✅ GeoJSON 查询端点
- ✅ 思维链查询端点
- ✅ 数据库信息端点
- ✅ 输入验证
- ✅ 性能测试

## 环境变量

测试使用的环境变量（在 `.env` 或 `conftest.py` 中配置）：

```env
TEST_DATABASE_URL=postgresql://user:password@localhost:5432/test_db
```

## CI/CD 集成

可以在 GitHub Actions 中使用：

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: pytest tests/ -v --cov=.
```

## 注意事项

1. **API 测试需要服务器运行**: `test_api.py` 中的测试需要 Sight Server 正在运行
2. **数据库依赖**: 某些测试可能需要数据库连接
3. **超时设置**: API 测试默认超时为 30 秒
4. **并发测试**: 性能测试会发送并发请求，确保服务器配置足够
