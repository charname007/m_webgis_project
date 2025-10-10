# 代码风格和约定

## 后端代码风格 (Python)

### 命名约定
- **类名**: 使用PascalCase，如 `SQLQueryAgent`
- **函数/方法名**: 使用snake_case，如 `build_node_context`
- **变量名**: 使用snake_case，如 `query_cache_manager`
- **常量**: 使用UPPER_SNAKE_CASE，如 `MAX_RETRY_COUNT`

### 类型提示
- 强制使用类型提示
- 使用Python 3.10+的类型提示语法
- 示例:
```python
def process_query(query: str, session_id: Optional[str] = None) -> QueryResult:
    pass
```

### 文档字符串
- 使用Google风格的docstring
- 包含参数、返回值和异常说明
- 示例:
```python
class SQLQueryAgent:
    """
    SQL查询Agent (LangGraph + Memory + Checkpoint 实现)

    Args:
        llm: LLM实例
        db_connector: 数据库连接器
    
    Returns:
        QueryResult: 查询结果
    """
```

### 导入顺序
1. 标准库导入
2. 第三方库导入
3. 本地模块导入

### 错误处理
- 使用结构化异常处理
- 实现适当的错误恢复机制
- 使用自定义异常类

## 前端代码风格 (Vue3)

### 组件命名
- 使用PascalCase，如 `MapComponent`
- 文件名与组件名保持一致

### 组合式API
- 优先使用组合式API
- 使用TypeScript类型定义

### 响应式数据
- 使用`ref()`和`reactive()`
- 正确使用计算属性和侦听器

## 项目特定约定

### 注释规范
- 对于不需要的代码，不直接删除而是注释
- 对代码需要有详尽的注释
- 在检测到可以预防的模式或错误时创建自己的规则

### 日志记录
- 使用结构化日志记录
- 包含适当的日志级别
- 记录关键操作和错误信息

### 配置管理
- 使用pydantic-settings进行配置管理
- 环境变量优先于配置文件
- 敏感信息使用环境变量

### 测试约定
- 测试文件以`test_`开头
- 使用描述性的测试名称
- 包含单元测试和集成测试

## 架构模式

### 后端架构
- 使用FastAPI的依赖注入
- 实现适当的中间件
- 使用SQLAlchemy ORM模式

### AI组件
- 实现适当的错误处理和重试逻辑
- 使用LangGraph的工作流模式
- 实现记忆和检查点机制

### 缓存策略
- 使用混合缓存架构
- 实现语义相似性搜索
- 支持多种缓存后端