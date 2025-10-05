/**
 * 聚合要素属性统计修复验证测试
 * 验证聚合要素属性统计只包含可见要素，而不是所有要素
 */

import MapUtils from './src/components/mapUtils.js';

// 测试数据 - 模拟不同等级的景区
const testFeatures = [
  { level: '5A', name: '黄鹤楼', coordinates: [114.305, 30.5928] },
  { level: '5A', name: '东湖', coordinates: [114.415, 30.5558] },
  { level: '4A', name: '归元寺', coordinates: [114.255, 30.5628] },
  { level: '4A', name: '古琴台', coordinates: [114.275, 30.5528] },
  { level: '4A', name: '晴川阁', coordinates: [114.285, 30.5728] },
  { level: '3A', name: '长春观', coordinates: [114.315, 30.5428] },
  { level: '3A', name: '宝通寺', coordinates: [114.325, 30.5328] },
  { level: '3A', name: '起义门', coordinates: [114.295, 30.5228] }
];

// 缩放级别配置 - 5A级在10级显示，4A级在12级显示，3A级在14级显示
const zoomConfig = {
  fieldName: 'level',
  fieldRange: {
    type: 'discrete',
    values: [
      { value: '5A', minZoom: 10 },
      { value: '4A', minZoom: 12 },
      { value: '3A', minZoom: 14 }
    ]
  }
};

