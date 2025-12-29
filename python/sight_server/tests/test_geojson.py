"""
GeoJSON 工具类测试
测试坐标转换和 GeoJSON 生成功能
"""

import pytest
from utils.geojson_utils import CoordinateConverter, GeoJSONConverter, CoordinateSystem


class TestCoordinateConverter:
    """坐标转换器测试"""

    def test_wgs84_to_gcj02(self):
        """测试 WGS84 转 GCJ02"""
        # 杭州西湖坐标
        wgs_lng, wgs_lat = 120.15, 30.25

        gcj_lng, gcj_lat = CoordinateConverter.wgs84_to_gcj02(wgs_lng, wgs_lat)

        # GCJ02 应该与 WGS84 有偏移
        assert gcj_lng != wgs_lng
        assert gcj_lat != wgs_lat

        # 偏移应该在合理范围内（几百米）
        assert abs(gcj_lng - wgs_lng) < 0.01
        assert abs(gcj_lat - wgs_lat) < 0.01

    def test_gcj02_to_bd09(self):
        """测试 GCJ02 转 BD09"""
        gcj_lng, gcj_lat = 120.156, 30.254

        bd_lng, bd_lat = CoordinateConverter.gcj02_to_bd09(gcj_lng, gcj_lat)

        # BD09 应该与 GCJ02 有偏移
        assert bd_lng != gcj_lng
        assert bd_lat != gcj_lat

        # 偏移应该在合理范围内
        assert abs(bd_lng - gcj_lng) < 0.01
        assert abs(bd_lat - gcj_lat) < 0.01

    def test_wgs84_to_bd09(self):
        """测试 WGS84 转 BD09（组合转换）"""
        wgs_lng, wgs_lat = 120.15, 30.25

        bd_lng, bd_lat = CoordinateConverter.wgs84_to_bd09(wgs_lng, wgs_lat)

        # BD09 应该与 WGS84 有明显偏移
        assert bd_lng != wgs_lng
        assert bd_lat != wgs_lat

    def test_bd09_to_wgs84(self):
        """测试 BD09 转 WGS84（逆转换）"""
        bd_lng, bd_lat = 120.162, 30.260

        wgs_lng, wgs_lat = CoordinateConverter.bd09_to_wgs84(bd_lng, bd_lat)

        # 应该接近原始 WGS84 坐标
        assert abs(wgs_lng - 120.15) < 0.02
        assert abs(wgs_lat - 30.25) < 0.02

    def test_convert_same_system(self):
        """测试相同坐标系转换（应该返回原值）"""
        lng, lat = 120.15, 30.25

        result_lng, result_lat = CoordinateConverter.convert(
            lng, lat,
            from_system=CoordinateSystem.WGS84,
            to_system=CoordinateSystem.WGS84
        )

        assert result_lng == lng
        assert result_lat == lat

    def test_convert_wgs84_to_gcj02(self):
        """测试通用转换接口"""
        lng, lat = 120.15, 30.25

        result_lng, result_lat = CoordinateConverter.convert(
            lng, lat,
            from_system=CoordinateSystem.WGS84,
            to_system=CoordinateSystem.GCJ02
        )

        # 应该与专用函数结果一致
        expected_lng, expected_lat = CoordinateConverter.wgs84_to_gcj02(lng, lat)
        assert result_lng == expected_lng
        assert result_lat == expected_lat

    def test_out_of_china(self):
        """测试中国境外判断"""
        # 中国境内
        assert not CoordinateConverter.out_of_china(120.15, 30.25)

        # 中国境外（美国）
        assert CoordinateConverter.out_of_china(-122.42, 37.78)

        # 边界测试
        assert CoordinateConverter.out_of_china(73.0, 30.0)  # 西边界外
        assert CoordinateConverter.out_of_china(136.0, 30.0)  # 东边界外


