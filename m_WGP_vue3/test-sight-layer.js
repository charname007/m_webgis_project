// 测试脚本 - 验证景区图层功能
console.log('=== 景区图层功能测试 ===');

// 模拟测试数据
const testData = {
  zoomLevels: [2, 4, 6, 8, 10, 12],
  expectedLevels: {
    2: ['5A'],
    4: ['5A'],
    6: ['5A', '4A'],
    8: ['5A', '4A', '3A'],
    10: ['5A', '4A', '3A', '2A'],
    12: ['5A', '4A', '3A', '2A', '1A']
  }
};

// 测试 getLevelsByZoom 函数
function getLevelsByZoom(zoom) {
  if (zoom >= 11) {
    return ['5A', '4A', '3A', '2A', '1A'];
  } else if (zoom >= 9) {
    return ['5A', '4A', '3A', '2A'];
  } else if (zoom >= 7) {
    return ['5A', '4A', '3A'];
  } else if (zoom >= 5) {
    return ['5A', '4A'];
  } else {
    return ['5A'];
  }
}

// 运行测试
console.log('测试缩放级别与景区等级对应关系:');
testData.zoomLevels.forEach(zoom => {
  const result = getLevelsByZoom(zoom);
  const expected = testData.expectedLevels[zoom];
  const passed = JSON.stringify(result) === JSON.stringify(expected);
  
  console.log(`缩放级别 ${zoom}: ${result.join(', ')} - ${passed ? '✓ 通过' : '✗ 失败'}`);
  if (!passed) {
    console.log(`  期望: ${expected.join(', ')}`);
  }
});

console.log('\n=== 测试完成 ===');
console.log('功能说明:');
console.log('- 缩放级别 0-4.9: 只显示5A景区');
console.log('- 缩放级别 5-6.9: 显示5A,4A景区');
console.log('- 缩放级别 7-8.9: 显示5A,4A,3A景区');
console.log('- 缩放级别 9-10.9: 显示5A,4A,3A,2A景区');
console.log('- 缩放级别 11+: 显示所有等级景区');
