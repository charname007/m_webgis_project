"""
配置管理模块 - Sight Server
使用 pydantic-settings 进行配置验证和环境变量管理
"""

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

    # 数据库连接池配置
    DB_POOL_SIZE: int = Field(default=5, ge=1, description="数据库连接池大小")
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, description="数据库连接池最大溢出连接数")
    DB_POOL_TIMEOUT: int = Field(default=30, ge=1, description="数据库连接池超时时间（秒）")
    DB_POOL_RECYCLE: int = Field(default=3600, ge=300, description="数据库连接回收时间（秒）")
    DB_CONNECT_TIMEOUT: int = Field(default=10, ge=1, description="数据库连接超时时间（秒）")

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
    SERVER_HOST: str = Field(default="0.0.0.0", description="服务器监听地址")
    SERVER_PORT: int = Field(default=8001, ge=1024, le=65535, description="服务器监听端口")
    SERVER_RELOAD: bool = Field(default=False, description="开发模式热重载")
    DEBUG: bool = Field(default=False, description="调试模式，显示详细错误信息")

    # ==================== 查询配置 ====================
    MAX_QUERY_LENGTH: int = Field(default=500, ge=1, description="查询文本最大长度")
    DEFAULT_QUERY_LIMIT: int = Field(default=1000, ge=1, description="默认查询结果限制数量")
    MAX_QUERY_LIMIT: int = Field(default=10000, ge=1, description="最大查询结果限制数量")

    # ==================== 日志配置 ====================
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
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
        default=75,
        ge=1,
        le=100,
        description="Agent最大迭代次数"
    )

    AGENT_MAX_EXECUTION_TIME: int = Field(
        default=450,
        ge=10,
        le=600,
        description="Agent最大执行时间（秒）"
    )

    # ✅ 新增：结果验证配置
    ENABLE_RESULT_VALIDATION: bool = Field(
        default=False,
        description="是否启用结果验证功能"
    )

    MAX_VALIDATION_RETRIES: int = Field(
        default=3,
        ge=0,
        le=10,
        description="最大验证重试次数"
    )

    # ✅ 新增：深度分析配置
    ENABLE_ANSWER_ANALYSIS: bool = Field(
        default=False,
        description="是否启用答案深度分析功能"
    )

    ANALYSIS_DETAIL_LEVEL: str = Field(
        default="detailed",
        description="分析详细程度: simple/detailed/comprehensive"
    )

    # ==================== 缓存配置 ==================== (✅ 新增)
    ENABLE_CACHE: bool = Field(
        default=True,
        description="是否启用查询缓存"
    )

    CACHE_DIR: str = Field(
        default="./cache",
        description="缓存文件目录"
    )

    CACHE_TTL: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="缓存生存时间（秒），默认1小时"
    )

    CACHE_MAX_SIZE: int = Field(
        default=1000,
        ge=10,
        le=10000,
        description="最大缓存条目数"
    )

    CACHE_SEMANTIC_SEARCH: bool = Field(
        default=True,
        description="是否启用语义相似度缓存搜索"
    )

    CACHE_SIMILARITY_THRESHOLD: float = Field(
        default=0.92,
        ge=0.8,
        le=0.99,
        description="语义相似度阈值（0-1），默认0.92"
    )

    CACHE_EMBEDDING_MODEL: str = Field(
        default="paraphrase-multilingual-MiniLM-L12-v2",
        description="Embedding模型名称（用于语义搜索）"
    )

    # ==================== Schema缓存 ====================
    SCHEMA_CACHE_ENABLED: bool = Field(
        default=True,
        description="是否启用本地schema缓存"
    )

    SCHEMA_CACHE_TTL: int = Field(
        default=43200,
        ge=0,
        description="Schema缓存有效期（秒），0表示不失效"
    )

    SCHEMA_CACHE_PATH: str = Field(
        default="schema_cache.json",
        description="Schema缓存文件路径（相对路径会拼接到CACHE_DIR）"
    )

    # ==================== CORS配置 ====================
    CORS_ORIGINS: list = Field(
        default=["*"],
        description="允许的CORS源"
    )

    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="允许携带凭证"
    )

    CORS_ALLOW_METHODS: list = Field(
        default=["*"],
        description="允许的HTTP方法"
    )

    CORS_ALLOW_HEADERS: list = Field(
        default=["*"],
        description="允许的HTTP头"
    )

    # ==================== Embedding模型配置 ====================
    EMBEDDING_MODEL_OFFLINE_MODE: bool = Field(
        default=False,
        description="强制离线模式，避免网络连接问题"
    )

    EMBEDDING_MODEL_TIMEOUT: int = Field(
        default=30,
        ge=5,
        le=300,
        description="模型加载网络超时时间（秒）"
    )

    EMBEDDING_MODEL_RETRY_COUNT: int = Field(
        default=2,
        ge=0,
        le=5,
        description="模型加载重试次数"
    )

    EMBEDDING_MODEL_RETRY_DELAY: int = Field(
        default=5,
        ge=1,
        le=30,
        description="重试间隔时间（秒）"
    )

    # ==================== Pydantic配置 ====================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
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
        """验证API密钥"""
        import os
        if v is None:
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
            "max_execution_time": self.AGENT_MAX_EXECUTION_TIME,
            # ✅ 新增：验证和分析配置
            "enable_result_validation": self.ENABLE_RESULT_VALIDATION,
            "max_validation_retries": self.MAX_VALIDATION_RETRIES,
            "enable_answer_analysis": self.ENABLE_ANSWER_ANALYSIS,
            "analysis_detail_level": self.ANALYSIS_DETAIL_LEVEL
        }

    def get_cache_config(self) -> dict:
        """获取缓存配置字典 (✅ 新增)"""
        return {
            "enable_cache": self.ENABLE_CACHE,
            "cache_dir": self.CACHE_DIR,
            "ttl": self.CACHE_TTL,
            "max_size": self.CACHE_MAX_SIZE,
            "enable_semantic_search": self.CACHE_SEMANTIC_SEARCH,
            "similarity_threshold": self.CACHE_SIMILARITY_THRESHOLD,
            "embedding_model": self.CACHE_EMBEDDING_MODEL
        }

    def get_cors_config(self) -> dict:
        """获取CORS配置字典"""
        return {
            "allow_origins": self.CORS_ORIGINS,
            "allow_credentials": self.CORS_ALLOW_CREDENTIALS,
            "allow_methods": self.CORS_ALLOW_METHODS,
            "allow_headers": self.CORS_ALLOW_HEADERS
        }