// 测试函数
async function testClusterPropertyFix() {
  console.log('=== 聚合要素属性统计修复验证测试 ===');
  
  // 创建地图容器
  const container = document.createElement('div');
  container.style.width = '800px';
  container.style.height = '600px';
  container.style.border = '1px solid #ccc';
  document.body.appendChild(container);
  
  // 初始化地图工具
  const mapUtils = new MapUtils(container);
  mapUtils.addBaseLayer();
  
  // 创建基于缩放级别的图层
  const layer = mapUtils.createZoomBasedVectorLayer(
    zoomConfig.fieldName,
    zoomConfig.fieldRange,
    '景区图层',
    { enableClustering: true }
  );
  
  // 添加测试要素
  const features = testFeatures.map(feature => {
    const olFeature = new ol.Feature({
      geometry: new ol.geom.Point(feature.coordinates),
      level: feature.level,
      name: feature.name,
      type: '景区'
    });
    return olFeature;
  });
  
  mapUtils.addFeaturesToZoomLayer(layer, features);
  
  // 测试不同缩放级别的聚合要素属性统计
  console.log('\n--- 测试不同缩放级别的聚合要素属性统计 ---');
  
  // 测试缩放级别 10 - 应该只显示 5A 级要素
  console.log('\n[测试] 缩放级别 10 - 应该只显示 5A 级要素');
  mapUtils.map.getView().setZoom(10);
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // 获取聚合要素并检查属性
  const clusterSource = layer.getSource();
  const clusterFeatures = clusterSource.getFeatures();
  
  console.log(`聚合要素数量: ${clusterFeatures.length}`);
  
  clusterFeatures.forEach((clusterFeature, index) => {
    const features = clusterFeature.get('features');
    const featureCount = clusterFeature.get('featureCount');
    const levelDistribution = clusterFeature.get('levelDistribution');
    
    console.log(`聚合要素 ${index}:`);
    console.log(`  - 要素总数: ${featureCount}`);
    console.log(`  - 等级分布:`, levelDistribution);
    console.log(`  - 实际子要素数量: ${features ? features.length : 0}`);
    
    // 验证：在缩放级别10，应该只有5A级要素
    if (levelDistribution) {
      const has5A = levelDistribution['5A'] > 0;
      const has4A = levelDistribution['4A'] > 0;
      const has3A = levelDistribution['3A'] > 0;
      
      console.log(`  - 验证结果: 5A=${has5A}, 4A=${has4A}, 3A=${has3A}`);
      
      if (has5A && !has4A && !has3A) {
        console.log('  ✅ 验证通过: 只包含5A级要素');
      } else {
        console.log('  ❌ 验证失败: 包含不应该显示的要素');
      }
    }
  });
  
  // 测试缩放级别 12 - 应该显示 5A 和 4A 级要素
  console.log('\n[测试] 缩放级别 12 - 应该显示 5A 和 4A 级要素');
  mapUtils.map.getView().setZoom(12);
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const clusterFeatures12 = clusterSource.getFeatures();
  
  console.log(`聚合要素数量: ${clusterFeatures12.length}`);
  
  clusterFeatures12.forEach((clusterFeature, index) => {
    const featureCount = clusterFeature.get('featureCount');
    const levelDistribution = clusterFeature.get('levelDistribution');
    
    console.log(`聚合要素 ${index}:`);
    console.log(`  - 要素总数: ${featureCount}`);
    console.log(`  - 等级分布:`, levelDistribution);
    
    if (levelDistribution) {
      const has5A = levelDistribution['5A'] > 0;
      const has4A = levelDistribution['4A'] > 0;
      const has3A = levelDistribution['3A'] > 0;
      
      console.log(`  - 验证结果: 5A=${has5A}, 4A=${has4A}, 3A=${has3A}`);
      
      if (has5A && has4A && !has3A) {
        console.log('  ✅ 验证通过: 只包含5A和4A级要素');
      } else {
        console.log('  ❌ 验证失败: 包含不应该显示的要素');
      }
    }
  });
  
  // 测试缩放级别 14 - 应该显示所有要素
  console.log('\n[测试] 缩放级别 14 - 应该显示所有要素');
  mapUtils.map.getView().setZoom(14);
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const clusterFeatures14 = clusterSource.getFeatures();
  
  console.log(`聚合要素数量: ${clusterFeatures14.length}`);
  
  clusterFeatures14.forEach((clusterFeature, index) => {
    const featureCount = clusterFeature.get('featureCount');
    const levelDistribution = clusterFeature.get('levelDistribution');
    
    console.log(`聚合要素 ${index}:`);
    console.log(`  - 要素总数: ${featureCount}`);
    console.log(`  - 等级分布:`, levelDistribution);
    
    if (levelDistribution) {
      const has5A = levelDistribution['5A'] > 0;
      const has4A = levelDistribution['4A'] > 0;
      const has3A = levelDistribution['3A'] > 0;
      
      console.log(`  - 验证结果: 5A=${has5A}, 4A=${has4A}, 3A=${has3A}`);
      
      if (has5A && has4A && has3A) {
        console.log('  ✅ 验证通过: 包含所有等级要素');
      } else {
        console.log('  ❌ 验证失败: 缺少应该显示的要素');
      }
    }
  });
  
  // 测试单个要素聚合的属性传递
  console.log('\n--- 测试单个要素聚合的属性传递 ---');
  
  // 放大到足够级别，让要素分散
  mapUtils.map.getView().setZoom(16);
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const singleClusterFeatures = clusterSource.getFeatures().filter(feature => {
    const features = feature.get('features');
    return features && features.length === 1;
  });
  
  console.log(`单个要素聚合数量: ${singleClusterFeatures.length}`);
  
  singleClusterFeatures.forEach((clusterFeature, index) => {
    const isSingleFeatureCluster = clusterFeature.get('isSingleFeatureCluster');
    const originalFeature = clusterFeature.get('originalFeature');
    const name = clusterFeature.get('name');
    const level = clusterFeature.get('level');
    
    console.log(`单个聚合要素 ${index}:`);
    console.log(`  - 是否为单个要素聚合: ${isSingleFeatureCluster}`);
    console.log(`  - 名称属性: ${name}`);
    console.log(`  - 等级属性: ${level}`);
    console.log(`  - 原始要素:`, originalFeature ? '存在' : '不存在');
    
    if (name && level) {
      console.log('  ✅ 验证通过: 属性正确传递');
    } else {
      console.log('  ❌ 验证失败: 属性未正确传递');
    }
  });
  
  console.log('\n=== 测试完成 ===');
  
  // 清理
  document.body.removeChild(container);
}

// 运行测试
testClusterPropertyFix().catch(console.error);
