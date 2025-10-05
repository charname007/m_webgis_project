/**
 * 测试基于缩放级别的聚合图层过滤逻辑修复
 * 验证聚合图层是否只包含当前缩放级别可见的要素
 */

// 模拟测试数据
const testFeatures = [
  {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [114.305, 30.5928]
    },
    properties: {
      name: '景区A',
      level: '5A',
      value: 5
    }
  },
  {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [114.315, 30.6028]
    },
    properties: {
      name: '景区B',
      level: '4A',
      value: 4
    }
  },
  {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [114.325, 30.6128]
    },
    properties: {
      name: '景区C',
      level: '3A',
      value: 3
    }
  },
  {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [114.335, 30.6228]
    },
    properties: {
      name: '景区D',
      level: '2A',
      value: 2
    }
  },
  {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [114.345, 30.6328]
    },
    properties: {
      name: '景区E',
      level: '1A',
      value: 1
    }
  }
];

// 测试配置
const fieldRangeConfig = {
  type: 'discrete',
  values: [
    { value: '5A', minZoom: 10 },  // 5A景区在缩放级别10+显示
    { value: '4A', minZoom: 12 },  // 4A景区在缩放级别12+显示
    { value: '3A', minZoom: 14 },  // 3A景区在缩放级别14+显示
    { value: '2A', minZoom: 16 },  // 2A景区在缩放级别16+显示
    { value: '1A', minZoom: 18 }   // 1A景区在缩放级别18+显示
  ]
};

// 测试函数
function testZoomBasedClusterLayer() {
  console.log('=== 测试基于缩放级别的聚合图层过滤逻辑 ===');
  
  // 创建地图实例
  const mapUtils = new MapUtils('map');
  mapUtils.addBaseLayer();
  
  // 创建基于缩放级别的图层
  const zoomLayer = mapUtils.createZoomBasedVectorLayer(
    'level',
    fieldRangeConfig,
    '景区聚合图层',
    {
      enableClustering: true,
      clusterDistance: 40,
      autoFitExtent: true
    }
  );
  
  // 添加测试要素
  const features = testFeatures.map(feature => {
    const olFeature = new Feature({
      geometry: new Point(feature.geometry.coordinates),
      name: feature.properties.name,
      level: feature.properties.level,
      value: feature.properties.value
    });
    return olFeature;
  });
  
  mapUtils.addFeaturesToZoomLayer(zoomLayer, features);
  
  // 测试不同缩放级别的可见性
  const testZoomLevels = [8, 10, 12, 14, 16, 18];
  
  testZoomLevels.forEach(zoom => {
    console.log(`\n--- 测试缩放级别 ${zoom} ---`);
    
    // 设置缩放级别
    mapUtils.map.getView().setZoom(zoom);
    
    // 获取可见要素数量
    const visibleCount = mapUtils.getVisibleFeatureCount(zoomLayer);
    console.log(`可见要素数量: ${visibleCount}`);
    
    // 获取聚合源中的要素数量
    const visibleSource = zoomLayer.get('visibleFeaturesSource');
    const clusterSource = zoomLayer.getSource();
    
    if (visibleSource) {
      const visibleFeatures = visibleSource.getFeatures();
      console.log(`可见要素源中的要素数量: ${visibleFeatures.length}`);
      
      // 检查每个要素的可见性
      visibleFeatures.forEach((feature, index) => {
        const level = feature.get('level');
        const name = feature.get('name');
        console.log(`  [${index}] ${name} (${level}) - 可见`);
      });
    }
    
    if (clusterSource && clusterSource instanceof Cluster) {
      const clusterFeatures = clusterSource.getFeatures();
      console.log(`聚合源中的要素数量: ${clusterFeatures.length}`);
      
      // 检查聚合要素
      clusterFeatures.forEach((cluster, index) => {
        const features = cluster.get('features');
        if (features) {
          console.log(`  聚合 ${index}: ${features.length} 个要素`);
        }
      });
    }
  });
  
  console.log('\n=== 测试完成 ===');
}

// 运行测试
if (typeof MapUtils !== 'undefined') {
  testZoomBasedClusterLayer();
} else {
  console.log('请在包含 MapUtils 类的页面中运行此测试');
}
