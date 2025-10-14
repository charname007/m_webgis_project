// API 配置模块
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8082',
  
  // Sight Server 配置
  sightServer: {
    baseURL: import.meta.env.VITE_SIGHT_SERVER_URL || 'http://localhost:8001',
    endpoints: {
      // 智能查询相关
      query: '/query',
      summary: '/summary',
      // 其他可能的端点
      health: '/health',
      status: '/status'
    }
  },
  
  // 后端 API 端点
  endpoints: {
    // 空间表相关
    spatialTables: {
      list: '/postgis/WGP_db/tables/SpatialTables',
      geojson: '/postgis/WGP_db/tables/SpatialTables/geojson',
      tableGeojson: (tableName) => 
        `/postgis/WGP_db/tables/SpatialTables/${tableName}/geojson`,
      tableGeojsonByExtent: (tableName) =>
        `/postgis/WGP_db/tables/SpatialTables/${tableName}/geojson/extent`
    },
    
    // 地图元素相关
    mapElements: {
      list: '/postgis/WGP_db/tables/map_elements/geojson',
      byExtent: '/postgis/WGP_db/tables/map_elements/geojson/extent'
    },
    
    // 用户相关
    users: {
      login: '/users/login',
      register: '/users/register'
    },
    
    // 动态表相关
    dynamicTables: {
      list: '/postgis/WGP_db/tables/DynamicTables',
      tableGeojson: (tableName) =>
        `/postgis/WGP_db/tables/DynamicTables/${tableName}/geojson`
    },
    
    // 景区相关
    sights: {
      geojsonByExtentAndLevel: '/postgis/WGP_db/tables/a_sight/geojson/extent-level'
    },
    
    // 旅游景点相关
    touristSpots: {
      list: '/api/tourist-spots',
      byId: (id) => `/api/tourist-spots/${id}`,
      byCity: (city) => `/api/tourist-spots/city/${city}`,
      search: '/api/tourist-spots/search',
      byName: (name) => `/api/tourist-spots/name/${name}`,
      count: '/api/tourist-spots/count',
      update: (id) => `/api/tourist-spots/${id}/with-sight`,
      updateByName: (name) => `/api/tourist-spots/by-name/${name}/with-sight`
    }
  },
  
  // 构建完整 URL
  buildURL: (endpoint) => {
    return `${API_CONFIG.baseURL}${endpoint}`;
  },
  
  // 构建 Sight Server URL
  buildSightServerURL: (endpoint) => {
    return `${API_CONFIG.sightServer.baseURL}${endpoint}`;
  },
  
  // 获取环境信息
  getEnvironment: () => {
    return {
      mode: import.meta.env.MODE,
      baseURL: API_CONFIG.baseURL,
      sightServerURL: API_CONFIG.sightServer.baseURL,
      appName: import.meta.env.VITE_APP_NAME,
      debug: import.meta.env.VITE_DEBUG === 'true'
    };
  }
};

// 开发环境日志
if (import.meta.env.DEV) {
  console.log('API 配置已加载:', API_CONFIG.getEnvironment());
}

export default API_CONFIG;
