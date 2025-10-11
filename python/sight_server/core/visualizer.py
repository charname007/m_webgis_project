
import json
from typing import List, Dict, Any, Optional

class Visualizer:
    """
    一个智能的数据可视化配置生成器。
    它分析查询结果，并生成前端可以直接使用的JSON配置。
    """

    def generate_config(self, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        主方法，分析数据并返回最合适的可视化配置。

        Args:
            data: SQL查询返回的数据列表。

        Returns:
            一个包含可视化配置的字典，或者如果找不到合适的 可视化方式则返回 None。
        """
        if not data:
            return None

        # 策略1：检测地理空间数据 (GeoJSON)
        map_config = self._try_generate_map_config(data)
        if map_config:
            return map_config

        # 策略2：可以添加检测图表数据的逻辑 (e.g., for charts)
        # chart_config = self._try_generate_chart_config(data)
        # if chart_config:
        #     return chart_config
        
        return None

    def _try_generate_map_config(self, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        尝试为地图生成配置（目前专注于OpenLayers）。
        """
        # 检查数据中是否存在名为 'geojson' 的字段，并且其内容是有效的JSON字符串
        geojson_features = []
        for row in data:
            if 'geojson' in row and isinstance(row['geojson'], str):
                try:
                    feature = json.loads(row['geojson'])
                    # 简单验证是否是有效的 GeoJSON Feature
                    if feature.get("type") == "Feature" and "geometry" in feature:
                        # 将其他属性也加入到 feature 的 properties 中，方便前端展示
                        feature["properties"] = {k: v for k, v in row.items() if k != 'geojson'}
                        geojson_features.append(feature)
                except json.JSONDecodeError:
                    continue # 如果解析失败，则跳过此行

        if not geojson_features:
            return None

        # 如果找到了 GeoJSON 数据，则构建 OpenLayers 可以直接使用的配置
        return {
            "type": "map",
            "engine": "openlayers",
            "config": {
                "features": geojson_features
            }
        }

