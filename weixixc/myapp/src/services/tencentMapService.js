/**
 * 腾讯地图服务封装
 * 简洁实用的API调用
 */

import { TENCENT_MAP_CONFIG } from '@/utils/config'

/**
 * 地点搜索
 * @param {string} keyword - 搜索关键词
 * @param {object} options - 可选参数
 */
export const searchPlace = (keyword, options = {}) => {
  const {
    location = '',      // 中心点坐标 "lat,lng"
    radius = 1000,      // 搜索半径(米)
    boundary = '',      // 区域范围 "region(城市名,auto_extend)" 或 "nearby(lat,lng,radius)"
    page_size = 20,
    page_index = 1
  } = options

  const params = {
    keyword,
    boundary: boundary || (location ? `nearby(${location},${radius})` : ''),
    page_size,
    page_index
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: TENCENT_MAP_CONFIG.buildURL(TENCENT_MAP_CONFIG.endpoints.search, params),
      success: (res) => {
        if (res.data.status === 0) {
          resolve(res.data.data)
        } else {
          reject(new Error(res.data.message || '搜索失败'))
        }
      },
      fail: reject
    })
  })
}

/**
 * 关键词输入提示
 * @param {string} keyword - 用户输入的关键词
 * @param {string} region - 城市名称
 */
export const getSuggestion = (keyword, region = '全国') => {
  const params = { keyword, region }

  return new Promise((resolve, reject) => {
    uni.request({
      url: TENCENT_MAP_CONFIG.buildURL(TENCENT_MAP_CONFIG.endpoints.suggestion, params),
      success: (res) => {
        if (res.data.status === 0) {
          resolve(res.data.data)
        } else {
          reject(new Error(res.data.message || '获取提示失败'))
        }
      },
      fail: reject
    })
  })
}

/**
 * 地址解析(地址转坐标)
 * @param {string} address - 地址
 */
export const geocoder = (address) => {
  const params = { address }

  return new Promise((resolve, reject) => {
    uni.request({
      url: TENCENT_MAP_CONFIG.buildURL(TENCENT_MAP_CONFIG.endpoints.geocoder, params),
      success: (res) => {
        if (res.data.status === 0) {
          resolve(res.data.result)
        } else {
          reject(new Error(res.data.message || '地址解析失败'))
        }
      },
      fail: reject
    })
  })
}

/**
 * 逆地址解析(坐标转地址)
 * @param {number} lat - 纬度
 * @param {number} lng - 经度
 */
export const reverseGeocoder = (lat, lng) => {
  const params = {
    location: `${lat},${lng}`,
    get_poi: 1
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: TENCENT_MAP_CONFIG.buildURL(TENCENT_MAP_CONFIG.endpoints.geocoder, params),
      success: (res) => {
        if (res.data.status === 0) {
          resolve(res.data.result)
        } else {
          reject(new Error(res.data.message || '逆地址解析失败'))
        }
      },
      fail: reject
    })
  })
}

/**
 * 驾车路线规划
 * @param {string} from - 起点坐标 "lat,lng"
 * @param {string} to - 终点坐标 "lat,lng"
 */
export const drivingRoute = (from, to) => {
  const params = { from, to }

  return new Promise((resolve, reject) => {
    uni.request({
      url: TENCENT_MAP_CONFIG.buildURL(TENCENT_MAP_CONFIG.endpoints.driving, params),
      success: (res) => {
        if (res.data.status === 0) {
          const route = res.data.result.routes[0]
          resolve({
            ...route,
            polyline: decodePolyline(route.polyline)
          })
        } else {
          reject(new Error(res.data.message || '路线规划失败'))
        }
      },
      fail: reject
    })
  })
}

/**
 * 步行路线规划
 * @param {string} from - 起点坐标 "lat,lng"
 * @param {string} to - 终点坐标 "lat,lng"
 */
export const walkingRoute = (from, to) => {
  const params = { from, to }

  return new Promise((resolve, reject) => {
    uni.request({
      url: TENCENT_MAP_CONFIG.buildURL(TENCENT_MAP_CONFIG.endpoints.walking, params),
      success: (res) => {
        if (res.data.status === 0) {
          const route = res.data.result.routes[0]
          resolve({
            ...route,
            polyline: decodePolyline(route.polyline)
          })
        } else {
          reject(new Error(res.data.message || '路线规划失败'))
        }
      },
      fail: reject
    })
  })
}

/**
 * 解码路线坐标(前向差分算法)
 * @param {Array} coors - 压缩的坐标数组
 */
const decodePolyline = (coors) => {
  const kr = 1000000
  const pl = []

  // 解压坐标
  for (let i = 2; i < coors.length; i++) {
    coors[i] = Number(coors[i - 2]) + Number(coors[i]) / kr
  }

  // 转换为点串数组
  for (let i = 0; i < coors.length; i += 2) {
    pl.push({
      latitude: coors[i],
      longitude: coors[i + 1]
    })
  }

  return pl
}

export default {
  searchPlace,
  getSuggestion,
  geocoder,
  reverseGeocoder,
  drivingRoute,
  walkingRoute
}
