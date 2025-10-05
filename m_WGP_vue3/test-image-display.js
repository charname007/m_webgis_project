// 测试图片显示功能
console.log('测试搜索组件图片显示功能');

// 模拟测试数据
const testSpots = [
  {
    id: 1,
    name: '故宫博物院',
    地址: '北京市东城区景山前街4号',
    评分: '4.8',
    门票: '60元',
    开放时间: '08:30-17:00',
    建议游玩时间: '3-4小时',
    建议季节: '春秋季',
    小贴士: '建议提前预约门票',
    介绍: '中国明清两代的皇家宫殿，旧称紫禁城'
  },
  {
    id: 2,
    name: '颐和园',
    地址: '北京市海淀区新建宫门路19号',
    评分: '4.7',
    门票: '30元',
    开放时间: '06:30-18:00',
    建议游玩时间: '2-3小时',
    建议季节: '春夏秋季',
    小贴士: '建议从东宫门进入',
    介绍: '中国清朝时期皇家园林，前身为清漪园'
  },
  {
    id: 3,
    name: '长城',
    地址: '北京市延庆区八达岭镇',
    评分: '4.9',
    门票: '45元',
    开放时间: '06:30-19:00',
    建议游玩时间: '4-5小时',
    建议季节: '春秋季',
    小贴士: '建议穿着舒适的运动鞋',
    介绍: '中国古代的军事防御工程，世界文化遗产'
  }
];

console.log('测试数据准备完成:', testSpots.map(spot => spot.name));

// 测试图片加载状态管理
console.log('\n测试图片加载状态管理:');
const imageLoadingStates = new Map();
const loadedImages = new Map();

// 模拟图片加载过程
function simulateImageLoading(spotName) {
  console.log(`开始加载图片: ${spotName}`);
  imageLoadingStates.set(spotName, 'loading');
  
  // 模拟异步加载
  setTimeout(() => {
    const success = Math.random() > 0.3; // 70%成功率
    if (success) {
      const imageUrl = `https://example.com/images/${spotName}.jpg`;
      loadedImages.set(spotName, imageUrl);
      imageLoadingStates.set(spotName, 'loaded');
      console.log(`✅ 图片加载成功: ${spotName}`);
    } else {
      imageLoadingStates.set(spotName, 'error');
      console.log(`❌ 图片加载失败: ${spotName}`);
    }
  }, 1000 + Math.random() * 2000);
}

// 测试分批加载
function batchLoadImages(spots) {
  console.log('\n开始分批加载图片...');
  const batchSize = 2;
  
  for (let i = 0; i < spots.length; i += batchSize) {
    const batch = spots.slice(i, i + batchSize);
    console.log(`加载批次 ${Math.floor(i/batchSize) + 1}:`, batch.map(spot => spot.name));
    
    batch.forEach(spot => {
      simulateImageLoading(spot.name);
    });
  }
}

// 运行测试
batchLoadImages(testSpots);

// 检查加载状态
setTimeout(() => {
  console.log('\n最终加载状态:');
  testSpots.forEach(spot => {
    const state = imageLoadingStates.get(spot.name) || 'idle';
    const image = loadedImages.get(spot.name);
    console.log(`${spot.name}: ${state} ${image ? `(${image})` : ''}`);
  });
}, 5000);

console.log('\n测试脚本执行完成，请检查浏览器控制台查看实际效果');
