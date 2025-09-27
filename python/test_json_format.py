"""
测试JSON格式是否正确
"""

import json

# 测试用例1
test_json1 = '''{
  "answer": "查询成功返回了whupoi表的前2条记录，以GeoJSON FeatureCollection格式呈现。结果包含以下信息：第一条记录：- gid: 1 - osm_id: 845686557 - highway: traffic_signals - 几何类型: Point - 坐标: [114.3699588, 30.5309076] 第二条记录：- gid: 2 - osm_id: 1148740588 - barrier: gate - 几何类型: Point - 坐标: [114.3465494, 30.5240617]",
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [114.3699588, 30.5309076]
        },
        "properties": {
          "gid": 1,
          "osm_id": "845686557",
          "highway": "traffic_signals"
        }
      },
      {
        "type": "Feature",
        "geometry": {
          "type": "Point",
          "coordinates": [114.3465494, 30.5240617]
        },
        "properties": {
          "gid": 2,
          "osm_id": "1148740588",
          "barrier": "gate"
        }
      }
    ]
  }
}'''

# 测试用例2
test_json2 = '''{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [114.3602621, 30.5326797]
      },
      "properties": {
        "gid": 3,
        "osm_id": "1178784609",
        "name": "珞珈山街道办事处"
      }
    },
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [114.3604447, 30.5326338]
      },
      "properties": {
        "gid": 8,
        "osm_id": "1196672341",
        "name": "珞珈山派出所"
      }
    }
  ]
}'''

print("=== 测试JSON格式 ===\n")

try:
    data1 = json.loads(test_json1)
    print("✅ 测试用例1 JSON格式正确")
    print(f"answer长度: {len(data1['answer'])}")
    print(f"geojson要素数: {len(data1['geojson']['features'])}")
except Exception as e:
    print(f"❌ 测试用例1 JSON格式错误: {e}")

try:
    data2 = json.loads(test_json2)
    print("✅ 测试用例2 JSON格式正确")
    print(f"geojson要素数: {len(data2['features'])}")
except Exception as e:
    print(f"❌ 测试用例2 JSON格式错误: {e}")
