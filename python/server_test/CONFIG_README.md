# 配置文件使用指南

## 📁 文件说明

### 1. `config.py` - 配置管理模块
集中管理所有应用配置项，使用 pydantic-settings 进行验证。

### 2. `.env` - 环境变量文件（已配置实际值）
存储实际的配置值，包含敏感信息。**此文件不应提交到 Git**。

### 3. `.env.example` - 环境变量示例文件
提供配置模板，可以提交到 Git 供团队参考。

---

## 🚀 快速开始

### 步骤1: 配置环境变量

复制示例配置文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，设置实际的配置值：
```env
# 数据库连接（必需）
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# DeepSeek API密钥（必需）
DEEPSEEK_API_KEY=your_actual_api_key_here

# 其他配置（可选，使用默认值）
SERVER_PORT=8001
LOG_LEVEL=INFO
```

### 步骤2: 在代码中使用配置

```python
from config import settings

# 访问配置
print(settings.DATABASE_URL)
print(settings.SERVER_PORT)

# 使用配置字典
db_config = settings.get_database_config()
llm_config = settings.get_llm_config()
```

---

## 📋 配置项说明

### 数据库配置
| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL连接字符串 | `postgresql://sagasama:cznb6666@localhost:5432/WGP_db` |
| `DB_POOL_SIZE` | 连接池大小 | `5` |
| `DB_MAX_OVERFLOW` | 最大溢出连接数 | `10` |
| `DB_POOL_TIMEOUT` | 连接池超时（秒） | `30` |
| `DB_POOL_RECYCLE` | 连接回收时间（秒） | `3600` |
| `DB_CONNECT_TIMEOUT` | 连接超时（秒） | `10` |

### LLM配置
| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | 从环境变量获取 |
| `DEEPSEEK_API_BASE` | API基础URL | `https://api.deepseek.com` |
| `LLM_MODEL` | 模型名称 | `deepseek-chat` |
| `LLM_TEMPERATURE` | 温度参数（0.0-2.0） | `1.3` |

### 服务器配置
| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `SERVER_HOST` | 监听地址 | `0.0.0.0` |
| `SERVER_PORT` | 监听端口 | `8001` |

### 查询配置
| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MAX_QUERY_LENGTH` | 查询文本最大长度 | `500` |
| `DEFAULT_QUERY_LIMIT` | 默认查询结果限制 | `1000` |
| `MAX_QUERY_LIMIT` | 最大查询结果限制 | `10000` |

### 日志配置
| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `LOG_LEVEL` | 日志级别 | `INFO` |

### Agent配置
| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `AGENT_MAX_ITERATIONS` | 最大迭代次数 | `15` |
| `AGENT_MAX_EXECUTION_TIME` | 最大执行时间（秒） | `90` |

---

## 🔧 高级用法

### 打印当前配置（脱敏）
```python
from config import print_config_info

print_config_info()
```

输出示例：
```
============================================================
配置信息
============================================================

[数据库配置]
  DATABASE_URL: postgresql:sagasama:****@localhost:5432/WGP_db
  DB_POOL_SIZE: 5
  DB_MAX_OVERFLOW: 10

[LLM配置]
  DEEPSEEK_API_KEY: sk-12345...abcd
  DEEPSEEK_API_BASE: https://api.deepseek.com
  LLM_MODEL: deepseek-chat
  LLM_TEMPERATURE: 1.3

...
```

### 获取配置字典
```python
from config import settings

# 数据库配置
db_config = settings.get_database_config()
# {
#     "connection_string": "...",
#     "pool_size": 5,
#     "max_overflow": 10,
#     ...
# }

# LLM配置
llm_config = settings.get_llm_config()
# {
#     "api_key": "...",
#     "api_base": "...",
#     "model": "deepseek-chat",
#     "temperature": 1.3
# }

# Agent配置
agent_config = settings.get_agent_config()
# {
#     "max_iterations": 15,
#     "max_execution_time": 90
# }
```

---

## 🔒 安全建议

### 1. 保护敏感信息
- ✅ 将 `.env` 添加到 `.gitignore`
- ✅ 使用环境变量存储密钥
- ❌ 不要在代码中硬编码密钥
- ❌ 不要将 `.env` 提交到 Git

### 2. 使用不同环境配置

**开发环境** (`.env.development`):
```env
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/dev_db
LOG_LEVEL=DEBUG
```

**生产环境** (`.env.production`):
```env
DATABASE_URL=postgresql://prod_user:prod_pass@prod-host:5432/prod_db
LOG_LEVEL=WARNING
```

加载指定环境配置：
```python
# 在 config.py 中修改
model_config = SettingsConfigDict(
    env_file=".env.production",  # 指定环境文件
    ...
)
```

---

## 🧪 测试配置

运行测试脚本：
```bash
python config.py
```

这会输出所有配置信息（敏感信息已脱敏）。

---

## 📝 迁移说明

### 旧代码迁移步骤

**之前（硬编码）:**
```python
connection_string = "postgresql://user:pass@localhost:5432/db"
api_key = os.getenv("DEEPSEEK_API_KEY")
port = 8001
```

**现在（使用配置）:**
```python
from config import settings

connection_string = settings.DATABASE_URL
api_key = settings.DEEPSEEK_API_KEY
port = settings.SERVER_PORT
```

### 已迁移的文件
- ✅ `server.py` - FastAPI服务器
- ✅ `sql_connector.py` - 数据库连接器
- ✅ `base_llm.py` - LLM基础类

---

## ❓ 常见问题

### Q1: 为什么我的配置没有生效？
**A:** 确保 `.env` 文件在正确的位置（与 `config.py` 同目录）。

### Q2: 如何覆盖配置文件中的值？
**A:** 可以在初始化时传入参数：
```python
from base_llm import BaseLLM

# 使用配置文件中的值
llm = BaseLLM()

# 覆盖配置
llm = BaseLLM(temperature=0.5, model="gpt-4")
```

### Q3: 如何验证配置是否正确？
**A:** 运行测试脚本：
```bash
python config.py
```

### Q4: 配置验证失败怎么办？
**A:** 检查 pydantic 的错误消息，通常会指出哪个配置项不符合要求。

---

## 📚 相关文档

- [Pydantic Settings 文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI 配置管理](https://fastapi.tiangolo.com/advanced/settings/)
- [环境变量最佳实践](https://12factor.net/config)
