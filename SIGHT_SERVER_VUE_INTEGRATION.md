# Sight Server Vue 项目集成指南

## 配置概述

已将 Sight Server 的端点添加到 Vue 项目的配置系统中，支持开发和生产环境。

## 配置文件更新

### 1. API 配置 (`src/config/api.js`)
```javascript
// Sight Server 配置
sightServer: {
  baseURL: import.meta.env.VITE_SIGHT_SERVER_URL || 'http://localhost:8000',
  endpoints: {
    // 智能查询相关
    query: '/api/query',
    summary: '/api/summary',
    // 其他可能的端点
    health: '/health',
    status: '/status'
  }
},

// 构建 Sight Server URL
buildSightServerURL: (endpoint) => {
  return `${API_CONFIG.sightServer.baseURL}${endpoint}`;
}
```

### 2. 环境配置

#### 开发环境 (`.env.development`)
```env
VITE_SIGHT_SERVER_URL=http://localhost:8000
```

#### 生产环境 (`.env.production`)
```env
# 方式1: 使用服务器IP地址
VITE_SIGHT_SERVER_URL=http://YOUR_SERVER_IP:8000

# 方式2: 使用域名（推荐）
# VITE_SIGHT_SERVER_URL=https://sight-server.your-domain.com

# 方式3: 使用环境变量（Docker部署时推荐）
# VITE_SIGHT_SERVER_URL=${VITE_SIGHT_SERVER_URL}
```

## 使用示例

### 1. 导入配置
```javascript
import API_CONFIG from '@/config/api.js';
```

### 2. 构建 Sight Server URL
```javascript
// 构建查询端点 URL
const queryURL = API_CONFIG.buildSightServerURL(API_CONFIG.sightServer.endpoints.query);
// 结果: http://localhost:8000/api/query

// 构建摘要端点 URL
const summaryURL = API_CONFIG.buildSightServerURL(API_CONFIG.sightServer.endpoints.summary);
// 结果: http://localhost:8000/api/summary

// 构建健康检查端点 URL
const healthURL = API_CONFIG.buildSightServerURL(API_CONFIG.sightServer.endpoints.health);
// 结果: http://localhost:8000/health
```

### 3. 在组件中使用

#### 智能查询示例
```vue
<template>
  <div>
    <input v-model="queryText" placeholder="输入查询问题" />
    <button @click="executeQuery">执行查询</button>
    <div v-if="loading">查询中...</div>
    <div v-if="result">
      <h3>查询结果:</h3>
      <p>{{ result.answer }}</p>
      <div v-if="result.data">
        <h4>数据详情:</h4>
        <pre>{{ JSON.stringify(result.data, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import API_CONFIG from '@/config/api.js';

export default {
  setup() {
    const queryText = ref('');
    const result = ref(null);
    const loading = ref(false);

    const executeQuery = async () => {
      if (!queryText.value.trim()) return;

      loading.value = true;
      try {
        const url = API_CONFIG.buildSightServerURL(API_CONFIG.sightServer.endpoints.query);
        
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            query: queryText.value,
            // 其他可能的参数
            spatial: true,
            max_results: 50
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        result.value = await response.json();
      } catch (error) {
        console.error('查询失败:', error);
        result.value = { error: error.message };
      } finally {
        loading.value = false;
      }
    };

    return {
      queryText,
      result,
      loading,
      executeQuery
    };
  }
};
</script>
```

#### 统计摘要查询示例
```javascript
// 统计摘要查询
async function executeSummaryQuery(query) {
  const url = API_CONFIG.buildSightServerURL(API_CONFIG.sightServer.endpoints.summary);
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      intent_type: 'summary',
      spatial: true
    })
  });

  return await response.json();
}

// 使用示例
const summaryResult = await executeSummaryQuery("统计武汉市各区的景区数量");
console.log(summaryResult);
```

### 4. 健康检查
```javascript
// 检查 Sight Server 状态
async function checkSightServerHealth() {
  try {
    const url = API_CONFIG.buildSightServerURL(API_CONFIG.sightServer.endpoints.health);
    const response = await fetch(url);
    
    if (response.ok) {
      console.log('Sight Server 运行正常');
      return true;
    } else {
      console.warn('Sight Server 状态异常');
      return false;
    }
  } catch (error) {
    console.error('无法连接到 Sight Server:', error);
    return false;
  }
}

// 在应用启动时检查
checkSightServerHealth();
```

## 环境信息获取

```javascript
// 获取当前环境配置
const envInfo = API_CONFIG.getEnvironment();
console.log('当前环境信息:', envInfo);
// 输出示例:
// {
//   mode: 'development',
//   baseURL: 'http://localhost:8081',
//   sightServerURL: 'http://localhost:8000',
//   appName: 'Web GIS App (Dev)',
//   debug: true
// }
```

## 错误处理

### 1. 网络错误处理
```javascript
async function safeSightServerCall(endpoint, data) {
  try {
    const url = API_CONFIG.buildSightServerURL(endpoint);
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`Sight Server 响应错误: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`调用 Sight Server 端点 ${endpoint} 失败:`, error);
    
    // 返回友好的错误信息
    return {
      success: false,
      error: error.message,
      fallback_message: '智能查询服务暂时不可用，请稍后重试'
    };
  }
}
```

### 2. 超时处理
```javascript
async function sightServerCallWithTimeout(endpoint, data, timeout = 30000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const url = API_CONFIG.buildSightServerURL(endpoint);
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      signal: controller.signal
    });

    clearTimeout(timeoutId);
    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('查询超时，请重试');
    }
    throw error;
  }
}
```

## 最佳实践

### 1. 环境检测
```javascript
// 根据环境调整配置
function getSightServerConfig() {
  const env = API_CONFIG.getEnvironment();
  
  return {
    baseURL: env.sightServerURL,
    timeout: env.mode === 'development' ? 60000 : 30000,
    retryCount: env.mode === 'development' ? 1 : 3
  };
}
```

### 2. 缓存策略
```javascript
// 简单的查询结果缓存
const queryCache = new Map();

async function cachedSightServerQuery(query) {
  const cacheKey = query.toLowerCase().trim();
  
  if (queryCache.has(cacheKey)) {
    return queryCache.get(cacheKey);
  }

  const result = await executeQuery(query);
  queryCache.set(cacheKey, result);
  
  // 设置缓存过期时间（5分钟）
  setTimeout(() => {
    queryCache.delete(cacheKey);
  }, 5 * 60 * 1000);

  return result;
}
```

## 部署注意事项

1. **端口配置**: 确保 Sight Server 在指定端口运行（默认 8000）
2. **CORS 配置**: Sight Server 需要配置允许 Vue 应用域的跨域请求
3. **环境变量**: 生产环境部署时正确设置 `VITE_SIGHT_SERVER_URL`
4. **HTTPS**: 生产环境建议使用 HTTPS

## 故障排除

### 常见问题

1. **连接失败**
   - 检查 Sight Server 是否正在运行
   - 验证端口配置是否正确
   - 检查防火墙设置

2. **CORS 错误**
   - 确认 Sight Server 已配置允许前端域名的跨域请求
   - 检查请求头是否正确

3. **响应超时**
   - 增加超时时间
   - 检查网络连接
   - 确认 Sight Server 性能正常

通过以上配置，Vue 应用现在可以方便地调用 Sight Server 的智能查询和摘要功能，享受增强的答案生成和结果验证能力。
