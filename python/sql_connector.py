import logging
from typing import List, Optional, Dict, Any
from langchain_community.utilities import SQLDatabase
from geoalchemy2 import Geometry


class SQLConnector:
    """SQL数据库连接器，提供数据库连接和查询功能"""
    
    def __init__(self, connection_string: Optional[str] = None, echo: bool = False):
        """
        初始化SQL连接器
        
        Args:
            connection_string: 数据库连接字符串，如果为None则使用默认连接
            echo: 是否打印SQL日志
        """
        self.connection_string = connection_string or "postgresql://sagasama:cznb6666@localhost:5432/WGP_db"
        self.echo = echo
        self.logger = self._setup_logger()
        self.db = None
        self._connect()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _connect(self) -> None:
        """建立数据库连接"""
        try:
            engine_args = {
                "connect_args": {"application_name": "webgis_project"},
                "echo": self.echo
            }
            
            self.db = SQLDatabase.from_uri(self.connection_string, engine_args=engine_args)
            self.logger.info(f"成功连接到数据库，方言: {self.db.dialect}")
            
            # 获取可用表名但不强制打印
            table_names = self.get_usable_table_names()
            self.logger.info(f"可用表: {table_names}")
            
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            raise
    
    def get_usable_table_names(self) -> List[str]:
        """获取可用表名列表"""
        if not self.db:
            raise ConnectionError("数据库未连接")
        return list(self.db.get_usable_table_names())
    
    def get_dialect(self) -> str:
        """获取数据库方言"""
        if not self.db:
            raise ConnectionError("数据库未连接")
        return self.db.dialect
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """执行SQL查询
        
        Args:
            query: SQL查询语句
            parameters: 查询参数
            
        Returns:
            查询结果
        """
        if not self.db:
            raise ConnectionError("数据库未连接")
        
        try:
            self.logger.info(f"执行查询: {query}")
            if parameters:
                self.logger.info(f"查询参数: {parameters}")
            
            result = self.db.run(query, parameters=parameters)
            return result
            
        except Exception as e:
            self.logger.error(f"查询执行失败: {e}")
            raise
    
    def get_table_info(self, table_names: Optional[List[str]] = None) -> str:
        """获取表结构信息
        
        Args:
            table_names: 表名列表，如果为None则获取所有表
            
        Returns:
            表结构信息字符串
        """
        if not self.db:
            raise ConnectionError("数据库未连接")
        
        return self.db.get_table_info(table_names=table_names)
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self.db:
            # SQLDatabase 内部使用 SQLAlchemy engine，通过私有属性访问
            if hasattr(self.db, '_engine') and self.db._engine:
                self.db._engine.dispose()
                self.logger.info("数据库连接已关闭")
            self.db = None
    
    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器时关闭连接"""
        self.close()
    
    def __del__(self):
        """析构函数中关闭连接"""
        try:
            self.close()
        except Exception:
            # 忽略析构函数中的异常，避免干扰正常程序退出
            pass


# 使用示例
if __name__ == "__main__":
    # 基本用法
    with SQLConnector(echo=True) as connector:
        print(f"数据库方言: {connector.get_dialect()}")
        print(f"可用表: {connector.get_usable_table_names()}")
        
        # 示例查询
        try:
            result = connector.execute_query("SELECT version()")
            print(f"数据库版本: {result}")
        except Exception as e:
            print(f"查询失败: {e}")
