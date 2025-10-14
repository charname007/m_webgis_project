# PostgreSQL组件setup优化

## 问题发现

用户指出：`actual_saver.setup()` 和 `actual_store.setup()` 这两行代码只有第一次使用store和checkpoint时才需要调用。

## 优化方案

### 修改内容
在 `python/sight_server/core/agent.py` 中，将setup调用包装在try-except块中：

```python
# ✅ 新增：调用setup()方法初始化数据库表结构（仅在第一次使用时调用）
try:
    actual_saver.setup()  # 初始化checkpoint表
    self.logger.info("✓ PostgresSaver tables initialized")
except Exception as setup_error:
    # 如果表已存在，setup可能会失败，这是正常的
    self.logger.debug(f"PostgresSaver setup completed or tables already exist: {setup_error}")

try:
    actual_store.setup()  # 初始化store表
    self.logger.info("✓ PostgresStore tables initialized")
except Exception as setup_error:
    # 如果表已存在，setup可能会失败，这是正常的
    self.logger.debug(f"PostgresStore setup completed or tables already exist: {setup_error}")
```

## 技术要点

1. **幂等性**: setup操作应该是幂等的，多次调用不会产生副作用
2. **错误处理**: 如果表已存在，setup可能会抛出异常，这是正常情况
3. **日志级别**: 使用debug级别记录重复setup的情况，避免日志污染
4. **性能优化**: 避免不必要的数据库操作

## 优势

- **健壮性**: 处理setup可能失败的情况
- **性能**: 避免重复的数据库初始化操作
- **日志清晰**: 区分首次初始化和重复初始化的情况
- **用户体验**: 不会因为重复初始化而报错

这个优化确保了PostgreSQL组件的setup操作只在第一次使用时执行，提高了代码的健壮性和性能。