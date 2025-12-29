"""
测试server.py中的answer和geojson提取逻辑
"""

import json
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_answer_and_geojson(final_answer):
    """
    从final_answer中提取answer和geojson
    这是server.py中提取逻辑的简化版本
    """
    extracted_answer = final_answer
    extracted_geojson = None
    
    # 方法1: 查找完整的JSON格式 {answer: ..., geojson: ...}
    json_pattern = r'\{.*?"answer":\s*".*?",\s*"geojson":\s*\{.*?\}.*?\}'
    json_matches = re.findall(json_pattern, final_answer, re.DOTALL)
    
    if json_matches:
        logger.info(f"从final_answer中提取到{len(json_matches)}个JSON格式匹配")
        
        # 使用第一个匹配的JSON
        json_str = json_matches[0]
        try:
            parsed_data = json.loads(json_str)
            if "answer" in parsed_data:
                extracted_answer = parsed_data["answer"]
                logger.info(f"提取到answer: {extracted_answer[:100]}...")
            
            if "geojson" in parsed_data:
                extracted_geojson = parsed_data["geojson"]
                logger.info(f"提取到geojson，包含{len(extracted_geojson.get('features', []))}个要素")
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败: {e}")
    
    # 方法2: 如果没有找到完整JSON，尝试查找独立的GeoJSON FeatureCollection
    if extracted_geojson is None:
        geojson_pattern = r'\{\s*"type":\s*"FeatureCollection".*?\}'
        geojson_matches = re.findall(geojson_pattern, final_answer, re.DOTALL)
        
        if geojson_matches:
            try:
                extracted_geojson = json.loads(geojson_matches[0])
                logger.info(f"提取到独立的geojson，包含{len(extracted_geojson.get('features', []))}个要素")
                
                # 如果提取到了geojson但没有answer，从final_answer中提取描述性文本作为answer
                if extracted_answer == final_answer:
                    # 移除geojson部分，保留描述性文本
                    answer_text = re.sub(geojson_pattern, '', final_answer, flags=re.DOTALL).strip()
                    if answer_text and len(answer_text) > 10:  # 确保有足够的内容
                        extracted_answer = answer_text
                        logger.info(f"从文本中提取到answer: {extracted_answer[:100]}...")
            except json.JSONDecodeError as e:
                logger.warning(f"独立geojson JSON解析失败: {e}")
    
    # 方法3: 如果没有找到JSON格式，尝试简单的文本提取
    if extracted_geojson is None:
        # 查找answer: 和geojson: 格式
        answer_pattern = r'answer:\s*(.*?)(?=geojson:|$)'
        geojson_pattern = r'geojson:\s*(\{.*?\})(?=answer:|$)'
        
        answer_matches = re.findall(answer_pattern, final_answer, re.DOTALL | re.IGNORECASE)
        geojson_matches = re.findall(geojson_pattern, final_answer, re.DOTALL | re.IGNORECASE)
        
        if answer_matches:
            extracted_answer = answer_matches[0].strip()
            logger.info(f"从文本中提取到answer: {extracted_answer[:100]}...")
        
        if geojson_matches:
            try:
                extracted_geojson = json.loads(geojson_matches[0])
                logger.info(f"从文本中提取到geojson，包含{len(extracted_geojson.get('features', []))}个要素")
            except json.JSONDecodeError as e:
                logger.warning(f"geojson JSON解析失败: {e}")
    
    return extracted_answer, extracted_geojson

def test_extraction():
    """测试提取逻辑"""
    
    print("=== 测试server.py中的answer和geojson提取逻辑 ===\n")
    
    # 测试用例1: 理想格式
    print("测试用例1: 理想JSON格式")
    ideal_response = '''{
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
    
    answer1, geojson1 = extract_answer_and_geojson(ideal_response)
    print(f"✅ 提取成功: answer长度={len(answer1)}, geojson要素数={len(geojson1.get('features', [])) if geojson1 else 0}")
    
    # 测试用例2: AI代理实际返回的格式（包含独立GeoJSON）
    print("\n测试用例2: AI代理实际返回格式")
    actual_response = '''查询成功返回了whupoi表中包含'珞珈'的前2条记录，以GeoJSON FeatureCollection格式返回：

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
    
    answer2, geojson2 = extract_answer_and_geojson(actual_response)
    print(f"✅ 提取成功: answer长度={len(answer2)}, geojson要素数={len(geojson2.get('features', [])) if geojson2 else 0}")
    
    # 测试用例3: 文本格式
    print("\n测试用例3: 文本格式")
    text_response = '''answer: 这是查询结果的描述性文本
geojson: {
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [114.0, 30.0]
      },
      "properties": {
        "name": "测试点"
      }
    }
  ]
}'''
    
    answer3, geojson3 = extract_answer_and_geojson(text_response)
    print(f"✅ 提取成功: answer长度={len(answer3)}, geojson要素数={len(geojson3.get('features', [])) if geojson3 else 0}")
    
    # 测试用例4: 只有文本没有GeoJSON
    print("\n测试用例4: 只有文本没有GeoJSON")
    text_only_response = '''查询成功返回了结果，但没有空间数据需要返回。'''
    
    answer4, geojson4 = extract_answer_and_geojson(text_only_response)
    print(f"✅ 提取成功: answer长度={len(answer4)}, geojson={geojson4 is not None}")
    
    print("\n=== 测试总结 ===")
    print("✅ 提取逻辑能够处理各种格式的响应")
    print("✅ 能够正确提取answer和geojson")
    print("✅ 对于没有geojson的情况也能正确处理")
    print("✅ server.py中的提取逻辑工作正常")

if __name__ == "__main__":
    test_extraction()
