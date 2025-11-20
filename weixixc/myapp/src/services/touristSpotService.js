/**
 * 景点数据服务
 * 封装景点相关的API调用和数据转换
 */

import { get, post, put, del } from '@/utils/request'
import API_CONFIG from '@/utils/config'

/**
 * 获取所有景点列表
 */
export const getAllSpots = async () => {
  try {
    const response = await get(API_CONFIG.endpoints.touristSpots.list)
    return {
      success: true,
      data: response
    }
  } catch (error) {
    console.error('获取景点列表失败，使用模拟数据:', error)
    // 如果API请求失败，返回武汉地区的模拟景点数据
    return {
      success: true,
      data: getMockSpots()
    }
  }
}

/**
 * 获取模拟景点数据（用于开发和演示）
 */
const getMockSpots = () => {
  return [
    {
      id: 1,
      name: '黄鹤楼',
      level: '5A',
      address: '武汉市武昌区蛇山西坡特1号',
      lng_wgs84: 114.305539,
      lat_wgs84: 30.544965,
      rating: 4.6,
      ticket_price: 70,
      description: '江南三大名楼之一，享有"天下江山第一楼"的美誉'
    },
    {
      id: 2,
      name: '东湖风景区',
      level: '5A',
      address: '武汉市武昌区沿湖大道16号',
      lng_wgs84: 114.377827,
      lat_wgs84: 30.553673,
      rating: 4.5,
      ticket_price: 0,
      description: '中国最大的城中湖，山清水秀'
    },
    {
      id: 3,
      name: '武汉大学',
      level: '4A',
      address: '武汉市武昌区八一路299号',
      lng_wgs84: 114.371785,
      lat_wgs84: 30.535812,
      rating: 4.7,
      ticket_price: 0,
      description: '著名的樱花胜地，中国最美大学校园之一'
    },
    {
      id: 4,
      name: '户部巷',
      level: '3A',
      address: '武汉市武昌区户部巷',
      lng_wgs84: 114.295044,
      lat_wgs84: 30.547831,
      rating: 4.3,
      ticket_price: 0,
      description: '汉味小吃第一巷，武汉著名美食街'
    },
    {
      id: 5,
      name: '武汉长江大桥',
      level: '4A',
      address: '武汉市武昌区临江大道',
      lng_wgs84: 114.283211,
      lat_wgs84: 30.557536,
      rating: 4.4,
      ticket_price: 0,
      description: '万里长江第一桥，武汉地标建筑'
    },
    {
      id: 6,
      name: '古琴台',
      level: '3A',
      address: '武汉市汉阳区琴台路10号',
      lng_wgs84: 114.266632,
      lat_wgs84: 30.549948,
      rating: 4.2,
      ticket_price: 15,
      description: '俞伯牙与钟子期高山流水遇知音的地方'
    },
    {
      id: 7,
      name: '木兰天池',
      level: '5A',
      address: '武汉市黄陂区长轩岭街道石门山',
      lng_wgs84: 114.596954,
      lat_wgs84: 31.046687,
      rating: 4.4,
      ticket_price: 80,
      description: '国家森林公园，武汉的后花园'
    },
    {
      id: 8,
      name: '归元禅寺',
      level: '4A',
      address: '武汉市汉阳区归元寺路20号',
      lng_wgs84: 114.254524,
      lat_wgs84: 30.548776,
      rating: 4.5,
      ticket_price: 20,
      description: '武汉佛教四大丛林之一，以罗汉堂著名'
    },
    {
      id: 9,
      name: '江汉路步行街',
      level: '3A',
      address: '武汉市江汉区江汉路',
      lng_wgs84: 114.274422,
      lat_wgs84: 30.595874,
      rating: 4.3,
      ticket_price: 0,
      description: '百年商业老街，购物休闲好去处'
    },
    {
      id: 10,
      name: '晴川阁',
      level: '3A',
      address: '武汉市汉阳区洗马长街86号',
      lng_wgs84: 114.272156,
      lat_wgs84: 30.552741,
      rating: 4.3,
      ticket_price: 0,
      description: '与黄鹤楼隔江相望，楚天第一名楼'
    }
  ]
}

