"""
GeoJSON 工具类 - Sight Server
提供坐标系转换和 GeoJSON 生成功能
"""

import logging
import math
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


logger = logging.getLogger(__name__)


# ==================== 坐标系枚举 ====================

class CoordinateSystem(str, Enum):
    """坐标系统枚举"""
    WGS84 = "wgs84"     # WGS-84 (EPSG:4326) - GPS标准，国际通用
    GCJ02 = "gcj02"     # GCJ-02 - 国测局火星坐标系，高德/腾讯地图
    BD09 = "bd09"       # BD-09 - 百度坐标系，百度地图


# ==================== 坐标转换器 ====================

class CoordinateConverter:
    """
    坐标系转换器

    支持的转换：
    - WGS84 ↔ GCJ02
    - GCJ02 ↔ BD09
    - WGS84 ↔ BD09

    参考：
    - https://github.com/wandergis/coordtransform
    """

    # 椭球参数
    X_PI = 3.14159265358979324 * 3000.0 / 180.0
    PI = 3.1415926535897932384626
    A = 6378245.0  # 长半轴
    EE = 0.00669342162296594323  # 偏心率平方

    @classmethod
    def out_of_china(cls, lng: float, lat: float) -> bool:
        """
        判断是否在中国境外

        GCJ-02 坐标系只在中国境内使用，境外不进行偏移

        Args:
            lng: 经度
            lat: 纬度

        Returns:
            True 表示在中国境外
        """
        return not (73.66 < lng < 135.05 and 3.86 < lat < 53.55)

    @classmethod
    def transform_lat(cls, lng: float, lat: float) -> float:
        """计算纬度偏移量"""
        ret = (
            -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat
            + 0.1 * lng * lat + 0.2 * math.sqrt(abs(lng))
        )
        ret += (
            (20.0 * math.sin(6.0 * lng * cls.PI) + 20.0 * math.sin(2.0 * lng * cls.PI))
            * 2.0 / 3.0
        )
        ret += (
            (20.0 * math.sin(lat * cls.PI) + 40.0 * math.sin(lat / 3.0 * cls.PI))
            * 2.0 / 3.0
        )
        ret += (
            (160.0 * math.sin(lat / 12.0 * cls.PI) + 320.0 * math.sin(lat * cls.PI / 30.0))
            * 2.0 / 3.0
        )
        return ret

    @classmethod
    def transform_lng(cls, lng: float, lat: float) -> float:
        """计算经度偏移量"""
        ret = (
            300.0 + lng + 2.0 * lat + 0.1 * lng * lng
            + 0.1 * lng * lat + 0.1 * math.sqrt(abs(lng))
        )
        ret += (
            (20.0 * math.sin(6.0 * lng * cls.PI) + 20.0 * math.sin(2.0 * lng * cls.PI))
            * 2.0 / 3.0
        )
        ret += (
            (20.0 * math.sin(lng * cls.PI) + 40.0 * math.sin(lng / 3.0 * cls.PI))
            * 2.0 / 3.0
        )
        ret += (
            (150.0 * math.sin(lng / 12.0 * cls.PI) + 300.0 * math.sin(lng / 30.0 * cls.PI))
            * 2.0 / 3.0
        )
        return ret

    @classmethod
    def wgs84_to_gcj02(cls, lng: float, lat: float) -> Tuple[float, float]:
        """
        WGS-84 转 GCJ-02

        Args:
            lng: WGS-84 经度
            lat: WGS-84 纬度

        Returns:
            (GCJ-02 经度, GCJ-02 纬度)
        """
        if cls.out_of_china(lng, lat):
            return lng, lat

        dlat = cls.transform_lat(lng - 105.0, lat - 35.0)
        dlng = cls.transform_lng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * cls.PI
        magic = math.sin(radlat)
        magic = 1 - cls.EE * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((cls.A * (1 - cls.EE)) / (magic * sqrtmagic) * cls.PI)
        dlng = (dlng * 180.0) / (cls.A / sqrtmagic * math.cos(radlat) * cls.PI)
        mglat = lat + dlat
        mglng = lng + dlng
        return mglng, mglat

    @classmethod
    def gcj02_to_wgs84(cls, lng: float, lat: float) -> Tuple[float, float]:
        """
        GCJ-02 转 WGS-84 (粗略逆转换)

        Args:
            lng: GCJ-02 经度
            lat: GCJ-02 纬度

        Returns:
            (WGS-84 经度, WGS-84 纬度)
        """
        if cls.out_of_china(lng, lat):
            return lng, lat

        dlat = cls.transform_lat(lng - 105.0, lat - 35.0)
        dlng = cls.transform_lng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * cls.PI
        magic = math.sin(radlat)
        magic = 1 - cls.EE * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((cls.A * (1 - cls.EE)) / (magic * sqrtmagic) * cls.PI)
        dlng = (dlng * 180.0) / (cls.A / sqrtmagic * math.cos(radlat) * cls.PI)
        mglat = lat + dlat
        mglng = lng + dlng
        return lng * 2 - mglng, lat * 2 - mglat

    @classmethod
    def gcj02_to_bd09(cls, lng: float, lat: float) -> Tuple[float, float]:
        """
        GCJ-02 转 BD-09

        Args:
            lng: GCJ-02 经度
            lat: GCJ-02 纬度

        Returns:
            (BD-09 经度, BD-09 纬度)
        """
        z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * cls.X_PI)
        theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * cls.X_PI)
        bd_lng = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006
        return bd_lng, bd_lat

    @classmethod
    def bd09_to_gcj02(cls, lng: float, lat: float) -> Tuple[float, float]:
        """
        BD-09 转 GCJ-02

        Args:
            lng: BD-09 经度
            lat: BD-09 纬度

        Returns:
            (GCJ-02 经度, GCJ-02 纬度)
        """
        x = lng - 0.0065
        y = lat - 0.006
        z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * cls.X_PI)
        theta = math.atan2(y, x) - 0.000003 * math.cos(x * cls.X_PI)
        gg_lng = z * math.cos(theta)
        gg_lat = z * math.sin(theta)
        return gg_lng, gg_lat

    @classmethod
    def wgs84_to_bd09(cls, lng: float, lat: float) -> Tuple[float, float]:
        """
        WGS-84 转 BD-09

        Args:
            lng: WGS-84 经度
            lat: WGS-84 纬度

        Returns:
            (BD-09 经度, BD-09 纬度)
        """
        gcj_lng, gcj_lat = cls.wgs84_to_gcj02(lng, lat)
        return cls.gcj02_to_bd09(gcj_lng, gcj_lat)

    @classmethod
    def bd09_to_wgs84(cls, lng: float, lat: float) -> Tuple[float, float]:
        """
        BD-09 转 WGS-84

        Args:
            lng: BD-09 经度
            lat: BD-09 纬度

        Returns:
            (WGS-84 经度, WGS-84 纬度)
        """
        gcj_lng, gcj_lat = cls.bd09_to_gcj02(lng, lat)
        return cls.gcj02_to_wgs84(gcj_lng, gcj_lat)

    @classmethod
    def convert(
        cls,
        lng: float,
        lat: float,
        from_system: CoordinateSystem,
        to_system: CoordinateSystem
    ) -> Tuple[float, float]:
        """
        通用坐标转换接口

        Args:
            lng: 经度
            lat: 纬度
            from_system: 源坐标系
            to_system: 目标坐标系

        Returns:
            (转换后的经度, 转换后的纬度)
        """
        # 如果坐标系相同，直接返回
        if from_system == to_system:
            return lng, lat

        # 转换映射表
        conversion_map = {
            (CoordinateSystem.WGS84, CoordinateSystem.GCJ02): cls.wgs84_to_gcj02,
            (CoordinateSystem.WGS84, CoordinateSystem.BD09): cls.wgs84_to_bd09,
            (CoordinateSystem.GCJ02, CoordinateSystem.WGS84): cls.gcj02_to_wgs84,
            (CoordinateSystem.GCJ02, CoordinateSystem.BD09): cls.gcj02_to_bd09,
            (CoordinateSystem.BD09, CoordinateSystem.WGS84): cls.bd09_to_wgs84,
            (CoordinateSystem.BD09, CoordinateSystem.GCJ02): cls.bd09_to_gcj02,
        }

        conversion_func = conversion_map.get((from_system, to_system))
        if conversion_func:
            return conversion_func(lng, lat)

        raise ValueError(f"不支持的坐标系转换: {from_system} -> {to_system}")


