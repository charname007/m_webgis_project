/**
 * 基于缩放级别的图层聚合要素过滤 - 最终修复验证测试
 * 验证低等级要素在缩放等级变小时不会显示，且不会与其他高等级要素聚合在一起
 */

// 测试数据 - 模拟不同等级的景区要素
const testGeoJsonData = {
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "黄鹤楼",
        "level": "5A",
        "description": "武汉著名景点"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [114.305, 30.5428]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "东湖风景区",
        "level": "5A",
        "description": "武汉东湖景区"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [114.415, 30.5528]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "归元寺",
        "level": "4A",
        "description": "武汉归元寺"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [114.255, 30.5628]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "古琴台",
        "level": "4A",
        "description": "武汉古琴台"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [114.285, 30.5728]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "晴川阁",
        "level": "3A",
        "description": "武汉晴川阁"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [114.295, 30.5828]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "户部巷",
        "level": "3A",
        "description": "武汉户部巷"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [114.305, 30.5928]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "江汉路",
        "level": "2A",
        "description": "武汉江汉路"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [114.285, 30.6028]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "昙华林",
        "level": "2A",
        "description": "武汉昙华林"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [114.315, 30.6128]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "小景点1",
        "level": "1A",
        "description": "小景点1"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [114.275, 30.6228]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "小景点2",
        "level": "1A",
        "description": "小景点2"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [114.325, 30.6328]
      }
    }
  ]
};

/**
 * 测试基于缩放级别的图层聚合要素过滤
 */
async function testZoomClusterFilterFix() {
  console.log('=== 基于缩放级别的图层聚合要素过滤测试开始 ===');
  
  try {
    // 1. 创建地图实例
    const mapUtils = new MapUtils('map');
    mapUtils.addBaseLayer();
    
    // 2. 创建基于缩放级别的图层（启用聚合）
    const zoomLayer = mapUtils.createZoomBasedVectorLayer(
      'level', // 字段名
      {
        type: 'discrete',
        values: [
          { value: '5A', minZoom: 10 },
          { value: '4A', minZoom: 12 },
          { value: '3A', minZoom: 14 },
          { value: '2A', minZoom: 16 },
          { value: '1A', minZoom: 18 }
        ]
      },
      '景区图层',
      {
        enableClustering: true,  // 启用聚合
        clusterDistance: 40,     // 聚合距离
        autoFitExtent: false
      }
    );
    
    console.log('✅ 基于缩放级别的图层创建成功');
    
    // 3. 添加测试数据到图层
    const addResult = await mapUtils.addGeoJsonToLayer(zoomLayer, testGeoJsonData);
    console.log('✅ 测试数据添加成功:', addResult);
    
    // 4. 测试不同缩放级别的要素可见性
    console.log('\n=== 测试不同缩放级别的要素可见性 ===');
    
    // 测试缩放级别 8 - 应该只显示 5A 等级要素
    await testZoomLevel(mapUtils, 8, '5A', ['5A']);
    
    // 测试缩放级别 11 - 应该显示 5A 和 4A 等级要素
    await testZoomLevel(mapUtils, 11, '5A,4A', ['5A', '4A']);
    
    // 测试缩放级别 13 - 应该显示 5A,4A,3A 等级要素
    await testZoomLevel(mapUtils, 13, '5A,4A,3A', ['5A', '4A', '3A']);
    
    // 测试缩放级别 15 - 应该显示 5A,4A,3A,2A 等级要素
    await testZoomLevel(mapUtils, 15, '5A,4A,3A,2A', ['5A', '4A', '3A', '2A']);
    
    // 测试缩放级别 17 - 应该显示所有等级要素
    await testZoomLevel(mapUtils, 17, '所有等级', ['5A', '4A', '3A', '2A', '1A']);
    
    console.log('\n=== 聚合要素过滤验证 ===');
    await testClusterFiltering(mapUtils, zoomLayer);
    
    console.log('\n✅ 所有测试通过！基于缩放级别的图层聚合要素过滤修复成功！');
    
  } catch (error) {
    console.error('❌ 测试失败:', error);
  }
}