/**
 * 根据地图边界获取景点（用于动态加载）
 * 使用PostGIS空间查询API，支持范围和等级筛选
 * @param {object} bounds - 地图边界 { southwest: {lng, lat}, northeast: {lng, lat} }
 * @param {number} zoom - 当前缩放级别（用于控制返回的景点等级）
 */
export const getSpotsByBounds = async (bounds, zoom = 12) => {
  try {
    const { southwest, northeast } = bounds

    // 根据缩放级别决定加载哪些等级的景点
    // zoom越大（放大），显示的等级越多
    let levels = []
    if (zoom >= 15) {
      // 放大到15级以上，显示所有等级
      levels = ['5A', '4A', '3A', '2A', '1A']
    } else if (zoom >= 13) {
      // 13-14级，显示4A及以上
      levels = ['5A', '4A', '3A']
    } else if (zoom >= 11) {
      // 11-12级，显示5A和4A
      levels = ['5A', '4A']
    } else {
      // 10级以下，只显示5A景点
      levels = ['5A']
    }

    const requestBody = {
      minLon: southwest.lng,
      minLat: southwest.lat,
      maxLon: northeast.lng,
      maxLat: northeast.lat,
      levels: levels
    }

    console.log('请求景点范围:', requestBody)

    // 使用POST方法调用PostGIS空间查询API
    const response = await post(API_CONFIG.endpoints.sights.geojsonByExtentAndLevel, requestBody)

    // 解析GeoJSON数据
    let spots = []
    if (response && response.features && Array.isArray(response.features)) {
      console.log(`✅ 后端返回 ${response.features.length} 个景点（GeoJSON格式）`)

      // 将GeoJSON features转换为景点对象
      spots = response.features.map((feature, index) => {
        const props = feature.properties || {}
        const coords = feature.geometry?.coordinates || [0, 0]

        return {
          id: props.id || props.gid || index,
          name: props.name || props.名称 || '未命名景点',
          level: props.level || props.等级,
          address: props.address || props.地址,
          lng_wgs84: coords[0],
          lat_wgs84: coords[1],
          rating: props.rating || props.评分,
          ticket_price: props.ticket_price || props.门票,
          description: props.description || props.介绍,
          // 保存原始properties用于调试
          _rawProperties: props
        }
      })

      // 最终保护：最多返回200个景点（GeoJSON数据量较小，可以多返回一些）
      if (spots.length > 200) {
        console.warn(`⚠️ 景点过多(${spots.length}个)，限制为200个`)
        spots = spots.slice(0, 200)
      }
    } else {
      console.warn('后端返回数据格式不正确:', response)
    }

    return {
      success: true,
      data: spots
    }
  } catch (error) {
    console.error('获取范围内景点失败，使用模拟数据筛选:', error)
    // 降级：从模拟数据中筛选范围内的景点
    const allSpots = getMockSpots()
    const filteredSpots = filterSpotsByBounds(allSpots, bounds)
    return {
      success: true,
      data: filteredSpots
    }
  }
}

/**
 * 从景点列表中筛选出在指定范围内的景点
 * @param {Array} spots - 景点数组
 * @param {object} bounds - 地图边界
 */
const filterSpotsByBounds = (spots, bounds) => {
  const { southwest, northeast } = bounds
  return spots.filter(spot => {
    const lng = spot.lng_wgs84 || spot.longitude
    const lat = spot.lat_wgs84 || spot.latitude
    return lng >= southwest.lng && lng <= northeast.lng &&
           lat >= southwest.lat && lat <= northeast.lat
  })
}
export const searchSpots = async (keyword) => {
  try {
    const response = await get(API_CONFIG.endpoints.touristSpots.search, { keyword })
    return {
      success: true,
      data: response
    }
  } catch (error) {
    console.error('搜索景点失败:', error)
    return {
      success: false,
      error: error.message || '搜索景点失败'
    }
  }
}

/**
 * 根据名称获取景点详情
 * @param {string} name - 景点名称
 */
export const getSpotByName = async (name) => {
  try {
    const url = API_CONFIG.endpoints.touristSpots.getByName(name)
    const response = await get(url)
    return {
      success: true,
      data: response
    }
  } catch (error) {
    console.error('获取景点详情失败:', error)
    return {
      success: false,
      error: error.message || '获取景点详情失败'
    }
  }
}

