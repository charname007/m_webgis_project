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
    console.error('获取景点列表失败:', error)
    return {
      success: false,
      error: error.message || '获取景点列表失败'
    }
  }
}

/**
 * 根据关键词搜索景点
 * @param {string} keyword - 搜索关键词
 */
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
  searchSpots,
  getSpotByName,
  addSpot,
  updateSpotByName,
  deleteSpotByName,
  convertSpotsToMarkers
}