# ==================== 全局配置实例 ====================
settings = Settings()


# ==================== 配置信息打印（用于调试） ====================
def print_config_info():
    """打印配置信息（敏感信息已脱敏）"""
    print("=" * 60)
    print("Sight Server 配置信息")
    print("=" * 60)

    print(f"\n[数据库配置]")
    # 脱敏数据库URL
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

    print(f"\n[LLM配置]")
    # 脱敏API密钥
    api_key = settings.DEEPSEEK_API_KEY
    if api_key:
        masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "****"
    else:
        masked_key = "未设置"
    print(f"  DEEPSEEK_API_KEY: {masked_key}")
    print(f"  LLM_MODEL: {settings.LLM_MODEL}")
    print(f"  LLM_TEMPERATURE: {settings.LLM_TEMPERATURE}")

    print(f"\n[服务器配置]")
    print(f"  SERVER_HOST: {settings.SERVER_HOST}")
    print(f"  SERVER_PORT: {settings.SERVER_PORT}")
    print(f"  SERVER_RELOAD: {settings.SERVER_RELOAD}")

    print(f"\n[日志配置]")
    print(f"  LOG_LEVEL: {settings.LOG_LEVEL}")

    print(f"\n[Agent配置]")
    print(f"  AGENT_MAX_ITERATIONS: {settings.AGENT_MAX_ITERATIONS}")
    print(f"  AGENT_MAX_EXECUTION_TIME: {settings.AGENT_MAX_EXECUTION_TIME}秒")
    print(f"  ENABLE_RESULT_VALIDATION: {settings.ENABLE_RESULT_VALIDATION}")
    print(f"  MAX_VALIDATION_RETRIES: {settings.MAX_VALIDATION_RETRIES}")
    print(f"  ENABLE_ANSWER_ANALYSIS: {settings.ENABLE_ANSWER_ANALYSIS}")
    print(f"  ANALYSIS_DETAIL_LEVEL: {settings.ANALYSIS_DETAIL_LEVEL}")

    print(f"\n[缓存配置] (✅ 新增)")
    print(f"  ENABLE_CACHE: {settings.ENABLE_CACHE}")
    print(f"  CACHE_DIR: {settings.CACHE_DIR}")
    print(f"  CACHE_TTL: {settings.CACHE_TTL}秒")
    print(f"  CACHE_MAX_SIZE: {settings.CACHE_MAX_SIZE}")
    print(f"  CACHE_SEMANTIC_SEARCH: {settings.CACHE_SEMANTIC_SEARCH}")
    print(f"  CACHE_SIMILARITY_THRESHOLD: {settings.CACHE_SIMILARITY_THRESHOLD}")
    print(f"  CACHE_EMBEDDING_MODEL: {settings.CACHE_EMBEDDING_MODEL}")

    print("=" * 60)


if __name__ == "__main__":
    print_config_info()
