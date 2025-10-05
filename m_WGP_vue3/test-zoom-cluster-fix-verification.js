/**
 * 测试脚本：验证基于缩放级别的图层聚合要素过滤修复
 * 用于验证低等级要素在缩放等级变小时不会显示，且不会和其他高等级要素聚合在一起
 */

// 测试配置
const testConfig = {
  fieldName: 'level',
  fieldRange: {
    type: 'discrete',
    values: [
      { value: '5A', minZoom: 10 },
      { value: '4A', minZoom: 12 },
      { value: '3A', minZoom: 14 },
      { value: '2A', minZoom: 16 },
      { value: '1A', minZoom: 18 }
    ]
  },
  layerName: '测试景区图层',
  options: {
    enableClustering: true,
    clusterDistance: 40,
    autoFitExtent: false
  }
};

// 测试数据 - 模拟不同等级的景区
const testFeatures = [
  {
    type: 'Feature',
    properties: {
      name: '黄鹤楼',
      level: '5A',
      description: '武汉著名景点'
    },
    geometry: {
      type: 'Point',
      coordinates: [114.305, 30.5928]
    }
  },
  {
    type: 'Feature',
    properties: {
      name: '东湖',
      level: '4A',
      description: '武汉东湖风景区'
    },
    geometry: {
      type: 'Point',
      coordinates: [114.415, 30.5528]
    }
  },
  {
    type: 'Feature',
    properties: {
      name: '归元寺',
      level: '3A',
      description: '武汉归元禅寺'
    },
    geometry: {
      type: 'Point',
      coordinates: [114.255, 30.5728]
    }
  },
  {
    type: 'Feature',
    properties: {
      name: '古琴台',
      level: '2A',
      description: '武汉古琴台'
    },
    geometry: {
      type: 'Point',
      coordinates: [114.285, 30.5428]
    }
  },
  {
    type: 'Feature',
    properties: {
      name: '晴川阁',
      level: '1A',
      description: '武汉晴川阁'
    },
    geometry: {
      type: 'Point',
      coordinates: [114.295, 30.5628]
    }
  }
];

/**
 * 运行测试
 */
async function runZoomClusterFixTest() {
  console.log('=== 开始基于缩放级别的图层聚合要素过滤测试 ===');
  
  try {
    // 1. 创建基于缩放级别的图层
    const zoomLayer = mapUtils.createZoomBasedVectorLayer(
      testConfig.fieldName,
      testConfig.fieldRange,
      testConfig.layerName,
      testConfig.options
    );
    
    console.log('✅ 基于缩放级别的图层创建成功');
    
    // 2. 添加测试要素
    const addResult = await mapUtils.addGeoJsonToLayer(zoomLayer, {
      type: 'FeatureCollection',
      features: testFeatures
    });
    
    console.log('✅ 测试要素添加成功:', addResult);
    
    // 3. 测试不同缩放级别的可见性
    console.log('\n=== 测试不同缩放级别的要素可见性 ===');
    
    // 测试缩放级别 8 (应该只显示 5A 景区)
    await testZoomLevel(8, '5A', zoomLayer);
    
    // 测试缩放级别 11 (应该显示 5A 和 4A 景区)
    await testZoomLevel(11, '5A,4A', zoomLayer);
    
    // 测试缩放级别 13 (应该显示 5A,4A,3A 景区)
    await testZoomLevel(13, '5A,4A,3A', zoomLayer);
    
    // 测试缩放级别 15 (应该显示 5A,4A,3A,2A 景区)
    await testZoomLevel(15, '5A,4A,3A,2A', zoomLayer);
    
    // 测试缩放级别 17 (应该显示所有景区)
    await testZoomLevel(17, '5A,4A,3A,2A,1A', zoomLayer);
    
    console.log('\n=== 测试聚合要素过滤 ===');
    
    // 4. 测试聚合要素是否只包含可见要素
    await testClusterFiltering(zoomLayer);
    
    console.log('\n✅ 所有测试完成！基于缩放级别的图层聚合要素过滤修复验证成功');
    
  } catch (error) {
    console.error('❌ 测试失败:', error);
  }
}

/**
 * 测试特定缩放级别的要素可见性
 */