/**
 * 添加新景点
 * @param {object} spotData - 景点数据
 */
export const addSpot = async (spotData) => {
  try {
    const response = await post(API_CONFIG.endpoints.touristSpots.add, spotData)
    return {
      success: true,
      data: response
    }
  } catch (error) {
    console.error('添加景点失败:', error)
    return {
      success: false,
      error: error.message || '添加景点失败'
    }
  }
}

/**
 * 更新景点信息
 * @param {string} name - 景点名称
 * @param {object} spotData - 更新的景点数据
 */
export const updateSpotByName = async (name, spotData) => {
  try {
    const url = API_CONFIG.endpoints.touristSpots.updateByName(name)
    const response = await put(url, spotData)
    return {
      success: true,
      data: response
    }
  } catch (error) {
    console.error('更新景点失败:', error)
    return {
      success: false,
      error: error.message || '更新景点失败'
    }
  }
}

/**
 * 删除景点
 * @param {string} name - 景点名称
 */
export const deleteSpotByName = async (name) => {
  try {
    const url = API_CONFIG.endpoints.touristSpots.deleteByName(name)
    const response = await del(url)
    return {
      success: true,
      data: response
    }
  } catch (error) {
    console.error('删除景点失败:', error)
    return {
      success: false,
      error: error.message || '删除景点失败'
    }
  }
}

/**
 * 将后端景点数据转换为地图markers格式
 * @param {Array} spots - 后端返回的景点数组
 * @returns {Array} 地图markers数组
 */
export const convertSpotsToMarkers = (spots) => {
  if (!Array.isArray(spots)) {
    console.error('Invalid spots data:', spots)
    return []
  }

  return spots.map((spot, index) => {
    // 确保有有效的坐标
    const lng = spot.lng_wgs84 || spot.longitude || 0
    const lat = spot.lat_wgs84 || spot.latitude || 0

    if (lng === 0 || lat === 0) {
      console.warn(`景点 ${spot.name} 缺少有效坐标`)
    }

    return {
      id: spot.id || index,
      latitude: lat,
      longitude: lng,
      // 根据景点等级选择不同图标
      iconPath: getSpotIcon(spot.level),
      width: 32,
      height: 32,
      // 标记气泡
      callout: {
        content: spot.name || '未命名景点',
        color: '#333333',
        fontSize: 12,
        borderRadius: 5,
        bgColor: '#ffffff',
        padding: 8,
        display: 'BYCLICK', // 点击时显示
        textAlign: 'center'
      },
      // 标记标签（一直显示）
      label: spot.level ? {
        content: getLevelText(spot.level),
        color: '#ffffff',
        fontSize: 10,
        x: 0,
        y: -5,
        borderRadius: 10,
        bgColor: getLevelColor(spot.level),
        padding: 3
      } : undefined,
      // 保存原始数据，方便后续使用
      spotData: spot
    }
  })
}

/**
 * 根据景点等级获取图标路径
 * @param {string} level - 景点等级
 */
const getSpotIcon = (level) => {
  // 这里使用emoji或者你可以替换为实际的图标路径
  const iconMap = {
    '5A': '/static/icons/spot-5a.png',
    '4A': '/static/icons/spot-4a.png',
    '3A': '/static/icons/spot-3a.png',
    '2A': '/static/icons/spot-2a.png',
    'default': '/static/icons/spot-default.png'
  }
  return iconMap[level] || iconMap.default
}

/**
 * 根据景点等级获取文本标签
 * @param {string} level - 景点等级
 */
const getLevelText = (level) => {
  if (!level) return ''
  return level
}

/**
 * 根据景点等级获取标签背景色
 * @param {string} level - 景点等级
 */
const getLevelColor = (level) => {
  const colorMap = {
    '5A': '#ff6b6b',  // 红色
    '4A': '#4ecdc4',  // 青色
    '3A': '#45b7d1',  // 蓝色
    '2A': '#96ceb4',  // 绿色
    'default': '#95a5a6'  // 灰色
  }
  return colorMap[level] || colorMap.default
}

export default {
  getAllSpots,
  getSpotsByBounds,
  searchSpots,
  getSpotByName,
  addSpot,
  updateSpotByName,
  deleteSpotByName,
  convertSpotsToMarkers
}
