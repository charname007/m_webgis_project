"""
配置管理模块 - 集中管理所有配置项
使用 pydantic-settings 进行配置验证和环境变量管理
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """应用配置类"""

    # ==================== 数据库配置 ====================
    DATABASE_URL: str = Field(
        default="postgresql://sagasama:cznb6666@localhost:5432/WGP_db",
        description="PostgreSQL数据库连接字符串"
    )

    # ==================== LLM配置 ====================
    DEEPSEEK_API_KEY: Optional[str] = Field(
        default=None,
        description="DeepSeek API密钥"
    )

    DEEPSEEK_API_BASE: str = Field(
        default="https://api.deepseek.com",
        description="DeepSeek API基础URL"
    )

    LLM_MODEL: str = Field(
        default="deepseek-chat",
        description="使用的LLM模型名称"
    )

    LLM_TEMPERATURE: float = Field(
        default=1.3,
        ge=0.0,
        le=2.0,
        description="LLM温度参数，控制随机性"
    )

    # ==================== 服务器配置 ====================
    SERVER_HOST: str = Field(
        default="0.0.0.0",
        description="服务器监听地址"
    )

    SERVER_PORT: int = Field(
        default=8001,
        ge=1024,
        le=65535,
        description="服务器监听端口"
    )

    # ==================== 查询配置 ====================
    MAX_QUERY_LENGTH: int = Field(
        default=500,
        ge=1,
        description="查询文本最大长度"
    )

    DEFAULT_QUERY_LIMIT: int = Field(
        default=1000,
        ge=1,
        description="默认查询结果限制数量"
    )

    MAX_QUERY_LIMIT: int = Field(
        default=10000,
        ge=1,
        description="最大查询结果限制数量"
    )

    # ==================== 日志配置 ====================
    LOG_LEVEL: str = Field(
        default="INFO",
        description="日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式"
    )

    LOG_DATE_FORMAT: str = Field(
        default="%Y-%m-%d %H:%M:%S",
        description="日志时间格式"
    )

    # ==================== Agent配置 ====================
    AGENT_MAX_ITERATIONS: int = Field(
        default=15,
        ge=1,
        le=50,
        description="Agent最大迭代次数"
    )

    AGENT_MAX_EXECUTION_TIME: int = Field(
        default=90,
        ge=10,
        le=300,
        description="Agent最大执行时间（秒）"
    )

    # ==================== 数据库连接池配置 ====================
    DB_POOL_SIZE: int = Field(
        default=5,
        ge=1,
        description="数据库连接池大小"
    )

    DB_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        description="数据库连接池最大溢出连接数"
    )

    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
        description="数据库连接池超时时间（秒）"
    )

    DB_POOL_RECYCLE: int = Field(
        default=3600,
        ge=300,
        description="数据库连接回收时间（秒）"
    )

    DB_CONNECT_TIMEOUT: int = Field(
        default=10,
        ge=1,
        description="数据库连接超时时间（秒）"
    )

    # ==================== Pydantic配置 ====================
    model_config = SettingsConfigDict(
        # .env 文件路径（相对于当前文件）
        env_file=".env",
        # .env 文件编码
        env_file_encoding="utf-8",
        # 忽略额外字段
        extra="ignore",
        # 大小写敏感
        case_sensitive=True
    )

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"日志级别必须是以下之一: {', '.join(valid_levels)}")
        return v.upper()

    @validator("DEEPSEEK_API_KEY", always=True)
    def validate_api_key(cls, v):
        """验证API密钥，如果未设置则从环境变量获取"""
        if v is None:
            # 尝试从环境变量获取
            v = os.getenv("DEEPSEEK_API_KEY")
        return v

    def get_database_config(self) -> dict:
        """获取数据库配置字典"""
        return {
            "connection_string": self.DATABASE_URL,
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "connect_timeout": self.DB_CONNECT_TIMEOUT
        }

    def get_llm_config(self) -> dict:
        """获取LLM配置字典"""
        return {
            "api_key": self.DEEPSEEK_API_KEY,
            "api_base": self.DEEPSEEK_API_BASE,
            "model": self.LLM_MODEL,
            "temperature": self.LLM_TEMPERATURE
        }

    def get_agent_config(self) -> dict:
        """获取Agent配置字典"""
        return {
            "max_iterations": self.AGENT_MAX_ITERATIONS,
            "max_execution_time": self.AGENT_MAX_EXECUTION_TIME
        }


# ==================== 全局配置实例 ====================
# 创建全局配置实例，供其他模块导入使用
settings = Settings()


# ==================== 配置信息打印（用于调试） ====================
def print_config_info():
    """打印配置信息（敏感信息已脱敏）"""
    print("=" * 60)
    print("配置信息")
    print("=" * 60)

    print(f"\n[数据库配置]")
    # 脱敏数据库URL（隐藏密码）
    db_url = settings.DATABASE_URL
    if "@" in db_url:
        user_part, host_part = db_url.split("@")
        if ":" in user_part:
            protocol_user = user_part.split(":")[0:2]
            masked_url = f"{protocol_user[0]}:{protocol_user[1]}:****@{host_part}"
        else:
            masked_url = f"{user_part}:****@{host_part}"
    else:
        masked_url = db_url
    print(f"  DATABASE_URL: {masked_url}")
    print(f"  DB_POOL_SIZE: {settings.DB_POOL_SIZE}")
    print(f"  DB_MAX_OVERFLOW: {settings.DB_MAX_OVERFLOW}")

    print(f"\n[LLM配置]")
    # 脱敏API密钥
    api_key = settings.DEEPSEEK_API_KEY
    if api_key:
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "****"
    else:
        masked_key = "未设置"
    print(f"  DEEPSEEK_API_KEY: {masked_key}")
    print(f"  DEEPSEEK_API_BASE: {settings.DEEPSEEK_API_BASE}")
    print(f"  LLM_MODEL: {settings.LLM_MODEL}")
    print(f"  LLM_TEMPERATURE: {settings.LLM_TEMPERATURE}")

    print(f"\n[服务器配置]")
    print(f"  SERVER_HOST: {settings.SERVER_HOST}")
    print(f"  SERVER_PORT: {settings.SERVER_PORT}")

    print(f"\n[查询配置]")
    print(f"  MAX_QUERY_LENGTH: {settings.MAX_QUERY_LENGTH}")
    print(f"  DEFAULT_QUERY_LIMIT: {settings.DEFAULT_QUERY_LIMIT}")
    print(f"  MAX_QUERY_LIMIT: {settings.MAX_QUERY_LIMIT}")

    print(f"\n[日志配置]")
    print(f"  LOG_LEVEL: {settings.LOG_LEVEL}")

    print(f"\n[Agent配置]")
    print(f"  AGENT_MAX_ITERATIONS: {settings.AGENT_MAX_ITERATIONS}")
    print(f"  AGENT_MAX_EXECUTION_TIME: {settings.AGENT_MAX_EXECUTION_TIME}秒")

    print("=" * 60)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 打印配置信息
    print_config_info()

    # 测试配置访问
    print(f"\n测试配置访问:")
    print(f"数据库配置: {settings.get_database_config()}")
    print(f"LLM配置: {settings.get_llm_config()}")
    print(f"Agent配置: {settings.get_agent_config()}")
