/**
 * 聚合源重建机制验证测试
 * 验证聚合源在缩放级别变化时是否正确重建，确保只包含可见要素
 */

import MapUtils from './src/components/mapUtils.js';

// 测试数据 - 模拟不同等级的景区要素
const testFeatures = [
  {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [114.305, 30.5928]
    },
    properties: {
      name: '黄鹤楼',
      level: '5A',
      description: '武汉著名景点'
    }
  },
  {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [114.315, 30.6028]
    },
    properties: {
      name: '东湖',
      level: '5A',
      description: '武汉著名湖泊'
    }
  },
  {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [114.325, 30.6128]
    },
    properties: {
      name: '武汉大学',
      level: '4A',
      description: '著名高校'
    }
  },
  {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [114.335, 30.6228]
    },
    properties: {
      name: '户部巷',
      level: '3A',
      description: '美食街'
    }
  },
  {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [114.345, 30.6328]
    },
    properties: {
      name: '江汉路',
      level: '2A',
      description: '商业步行街'
    }
  }
];

// 创建测试函数
async function testClusterSourceRebuild() {
  console.log('=== 聚合源重建机制验证测试 ===');
  
  // 创建地图实例
  const mapContainer = document.createElement('div');
  mapContainer.style.width = '800px';
  mapContainer.style.height = '600px';
  document.body.appendChild(mapContainer);
  
  const mapUtils = new MapUtils(mapContainer);
  mapUtils.addBaseLayer();
  
  // 创建基于缩放级别的图层
  const fieldRange = {
    type: 'discrete',
    values: [
      { value: '5A', minZoom: 10 },
      { value: '4A', minZoom: 12 },
      { value: '3A', minZoom: 14 },
      { value: '2A', minZoom: 16 }
    ]
  };
  
  const zoomLayer = mapUtils.createZoomBasedVectorLayer('level', fieldRange, '景区图层', {
    enableClustering: true,
    clusterDistance: 40
  });
  
  // 添加测试要素
  const result = await mapUtils.addGeoJsonToLayer(zoomLayer, {
    type: 'FeatureCollection',
    features: testFeatures
  });
  
  console.log('要素添加结果:', result);
  
  // 测试不同缩放级别的聚合源重建
  const testZooms = [8, 10, 12, 14, 16];
  
  for (const zoom of testZooms) {
    console.log(`\n--- 测试缩放级别: ${zoom} ---`);
    
    // 设置缩放级别
    mapUtils.map.getView().setZoom(zoom);
    
    // 等待聚合源重建完成
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 获取聚合图层的数据源
    const clusterSource = zoomLayer.getSource();
    const clusterFeatures = clusterSource.getFeatures();
    
    console.log(`聚合要素数量: ${clusterFeatures.length}`);
    
    // 验证每个聚合要素的组成
    let totalVisibleCount = 0;
    let totalInvisibleCount = 0;
    
    clusterFeatures.forEach((clusterFeature, index) => {
      const childFeatures = clusterFeature.get('features');
      if (childFeatures) {
        const visibleChildCount = childFeatures.filter(child => 
          child.get('visible') !== false
        ).length;
        
        const invisibleChildCount = childFeatures.length - visibleChildCount;
        totalVisibleCount += visibleChildCount;
        totalInvisibleCount += invisibleChildCount;
        
        console.log(`聚合要素 ${index}: ${childFeatures.length} 个子要素, ${visibleChildCount} 个可见, ${invisibleChildCount} 个不可见`);
        
        // 验证不可见要素的等级
        if (invisibleChildCount > 0) {
          const invisibleLevels = {};
          childFeatures.forEach(child => {
            if (child.get('visible') === false) {
              const level = child.get('level');
              invisibleLevels[level] = (invisibleLevels[level] || 0) + 1;
            }
          });
          console.warn(`聚合要素 ${index} 包含不可见要素:`, invisibleLevels);
        }
      }
    });
    
    // 验证聚合源重建结果
    const expectedVisibleCount = testFeatures.filter(feature => {
      const level = feature.properties.level;
      const config = fieldRange.values.find(c => c.value === level);
      return config && zoom >= config.minZoom;
    }).length;
    
    console.log(`预期可见要素: ${expectedVisibleCount}, 实际可见要素: ${totalVisibleCount}`);
    
    if (totalVisibleCount === expectedVisibleCount && totalInvisibleCount === 0) {
      console.log(`✅ 缩放级别 ${zoom} 聚合源重建验证通过`);
    } else {
      console.error(`❌ 缩放级别 ${zoom} 聚合源重建验证失败`);
      console.error(`   预期可见: ${expectedVisibleCount}, 实际可见: ${totalVisibleCount}`);
      console.error(`   不可见要素: ${totalInvisibleCount}`);
    }
  }
  
  // 测试单个要素聚合的属性传递
  console.log('\n--- 测试单个要素聚合属性传递 ---');
  
  // 设置到高缩放级别，确保只有一个5A级要素可见
  mapUtils.map.getView().setZoom(16);
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const clusterSource = zoomLayer.getSource();
  const clusterFeatures = clusterSource.getFeatures();
  
  // 查找单个要素的聚合
  const singleFeatureClusters = clusterFeatures.filter(cluster => {
    const childFeatures = cluster.get('features');
    return childFeatures && childFeatures.length === 1;
  });
  
  if (singleFeatureClusters.length > 0) {
    const singleCluster = singleFeatureClusters[0];
    const processedCluster = mapUtils.ensureSingleClusterFeatureProperties(singleCluster);
    
    console.log('单个聚合要素属性:', processedCluster.getProperties());
    
    // 验证属性是否正确传递
    const originalFeature = singleCluster.get('features')[0];
    const originalProperties = originalFeature.getProperties();
    const clusterProperties = processedCluster.getProperties();
    
    const nameMatch = clusterProperties.name === originalProperties.name;
    const levelMatch = clusterProperties.level === originalProperties.level;
    
    if (nameMatch && levelMatch) {
      console.log('✅ 单个要素聚合属性传递验证通过');
    } else {
      console.error('❌ 单个要素聚合属性传递验证失败');
      console.error('   原始属性:', originalProperties);
      console.error('   聚合属性:', clusterProperties);
    }
  } else {
    console.log('⚠️ 未找到单个要素的聚合进行测试');
  }
  
  // 清理
  document.body.removeChild(mapContainer);
  console.log('\n=== 聚合源重建机制验证测试完成 ===');
}

// 运行测试
testClusterSourceRebuild().catch(console.error);