class TestGeoJSONConverter:
    """GeoJSON 转换器测试"""

    def test_create_point_feature(self):
        """测试创建点要素"""
        coordinates = [120.15, 30.25]
        properties = {"name": "西湖", "level": "5A"}

        feature = GeoJSONConverter.create_point_feature(
            coordinates=coordinates,
            properties=properties,
            feature_id=1
        )

        assert feature["type"] == "Feature"
        assert feature["id"] == 1
        assert feature["geometry"]["type"] == "Point"
        assert feature["geometry"]["coordinates"] == coordinates
        assert feature["properties"] == properties

    def test_create_feature_collection(self):
        """测试创建要素集合"""
        features = [
            GeoJSONConverter.create_point_feature([120.15, 30.25], {"name": "西湖"}),
            GeoJSONConverter.create_point_feature([120.14, 30.23], {"name": "雷峰塔"})
        ]
        metadata = {"count": 2, "coordinate_system": "wgs84"}

        collection = GeoJSONConverter.create_feature_collection(features, metadata)

        assert collection["type"] == "FeatureCollection"
        assert len(collection["features"]) == 2
        assert collection["metadata"] == metadata

    def test_from_query_result(self):
        """测试从查询结果生成 GeoJSON"""
        query_data = [
            {
                "gid": 1,
                "name": "西湖",
                "level": "5A",
                "coordinates": [120.15, 30.25]
            },
            {
                "gid": 2,
                "name": "雷峰塔",
                "level": "4A",
                "coordinates": [120.14, 30.23]
            }
        ]

        geojson = GeoJSONConverter.from_query_result(
            data=query_data,
            coordinate_system=CoordinateSystem.WGS84,
            source_coordinate_system=CoordinateSystem.WGS84,
            include_properties=True,
            geometry_field="coordinates",
            id_field="gid"
        )

        assert geojson["type"] == "FeatureCollection"
        assert len(geojson["features"]) == 2
        assert geojson["metadata"]["count"] == 2
        assert geojson["metadata"]["skipped"] == 0
        assert geojson["features"][0]["properties"]["name"] == "西湖"

    def test_from_query_result_with_conversion(self):
        """测试带坐标转换的 GeoJSON 生成"""
        query_data = [
            {
                "gid": 1,
                "name": "西湖",
                "coordinates": [120.15, 30.25]
            }
        ]

        # WGS84 -> GCJ02 转换
        geojson = GeoJSONConverter.from_query_result(
            data=query_data,
            coordinate_system=CoordinateSystem.GCJ02,
            source_coordinate_system=CoordinateSystem.WGS84,
            geometry_field="coordinates"
        )

        # 坐标应该已转换
        original_coords = query_data[0]["coordinates"]
        feature_coords = geojson["features"][0]["geometry"]["coordinates"]

        assert feature_coords[0] != original_coords[0]
        assert feature_coords[1] != original_coords[1]

    def test_from_query_result_skip_invalid(self):
        """测试跳过无效坐标"""
        query_data = [
            {"gid": 1, "name": "西湖", "coordinates": [120.15, 30.25]},
            {"gid": 2, "name": "无效", "coordinates": None},  # 无效坐标
            {"gid": 3, "name": "雷峰塔", "coordinates": [120.14, 30.23]}
        ]

        geojson = GeoJSONConverter.from_query_result(
            data=query_data,
            coordinate_system=CoordinateSystem.WGS84,
            source_coordinate_system=CoordinateSystem.WGS84,
            geometry_field="coordinates"
        )

        # 应该只有 2 个有效要素
        assert geojson["metadata"]["count"] == 2
        assert geojson["metadata"]["skipped"] == 1

    def test_from_query_result_auto(self):
        """测试自动检测坐标字段"""
        query_data = [
            {
                "gid": 1,
                "name": "西湖",
                "coordinates_wgs84": [120.15, 30.25],
                "coordinates_gcj02": [120.156, 30.254]
            }
        ]

        # WGS84
        geojson_wgs84 = GeoJSONConverter.from_query_result_auto(
            data=query_data,
            target_system=CoordinateSystem.WGS84
        )
        assert geojson_wgs84["features"][0]["geometry"]["coordinates"] == [120.15, 30.25]

        # GCJ02
        geojson_gcj02 = GeoJSONConverter.from_query_result_auto(
            data=query_data,
            target_system=CoordinateSystem.GCJ02
        )
        assert geojson_gcj02["features"][0]["geometry"]["coordinates"] == [120.156, 30.254]


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