async function testZoomLevel(zoomLevel, expectedLevels, zoomLayer) {
  console.log(`\n--- 测试缩放级别 ${zoomLevel} ---`);
  
  // 设置缩放级别
  mapUtils.map.getView().setZoom(zoomLevel);
  
  // 等待视图更新
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // 获取当前可见要素
  const visibleCount = mapUtils.getVisibleFeatureCount(zoomLayer);
  const currentZoom = mapUtils.map.getView().getZoom();
  
  console.log(`当前缩放级别: ${currentZoom.toFixed(2)}`);
  console.log(`可见要素数量: ${visibleCount}`);
  console.log(`预期显示的等级: ${expectedLevels}`);
  
  // 验证聚合图层中的要素
  const layerSource = zoomLayer.getSource();
  if (layerSource instanceof Cluster) {
    const clusterFeatures = layerSource.getFeatures();
    console.log(`聚合要素数量: ${clusterFeatures.length}`);
    
    // 检查每个聚合要素
    clusterFeatures.forEach((cluster, index) => {
      const features = cluster.get('features');
      if (features) {
        console.log(`聚合 ${index + 1}: ${features.length} 个要素`);
        
        // 检查每个要素的等级
        features.forEach(feature => {
          const level = feature.get('level');
          const name = feature.get('name');
          console.log(`  - ${name} (${level})`);
        });
      }
    });
  }
  
  // 验证是否只有预期等级的要素可见
  const allFeaturesSource = zoomLayer.get('allFeaturesSource');
  const allFeatures = allFeaturesSource.getFeatures();
  
  let visibleFeatures = [];
  let hiddenFeatures = [];
  
  allFeatures.forEach(feature => {
    const level = feature.get('level');
    const name = feature.get('name');
    const isVisible = feature.get('visible');
    
    if (isVisible) {
      visibleFeatures.push(`${name} (${level})`);
    } else {
      hiddenFeatures.push(`${name} (${level})`);
    }
  });
  
  console.log(`可见要素: ${visibleFeatures.join(', ')}`);
  console.log(`隐藏要素: ${hiddenFeatures.join(', ')}`);
  
  // 验证结果
  const expectedLevelsArray = expectedLevels.split(',');
  let isValid = true;
  
  visibleFeatures.forEach(visibleFeature => {
    const level = visibleFeature.match(/\(([^)]+)\)/)[1];
    if (!expectedLevelsArray.includes(level)) {
      console.error(`❌ 错误: ${visibleFeature} 不应该在缩放级别 ${zoomLevel} 可见`);
      isValid = false;
    }
  });
  
  if (isValid) {
    console.log(`✅ 缩放级别 ${zoomLevel} 的要素可见性验证通过`);
  }
}

/**
 * 测试聚合要素过滤
 */
async function testClusterFiltering(zoomLayer) {
  console.log('\n--- 测试聚合要素过滤 ---');
  
  // 设置到中等缩放级别 (应该显示 5A,4A,3A)
  mapUtils.map.getView().setZoom(13);
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const layerSource = zoomLayer.getSource();
  if (layerSource instanceof Cluster) {
    const clusterFeatures = layerSource.getFeatures();
    
    console.log(`当前聚合要素数量: ${clusterFeatures.length}`);
    
    // 检查每个聚合要素是否只包含可见要素
    clusterFeatures.forEach((cluster, index) => {
      const features = cluster.get('features');
      if (features) {
        console.log(`聚合 ${index + 1}: ${features.length} 个要素`);
        
        let hasInvisibleFeature = false;
        features.forEach(feature => {
          const level = feature.get('level');
          const name = feature.get('name');
          const isVisible = feature.get('visible');
          
          console.log(`  - ${name} (${level}) - 可见: ${isVisible}`);
          
          if (!isVisible) {
            hasInvisibleFeature = true;
            console.error(`❌ 错误: 聚合要素中包含不可见要素 ${name} (${level})`);
          }
        });
        
        if (!hasInvisibleFeature) {
          console.log(`✅ 聚合 ${index + 1} 只包含可见要素`);
        }
      }
    });
  }
  
  // 验证聚合要素总数与可见要素总数一致
  const allFeaturesSource = zoomLayer.get('allFeaturesSource');
  const allFeatures = allFeaturesSource.getFeatures();
  
  const visibleFeatures = allFeatures.filter(feature => feature.get('visible'));
  const clusterFeatures = layerSource.getFeatures();
  
  let totalFeaturesInClusters = 0;
  clusterFeatures.forEach(cluster => {
    const features = cluster.get('features');
    if (features) {
      totalFeaturesInClusters += features.length;
    }
  });
  
  console.log(`可见要素总数: ${visibleFeatures.length}`);
  console.log(`聚合要素中的要素总数: ${totalFeaturesInClusters}`);
  
  if (visibleFeatures.length === totalFeaturesInClusters) {
    console.log('✅ 聚合要素过滤验证通过 - 聚合图层只包含可见要素');
  } else {
    console.error('❌ 聚合要素过滤验证失败 - 聚合图层包含不可见要素');
  }
}

/**
 * 初始化测试环境
 */
function initTestEnvironment() {
  console.log('初始化测试环境...');
  
  // 创建地图容器
  const mapContainer = document.createElement('div');
  mapContainer.id = 'test-map';
  mapContainer.style.width = '800px';
  mapContainer.style.height = '600px';
  mapContainer.style.border = '1px solid #ccc';
  document.body.appendChild(mapContainer);
  
  // 初始化地图工具
  window.mapUtils = new MapUtils('test-map');
  mapUtils.addBaseLayer();
  
  console.log('测试环境初始化完成');
}

// 运行测试
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM 加载完成，开始测试...');
  
  // 添加测试按钮
  const testButton = document.createElement('button');
  testButton.textContent = '运行基于缩放级别的图层聚合要素过滤测试';
  testButton.style.cssText = `
    position: fixed;
    top: 10px;
    left: 10px;
    z-index: 10000;
    padding: 10px 20px;
    background: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  `;
  testButton.onclick = function() {
    runZoomClusterFixTest();
  };
  document.body.appendChild(testButton);
  
  // 初始化测试环境
  initTestEnvironment();
});

// 导出测试函数供其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    runZoomClusterFixTest,
    testZoomLevel,
    testClusterFiltering,
    initTestEnvironment
  };
}
