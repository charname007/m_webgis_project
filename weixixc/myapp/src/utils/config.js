/**
 * API配置文件
 */

// API地址配置
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? 'https://your-domain.com:8082'
  : 'http://localhost:8082'

const SIGHT_SERVER_URL = process.env.NODE_ENV === 'production'
  ? 'https://your-domain.com:8001'
  : 'http://localhost:8001'

const API_CONFIG = {
  baseURL: API_BASE_URL,
  sightServerBaseURL: SIGHT_SERVER_URL,

  endpoints: {
    touristSpots: {
      list: '/api/tourist-spots',
      search: '/api/tourist-spots/search',
      add: '/api/tourist-spots',
      update: (id) => `/api/tourist-spots/${id}`,
      updateByName: (name) => `/api/tourist-spots/name/${name}`,
      delete: (id) => `/api/tourist-spots/${id}`,
      deleteByName: (name) => `/api/tourist-spots/name/${name}`,
      getByName: (name) => `/api/tourist-spots/name/${name}`
    },

    sights: {
      geojsonByExtentAndLevel: '/api/sights/geojson/extent-level',
      all: '/api/sights/all'
    },

    aiQuery: {
      query: '/query',
      session: (sessionId) => `/session/${sessionId}`
    }
  },

  buildURL(endpoint, useSightServer = false) {
    const baseURL = useSightServer ? this.sightServerBaseURL : this.baseURL
    return `${baseURL}${endpoint}`
  }
}

// 腾讯地图配置
// 请在腾讯位置服务平台申请Key: https://lbs.qq.com/
export const TENCENT_MAP_CONFIG = {
  key: 'WBYBZ-UJVCN-RMGFD-SMORX-7C53K-VZBSX', // 替换为你的腾讯地图Key
  apiBaseUrl: 'https://apis.map.qq.com',

  endpoints: {
    // 地点搜索
    search: '/ws/place/v1/search',
    // 关键词输入提示
    suggestion: '/ws/place/v1/suggestion',
    // 地址解析（地址转坐标）
    geocoder: '/ws/geocoder/v1',
    // 逆地址解析（坐标转地址）
    reverseGeocoder: '/ws/geocoder/v1',
    // 驾车路线规划
    driving: '/ws/direction/v1/driving',
    // 步行路线规划
    walking: '/ws/direction/v1/walking',
    // 公交路线规划
    transit: '/ws/direction/v1/transit'
  },

  /**
   * 构建完整的腾讯地图API URL
   * @param {string} endpoint - API端点
   * @param {object} params - 请求参数
   * @returns {string} 完整URL
   */
  buildURL(endpoint, params = {}) {
    const url = `${this.apiBaseUrl}${endpoint}`
    const queryParams = { ...params, key: this.key }
    const queryString = Object.keys(queryParams)
      .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(queryParams[key])}`)
      .join('&')
    return `${url}?${queryString}`
  }
}

export default API_CONFIG