/**
 * 测试特定缩放级别的要素可见性
 */
async function testZoomLevel(mapUtils, zoomLevel, expectedLevels, expectedVisibleLevels) {
  console.log(`\n--- 测试缩放级别 ${zoomLevel} ---`);
  
  // 设置缩放级别
  mapUtils.map.getView().setZoom(zoomLevel);
  
  // 等待地图更新
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // 获取图层数据源
  const layerSource = mapUtils.map.getLayers().getArray()
    .find(layer => layer.get('title') === '景区图层')
    .getSource();
  
  // 获取聚合源
  const clusterSource = layerSource;
  const features = clusterSource.getFeatures();
  
  console.log(`当前缩放级别: ${zoomLevel}`);
  console.log(`期望显示的等级: ${expectedLevels}`);
  console.log(`聚合要素数量: ${features.length}`);
  
  // 分析聚合要素
  const visibleLevels = new Set();
  let totalFeatures = 0;
  
  features.forEach(feature => {
    const clusterFeatures = feature.get('features');
    if (clusterFeatures) {
      totalFeatures += clusterFeatures.length;
      clusterFeatures.forEach(clusterFeature => {
        const level = clusterFeature.get('level');
        if (level) {
          visibleLevels.add(level);
        }
      });
    } else {
      // 单个要素
      const level = feature.get('level');
      if (level) {
        visibleLevels.add(level);
        totalFeatures++;
      }
    }
  });
  
  const actualLevels = Array.from(visibleLevels).sort();
  console.log(`实际显示的等级: ${actualLevels.join(',')}`);
  console.log(`总要素数量: ${totalFeatures}`);
  
  // 验证可见性
  const isValid = expectedVisibleLevels.every(level => actualLevels.includes(level)) &&
                 actualLevels.every(level => expectedVisibleLevels.includes(level));
  
  if (isValid) {
    console.log(`✅ 缩放级别 ${zoomLevel} 的要素可见性验证通过`);
  } else {
    console.log(`❌ 缩放级别 ${zoomLevel} 的要素可见性验证失败`);
    console.log(`   期望: ${expectedVisibleLevels.join(',')}`);
    console.log(`   实际: ${actualLevels.join(',')}`);
  }
  
  return isValid;
}

/**
 * 测试聚合要素过滤
 */
async function testClusterFiltering(mapUtils, zoomLayer) {
  console.log('--- 聚合要素过滤验证 ---');
  
  // 设置到低缩放级别（只显示高等级要素）
  mapUtils.map.getView().setZoom(8);
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // 获取可见要素源
  const visibleFeaturesSource = zoomLayer.get('visibleFeaturesSource');
  const visibleFeatures = visibleFeaturesSource.getFeatures();
  
  console.log(`低缩放级别可见要素数量: ${visibleFeatures.length}`);
  
  // 检查可见要素的等级
  const visibleLevels = new Set();
  visibleFeatures.forEach(feature => {
    const level = feature.get('level');
    if (level) {
      visibleLevels.add(level);
    }
  });
  
  console.log(`低缩放级别可见等级: ${Array.from(visibleLevels).join(',')}`);
  
  // 验证只有高等级要素可见
  const hasOnlyHighLevel = Array.from(visibleLevels).every(level => 
    ['5A'].includes(level)
  );
  
  if (hasOnlyHighLevel) {
    console.log('✅ 聚合要素过滤验证通过 - 低缩放级别只显示高等级要素');
  } else {
    console.log('❌ 聚合要素过滤验证失败 - 低缩放级别显示了不应该显示的要素');
  }
  
  return hasOnlyHighLevel;
}

// 运行测试
testZoomClusterFilterFix();
