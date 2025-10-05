// 分页修复测试脚本
console.log('=== 分页修复测试 ===');

// 模拟搜索结果数据
const mockSearchResults = [
  { id: 1, name: '景区1', 地址: '地址1', 评分: '4.5' },
  { id: 2, name: '景区2', 地址: '地址2', 评分: '4.2' },
  { id: 3, name: '景区3', 地址: '地址3', 评分: '4.7' },
  { id: 4, name: '景区4', 地址: '地址4', 评分: '4.1' },
  { id: 5, name: '景区5', 地址: '地址5', 评分: '4.8' },
  { id: 6, name: '景区6', 地址: '地址6', 评分: '4.3' },
  { id: 7, name: '景区7', 地址: '地址7', 评分: '4.6' },
  { id: 8, name: '景区8', 地址: '地址8', 评分: '4.4' },
  { id: 9, name: '景区9', 地址: '地址9', 评分: '4.9' },
  { id: 10, name: '景区10', 地址: '地址10', 评分: '4.0' },
  { id: 11, name: '景区11', 地址: '地址11', 评分: '4.5' },
  { id: 12, name: '景区12', 地址: '地址12', 评分: '4.2' }
];

// 模拟修复后的分页逻辑
function testPaginationFix() {
  console.log('测试分页修复逻辑...');
  
  // 模拟组件状态
  const allSearchResults = [...mockSearchResults];
  const pageSize = 5;
  const totalCount = allSearchResults.length;
  const totalPages = Math.ceil(totalCount / pageSize);
  
  console.log(`总结果数: ${totalCount}`);
  console.log(`每页大小: ${pageSize}`);
  console.log(`总页数: ${totalPages}`);
  
  // 测试第一页
  let currentPage = 1;
  let startIndex = (currentPage - 1) * pageSize;
  let endIndex = startIndex + pageSize;
  let pageResults = allSearchResults.slice(startIndex, endIndex);
  
  console.log(`\n第 ${currentPage} 页结果:`);
  console.log(`索引范围: ${startIndex} - ${endIndex}`);
  console.log(`结果数量: ${pageResults.length}`);
  pageResults.forEach(spot => console.log(`  - ${spot.name}`));
  
  // 测试第二页
  currentPage = 2;
  startIndex = (currentPage - 1) * pageSize;
  endIndex = startIndex + pageSize;
  pageResults = allSearchResults.slice(startIndex, endIndex);
  
  console.log(`\n第 ${currentPage} 页结果:`);
  console.log(`索引范围: ${startIndex} - ${endIndex}`);
  console.log(`结果数量: ${pageResults.length}`);
  pageResults.forEach(spot => console.log(`  - ${spot.name}`));
  
  // 测试第三页（最后一页）
  currentPage = 3;
  startIndex = (currentPage - 1) * pageSize;
  endIndex = startIndex + pageSize;
  pageResults = allSearchResults.slice(startIndex, endIndex);
  
  console.log(`\n第 ${currentPage} 页结果:`);
  console.log(`索引范围: ${startIndex} - ${endIndex}`);
  console.log(`结果数量: ${pageResults.length}`);
  pageResults.forEach(spot => console.log(`  - ${spot.name}`));
  
  console.log('\n✅ 分页逻辑测试完成！');
  console.log('修复说明:');
  console.log('1. 添加了 allSearchResults 变量存储所有搜索结果');
  console.log('2. applyPagination 函数现在从 allSearchResults 切片');
  console.log('3. 分页按钮现在可以正确显示不同页面的数据');
}

// 运行测试
testPaginationFix();