# ==================== GeoJSON 转换器 ====================

class GeoJSONConverter:
    """
    GeoJSON 转换器

    功能：
    - 将查询结果转换为 GeoJSON FeatureCollection
    - 支持多种坐标系转换
    - 支持点、线、面等几何类型
    """

    @staticmethod
    def create_point_feature(
        coordinates: List[float],
        properties: Optional[Dict[str, Any]] = None,
        feature_id: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        创建 GeoJSON Point Feature

        Args:
            coordinates: [经度, 纬度] 或 [经度, 纬度, 高程]
            properties: 属性字典
            feature_id: Feature ID（可选）

        Returns:
            GeoJSON Feature 对象
        """
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": coordinates
            },
            "properties": properties or {}
        }

        if feature_id is not None:
            feature["id"] = feature_id

        return feature

    @staticmethod
    def create_feature_collection(
        features: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建 GeoJSON FeatureCollection

        Args:
            features: Feature 对象列表
            metadata: 元数据（可选）

        Returns:
            GeoJSON FeatureCollection 对象
        """
        collection = {
            "type": "FeatureCollection",
            "features": features
        }

        # 添加元数据
        if metadata:
            collection["metadata"] = metadata

        return collection

    @classmethod
    def from_query_result(
        cls,
        data: List[Dict[str, Any]],
        coordinate_system: CoordinateSystem = CoordinateSystem.WGS84,
        source_coordinate_system: CoordinateSystem = CoordinateSystem.WGS84,
        include_properties: bool = True,
        geometry_field: str = "coordinates",
        id_field: str = "gid"
    ) -> Dict[str, Any]:
        """
        从查询结果生成 GeoJSON FeatureCollection

        Args:
            data: 查询结果列表
            coordinate_system: 目标坐标系
            source_coordinate_system: 源坐标系（数据库中的坐标系）
            include_properties: 是否包含属性
            geometry_field: 几何字段名称
            id_field: ID字段名称

        Returns:
            GeoJSON FeatureCollection
        """
        features = []
        skipped_count = 0

        for record in data:
            try:
                # 提取坐标
                coords = record.get(geometry_field)
                if not coords or not isinstance(coords, (list, tuple)) or len(coords) < 2:
                    logger.warning(f"跳过无效坐标记录: {record.get(id_field, 'unknown')}")
                    skipped_count += 1
                    continue

                lng, lat = coords[0], coords[1]

                # 坐标系转换（如果需要）
                if source_coordinate_system != coordinate_system:
                    lng, lat = CoordinateConverter.convert(
                        lng, lat,
                        from_system=source_coordinate_system,
                        to_system=coordinate_system
                    )

                # 构建属性
                properties = {}
                if include_properties:
                    # 复制所有属性，但排除几何字段
                    properties = {
                        k: v for k, v in record.items()
                        if k != geometry_field
                    }

                # 创建 Feature
                feature_id = record.get(id_field)
                feature = cls.create_point_feature(
                    coordinates=[lng, lat],
                    properties=properties,
                    feature_id=feature_id
                )

                features.append(feature)

            except Exception as e:
                logger.error(f"转换记录失败: {record.get(id_field, 'unknown')}, 错误: {e}")
                skipped_count += 1
                continue

        # 构建元数据
        metadata = {
            "count": len(features),
            "skipped": skipped_count,
            "coordinate_system": coordinate_system.value,
            "source_coordinate_system": source_coordinate_system.value
        }

        # 创建 FeatureCollection
        return cls.create_feature_collection(features, metadata)

    @classmethod
    def from_query_result_auto(
        cls,
        data: List[Dict[str, Any]],
        target_system: CoordinateSystem = CoordinateSystem.WGS84,
        include_properties: bool = True
    ) -> Dict[str, Any]:
        """
        自动检测坐标字段并生成 GeoJSON

        优先使用对应坐标系的字段：
        - wgs84: coordinates_wgs84
        - gcj02: coordinates_gcj02
        - bd09: coordinates_bd09

        Args:
            data: 查询结果列表
            target_system: 目标坐标系
            include_properties: 是否包含属性

        Returns:
            GeoJSON FeatureCollection
        """
        # 坐标字段映射
        coordinate_field_map = {
            CoordinateSystem.WGS84: "coordinates_wgs84",
            CoordinateSystem.GCJ02: "coordinates_gcj02",
            CoordinateSystem.BD09: "coordinates_bd09"
        }

        # 确定使用的坐标字段
        geometry_field = coordinate_field_map.get(target_system, "coordinates_wgs84")

        # 检查第一条记录，判断字段是否存在
        if data and geometry_field not in data[0]:
            logger.warning(f"字段 {geometry_field} 不存在，尝试使用通用字段 'coordinates'")
            geometry_field = "coordinates"

        # 生成 GeoJSON
        return cls.from_query_result(
            data=data,
            coordinate_system=target_system,
            source_coordinate_system=target_system,  # 假设源坐标系与目标坐标系一致
            include_properties=include_properties,
            geometry_field=geometry_field
        )


# ==================== 测试代码 ====================

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n=== 测试坐标转换 ===\n")

    # 测试1: WGS84 -> GCJ02
    print("--- 测试1: WGS84 -> GCJ02 ---")
    wgs_lng, wgs_lat = 120.15, 30.25  # 杭州西湖
    gcj_lng, gcj_lat = CoordinateConverter.wgs84_to_gcj02(wgs_lng, wgs_lat)
    print(f"WGS84: ({wgs_lng}, {wgs_lat})")
    print(f"GCJ02: ({gcj_lng:.6f}, {gcj_lat:.6f})")

    # 测试2: GCJ02 -> BD09
    print("\n--- 测试2: GCJ02 -> BD09 ---")
    bd_lng, bd_lat = CoordinateConverter.gcj02_to_bd09(gcj_lng, gcj_lat)
    print(f"GCJ02: ({gcj_lng:.6f}, {gcj_lat:.6f})")
    print(f"BD09:  ({bd_lng:.6f}, {bd_lat:.6f})")

    # 测试3: 通用转换
    print("\n--- 测试3: 通用转换接口 ---")
    result = CoordinateConverter.convert(
        wgs_lng, wgs_lat,
        from_system=CoordinateSystem.WGS84,
        to_system=CoordinateSystem.BD09
    )
    print(f"WGS84 -> BD09: ({result[0]:.6f}, {result[1]:.6f})")

    print("\n=== 测试 GeoJSON 转换 ===\n")

    # 测试4: 创建 Point Feature
    print("--- 测试4: 创建 Point Feature ---")
    feature = GeoJSONConverter.create_point_feature(
        coordinates=[120.15, 30.25],
        properties={"name": "西湖", "level": "5A"},
        feature_id=1
    )
    print(f"Feature: {feature}")

    # 测试5: 从查询结果生成 GeoJSON
    print("\n--- 测试5: 从查询结果生成 GeoJSON ---")
    query_data = [
        {
            "gid": 1,
            "name": "西湖",
            "level": "5A",
            "coordinates_wgs84": [120.15, 30.25]
        },
        {
            "gid": 2,
            "name": "雷峰塔",
            "level": "4A",
            "coordinates_wgs84": [120.14, 30.23]
        }
    ]

    geojson = GeoJSONConverter.from_query_result_auto(
        data=query_data,
        target_system=CoordinateSystem.WGS84,
        include_properties=True
    )

    import json
    print(json.dumps(geojson, ensure_ascii=False, indent=2))
    print(f"\n✓ 生成 {geojson['metadata']['count']} 个 Feature")
