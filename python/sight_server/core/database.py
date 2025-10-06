"""
数据库连接模块 - Sight Server
提供PostgreSQL数据库连接和查询功能，支持PostGIS空间查询
"""

import logging
import json
import time
import copy
from pathlib import Path
from typing import List, Optional, Dict, Any, Sequence, Tuple
from langchain_community.utilities import SQLDatabase
import psycopg2
from psycopg2.extras import RealDictCursor
from config import settings

logger = logging.getLogger(__name__)


class DatabaseConnector:
    """
    数据库连接器

    功能:
    - PostgreSQL数据库连接管理
    - 连接池配置
    - LangChain SQLDatabase集成
    - PostGIS空间查询支持
    - 原始SQL查询执行
    """

    SPATIAL_INDEX_TYPES = {"gist", "gin", "spgist"}

    def __init__(self, connection_string: Optional[str] = None, echo: bool = False):
        """
        初始化数据库连接器

        Args:
            connection_string: 数据库连接字符串。默认使用配置文件
            echo: 是否打印SQL日志
        """
        self.logger = logger
        self.default_schema = "public"
        self.schema_cache_enabled = settings.SCHEMA_CACHE_ENABLED
        self.schema_cache_ttl = settings.SCHEMA_CACHE_TTL
        cache_path = Path(settings.SCHEMA_CACHE_PATH)
        if not cache_path.is_absolute():
            cache_path = Path(settings.CACHE_DIR) / cache_path
        self.schema_cache_path = cache_path
        self._schema_cache_data: Optional[Dict[str, Any]] = None
        self._schema_cache_timestamp: Optional[float] = None

        self.logger.info("Initializing DatabaseConnector...")

        # 使用配置文件中的连接字符串，允许参数覆盖
        self.connection_string = connection_string or settings.DATABASE_URL
        self.echo = echo
        self.db = None
        self.raw_connection = None

        # 建立连接
        try:
            self._connect()
            self.logger.info("✓ DatabaseConnector initialized successfully")
        except Exception as e:
            self.logger.error(f"✗ DatabaseConnector initialization failed: {e}")
            raise

    def _connect(self) -> None:
        """建立数据库连接，使用配置文件中的连接池参数"""
        try:
            # 配置SQLAlchemy引擎参数
            engine_args = {
                "connect_args": {
                    "application_name": "sight_server",
                    "connect_timeout": settings.DB_CONNECT_TIMEOUT
                },
                "echo": self.echo,
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_timeout": settings.DB_POOL_TIMEOUT,
                "pool_recycle": settings.DB_POOL_RECYCLE
            }

            # 创建LangChain SQLDatabase连接（用于Agent）
            self.db = SQLDatabase.from_uri(
                self.connection_string,
                engine_args=engine_args
            )
            self.logger.info(f"✓ SQLDatabase connected (dialect: {self.db.dialect})")

            # 建立原始psycopg2连接（用于空间查询）
            self.raw_connection = psycopg2.connect(
                self.connection_string,
                connect_timeout=settings.DB_CONNECT_TIMEOUT
            )
            # ✅ 设置为autocommit模式，避免事务被阻塞
            self.raw_connection.autocommit = True
            self.logger.info("✓ Raw psycopg2 connection established (autocommit mode)")

            # 检查PostGIS扩展
            if self._check_postgis_extension():
                self.logger.info("✓ PostGIS extension available")

            # 获取表信息
            table_names = self.get_usable_table_names()
            self.logger.info(f"Found {len(table_names)} tables")

            if self.schema_cache_enabled:
                self.logger.info(
                    f"Schema cache enabled (path: {self.schema_cache_path})"
                )
            else:
                self.logger.info("Schema cache disabled")

        except Exception as e:
            self.logger.error(f"✗ Database connection failed: {e}")
            raise

    def _check_postgis_extension(self) -> bool:
        """检查PostGIS扩展是否已安装"""
        try:
            with self.raw_connection.cursor() as cursor:
                cursor.execute("SELECT PostGIS_Version()")
                version = cursor.fetchone()
                if version:
                    self.logger.info(f"PostGIS version: {version[0]}")
                    return True
                return False
        except Exception as e:
            self.logger.warning(f"PostGIS extension check failed: {e}")
            return False

    def get_usable_table_names(self) -> List[str]:
        """
        获取可用表名列表

        Returns:
            表名列表
        """
        if not self.db:
            raise ConnectionError("Database not connected")
        return list(self.db.get_usable_table_names())

    def get_dialect(self) -> str:
        """
        获取数据库方言

        Returns:
            数据库方言（如: postgresql）
        """
        if not self.db:
            raise ConnectionError("Database not connected")
        return self.db.dialect

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        执行SQL查询（使用LangChain SQLDatabase）

        Args:
            query: SQL查询语句
            parameters: 查询参数

        Returns:
            查询结果
        """
        if not self.db:
            raise ConnectionError("Database not connected")

        try:
            self.logger.debug(f"Executing query: {query[:100]}...")
            if parameters:
                self.logger.debug(f"Parameters: {parameters}")

            result = self.db.run(query, parameters=parameters)
            return result

        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise

    def execute_raw_query(
        self,
        query: str,
        parameters: Optional[tuple] = None
    ) -> Sequence[Dict[str, Any]]:
        """
        执行原始SQL查询（使用psycopg2，返回字典格式）

        Args:
            query: SQL查询语句
            parameters: 查询参数元组

        Returns:
            查询结果列表
        """
        if not self.raw_connection:
            raise ConnectionError("Raw connection not established")

        try:
            self.logger.debug(f"Executing raw query: {query[:100]}...")
            if parameters:
                self.logger.debug(f"Parameters: {parameters}")

            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, parameters)
                result = cursor.fetchall()
                return result

        except Exception as e:
            # ✅ autocommit模式下无需手动回滚，连接会自动恢复
            self.logger.error(f"Raw query execution failed: {e}")
            raise

    def get_table_info(self, table_names: Optional[List[str]] = None) -> str:
        """
        获取表结构信息

        Args:
            table_names: 表名列表。如果为None则获取所有表

        Returns:
            表结构信息字符串
        """
        if not self.db:
            raise ConnectionError("Database not connected")

        return self.db.get_table_info(table_names=table_names)

    def get_spatial_tables(
        self,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Sequence[Dict[str, Any]]:
        """获取空间表信息（支持缓存）。"""
        snapshot = self.get_detailed_schema(use_cache=use_cache, force_refresh=force_refresh)
        spatial_map = snapshot.get("spatial_tables", {})
        return list(spatial_map.values())

    def get_spatial_indexes(
        self,
        table_name: str,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Sequence[Dict[str, Any]]:
        """获取指定表的空间索引信息。"""
        snapshot = self.get_detailed_schema(
            table_names=[table_name],
            use_cache=use_cache,
            force_refresh=force_refresh,
        )
        spatial_tables = snapshot.get("spatial_tables", {})
        info = spatial_tables.get(self._normalize_table_name(table_name))
        if not info:
            return []
        return info.get("spatial_indexes", [])

    def get_detailed_schema(
        self,
        table_names: Optional[List[str]] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """获取数据库 schema，支持本地缓存。"""
        normalized_names = (
            [self._normalize_table_name(name) for name in table_names]
            if table_names
            else None
        )

        if normalized_names is None:
            cached = self._get_cached_schema_snapshot(use_cache=use_cache, force_refresh=force_refresh)
            if cached is not None:
                return cached

            snapshot = self._build_schema_snapshot()
            if self.schema_cache_enabled:
                self._save_schema_cache_to_disk(snapshot)
                self._schema_cache_data = snapshot
                self._schema_cache_timestamp = snapshot.get("cached_at", time.time())
            return snapshot

        # 请求指定表
        if use_cache and not force_refresh:
            base_snapshot = self._get_cached_schema_snapshot(use_cache=True, force_refresh=False)
            if base_snapshot is not None:
                return self._filter_schema_snapshot(base_snapshot, normalized_names)

        return self._build_schema_snapshot(table_names=normalized_names)

    def refresh_schema_cache(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """手动刷新 schema 缓存，可选指定表。"""
        snapshot = self._build_schema_snapshot(table_names=table_names)
        if table_names is None and self.schema_cache_enabled:
            self._save_schema_cache_to_disk(snapshot)
            self._schema_cache_data = snapshot
            self._schema_cache_timestamp = snapshot.get("cached_at", time.time())
        return snapshot

    def clear_schema_cache(self) -> None:
        """清空 schema 缓存（内存+文件）。"""
        self._schema_cache_data = None
        self._schema_cache_timestamp = None
        if self.schema_cache_path.exists():
            try:
                self.schema_cache_path.unlink()
                self.logger.info(f"Schema cache file removed: {self.schema_cache_path}")
            except Exception as exc:
                self.logger.warning(f"Failed to remove schema cache file: {exc}")

    def _get_cached_schema_snapshot(
        self,
        use_cache: bool,
        force_refresh: bool,
    ) -> Optional[Dict[str, Any]]:
        if not self.schema_cache_enabled or not use_cache or force_refresh:
            return None

        if (
            self._schema_cache_data is not None
            and self._schema_cache_timestamp is not None
            and not self._is_cache_expired(self._schema_cache_timestamp)
        ):
            return copy.deepcopy(self._schema_cache_data)

        snapshot = self._load_schema_cache_from_disk()
        if snapshot is None:
            return None

        cached_at = snapshot.get("cached_at")
        if cached_at is None or self._is_cache_expired(cached_at):
            return None

        self._schema_cache_data = snapshot
        self._schema_cache_timestamp = cached_at
        return copy.deepcopy(snapshot)

    def _load_schema_cache_from_disk(self) -> Optional[Dict[str, Any]]:
        if not self.schema_cache_enabled:
            return None
        try:
            if not self.schema_cache_path.exists():
                return None
            with self.schema_cache_path.open("r", encoding="utf-8") as f:
                snapshot = json.load(f)
            return snapshot
        except Exception as exc:
            self.logger.warning(f"Failed to load schema cache: {exc}")
            return None

    def _save_schema_cache_to_disk(self, snapshot: Dict[str, Any]) -> None:
        if not self.schema_cache_enabled:
            return
        try:
            self.schema_cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.schema_cache_path.open("w", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            self.logger.warning(f"Failed to save schema cache: {exc}")

    def _build_schema_snapshot(
        self,
        table_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        schema_name = self.default_schema
        source_tables = table_names or self.get_usable_table_names()
        normalized_tables = []
        for name in source_tables:
            schema, plain_name = self._split_table_identifier(name)
            if schema != self.default_schema:
                continue
            normalized_tables.append(plain_name)

        spatial_entries = self._query_spatial_tables_raw(schema_name)
        spatial_map = {entry["table_name"]: entry for entry in spatial_entries}
        index_map = self._query_indexes_by_schema(schema_name)

        snapshot = {
            "tables": {},
            "spatial_tables": {},
            "database_info": self.get_database_info(),
            "cached_at": time.time(),
        }

        for table in normalized_tables:
            columns = self.get_table_columns(table)
            primary_keys = self.get_primary_keys(table)
            foreign_keys = self.get_foreign_keys(table)
            constraints = self.get_table_constraints(table)

            table_info = {
                "columns": [
                    {
                        "name": col["column_name"],
                        "type": col["data_type"],
                        "nullable": col["is_nullable"] == "YES",
                        "default": col["column_default"],
                        "max_length": col["character_maximum_length"],
                        "is_primary_key": col["column_name"] in primary_keys,
                    }
                    for col in columns
                ],
                "primary_keys": primary_keys,
                "foreign_keys": [
                    {
                        "column": fk["column_name"],
                        "references_table": fk["foreign_table_name"],
                        "references_column": fk["foreign_column_name"],
                    }
                    for fk in foreign_keys
                ],
                "constraints": [
                    {
                        "name": c["constraint_name"],
                        "type": c["constraint_type"],
                    }
                    for c in constraints
                ],
            }

            spatial_entry = spatial_map.get(table)
            if spatial_entry:
                spatial_indexes = [
                    idx
                    for idx in index_map.get(table, [])
                    if idx.get("index_type") in self.SPATIAL_INDEX_TYPES
                ]
                table_info.update(
                    {
                        "spatial_column": spatial_entry.get("geometry_column"),
                        "geometry_type": spatial_entry.get("geometry_type"),
                        "srid": spatial_entry.get("srid"),
                    }
                )
                table_info["spatial_indexes"] = spatial_indexes
                snapshot["spatial_tables"][table] = {
                    "table_name": table,
                    "schema_name": spatial_entry.get("schema_name"),
                    "geometry_column": spatial_entry.get("geometry_column"),
                    "geometry_type": spatial_entry.get("geometry_type"),
                    "srid": spatial_entry.get("srid"),
                    "coord_dimension": spatial_entry.get("coord_dimension"),
                    "spatial_indexes": spatial_indexes,
                }

            snapshot["tables"][table] = table_info

        return snapshot

    def _query_spatial_tables_raw(self, schema_name: str) -> List[Dict[str, Any]]:
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        f_table_schema AS schema_name,
                        f_table_name AS table_name,
                        f_geometry_column AS geometry_column,
                        type AS geometry_type,
                        srid,
                        coord_dimension
                    FROM geometry_columns
                    WHERE f_table_schema = %s
                    ORDER BY f_table_name;
                    """,
                    (schema_name,),
                )
                return cursor.fetchall()
        except Exception as exc:
            self.logger.error(f"Failed to query spatial tables: {exc}")
            return []

    def _query_indexes_by_schema(self, schema_name: str) -> Dict[str, List[Dict[str, Any]]]:
        indexes: Dict[str, List[Dict[str, Any]]] = {}
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        tbl.relname AS table_name,
                        idx.relname AS index_name,
                        am.amname AS index_type,
                        pg_get_indexdef(idx.oid) AS index_def
                    FROM pg_index ind
                    JOIN pg_class idx ON idx.oid = ind.indexrelid
                    JOIN pg_class tbl ON tbl.oid = ind.indrelid
                    JOIN pg_namespace ns ON ns.oid = tbl.relnamespace
                    JOIN pg_am am ON am.oid = idx.relam
                    WHERE ns.nspname = %s;
                    """,
                    (schema_name,),
                )
                for row in cursor.fetchall():
                    table = row.get("table_name")
                    if not table:
                        continue
                    indexes.setdefault(table, []).append(
                        {
                            "indexname": row.get("index_name"),
                            "indexdef": row.get("index_def"),
                            "index_type": row.get("index_type"),
                        }
                    )
        except Exception as exc:
            self.logger.error(f"Failed to query index metadata: {exc}")
        return indexes

    def _filter_schema_snapshot(
        self,
        snapshot: Dict[str, Any],
        table_names: List[str],
    ) -> Dict[str, Any]:
        filtered_tables = {}
        filtered_spatial = {}
        for name in table_names:
            table = self._normalize_table_name(name)
            if table in snapshot.get("tables", {}):
                filtered_tables[table] = copy.deepcopy(snapshot["tables"][table])
            if table in snapshot.get("spatial_tables", {}):
                filtered_spatial[table] = copy.deepcopy(snapshot["spatial_tables"][table])

        return {
            "tables": filtered_tables,
            "spatial_tables": filtered_spatial,
            "database_info": snapshot.get("database_info", {}),
            "cached_at": snapshot.get("cached_at"),
        }

    def _normalize_table_name(self, table_name: str) -> str:
        return table_name.split(".")[-1].strip('"')

    def _split_table_identifier(self, table_name: str) -> Tuple[str, str]:
        if "." in table_name:
            schema, name = table_name.split(".", 1)
            return schema.strip('"'), name.strip('"')
        return self.default_schema, table_name.strip('"')

    def _is_cache_expired(self, cached_at: float) -> bool:
        if self.schema_cache_ttl <= 0:
            return False
        return (time.time() - cached_at) > self.schema_cache_ttl
    def check_spatial_function_availability(self) -> Dict[str, bool]:
        """
        检查常用空间函数的可用性

        Returns:
            空间函数可用性字典
        """
        spatial_functions = [
            "ST_Intersects", "ST_Contains", "ST_Within", "ST_Distance",
            "ST_Buffer", "ST_Union", "ST_Transform", "ST_AsGeoJSON",
            "ST_MakePoint", "ST_SetSRID", "ST_DWithin"
        ]

        availability = {}

        try:
            with self.raw_connection.cursor() as cursor:
                for func in spatial_functions:
                    try:
                        # 测试函数是否可用
                        test_query = f"SELECT {func} IS NOT NULL"
                        cursor.execute(test_query)
                        availability[func] = True
                    except Exception:
                        availability[func] = False

        except Exception as e:
            self.logger.error(f"Failed to check spatial function availability: {e}")
            availability = {func: False for func in spatial_functions}

        return availability

    def get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库基本信息

        Returns:
            数据库信息字典
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # PostgreSQL版本
                cursor.execute("SELECT version() as pg_version")
                pg_version = cursor.fetchone()

                # PostGIS版本
                postgis_version = None
                try:
                    cursor.execute("SELECT PostGIS_Version() as postgis_version")
                    postgis_version = cursor.fetchone()
                except:
                    pass

                # 数据库大小
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size
                """)
                db_size = cursor.fetchone()

                # 表数量
                cursor.execute("""
                    SELECT COUNT(*) as table_count
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)
                table_count = cursor.fetchone()

                # 空间表数量
                cursor.execute("""
                    SELECT COUNT(*) as spatial_table_count
                    FROM geometry_columns
                    WHERE f_table_schema = 'public'
                """)
                spatial_table_count = cursor.fetchone()

                return {
                    "pg_version": pg_version["pg_version"] if pg_version else "Unknown",
                    "postgis_version": postgis_version["postgis_version"] if postgis_version else "Not installed",
                    "database_size": db_size["db_size"] if db_size else "Unknown",
                    "table_count": table_count["table_count"] if table_count else 0,
                    "spatial_table_count": spatial_table_count["spatial_table_count"] if spatial_table_count else 0,
                    "connection_string": self._mask_connection_string()
                }

        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}")
            return {
                "error": str(e)
            }

    def _mask_connection_string(self) -> str:
        """脱敏数据库连接字符串"""
        if "@" in self.connection_string:
            user_part, host_part = self.connection_string.split("@")
            if ":" in user_part:
                protocol_user = user_part.split(":")[0:2]
                return f"{protocol_user[0]}:{protocol_user[1]}:****@{host_part}"
        return self.connection_string

    def get_table_columns(self, table_name: str) -> Sequence[Dict[str, Any]]:
        """
        获取表的所有列信息

        Args:
            table_name: 表名

        Returns:
            列信息列表
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        column_name,
                        data_type,
                        character_maximum_length,
                        is_nullable,
                        column_default,
                        ordinal_position
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    ORDER BY ordinal_position;
                """, (table_name,))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Failed to get columns for table {table_name}: {e}")
            return []

    def get_primary_keys(self, table_name: str) -> List[str]:
        """
        获取表的主键列

        Args:
            table_name: 表名

        Returns:
            主键列名列表
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT a.attname as column_name
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid
                        AND a.attnum = ANY(i.indkey)
                    WHERE i.indrelid = %s::regclass
                    AND i.indisprimary;
                """, (table_name,))
                results = cursor.fetchall()
                return [row['column_name'] for row in results]
        except Exception as e:
            self.logger.error(f"Failed to get primary keys for table {table_name}: {e}")
            return []

    def get_foreign_keys(self, table_name: str) -> Sequence[Dict[str, Any]]:
        """
        获取表的外键约束

        Args:
            table_name: 表名

        Returns:
            外键信息列表
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        tc.constraint_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
                    AND tc.table_name = %s;
                """, (table_name,))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Failed to get foreign keys for table {table_name}: {e}")
            return []

    def get_table_constraints(self, table_name: str) -> Sequence[Dict[str, Any]]:
        """
        获取表的所有约束

        Args:
            table_name: 表名

        Returns:
            约束信息列表
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        constraint_name,
                        constraint_type
                    FROM information_schema.table_constraints
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    ORDER BY constraint_type;
                """, (table_name,))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Failed to get constraints for table {table_name}: {e}")
            return []

    
    def close(self) -> None:
        """关闭数据库连接，释放资源"""
        # 关闭原始psycopg2连接
        if self.raw_connection:
            try:
                self.raw_connection.close()
                self.logger.info("✓ Raw connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing raw connection: {e}")
            finally:
                self.raw_connection = None

        # 关闭SQLDatabase连接
        if self.db:
            try:
                if hasattr(self.db, '_engine') and self.db._engine:
                    self.db._engine.dispose()
                    self.logger.info("✓ SQLDatabase connection closed")
            except Exception as e:
                self.logger.warning(f"Error closing SQLDatabase: {e}")
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
            pass


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # 创建数据库连接
        print("\n=== 测试数据库连接 ===")
        with DatabaseConnector() as db:
            # 获取数据库信息
            print("\n数据库信息:")
            info = db.get_database_info()
            for key, value in info.items():
                print(f"  {key}: {value}")

            # 获取表列表
            print("\n可用表:")
            tables = db.get_usable_table_names()
            for table in tables[:5]:  # 只显示前5个
                print(f"  - {table}")

            # 获取空间表
            print("\n空间表:")
            spatial_tables = db.get_spatial_tables()
            for table in spatial_tables:
                print(f"  - {table['table_name']} ({table['geometry_type']})")

            # 测试简单查询
            print("\n测试查询:")
            result = db.execute_query("SELECT version()")
            print(f"  PostgreSQL版本: {result}")

    except Exception as e:
        print(f"Error: {e}")



