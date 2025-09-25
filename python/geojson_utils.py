import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text, create_engine
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_AsGeoJSON

class GeoJSONGenerator:
    """GeoJSON生成器，用于将数据库中的空间数据转换为GeoJSON格式"""
    
    def __init__(self, connection_string: str):
        """
        初始化GeoJSON生成器
        
        Args:
            connection_string: 数据库连接字符串
        """
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)
        self.logger = logging.getLogger(__name__)
    
    def get_spatial_tables(self) -> List[Dict[str, Any]]:
        """
        获取包含空间数据的表信息
        
        Returns:
            空间表信息列表
        """
        query = text("""
            SELECT 
                f_table_name as table_name,
                f_geometry_column as geometry_column,
                type as geometry_type,
                srid
            FROM geometry_columns
            WHERE f_table_schema = 'public'
            ORDER BY f_table_name
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query)
            tables = []
            for row in result:
                tables.append({
                    'table_name': row.table_name,
                    'geometry_column': row.geometry_column,
                    'geometry_type': row.geometry_type,
                    'srid': row.srid
                })
        
        return tables
    
    def table_to_geojson(self, table_name: str, geometry_column: str = 'geom', 
                        where_clause: str = "", limit: int = 1000) -> Dict[str, Any]:
        """
        将数据库表转换为GeoJSON格式
        
        Args:
            table_name: 表名
            geometry_column: 几何列名
            where_clause: WHERE条件子句
            limit: 限制返回的记录数
            
        Returns:
            GeoJSON格式的数据
        """
        # 构建查询
        where_sql = f"WHERE {where_clause}" if where_clause else ""
        limit_sql = f"LIMIT {limit}" if limit else ""
        
        query = text(f"""
            SELECT 
                json_build_object(
                    'type', 'FeatureCollection',
                    'features', COALESCE(json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'geometry', ST_AsGeoJSON({geometry_column})::json,
                            'properties', to_jsonb(row) - '{geometry_column}'
                        )
                    ), '[]'::json)
                ) as geojson
            FROM (
                SELECT * FROM {table_name} 
                {where_sql} 
                {limit_sql}
            ) as row
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query)
                geojson_data = result.scalar()
                # 如果结果是字符串，则解析为JSON；如果已经是字典，则直接返回
                if isinstance(geojson_data, str):
                    return json.loads(geojson_data) if geojson_data else self._empty_geojson()
                elif isinstance(geojson_data, dict):
                    return geojson_data
                else:
                    return self._empty_geojson()
                
        except Exception as e:
            self.logger.error(f"生成GeoJSON失败: {e}")
            return self._empty_geojson()
    
    def get_features_by_geometry_type(self, table_name: str, geometry_column: str = 'geom',
                                    geometry_type: str = "POINT", where_clause: str = "",
                                    limit: int = 1000) -> Dict[str, Any]:
        """
        按几何类型获取要素
        
        Args:
            table_name: 表名
            geometry_column: 几何列名
            geometry_type: 几何类型 (POINT, LINESTRING, POLYGON等)
            where_clause: WHERE条件子句
            limit: 限制返回的记录数
            
        Returns:
            指定几何类型的GeoJSON数据
        """
        # 构建WHERE条件 - 使用ILIKE进行不区分大小写的比较
        type_condition = f"ST_GeometryType({geometry_column}) ILIKE 'ST_{geometry_type}'"
        if where_clause:
            full_where = f"{where_clause} AND {type_condition}"
        else:
            full_where = type_condition
        
        return self.table_to_geojson(table_name, geometry_column, full_where, limit)
    
    def get_all_geometry_types(self, table_name: str, geometry_column: str = 'geom') -> Dict[str, Dict[str, Any]]:
        """
        获取表中所有几何类型及其统计信息
        
        Args:
            table_name: 表名
            geometry_column: 几何列名
            
        Returns:
            几何类型统计信息
        """
        query = text(f"""
            SELECT 
                ST_GeometryType({geometry_column}) as geometry_type,
                COUNT(*) as count
            FROM {table_name}
            WHERE {geometry_column} IS NOT NULL
            GROUP BY ST_GeometryType({geometry_column})
            ORDER BY count DESC
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query)
            types_info = {}
            for row in result:
                types_info[row.geometry_type] = {'count': row.count}
            return types_info
    
    def _empty_geojson(self) -> Dict[str, Any]:
        """返回空的GeoJSON结构"""
        return {
            "type": "FeatureCollection",
            "features": []
        }
    
    def query_to_geojson(self, sql_query: str) -> Dict[str, Any]:
        """
        执行自定义SQL查询并返回GeoJSON
        
        Args:
            sql_query: 包含几何列的SQL查询
            
        Returns:
            GeoJSON格式的查询结果
        """
        try:
            # 首先执行原始查询来获取结果
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                rows = result.fetchall()
                
                # 如果没有结果，返回空的GeoJSON
                if not rows:
                    return self._empty_geojson()
                
                # 获取列名
                columns = result.keys()
                
                # 查找几何列（假设几何列包含'geom'或'geometry'）
                geometry_column = None
                for col in columns:
                    if 'geom' in col.lower() or 'geometry' in col.lower():
                        geometry_column = col
                        break
                
                # 如果没有找到几何列，返回空的GeoJSON
                if not geometry_column:
                    self.logger.warning(f"在查询结果中未找到几何列。列名: {list(columns)}")
                    return self._empty_geojson()
                
                # 构建GeoJSON特征
                features = []
                for row in rows:
                    # 将行转换为字典
                    row_dict = dict(zip(columns, row))
                    
                    # 提取几何数据
                    geometry_data = row_dict.get(geometry_column)
                    
                    # 如果几何数据为空，跳过该记录
                    if not geometry_data:
                        continue
                    
                    # 构建属性（排除几何列）
                    properties = {k: v for k, v in row_dict.items() if k != geometry_column}
                    
                    # 构建特征
                    feature = {
                        'type': 'Feature',
                        'geometry': self._convert_geometry_to_geojson(geometry_data),
                        'properties': properties
                    }
                    features.append(feature)
                
                # 构建完整的GeoJSON
                geojson = {
                    'type': 'FeatureCollection',
                    'features': features
                }
                
                return geojson
                
        except Exception as e:
            self.logger.error(f"查询生成GeoJSON失败: {e}")
            return self._empty_geojson()
    
    def _convert_geometry_to_geojson(self, geometry_data) -> Dict[str, Any]:
        """
        将几何数据转换为GeoJSON格式
        
        Args:
            geometry_data: 几何数据（WKB格式或其他格式）
            
        Returns:
            GeoJSON几何对象
        """
        try:
            # 如果已经是字典格式，直接返回
            if isinstance(geometry_data, dict):
                return geometry_data
            
            # 如果是WKB格式的字符串，使用PostGIS函数转换
            if isinstance(geometry_data, str) and geometry_data.startswith('0101'):
                # 使用ST_AsGeoJSON函数转换WKB格式
                query = text(f"SELECT ST_AsGeoJSON(ST_GeomFromEWKB('\\x{geometry_data}')) as geojson")
                with self.engine.connect() as conn:
                    result = conn.execute(query)
                    geojson_result = result.scalar()
                    if geojson_result:
                        # 处理不同类型的返回结果
                        if isinstance(geojson_result, str):
                            try:
                                return json.loads(geojson_result)
                            except json.JSONDecodeError:
                                # 如果解析失败，返回默认几何
                                return {"type": "Point", "coordinates": [0, 0]}
                        elif isinstance(geojson_result, dict):
                            return geojson_result
                        else:
                            # 其他类型，返回默认几何
                            return {"type": "Point", "coordinates": [0, 0]}
            
            # 如果是其他格式，尝试直接解析
            if isinstance(geometry_data, str):
                try:
                    # 尝试解析为JSON
                    return json.loads(geometry_data)
                except:
                    pass
            
            # 如果是其他格式，返回空几何
            return {"type": "Point", "coordinates": [0, 0]}
            
        except Exception as e:
            self.logger.error(f"几何数据转换失败: {e}")
            return {"type": "Point", "coordinates": [0, 0]}


# 使用示例
if __name__ == "__main__":
    # 测试GeoJSON生成器
    connection_string = "postgresql://sagasama:cznb6666@localhost:5432/WGP_db"
    generator = GeoJSONGenerator(connection_string)
    
    # 获取空间表信息
    spatial_tables = generator.get_spatial_tables()
    print("空间表信息:")
    for table in spatial_tables:
        print(f"- {table['table_name']}: {table['geometry_type']} (SRID: {table['srid']})")
    
    # 测试生成GeoJSON
    if spatial_tables:
        sample_table = spatial_tables[0]['table_name']
        geojson = generator.table_to_geojson(sample_table, limit=10)
        print(f"\n{sample_table}表的GeoJSON样本:")
        print(json.dumps(geojson, indent=2, ensure_ascii=False))
