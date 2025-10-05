/**
 * 聚合要素属性显示修复验证脚本
 * 用于测试修复后的聚合要素属性显示功能
 */

// 模拟聚合要素数据
const mockClusterFeatures = [
  {
    name: '黄鹤楼',
    level: '5A',
    properties: {
      name: '黄鹤楼',
      level: '5A',
      address: '武汉市武昌区蛇山西山坡特1号'
    }
  },
  {
    name: '东湖风景区',
    level: '5A',
    properties: {
      name: '东湖风景区',
      level: '5A',
      address: '武汉市武昌区沿湖大道16号'
    }
  },
  {
    name: '归元禅寺',
    level: '4A',
    properties: {
      name: '归元禅寺',
      level: '4A',
      address: '武汉市汉阳区翠微路20号'
    }
  }
];

// 测试修复后的属性提取逻辑
function testFixedClusterFeatureExtraction() {
  console.log('=== 聚合要素属性提取修复验证 ===');
  
  // 模拟修复前的错误逻辑（使用 .map(f => f.properties)）
  const oldLogic = mockClusterFeatures.map(f => f.properties);
  console.log('修复前逻辑结果:', oldLogic);
  console.log('修复前属性结构问题:', oldLogic[0].properties); // 这会是 undefined
  
  // 模拟修复后的正确逻辑（直接使用原始要素）
  const newLogic = mockClusterFeatures;
  console.log('修复后逻辑结果:', newLogic);
  console.log('修复后属性结构正确:', newLogic[0].properties); // 这会是正确的属性对象
  
  // 测试单个要素的聚合情况
  const singleFeatureCluster = [mockClusterFeatures[0]];
  console.log('单个要素聚合测试:', singleFeatureCluster);
  console.log('单个要素属性:', singleFeatureCluster[0].properties);
  
  // 测试属性显示逻辑
  const featuresList = newLogic
    .slice(0, 10)
    .map((f, i) => `${i + 1}. ${f.name || f.properties?.name || '未知'} (${f.level || f.properties?.level || '未知'})`)
    .join('\n');
  
  console.log('修复后的要素列表显示:');
  console.log(featuresList);
  
  // 测试等级分布统计
  const levelDistribution = {};
  newLogic.forEach(feature => {
    const level = feature.level || feature.properties?.level;
    if (level) {
      levelDistribution[level] = (levelDistribution[level] || 0) + 1;
    }
  });
  
  console.log('等级分布统计:', levelDistribution);
  
  const levelText = Object.entries(levelDistribution)
    .sort((a, b) => b[1] - a[1])
    .map(([level, count]) => `${level}: ${count}个`)
    .join(', ');
  
  console.log('格式化等级分布:', levelText);
  
  console.log('=== 验证完成 ===');
}

// 运行测试
testFixedClusterFeatureExtraction();

// 导出测试函数供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    testFixedClusterFeatureExtraction,
    mockClusterFeatures
  };
}
