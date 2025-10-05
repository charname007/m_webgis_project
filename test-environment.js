// 环境配置测试脚本
// 运行此脚本来验证环境变量配置

console.log('=== 环境配置测试 ===');

// 模拟不同环境下的配置
const environments = {
  development: {
    VITE_API_BASE_URL: 'http://localhost:8081',
    VITE_APP_NAME: 'Web GIS App (Dev)',
    VITE_DEBUG: 'true',
    MODE: 'development'
  },
  production: {
    VITE_API_BASE_URL: 'http://YOUR_SERVER_IP:8080',
    VITE_APP_NAME: 'Web GIS Application',
    VITE_DEBUG: 'false',
    MODE: 'production'
  }
};

function testEnvironment(envName, config) {
  console.log(`\n--- ${envName.toUpperCase()} 环境测试 ---`);
  console.log('后端地址:', config.VITE_API_BASE_URL);
  console.log('应用名称:', config.VITE_APP_NAME);
  console.log('调试模式:', config.VITE_DEBUG);
  console.log('环境模式:', config.MODE);
  
  // 验证配置
  if (envName === 'development' && config.VITE_API_BASE_URL.includes('localhost')) {
    console.log('✅ 开发环境配置正确');
  } else if (envName === 'production' && !config.VITE_API_BASE_URL.includes('localhost')) {
    console.log('✅ 生产环境配置正确');
  } else {
    console.log('❌ 环境配置需要检查');
  }
}

// 测试所有环境
Object.entries(environments).forEach(([envName, config]) => {
  testEnvironment(envName, config);
});

console.log('\n=== 部署说明 ===');
console.log('1. 开发环境: 使用 npm run dev');
console.log('2. 生产环境: 使用 npm run build');
console.log('3. 后端配置: 检查 application-{env}.properties 文件');
console.log('4. 前端配置: 检查 .env.{env} 文件');

console.log('\n=== 环境切换验证 ===');
console.log('开发环境: 后端地址应为 localhost:8081');
console.log('生产环境: 后端地址应为服务器公网IP或域名');
console.log('API 配置文件会自动使用正确的环境变量');
