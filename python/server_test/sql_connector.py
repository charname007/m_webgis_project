import logging
from typing import List, Optional, Dict, Any, Sequence
from langchain_community.utilities import SQLDatabase
# from geoalchemy2 import Geometry  # 未使用,已注释
import psycopg2
from psycopg2.extras import RealDictCursor
from config import settings  # 导入配置


class SQLConnector:
    """SQL数据库连接器，提供数据库连接和查询功能，特别优化支持空间查询"""

    def __init__(self, connection_string: Optional[str] = None, echo: bool = False):
        """
        初始化SQL连接器 - 优化版本

        Args:
            connection_string: 数据库连接字符串,如果为None则使用配置中的默认连接
            echo: 是否打印SQL日志
        """
        # 设置日志
        self.logger = self._setup_logger()
        self.logger.info("开始初始化SQLConnector...")

        # 保存配置 - 优先使用传入的连接字符串,否则使用配置文件中的
        self.connection_string = connection_string or settings.DATABASE_URL
        self.echo = echo
        self.db = None
        self.raw_connection = None

        # 建立连接
        try:
            self._connect()
            self.logger.info("✓ SQLConnector 初始化完成")
        except Exception as e:
            self.logger.error(f"✗ SQLConnector 初始化失败: {e}")
            raise
    
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
        """建立数据库连接 - 优化版本，使用配置文件中的连接池参数"""
        try:
            # 配置SQLAlchemy引擎参数 - 使用配置文件中的值
            engine_args = {
                "connect_args": {
                    "application_name": "webgis_nlq_project",
                    "connect_timeout": settings.DB_CONNECT_TIMEOUT
                },
                "echo": self.echo,
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_timeout": settings.DB_POOL_TIMEOUT,
                "pool_recycle": settings.DB_POOL_RECYCLE
            }

            # 创建SQLDatabase连接
            self.db = SQLDatabase.from_uri(self.connection_string, engine_args=engine_args)
            self.logger.info(f"✓ SQLDatabase连接成功 (方言: {self.db.dialect})")

            # 建立原始psycopg2连接用于空间查询
            self.raw_connection = psycopg2.connect(
                self.connection_string,
                connect_timeout=settings.DB_CONNECT_TIMEOUT
            )
            self.logger.info("✓ 原始数据库连接已建立")

            # 检查PostGIS扩展
            if self._check_postgis_extension():
                self.logger.info("✓ PostGIS扩展可用")

            # 获取表信息
            table_names = self.get_usable_table_names()
            self.logger.info(f"✓ 发现 {len(table_names)} 个可用表")

            # 获取空间表信息
            spatial_tables = self.get_spatial_tables()
            if spatial_tables:
                self.logger.info(f"✓ 发现 {len(spatial_tables)} 个空间表")

        except Exception as e:
            self.logger.error(f"✗ 数据库连接失败: {e}", exc_info=True)
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
    
    def _check_postgis_extension(self) -> bool:
        """检查PostGIS扩展是否已安装"""
        try:
            with self.raw_connection.cursor() as cursor:
                cursor.execute("SELECT PostGIS_Version()")
                version = cursor.fetchone()
                self.logger.info(f"PostGIS版本: {version[0] if version else '未安装'}")
                return version is not None
        except Exception as e:
            self.logger.warning(f"PostGIS扩展检查失败: {e}")
            return False
    
    def get_spatial_tables(self) -> Sequence[Dict[str, Any]]:
        """获取包含几何列的空间表信息"""
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        f_table_schema as schema_name,
                        f_table_name as table_name,
                        f_geometry_column as geometry_column,
                        type as geometry_type,
                        srid,
                        coord_dimension
                    FROM geometry_columns
                    WHERE f_table_schema = 'public'
                    ORDER BY f_table_name;
                """)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"获取空间表信息失败: {e}")
            return []
    
    def execute_spatial_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Sequence[Dict[str, Any]]:
        """执行空间查询并返回字典格式结果
        
        Args:
            query: SQL查询语句
            parameters: 查询参数
            
        Returns:
            查询结果列表
        """
        if not self.raw_connection:
            raise ConnectionError("原始数据库连接未建立")
        
        try:
            self.logger.info(f"执行空间查询: {query}")
            if parameters:
                self.logger.info(f"查询参数: {parameters}")
            
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchall()
                return result
                
        except Exception as e:
            self.logger.error(f"空间查询执行失败: {e}")
            raise
    
    def get_spatial_indexes(self, table_name: str) -> Sequence[Dict[str, Any]]:
        """获取表的空间索引信息"""
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE tablename = %s 
                    AND indexdef LIKE '%gist%'
                    ORDER BY indexname;
                """, (table_name,))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"获取空间索引信息失败: {e}")
            return []
    
    def check_spatial_function_availability(self) -> Dict[str, bool]:
        """检查常用空间函数的可用性"""
        spatial_functions = [
            "ST_Intersects", "ST_Contains", "ST_Within", "ST_Distance",
            "ST_Buffer", "ST_Union", "ST_Transform", "ST_AsGeoJSON",
            "pgr_dijkstra", "pgr_aStar", "TopoGeo_CreateTopology"
        ]
        
        availability = {}
        
        try:
            with self.raw_connection.cursor() as cursor:
                for func in spatial_functions:
                    try:
                        # 尝试执行一个简单的测试查询
                        if func.startswith("pgr_"):
                            # PgRouting函数需要特定的参数格式
                            cursor.execute(f"SELECT {func} IS NOT NULL")
                        else:
                            cursor.execute(f"SELECT {func}('POINT(0 0)', 'POINT(1 1)') IS NOT NULL")
                        availability[func] = True
                    except Exception:
                        availability[func] = False
        
        except Exception as e:
            self.logger.error(f"检查空间函数可用性失败: {e}")
            # 如果检查失败，假设所有函数都不可用
            availability = {func: False for func in spatial_functions}
        
        return availability
    
    def get_database_spatial_info(self) -> Dict[str, Any]:
        """获取数据库的空间相关信息"""
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # 获取PostGIS版本
                cursor.execute("SELECT PostGIS_Version() as postgis_version")
                postgis_version = cursor.fetchone()
                
                # 获取PgRouting版本（如果安装）
                pgrouting_version = None
                try:
                    cursor.execute("SELECT pgr_version() as pgrouting_version")
                    pgrouting_version = cursor.fetchone()
                except:
                    pass
                
                # 获取空间表统计
                cursor.execute("SELECT COUNT(*) as spatial_table_count FROM geometry_columns WHERE f_table_schema = 'public'")
                spatial_table_count = cursor.fetchone()
                
                return {
                    "postgis_version": postgis_version["postgis_version"] if postgis_version else "未安装",
                    "pgrouting_version": pgrouting_version["pgrouting_version"] if pgrouting_version else "未安装",
                    "spatial_table_count": spatial_table_count["spatial_table_count"] if spatial_table_count else 0,
                    "spatial_functions_available": self.check_spatial_function_availability()
                }
                
        except Exception as e:
            self.logger.error(f"获取数据库空间信息失败: {e}")
            return {
                "postgis_version": "未知",
                "pgrouting_version": "未知",
                "spatial_table_count": 0,
                "spatial_functions_available": {}
            }
    
    def close(self) -> None:
        """关闭数据库连接 - 优化版本，确保资源正确释放"""
        # 关闭原始psycopg2连接
        if self.raw_connection:
            try:
                self.raw_connection.close()
                self.logger.info("✓ 原始数据库连接已关闭")
            except Exception as e:
                self.logger.warning(f"关闭原始连接时出错: {e}")
            finally:
                self.raw_connection = None

        # 关闭SQLDatabase连接
        if self.db:
            try:
                # SQLDatabase 内部使用 SQLAlchemy engine，通过私有属性访问
                if hasattr(self.db, '_engine') and self.db._engine:
                    self.db._engine.dispose()
                    self.logger.info("✓ SQLDatabase连接已关闭")
            except Exception as e:
                self.logger.warning(f"关闭SQLDatabase时出错: {e}")
            finally:
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
        
        # 空间功能测试
        spatial_info = connector.get_database_spatial_info()
        print(f"数据库空间信息: {spatial_info}")
        
        # 获取空间表
        spatial_tables = connector.get_spatial_tables()
        print(f"空间表: {spatial_tables}")
        
        # 示例查询
        try:
            result = connector.execute_query("SELECT version()")
            print(f"数据库版本: {result}")
            
            # 空间查询示例
            if spatial_tables:
                sample_table = spatial_tables[0]["table_name"]
                spatial_query = f"SELECT COUNT(*) as feature_count FROM {sample_table} WHERE geom IS NOT NULL"
                spatial_result = connector.execute_spatial_query(spatial_query)
                print(f"空间查询结果: {spatial_result}")
                
        except Exception as e:
            print(f"查询失败: {e}")
