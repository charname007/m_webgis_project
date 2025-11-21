// API 配置模块
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8082",

  // Sight Server 配置
  sightServer: {
    baseURL: import.meta.env.VITE_SIGHT_SERVER_URL || "http://localhost:8001",
    endpoints: {
      // 智能查询相关
      query: "/query",
      summary: "/summary",
      // 其他可能的端点
      health: "/health",
      status: "/status",
    },
  },

  // 后端 API 端点
  endpoints: {
    // 空间表相关
    spatialTables: {
      list: "/postgis/WGP_db/tables/SpatialTables",
      geojson: "/postgis/WGP_db/tables/SpatialTables/geojson",
      tableGeojson: (tableName) =>
        `/postgis/WGP_db/tables/SpatialTables/${tableName}/geojson`,
      tableGeojsonByExtent: (tableName) =>
        `/postgis/WGP_db/tables/SpatialTables/${tableName}/geojson/extent`,
    },

    // 地图元素相关
    mapElements: {
      list: "/postgis/WGP_db/tables/map_elements/geojson",
      byExtent: "/postgis/WGP_db/tables/map_elements/geojson/extent",
    },

    // 用户相关
    users: {
      login: "/users/login",
      register: "/users/register",
    },

    // 动态表相关
    dynamicTables: {
      list: "/postgis/WGP_db/tables/DynamicTables",
      tableGeojson: (tableName) =>
        `/postgis/WGP_db/tables/DynamicTables/${tableName}/geojson`,
    },

    // 景区相关
    sights: {
      geojsonByExtentAndLevel:
        "/postgis/WGP_db/tables/a_sight/geojson/extent-level",
      search:'/postgis/WGP_db/tables/a_sight/geojson/search'
    },

    // 旅游景点相关
    touristSpots: {
      list: "/api/tourist-spots",
      byId: (id) => `/api/tourist-spots/${id}`,
      byCity: (city) => `/api/tourist-spots/city/${city}`,
      search: "/api/tourist-spots/search",
      byName: (name) => `/api/tourist-spots/name/${name}`,
      count: "/api/tourist-spots/count",
      update: (id) => `/api/tourist-spots/${id}/with-sight`,
      updateByName: (name) => `/api/tourist-spots/by-name/${name}/with-sight`,
      add: "/api/tourist-spots/with-sight",
      deleteById: (id) => `/api/tourist-spots/${id}/with-sight`,
      deleteByName: (name) => `/api/tourist-spots/by-name/${name}/with-sight`,
    },
    // 路线规划相关
    routes: {
      driving: "/route/driving",
      walking: "/route/walking",
      bicycling: "/route/bicycling",
    },

    // Spring Boot 后端路由端点
    springBoot: {
      // 空间表相关
      spatialTables: {
        list: "/postgis/WGP_db/tables/SpatialTables",
        geojson: "/postgis/WGP_db/tables/SpatialTables/geojson",
        tableGeojson: (tableName) =>
          `/postgis/WGP_db/tables/SpatialTables/${tableName}/geojson`,
        tableGeojsonByExtent: (tableName) =>
          `/postgis/WGP_db/tables/SpatialTables/${tableName}/geojson/extent`,
        tableGeojsonByFields:
          "/postgis/WGP_db/tables/SpatialTables/geojson/fields",
        tableData: (tableName) => `/postgis/WGP_db/tables/${tableName}/data`,
        tableSchema: (tableName) =>
          `/postgis/WGP_db/tables/${tableName}/schema`,
        allTables: "/postgis/WGP_db/tables",
      },

      // 地图元素相关
      mapElements: {
        list: "/postgis2/WGP_db/list",
        byPage: "/postgis2/WGP_db",
        byCondition: "/postgis2/WGP_db/condition",
        byCircle: "/postgis2/WGP_db/circle",
        byPolygon: "/postgis2/WGP_db/polygon",
        add: "/postgis2/WGP_db",
        update: "/postgis2/WGP_db",
        delete: (id) => `/postgis2/WGP_db/${id}`,
        geojson: "/postgis/WGP_db/tables/map_elements/geojson",
        geojsonByExtent: "/postgis/WGP_db/tables/map_elements/geojson/extent",
      },

      // 动态表相关
      dynamicTables: {
        list: "/postgis/WGP_db/dynamic-tables/tables/SpatialTables",
        tableGeojson: (tableName) =>
          `/postgis/WGP_db/dynamic-tables/tables/SpatialTables/${tableName}/geojson`,
        tableGeojsonByExtent: (tableName) =>
          `/postgis/WGP_db/dynamic-tables/tables/SpatialTables/${tableName}/geojson/extent`,
        tableGeojsonByFields:
          "/postgis/WGP_db/dynamic-tables/tables/SpatialTables/geojson/fields",
        tableData: (tableName) =>
          `/postgis/WGP_db/dynamic-tables/tables/${tableName}/data`,
        tableSchema: (tableName) =>
          `/postgis/WGP_db/dynamic-tables/tables/${tableName}/schema`,
        allTables: "/postgis/WGP_db/dynamic-tables/tables",
      },

      // 景区相关
      sights: {
        geojsonByExtentAndLevel:
          "/postgis/WGP_db/tables/a_sight/geojson/extent-level",
      },

      // 路线规划相关
      routes: {
        driving: {
          post: "/route/driving",
          get: "/route/driving",
        },
        walking: {
          post: "/route/walking",
          get: "/route/walking",
        },
        bicycling: {
          post: "/route/bicycling",
          get: "/route/bicycling",
        },
      },

      // 特征详情相关
      featureDetails: {
        get: "/feature-details",
      },

      // 查询相关
      queries: {
        execute: "/query",
      },

      // 用户相关
      users: {
        login: "/users/login",
        register: "/users/register",
      },
    },
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
      debug: import.meta.env.VITE_DEBUG === "true",
    };
  },
};

// 开发环境日志
if (import.meta.env.DEV) {
  console.log('API 配置已加载:', API_CONFIG.getEnvironment());
}

export default API_CONFIG;
