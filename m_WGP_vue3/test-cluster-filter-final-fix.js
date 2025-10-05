/**
 * 聚合要素过滤最终修复测试
 * 彻底解决聚合要素根据缩放等级自动排除低等级要素的问题
 */

import MapUtils from './src/components/mapUtils.js';

// 测试数据 - 模拟不同等级的景区
const testFeatures = [
  {
    type: 'Feature',
    properties: {
      name: '5A级景区1',
      level: '5A',
      description: '国家级5A景区'
    },
    geometry: {
      type: 'Point',
      coordinates: [114.305, 30.5928]
    }
  },
  {
    type: 'Feature',
    properties: {
      name: '5A级景区2',
      level: '5A',
      description: '国家级5A景区'
    },
    geometry: {
      type: 'Point',
      coordinates: [114.315, 30.6028]
    }
  },
  {
    type: 'Feature',
    properties: {
      name: '4A级景区1',
      level: '4A',
      description: '国家级4A景区'
    },
    geometry: {
      type: 'Point',
      coordinates: [114.325, 30.6128]
    }
  },
  {
    type: 'Feature',
    properties: {
      name: '4A级景区2',
      level: '4A',
      description: '国家级4A景区'
    },
    geometry: {
      type: 'Point',
      coordinates: [114.335, 30.6228]
    }
  },
  {
    type: 'Feature',
    properties: {
      name: '3A级景区1',
      level: '3A',
      description: '国家级3A景区'
    },
    geometry: {
      type: 'Point',
      coordinates: [114.345, 30.6328]
    }
  },
  {
    type: 'Feature',
    properties: {
      name: '3A级景区2',
      level: '3A',
      description: '国家级3A景区'
    },
    geometry: {
      type: 'Point',
      coordinates: [114.355, 30.6428]
    }
  }
];

// 配置基于缩放级别的过滤规则
const zoomBasedConfig = {
  fieldName: 'level',
  fieldRange: {
    type: 'discrete',
    values: [
      { value: '5A', minZoom: 10 },  // 5A级景区在缩放级别10+显示
      { value: '4A', minZoom: 12 },  // 4A级景区在缩放级别12+显示
      { value: '3A', minZoom: 14 }   // 3A级景区在缩放级别14+显示
    ]
  }
};

/**
 * 测试聚合要素过滤功能
 */
async function testClusterFilterFix() {
  console.log('=== 开始聚合要素过滤最终修复测试 ===');
  
  // 创建地图实例
  const mapContainer = document.createElement('div');
  mapContainer.style.width = '800px';
  mapContainer.style.height = '600px';
  document.body.appendChild(mapContainer);
  
  const mapUtils = new MapUtils(mapContainer);
  mapUtils.addBaseLayer();
  
  // 创建基于缩放级别的图层
  const zoomLayer = mapUtils.createZoomBasedVectorLayer(
    zoomBasedConfig.fieldName,
    zoomBasedConfig.fieldRange,
    '景区图层',
    {
      enableClustering: true,
      clusterDistance: 40,
      autoFitExtent: true
    }
  );
  
  // 添加测试要素
  const addResult = await mapUtils.addGeoJsonToLayer(zoomLayer, {
    type: 'FeatureCollection',
    features: testFeatures
  });
  
  console.log('要素添加结果:', addResult);
  
  // 测试不同缩放级别的过滤效果
  await testZoomLevels(mapUtils, zoomLayer);
  
  return { mapUtils, zoomLayer };
}

/**
 * 测试不同缩放级别的过滤效果
 */
async function testZoomLevels(mapUtils, zoomLayer) {
  console.log('\n=== 测试不同缩放级别的过滤效果 ===');
  
  const testZoomLevels = [9, 11, 13, 15];
  
  for (const zoomLevel of testZoomLevels) {
    console.log(`\n--- 测试缩放级别 ${zoomLevel} ---`);
    
    // 设置缩放级别
    mapUtils.setCenter([114.305, 30.5928], zoomLevel, { animate: false });
    
    // 等待地图更新
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 获取当前可见要素
    const visibleCount = mapUtils.getVisibleFeatureCount(zoomLayer);
    console.log(`缩放级别 ${zoomLevel}: ${visibleCount} 个要素可见`);
    
    // 验证聚合要素组成
    await validateClusterComposition(mapUtils, zoomLayer, zoomLevel);
  }
}

/**
 * 验证聚合要素组成
 */
async function validateClusterComposition(mapUtils, zoomLayer, currentZoom) {
  const source = zoomLayer.getSource();
  const clusterFeatures = source.getFeatures();
  
  console.log(`聚合要素数量: ${clusterFeatures.length}`);
  
  let totalInvisibleInClusters = 0;
  
  clusterFeatures.forEach((clusterFeature, index) => {
    const childFeatures = clusterFeature.get('features');
    if (childFeatures) {
      const visibleChildCount = childFeatures.filter(child => 
        child.get('visible') !== false
      ).length;
      
      const invisibleChildCount = childFeatures.length - visibleChildCount;
      totalInvisibleInClusters += invisibleChildCount;
      
      if (invisibleChildCount > 0) {
        console.warn(`⚠️ 聚合要素 ${index} 包含 ${invisibleChildCount} 个不可见要素`);
        
        // 显示不可见要素的详细信息
        const invisibleLevels = {};
        childFeatures.forEach(child => {
          if (child.get('visible') === false) {
            const level = child.get('level');
            invisibleLevels[level] = (invisibleLevels[level] || 0) + 1;
          }
        });
        console.warn(`  不可见要素等级分布:`, invisibleLevels);
      } else {
        console.log(`✅ 聚合要素 ${index} 完全由可见要素组成`);
      }
    }
  });
  
  if (totalInvisibleInClusters > 0) {
    console.error(`❌ 发现 ${totalInvisibleInClusters} 个不可见要素混入聚合中`);
    return false;
  } else {
    console.log(`✅ 所有聚合要素完全由可见要素组成`);
    return true;
  }
}

/**
 * 运行测试
 */
testClusterFilterFix().then(result => {
  console.log('\n=== 聚合要素过滤测试完成 ===');
  console.log('如果所有测试都通过，说明修复成功');
}).catch(error => {
  console.error('测试失败:', error);
});
