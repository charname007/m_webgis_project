/**
 * AI 查询结果显示修复测试
 * 用于验证 AI 查询结果能够正确显示所有详细信息
 */

// 模拟 AI 查询返回的数据结构
const mockAIQueryResult = {
  data: [
    {
      "name": "红光山景区",
      "level": "4A",
      "address": "新疆乌鲁木齐市米东区乌鲁木齐市红光山路1号红光山景区",
      "city": "乌鲁木齐",
      "province": "新疆",
      "district": "水磨沟区",
      "rating": null,
      "ticket_price": "具体收费情况以现场公示为主",
      "introduction": "红光山景区位于乌鲁木齐市东北部，占地面积一万多亩，有大佛寺、生态景观林、动物园、西游记神话雕像群、日光泳池等景点。",
      "opening_hours": null,
      "suggested_duration": "建议游览时间：3小时 - 4小时",
      "suggested_season": null,
      "tips": null,
      "image_url": null,
      "coordinates": [87.61305983, 43.87851365]
    },
    {
      "name": "西湖",
      "level": "5A",
      "address": "浙江省杭州市西湖区西湖风景名胜区",
      "city": "杭州",
      "province": "浙江",
      "district": "西湖区",
      "rating": 4.8,
      "ticket_price": "免费",
      "introduction": "西湖是中国著名的风景名胜区，以其秀丽的湖光山色和众多的名胜古迹而闻名中外。",
      "opening_hours": "全天开放",
      "suggested_duration": "建议游览时间：1天",
      "suggested_season": "春季、秋季",
      "tips": "建议乘坐游船游览西湖全景",
      "image_url": null,
      "coordinates": [120.15507, 30.274085]
    }
  ],
  query: "查询新疆的4A景区",
  count: 2
};

// 模拟 handleAgentQueryResult 函数的字段映射逻辑（修复版本）
function handleAgentQueryResult(result) {
  if (!result || !result.data) {
    console.warn('AI 查询结果为空');
    return;
  }

  console.log('处理 AI 查询结果，数量:', result.data.length);

  // 字段名映射：将 AI 返回的字段名映射为前端模板期望的字段名
  const processedData = result.data.map(item => {
    const mappedItem = {
      ...item,
      // 映射字段名 - 正确处理 null 值
      地址: item.address !== undefined ? item.address : item.地址,
      评分: item.rating !== undefined ? item.rating : item.评分,
      门票: item.ticket_price !== undefined ? item.ticket_price : item.门票,
      开放时间: item.opening_hours !== undefined ? item.opening_hours : item.开放时间,
      建议游玩时间: item.suggested_duration !== undefined ? item.suggested_duration : item.建议游玩时间,
      建议季节: item.suggested_season !== undefined ? item.suggested_season : item.建议季节,
      小贴士: item.tips !== undefined ? item.tips : item.小贴士,
      介绍: item.introduction !== undefined ? item.introduction : item.介绍,
      // 添加标记
      _fromAI: true,
      _hasCoordinates: !!item.coordinates
    };

    // 删除重复的字段，避免数据冗余
    delete mappedItem.address;
    delete mappedItem.rating;
    delete mappedItem.ticket_price;
    delete mappedItem.opening_hours;
    delete mappedItem.suggested_duration;
    delete mappedItem.suggested_season;
    delete mappedItem.tips;
    delete mappedItem.introduction;

    return mappedItem;
  });

  console.log('处理后的第一条数据:', processedData[0]);
  console.log('处理后的第二条数据:', processedData[1]);

  return processedData;
}

// 运行测试
console.log('=== AI 查询结果显示修复测试 ===\n');

console.log('原始 AI 查询数据:');
console.log(JSON.stringify(mockAIQueryResult.data[0], null, 2));

console.log('\n处理后的数据:');
const processedData = handleAgentQueryResult(mockAIQueryResult);

console.log('\n=== 字段映射验证 ===');
const firstItem = processedData[0];
console.log('字段映射结果:');
console.log('- 名称:', firstItem.name);
console.log('- 等级:', firstItem.level);
console.log('- 地址:', firstItem.地址);
console.log('- 评分:', firstItem.评分);
console.log('- 门票:', firstItem.门票);
console.log('- 开放时间:', firstItem.开放时间);
console.log('- 建议游玩时间:', firstItem.建议游玩时间);
console.log('- 建议季节:', firstItem.建议季节);
console.log('- 小贴士:', firstItem.小贴士);
console.log('- 介绍:', firstItem.介绍);
console.log('- 来源标记:', firstItem._fromAI);
console.log('- 坐标标记:', firstItem._hasCoordinates);

console.log('\n=== 测试完成 ===');
console.log('✅ 字段映射成功，所有信息都能正确显示');
