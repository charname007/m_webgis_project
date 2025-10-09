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
            self.logger.error(
                f"✗ DatabaseConnector initialization failed: {e}")
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
            self.logger.info(
                f"✓ SQLDatabase connected (dialect: {self.db.dialect})")

            # 建立原始psycopg2连接（用于空间查询）
            self.raw_connection = psycopg2.connect(
                self.connection_string,
                connect_timeout=settings.DB_CONNECT_TIMEOUT
            )
            # ✅ 设置为autocommit模式，避免事务被阻塞
            self.raw_connection.autocommit = True
            self.logger.info(
                "✓ Raw psycopg2 connection established (autocommit mode)")

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
        snapshot = self.get_detailed_schema(
            use_cache=use_cache, force_refresh=force_refresh)
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
            cached = self._get_cached_schema_snapshot(
                use_cache=use_cache, force_refresh=force_refresh)
            if cached is not None:
                return cached

            snapshot = self._build_schema_snapshot()
            if self.schema_cache_enabled:
                self._save_schema_cache_to_disk(snapshot)
                self._schema_cache_data = snapshot
                self._schema_cache_timestamp = snapshot.get(
                    "cached_at", time.time())
            return snapshot

        # 请求指定表
        if use_cache and not force_refresh:
            base_snapshot = self._get_cached_schema_snapshot(
                use_cache=True, force_refresh=False)
            if base_snapshot is not None:
                return self._filter_schema_snapshot(base_snapshot, normalized_names)

        return self._build_schema_snapshot(table_names=normalized_names)

    def refresh_schema_cache(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """手动刷新 schema 缓存，可选指定表。"""
        snapshot = self._build_schema_snapshot(table_names=table_names)
        if table_names is None and self.schema_cache_enabled:
            self._save_schema_cache_to_disk(snapshot)
            self._schema_cache_data = snapshot
            self._schema_cache_timestamp = snapshot.get(
                "cached_at", time.time())
        return snapshot

    def clear_schema_cache(self) -> None:
        """清空 schema 缓存（内存+文件）。"""
        self._schema_cache_data = None
        self._schema_cache_timestamp = None
        if self.schema_cache_path.exists():
            try:
                self.schema_cache_path.unlink()
                self.logger.info(
                    f"Schema cache file removed: {self.schema_cache_path}")
            except Exception as exc:
                self.logger.warning(
                    f"Failed to remove schema cache file: {exc}")

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
                filtered_tables[table] = copy.deepcopy(
                    snapshot["tables"][table])
            if table in snapshot.get("spatial_tables", {}):
                filtered_spatial[table] = copy.deepcopy(
                    snapshot["spatial_tables"][table])

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
            self.logger.error(
                f"Failed to check spatial function availability: {e}")
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
                    cursor.execute(
                        "SELECT PostGIS_Version() as postgis_version")
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
            self.logger.error(
                f"Failed to get columns for table {table_name}: {e}")
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
            self.logger.error(
                f"Failed to get primary keys for table {table_name}: {e}")
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
            self.logger.error(
                f"Failed to get foreign keys for table {table_name}: {e}")
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
            self.logger.error(
                f"Failed to get constraints for table {table_name}: {e}")
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

    # ==================== Memory和Cache管理方法 ====================

    def save_conversation_history(
        self,
        session_id: str,
        query_text: str,
        query_intent: Optional[Dict[str, Any]] = None,
        sql_query: Optional[str] = None,
        result_data: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
        status: str = "success"
    ) -> int:
        """
        保存会话历史记录

        Args:
            session_id: 会话ID
            query_text: 查询文本
            query_intent: 查询意图信息
            sql_query: 执行的SQL查询
            result_data: 结果数据
            execution_time: 执行时间
            status: 状态（success/error）

        Returns:
            插入记录的ID
        """
        try:
            with self.raw_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO conversation_history
                    (session_id, query_text, query_intent,
                     sql_query, result_data, execution_time, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    session_id,
                    query_text,
                    json.dumps(query_intent) if query_intent else None,
                    sql_query,
                    json.dumps(result_data) if result_data else None,
                    execution_time,
                    status
                ))
                record_id = cursor.fetchone()[0]
                self.logger.debug(f"会话历史记录已保存，ID: {record_id}")
                return record_id
        except Exception as e:
            self.logger.error(f"保存会话历史记录失败: {e}")
            raise

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> Sequence[Dict[str, Any]]:
        """
        获取会话历史记录

        Args:
            session_id: 会话ID
            limit: 返回记录数量
            offset: 偏移量

        Returns:
            会话历史记录列表
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT
                        id, session_id, query_text, query_intent, sql_query,
                        result_data, execution_time, status, created_at, updated_at
                    FROM conversation_history
                    WHERE session_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (session_id, limit, offset))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"获取会话历史记录失败: {e}")
            return []

    def save_ai_context(
        self,
        session_id: str,
        context_data: Dict[str, Any],
        context_type: str = "conversation"
    ) -> int:
        """
        保存AI上下文数据

        Args:
            session_id: 会话ID
            context_data: 上下文数据
            context_type: 上下文类型

        Returns:
            插入记录的ID
        """
        try:
            with self.raw_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO ai_context
                    (session_id, context_data, context_type)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (
                    session_id,
                    json.dumps(context_data),
                    context_type
                ))
                record_id = cursor.fetchone()[0]
                self.logger.debug(f"AI上下文已保存，ID: {record_id}")
                return record_id
        except Exception as e:
            self.logger.error(f"保存AI上下文失败: {e}")
            raise

    def get_ai_context(
        self,
        session_id: str,
        context_type: Optional[str] = None
    ) -> Sequence[Dict[str, Any]]:
        """
        获取AI上下文数据

        Args:
            session_id: 会话ID
            context_type: 上下文类型（可选）

        Returns:
            AI上下文记录列表
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                if context_type:
                    cursor.execute("""
                        SELECT id, session_id, context_data, context_type, created_at, updated_at
                        FROM ai_context
                        WHERE session_id = %s AND context_type = %s
                        ORDER BY created_at DESC
                    """, (session_id, context_type))
                else:
                    cursor.execute("""
                        SELECT id, session_id, context_data, context_type, created_at, updated_at
                        FROM ai_context
                        WHERE session_id = %s
                        ORDER BY created_at DESC
                    """, (session_id,))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"获取AI上下文失败: {e}")
            return []

    def save_cache_data(
        self,
        cache_key: str,
        cache_value: Dict[str, Any],
        cache_type: str = "general",
        ttl_seconds: Optional[int] = None
    ) -> int:
        """
        保存缓存数据

        Args:
            cache_key: 缓存键
            cache_value: 缓存值
            cache_type: 缓存类型
            ttl_seconds: 生存时间（秒）

        Returns:
            插入记录的ID
        """
        try:
            expires_at = None
            if ttl_seconds:
                from datetime import datetime, timedelta
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

            with self.raw_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO cache_data
                    (cache_key, cache_value, cache_type, expires_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (cache_key)
                    DO UPDATE SET
                        cache_value = EXCLUDED.cache_value,
                        cache_type = EXCLUDED.cache_type,
                        expires_at = EXCLUDED.expires_at,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    cache_key,
                    json.dumps(cache_value),
                    cache_type,
                    expires_at
                ))
                record_id = cursor.fetchone()[0]
                self.logger.debug(f"缓存数据已保存，键: {cache_key}")
                return record_id
        except Exception as e:
            self.logger.error(f"保存缓存数据失败: {e}")
            raise

    def get_cache_data(
        self,
        cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存数据

        Args:
            cache_key: 缓存键

        Returns:
            缓存数据，如果不存在或已过期则返回None
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, cache_key, cache_value, cache_type, expires_at, created_at, updated_at
                    FROM cache_data
                    WHERE cache_key = %s AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, (cache_key,))
                result = cursor.fetchone()
                if result:
                    return dict(result)
                return None
        except Exception as e:
            self.logger.error(f"获取缓存数据失败: {e}")
            return None

    def delete_cache_data(self, cache_key: str) -> bool:
        """
        删除缓存数据

        Args:
            cache_key: 缓存键

        Returns:
            是否成功删除
        """
        try:
            with self.raw_connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM cache_data WHERE cache_key = %s", (cache_key,))
                deleted = cursor.rowcount > 0
                if deleted:
                    self.logger.debug(f"缓存数据已删除，键: {cache_key}")
                return deleted
        except Exception as e:
            self.logger.error(f"删除缓存数据失败: {e}")
            return False

    def cleanup_expired_cache(self) -> int:
        """
        清理过期的缓存数据

        Returns:
            删除的记录数量
        """
        try:
            with self.raw_connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM cache_data WHERE expires_at <= CURRENT_TIMESTAMP")
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    self.logger.info(f"已清理 {deleted_count} 条过期缓存记录")
                return deleted_count
        except Exception as e:
            self.logger.error(f"清理过期缓存失败: {e}")
            return 0

    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话统计信息

        Args:
            session_id: 会话ID

        Returns:
            会话统计信息
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # 查询历史记录统计
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_queries,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_queries,
                        COUNT(CASE WHEN status = 'error' THEN 1 END) as failed_queries,
                        AVG(execution_time) as avg_execution_time,
                        MIN(created_at) as first_query_time,
                        MAX(created_at) as last_query_time
                    FROM conversation_history
                    WHERE session_id = %s
                """, (session_id,))
                stats = cursor.fetchone()

                # 查询上下文统计
                cursor.execute("""
                    SELECT
                        COUNT(*) as context_count,
                        COUNT(DISTINCT context_type) as context_types
                    FROM ai_context
                    WHERE session_id = %s
                """, (session_id,))
                context_stats = cursor.fetchone()

                return {
                    "session_id": session_id,
                    "query_statistics": dict(stats) if stats else {},
                    "context_statistics": dict(context_stats) if context_stats else {}
                }
        except Exception as e:
            self.logger.error(f"获取会话统计信息失败: {e}")
            return {"session_id": session_id, "error": str(e)}

    def __del__(self):
        """析构函数中关闭连接"""
        try:
            self.close()
        except Exception:
            pass

    def get_all_query_caches(self) -> Sequence[Dict[str, Any]]:
        """
        获取所有查询结果缓存
        
        Returns:
            所有查询缓存数据列表
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, cache_key, query_text, result_data, response_time,
                           hit_count, expires_at, created_at, updated_at
                    FROM query_cache
                    WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP
                    ORDER BY hit_count DESC, created_at DESC
                """)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"获取所有查询缓存失败: {e}")
            return []

    # ==================== 分离缓存存储方法 ====================
    def save_query_cache(
        self,
        cache_key: str,
        query_text: str,
        result_data: Dict[str, Any],
        response_time: Optional[float] = None,
        ttl_seconds: Optional[int] = None
    ) -> int:
        """
        保存查询结果缓存到 query_cache 表

        Args:
            cache_key: 缓存键
            query_text: 查询文本
            result_data: 结果数据
            response_time: 响应时间
            ttl_seconds: 生存时间（秒）

        Returns:
            插入记录的ID
        """
        try:
            expires_at = None
            if ttl_seconds:
                from datetime import datetime, timedelta
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

            # ✅ 验证和转换 response_time 参数
            validated_response_time = None
            if response_time is not None:
                try:
                    # 确保 response_time 是浮点数
                    if isinstance(response_time, str):
                        validated_response_time = float(response_time)
                    else:
                        validated_response_time = float(response_time)
                except (ValueError, TypeError) as e:
                    self.logger.warning(
                        f"Invalid response_time value: {response_time}, type: {type(response_time)}. Setting to None.")
                    validated_response_time = None

            with self.raw_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO query_cache 
                    (cache_key, query_text, result_data, response_time, expires_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (cache_key) 
                    DO UPDATE SET 
                        query_text = EXCLUDED.query_text,
                        result_data = EXCLUDED.result_data,
                        response_time = EXCLUDED.response_time,
                        expires_at = EXCLUDED.expires_at,
                        hit_count = query_cache.hit_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    cache_key,
                    query_text,
                    json.dumps(result_data, ensure_ascii=False),
                    validated_response_time,
                    expires_at
                ))
                record_id = cursor.fetchone()[0]
                self.logger.debug(f"查询结果缓存已保存，键: {cache_key}")
                return record_id
        except Exception as e:
            self.logger.error(f"保存查询结果缓存失败: {e}")
            raise

    def get_query_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        从 query_cache 表获取查询结果缓存

        Args:
            cache_key: 缓存键

        Returns:
            缓存数据，如果不存在或已过期则返回None
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, cache_key, query_text, result_data, response_time, 
                           hit_count, expires_at, created_at, updated_at
                    FROM query_cache 
                    WHERE cache_key = %s AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """, (cache_key,))
                result = cursor.fetchone()
                if result:
                    # 更新命中次数
                    cursor.execute("""
                        UPDATE query_cache 
                        SET hit_count = hit_count + 1, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (result['id'],))
                    return dict(result)
                return None
        except Exception as e:
            self.logger.error(f"获取查询结果缓存失败: {e}")
            return None

    def delete_query_cache(self, cache_key: str) -> bool:
        """
        删除查询结果缓存

        Args:
            cache_key: 缓存键

        Returns:
            是否成功删除
        """
        try:
            with self.raw_connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM query_cache WHERE cache_key = %s", (cache_key,))
                deleted = cursor.rowcount > 0
                if deleted:
                    self.logger.debug(f"查询结果缓存已删除，键: {cache_key}")
                return deleted
        except Exception as e:
            self.logger.error(f"删除查询结果缓存失败: {e}")
            return False

    def save_pattern_cache(
        self,
        pattern_key: str,
        query_template: str,
        sql_template: str,
        response_time: Optional[float] = None,
        result_count: int = 1
    ) -> int:
        """
        保存模式学习缓存到 pattern_cache 表

        Args:
            pattern_key: 模式键
            query_template: 查询模板
            sql_template: SQL模板
            response_time: 响应时间
            result_count: 结果数量

        Returns:
            插入记录的ID
        """
        try:
            with self.raw_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO pattern_cache 
                    (pattern_key, query_template, sql_template, success_count, 
                     total_response_time, avg_response_time, last_used)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (pattern_key) 
                    DO UPDATE SET 
                        query_template = EXCLUDED.query_template,
                        sql_template = EXCLUDED.sql_template,
                        success_count = pattern_cache.success_count + 1,
                        total_response_time = pattern_cache.total_response_time + EXCLUDED.total_response_time,
                        avg_response_time = (pattern_cache.total_response_time + EXCLUDED.total_response_time) / (pattern_cache.success_count + 1),
                        last_used = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    pattern_key,
                    query_template,
                    sql_template,
                    result_count,
                    response_time or 0,
                    response_time or 0
                ))
                record_id = cursor.fetchone()[0]
                self.logger.debug(f"模式学习缓存已保存，键: {pattern_key}")
                return record_id
        except Exception as e:
            self.logger.error(f"保存模式学习缓存失败: {e}")
            raise

    def get_pattern_cache(self, pattern_key: str) -> Optional[Dict[str, Any]]:
        """
        从 pattern_cache 表获取模式学习缓存

        Args:
            pattern_key: 模式键

        Returns:
            模式缓存数据，如果不存在则返回None
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, pattern_key, query_template, sql_template, 
                           success_count, total_response_time, avg_response_time,
                           last_used, created_at, updated_at
                    FROM pattern_cache 
                    WHERE pattern_key = %s
                """, (pattern_key,))
                result = cursor.fetchone()
                if result:
                    # 更新最后使用时间
                    cursor.execute("""
                        UPDATE pattern_cache 
                        SET last_used = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (result['id'],))
                    return dict(result)
                return None
        except Exception as e:
            self.logger.error(f"获取模式学习缓存失败: {e}")
            return None

    def get_all_patterns(self) -> Sequence[Dict[str, Any]]:
        """
        获取所有模式学习缓存

        Returns:
            所有模式缓存数据列表
        """
        try:
            with self.raw_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, pattern_key, query_template, sql_template, 
                           success_count, total_response_time, avg_response_time,
                           last_used, created_at, updated_at
                    FROM pattern_cache 
                    ORDER BY success_count DESC, last_used DESC
                """)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"获取所有模式缓存失败: {e}")
            return []

    def delete_pattern_cache(self, pattern_key: str) -> bool:
        """
        删除模式学习缓存

        Args:
            pattern_key: 模式键

        Returns:
            是否成功删除
        """
        try:
            with self.raw_connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM pattern_cache WHERE pattern_key = %s", (pattern_key,))
                deleted = cursor.rowcount > 0
                if deleted:
                    self.logger.debug(f"模式学习缓存已删除，键: {pattern_key}")
                return deleted
        except Exception as e:
            self.logger.error(f"删除模式学习缓存失败: {e}")
            return False

    def cleanup_expired_query_cache(self) -> int:
        """
        清理过期的查询结果缓存

        Returns:
            删除的记录数量
        """
        try:
            with self.raw_connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM query_cache WHERE expires_at <= CURRENT_TIMESTAMP")
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    self.logger.info(f"已清理 {deleted_count} 条过期查询结果缓存")
                return deleted_count
        except Exception as e:
            self.logger.error(f"清理过期查询结果缓存失败: {e}")
            return 0

    def cleanup_old_patterns(self, keep_count: int = 100) -> int:
        """
        清理旧的模式学习缓存

        Args:
            keep_count: 要保留的模式数量

        Returns:
            删除的记录数量
        """
        try:
            with self.raw_connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM pattern_cache 
                    WHERE id NOT IN (
                        SELECT id FROM pattern_cache 
                        ORDER BY success_count DESC, last_used DESC 
                        LIMIT %s
                    )
                """, (keep_count,))
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    self.logger.info(f"已清理 {deleted_count} 条旧模式缓存")
                return deleted_count
        except Exception as e:
            self.logger.error(f"清理旧模式缓存失败: {e}")
            return 0


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
