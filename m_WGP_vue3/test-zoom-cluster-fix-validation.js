/**
 * 聚合要素过滤修复验证脚本
 * 测试基于缩放级别的图层中聚合要素是否只包含当前可见要素
 */

// 测试配置
const testConfig = {
  fieldName: 'level',
  fieldRange: {
    type: 'discrete',
    values: [
      { value: '5A', minZoom: 3 },
      { value: '4A', minZoom: 6 },
      { value: '3A', minZoom: 9 },
      { value: '2A', minZoom: 12 },
      { value: '1A', minZoom: 15 }
    ]
  },
  layerName: '景区等级测试图层',
  testZoomLevels: [3, 6, 9, 12, 15, 18]
};

/**
 * 创建测试要素
 */
function createTestFeatures() {
  const features = [];
  
  // 创建不同等级的测试要素
  const levels = ['5A', '4A', '3A', '2A', '1A'];
  const coordinates = [
    [114.305, 30.5928], // 武汉中心
    [114.315, 30.6028], // 稍微偏移
    [114.295, 30.5828], // 稍微偏移
    [114.325, 30.6128], // 更远
    [114.285, 30.5728]  // 更远
  ];
  
  levels.forEach((level, index) => {
    const feature = new ol.Feature({
      geometry: new ol.geom.Point(coordinates[index]),
      level: level,
      name: `测试${level}景区`,
      description: `这是一个${level}级景区的测试要素`
    });
    features.push(feature);
  });
  
  return features;
}

/**
 * 验证聚合要素可见性
 */
function validateClusterVisibility(mapUtils, layer, currentZoom) {
  console.log(`\n=== 验证缩放级别 ${currentZoom} 的聚合要素可见性 ===`);
  
  const layerSource = layer.getSource();
  const clusterFeatures = layerSource.getFeatures();
  
  console.log(`聚合要素数量: ${clusterFeatures.length}`);
  
  let totalVisibleFeatures = 0;
  let totalInvisibleFeatures = 0;
  
  clusterFeatures.forEach((clusterFeature, index) => {
    const childFeatures = clusterFeature.get('features');
    if (childFeatures) {
      console.log(`\n聚合要素 ${index}:`);
      console.log(`  包含子要素数量: ${childFeatures.length}`);
      
      let visibleInCluster = 0;
      let invisibleInCluster = 0;
      
      childFeatures.forEach((child, childIndex) => {
        const level = child.get('level');
        const visible = child.get('visible');
        
        if (visible) {
          visibleInCluster++;
          console.log(`    子要素 ${childIndex}: ${level} - 可见`);
        } else {
          invisibleInCluster++;
          console.log(`    子要素 ${childIndex}: ${level} - 不可见`);
        }
      });
      
      totalVisibleFeatures += visibleInCluster;
      totalInvisibleFeatures += invisibleInCluster;
      
      if (invisibleInCluster > 0) {
        console.warn(`  ⚠️ 警告: 聚合要素 ${index} 包含 ${invisibleInCluster} 个不可见要素`);
      } else {
        console.log(`  ✅ 聚合要素 ${index} 完全由可见要素组成`);
      }
    }
  });
  
  console.log(`\n=== 汇总统计 ===`);
  console.log(`可见要素总数: ${totalVisibleFeatures}`);
  console.log(`不可见要素总数: ${totalInvisibleFeatures}`);
  
  if (totalInvisibleFeatures === 0) {
    console.log('✅ 验证通过: 所有聚合要素只包含可见要素');
    return true;
  } else {
    console.error('❌ 验证失败: 发现聚合要素包含不可见要素');
    return false;
  }
}

/**
 * 运行测试
 */
async function runZoomClusterFixTest() {
  console.log('🚀 开始聚合要素过滤修复验证测试');
  
  try {
    // 创建地图工具实例
    const mapUtils = new MapUtils('map');
    mapUtils.addBaseLayer();
    
    // 创建基于缩放级别的图层
    const layer = mapUtils.createZoomBasedVectorLayer(
      testConfig.fieldName,
      testConfig.fieldRange,
      testConfig.layerName,
      {
        enableClustering: true,
        clusterDistance: 40
      }
    );
    
    // 添加测试要素
    const testFeatures = createTestFeatures();
    mapUtils.addFeaturesToZoomLayer(layer, testFeatures);
    
    console.log('✅ 测试图层和要素创建完成');
    
    // 等待图层加载完成
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 测试不同缩放级别
    let allTestsPassed = true;
    
    for (const zoomLevel of testConfig.testZoomLevels) {
      console.log(`\n📊 测试缩放级别: ${zoomLevel}`);
      
      // 设置缩放级别
      mapUtils.map.getView().setZoom(zoomLevel);
      
      // 等待缩放完成和聚合更新
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // 手动刷新可见性
      mapUtils.refreshZoomBasedLayerVisibility(layer);
      
      // 等待聚合更新
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // 验证聚合要素可见性
      const testPassed = validateClusterVisibility(mapUtils, layer, zoomLevel);
      
      if (!testPassed) {
        allTestsPassed = false;
      }
    }
    
    // 最终测试结果
    console.log('\n🎯 最终测试结果:');
    if (allTestsPassed) {
      console.log('✅ 所有测试通过！聚合要素过滤修复成功');
    } else {
      console.log('❌ 部分测试失败，需要进一步调试');
    }
    
    return allTestsPassed;
    
  } catch (error) {
    console.error('❌ 测试执行失败:', error);
    return false;
  }
}

/**
 * 运行调试模式测试
 */
function runDebugTest() {
  console.log('🔍 运行调试模式测试');
  
  const mapUtils = new MapUtils('map');
  mapUtils.addBaseLayer();
  
  const layer = mapUtils.createZoomBasedVectorLayer(
    testConfig.fieldName,
    testConfig.fieldRange,
    testConfig.layerName,
    {
      enableClustering: true,
      clusterDistance: 40
    }
  );
  
  const testFeatures = createTestFeatures();
  mapUtils.addFeaturesToZoomLayer(layer, testFeatures);
  
  // 添加调试信息输出
  const originalUpdateMethod = mapUtils._MapUtils__updateFeatureVisibility;
  mapUtils._MapUtils__updateFeatureVisibility = function(layer) {
    console.log('🔧 调试: 开始更新要素可见性');
    const result = originalUpdateMethod.call(this, layer);
    console.log('🔧 调试: 要素可见性更新完成');
    return result;
  };
  
  console.log('✅ 调试模式设置完成');
  return mapUtils;
}

// 导出测试函数供外部调用
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    runZoomClusterFixTest,
    runDebugTest,
    testConfig,
    createTestFeatures
  };
}

// 如果直接在浏览器中运行，自动执行测试
if (typeof window !== 'undefined') {
  console.log('🌐 在浏览器环境中检测到测试脚本');
  
  // 等待OpenLayers加载完成
  if (typeof ol !== 'undefined' && typeof MapUtils !== 'undefined') {
    console.log('✅ OpenLayers 和 MapUtils 已加载，可以运行测试');
    
    // 提供全局测试函数
    window.runZoomClusterFixTest = runZoomClusterFixTest;
    window.runDebugTest = runDebugTest;
    
    console.log('📝 测试函数已注册到全局作用域:');
    console.log('   - runZoomClusterFixTest() - 运行完整测试');
    console.log('   - runDebugTest() - 运行调试模式测试');
  } else {
    console.warn('⚠️ OpenLayers 或 MapUtils 未加载，无法运行测试');
  }
}
