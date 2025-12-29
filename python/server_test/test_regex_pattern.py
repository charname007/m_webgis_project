"""
测试正则表达式模式
"""

import re
import json

# 测试用例
test_response = '''查询成功返回了whupoi表中包含'珞珈'的前2条记录，以GeoJSON FeatureCollection格式返回：

{
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
}

这两个地点分别是：
1. 珞珈山街道办事处（街道办事处）
2. 珞珈山派出所（派出所）'''

print("=== 测试正则表达式模式 ===\n")

# 方法1: 查找完整的JSON格式 {answer: ..., geojson: ...}
json_pattern = r'\{.*?"answer":\s*".*?",\s*"geojson":\s*\{.*?\}.*?\}'
json_matches = re.findall(json_pattern, test_response, re.DOTALL)
print(f"方法1 - 完整JSON匹配数: {len(json_matches)}")
if json_matches:
    print(f"匹配内容: {json_matches[0][:100]}...")

# 方法2: 查找独立的GeoJSON FeatureCollection
geojson_pattern = r'\{\s*"type":\s*"FeatureCollection".*?\}'
geojson_matches = re.findall(geojson_pattern, test_response, re.DOTALL)
print(f"方法2 - 独立GeoJSON匹配数: {len(geojson_matches)}")
if geojson_matches:
    print(f"匹配内容长度: {len(geojson_matches[0])}")
    try:
        geojson_data = json.loads(geojson_matches[0])
        print(f"✅ GeoJSON解析成功，要素数: {len(geojson_data.get('features', []))}")
    except Exception as e:
        print(f"❌ GeoJSON解析失败: {e}")

# 方法3: 文本格式
answer_pattern = r'answer:\s*(.*?)(?=geojson:|$)'
geojson_pattern2 = r'geojson:\s*(\{.*?\})(?=answer:|$)'

answer_matches = re.findall(answer_pattern, test_response, re.DOTALL | re.IGNORECASE)
geojson_matches2 = re.findall(geojson_pattern2, test_response, re.DOTALL | re.IGNORECASE)

print(f"方法3 - answer匹配数: {len(answer_matches)}")
print(f"方法3 - geojson匹配数: {len(geojson_matches2)}")

# 测试提取描述性文本
if geojson_matches:
    answer_text = re.sub(geojson_pattern, '', test_response, flags=re.DOTALL).strip()
    print(f"提取的描述性文本长度: {len(answer_text)}")
    print(f"描述性文本前100字符: {answer_text[:100]}...")
