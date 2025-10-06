"""
SchemaFetcher处理器模块 - Sight Server
负责获取和格式化数据库schema信息
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SchemaFetcher:
    """
    Schema获取器

    功能:
    - 获取数据库schema信息
    - 格式化为LLM友好的文本格式
    - 支持schema缓存
    - 压缩schema信息避免提示词过长
    """

    def __init__(self, db_connector):
        """
        初始化Schema获取器

        Args:
            db_connector: 数据库连接器实例
        """
        self.db_connector = db_connector
        self.logger = logger
        self._schema_cache: Optional[Dict[str, Any]] = None

    def fetch_schema(
        self,
        table_names: Optional[List[str]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取数据库schema

        Args:
            table_names: 要获取的表名列表。None表示获取所有表
            use_cache: 是否使用缓存

        Returns:
            Schema信息字典
        """
        try:
            # 检查缓存
            if use_cache and self._schema_cache:
                self.logger.info("Using cached schema")
                return self._schema_cache

            self.logger.info(f"Fetching schema for {len(table_names) if table_names else 'all'} tables...")

            # 获取详细schema
            schema = self.db_connector.get_detailed_schema(
                table_names=table_names,
                use_cache=use_cache,
                force_refresh=not use_cache,
            )

            # 缓存结果
            if use_cache:
                self._schema_cache = schema

            self.logger.info(f"✓ Fetched schema for {len(schema.get('tables', {}))} tables")
            return schema

        except Exception as e:
            self.logger.error(f"Failed to fetch schema: {e}")
            return {
                "error": str(e),
                "tables": {},
                "spatial_tables": {}
            }

    def format_schema_for_llm(
        self,
        schema: Dict[str, Any],
        include_constraints: bool = False,
        include_indexes: bool = False
    ) -> str:
        """
        将schema格式化为LLM友好的文本

        Args:
            schema: Schema字典
            include_constraints: 是否包含约束信息
            include_indexes: 是否包含索引信息

        Returns:
            格式化后的schema文本
        """
        try:
            lines = ["=== 数据库Schema信息 ===\n"]

            # 数据库信息
            db_info = schema.get("database_info", {})
            if db_info and "error" not in db_info:
                lines.append(f"数据库: PostgreSQL {db_info.get('pg_version', 'Unknown')}")
                lines.append(f"PostGIS: {db_info.get('postgis_version', 'Not installed')}")
                lines.append(f"表数量: {db_info.get('table_count', 0)}")
                lines.append(f"空间表数量: {db_info.get('spatial_table_count', 0)}\n")

            # 表结构
            tables = schema.get("tables", {})
            spatial_tables = schema.get("spatial_tables", {})

            if not tables:
                lines.append("未找到表信息")
                return "\n".join(lines)

            lines.append(f"--- 表结构 ({len(tables)}个表) ---\n")

            for table_name, table_info in tables.items():
                # 表名（标记空间表）
                is_spatial = table_name in spatial_tables
                spatial_mark = " [空间表]" if is_spatial else ""
                lines.append(f"表名: {table_name}{spatial_mark}")

                # 列信息
                columns = table_info.get("columns", [])
                if columns:
                    lines.append("  字段:")
                    for col in columns:
                        pk_mark = " [PK]" if col.get("is_primary_key") else ""
                        nullable = "NULL" if col.get("nullable") else "NOT NULL"
                        col_type = col["type"]
                        if col.get("max_length"):
                            col_type += f"({col['max_length']})"

                        lines.append(f"    - {col['name']}: {col_type} {nullable}{pk_mark}")

                # 空间列信息
                if is_spatial:
                    spatial_col = table_info.get("spatial_column")
                    geom_type = table_info.get("geometry_type")
                    srid = table_info.get("srid")
                    if spatial_col:
                        lines.append(f"  空间列: {spatial_col} ({geom_type}, SRID={srid})")

                # 主键
                primary_keys = table_info.get("primary_keys", [])
                if primary_keys:
                    lines.append(f"  主键: {', '.join(primary_keys)}")

                # 外键
                foreign_keys = table_info.get("foreign_keys", [])
                if foreign_keys:
                    lines.append("  外键:")
                    for fk in foreign_keys:
                        lines.append(
                            f"    - {fk['column']} → "
                            f"{fk['references_table']}.{fk['references_column']}"
                        )

                # 约束（可选）
                if include_constraints:
                    constraints = table_info.get("constraints", [])
                    if constraints:
                        lines.append(f"  约束: {len(constraints)}个")

                # 空间索引（可选）
                if include_indexes and is_spatial:
                    spatial_indexes = table_info.get("spatial_indexes", [])
                    if spatial_indexes:
                        lines.append(f"  空间索引: {len(spatial_indexes)}个")

                lines.append("")  # 空行分隔

            return "\n".join(lines)

        except Exception as e:
            self.logger.error(f"Failed to format schema: {e}")
            return f"Schema格式化失败: {str(e)}"

    def get_table_schema_summary(self, table_name: str) -> str:
        """
        获取单个表的schema摘要

        Args:
            table_name: 表名

        Returns:
            表schema摘要文本
        """
        try:
            schema = self.fetch_schema(table_names=[table_name])
            tables = schema.get("tables", {})

            if table_name not in tables:
                return f"未找到表 {table_name}"

            table_info = tables[table_name]
            columns = table_info.get("columns", [])

            lines = [f"表: {table_name}"]
            lines.append(f"字段: {', '.join([col['name'] for col in columns])}")

            # 主键
            pk = table_info.get("primary_keys", [])
            if pk:
                lines.append(f"主键: {', '.join(pk)}")

            # 空间列
            if "spatial_column" in table_info:
                lines.append(
                    f"空间列: {table_info['spatial_column']} "
                    f"({table_info.get('geometry_type')})"
                )

            return " | ".join(lines)

        except Exception as e:
            self.logger.error(f"Failed to get table schema summary: {e}")
            return f"获取表schema失败: {str(e)}"

    def clear_cache(self):
        """清除schema缓存"""
        self._schema_cache = None
        if hasattr(self.db_connector, "clear_schema_cache"):
            self.db_connector.clear_schema_cache()
        self.logger.info("Schema cache cleared")


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== SchemaFetcher 测试 ===\n")
    print("需要真实的 DatabaseConnector 实例才能完整测试")
    print()

    # 示例schema格式化
    sample_schema = {
        "tables": {
            "a_sight": {
                "columns": [
                    {"name": "id", "type": "integer", "nullable": False, "is_primary_key": True},
                    {"name": "name", "type": "character varying", "nullable": False, "max_length": 100},
                    {"name": "level", "type": "character varying", "nullable": True, "max_length": 10},
                ],
                "primary_keys": ["id"],
                "foreign_keys": []
            }
        },
        "spatial_tables": {},
        "database_info": {
            "pg_version": "PostgreSQL 14.0",
            "postgis_version": "3.2.0",
            "table_count": 1,
            "spatial_table_count": 0
        }
    }

    # 测试格式化
    from core.processors.schema_fetcher import SchemaFetcher

    class MockDBConnector:
        def get_detailed_schema(self, table_names=None):
            return sample_schema

    fetcher = SchemaFetcher(MockDBConnector())
    formatted = fetcher.format_schema_for_llm(sample_schema)
    print(formatted)
