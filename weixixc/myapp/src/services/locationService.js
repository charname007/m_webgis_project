/**
 * 位置服务核心模块
 * 基于uni-app的持续位置监听服务
 */

import { handleLocationError } from '@/utils/errorHandler'

/**
 * 位置服务配置
 */
const LOCATION_CONFIG = {
  updateInterval: 3000,        // 更新频率(毫秒)，默认3秒
  accuracy: 50,               // 精度要求(米)，默认50米
  maxCacheSize: 100,          // 最大缓存条数
  maxRetries: 3,             // 最大重试次数
  retryDelay: 1000,           // 重试基础延迟(毫秒)
  timeout: 10000              // 请求超时时间(毫秒)
}

/**
 * 位置缓存管理
 */
class LocationCache {
  constructor(maxSize = LOCATION_CONFIG.maxCacheSize) {
    this.cache = []
    this.maxSize = maxSize
  }

  /**
   * 添加位置到缓存
   * @param {Object} location - 位置对象
   */
  add(location) {
    this.cache.unshift({
      ...location,
      timestamp: Date.now()
    })
    
    if (this.cache.length > this.maxSize) {
      this.cache = this.cache.slice(0, this.maxSize)
    }
  }

  /**
   * 获取最新位置
   * @returns {Object|null} 最新位置
   */
  getLatest() {
    return this.cache.length > 0 ? this.cache[0] : null
  }

  /**
   * 获取历史位置
   * @param {number} count - 获取数量
   * @returns {Array} 位置数组
   */
  getHistory(count = 10) {
    return this.cache.slice(0, count)
  }

  /**
   * 清空缓存
   */
  clear() {
    this.cache = []
  }
}

/**
 * 位置服务主类
 */
class LocationService {
  constructor() {
    this.cache = new LocationCache()
    this.isWatching = false
    this.lastLocation = null
    this.retryCount = 0
    this.callbacks = new Set()
  }

  /**
   * 检查位置权限
   * @returns {Promise<boolean>} 权限状态
   */
  async checkPermission() {
    return new Promise((resolve) => {
      uni.getSystemInfo({
        success: (res) => {
          const { platform } = res
          if (platform === 'android') {
            resolve(true) // Android通过manifest配置
          } else {
            uni.getSetting({
              success: (setting) => {
                resolve(!!setting.authSetting['scope.userLocation'])
              },
              fail: () => resolve(false)
            })
          }
        },
        fail: () => resolve(false)
      })
    })
  }

  /**
   * 请求位置权限
   * @returns {Promise<boolean>} 授权结果
   */
  async requestPermission() {
    return new Promise((resolve) => {
      uni.authorize({
        scope: 'scope.userLocation',
        success: () => resolve(true),
        fail: () => resolve(false)
      })
    })
  }

  /**
   * 获取单次位置
   * @returns {Promise<Object>} 位置信息
   */
  async getCurrentLocation() {
    return new Promise((resolve, reject) => {
      uni.getLocation({
        type: 'gcj02',
        altitude: true,
        accuracy: LOCATION_CONFIG.accuracy,
        timeout: LOCATION_CONFIG.timeout,
        success: resolve,
        fail: (err) => reject(handleLocationError(err))
      })
    })
  }

  /**
   * 启动位置监听
   * @param {Function} callback - 位置更新回调
   * @param {Object} options - 配置选项
   * @returns {Promise<boolean>} 启动结果
   */
  async startWatching(callback, options = {}) {
    if (this.isWatching) {
      console.log('位置监听已启动')
      return true
    }

    const config = { ...LOCATION_CONFIG, ...options }

    // 检查权限
    const hasPermission = await this.checkPermission()
    if (!hasPermission) {
      const granted = await this.requestPermission()
      if (!granted) {
        throw new Error('位置权限被拒绝')
      }
    }

    // 保存回调函数
    if (callback) {
      this.addListener(callback)
    }

    return new Promise((resolve, reject) => {
      // 第一步:启动位置更新
      uni.startLocationUpdate({
        success: () => {
          console.log('开始接收位置更新')

          // 第二步:监听位置变化
          uni.onLocationChange((location) => {
            this.handleLocationUpdate(location)
          })

          this.isWatching = true
          this.retryCount = 0
          resolve(true)
        },
        fail: (err) => {
          console.error('启动位置更新失败:', err)
          const error = handleLocationError(err)

          // 尝试重试
          if (this.retryCount < LOCATION_CONFIG.maxRetries) {
            this.retryCount++
            const delay = LOCATION_CONFIG.retryDelay * Math.pow(2, this.retryCount - 1)

            setTimeout(() => {
              console.log(`重试启动位置监听 (${this.retryCount}/${LOCATION_CONFIG.maxRetries})`)
              this.startWatching(callback, options).then(resolve).catch(reject)
            }, delay)
          } else {
            reject(error)
          }
        }
      })
    })
  }

  /**
   * 停止位置监听
   */
  stopWatching() {
    if (!this.isWatching) {
      return
    }

    // 停止位置更新
    uni.stopLocationUpdate({
      success: () => {
        console.log('位置更新已停止')
      },
      fail: (err) => {
        console.error('停止位置更新失败:', err)
      }
    })

    // 取消位置变化监听
    uni.offLocationChange()

    this.isWatching = false
    this.retryCount = 0
    this.callbacks.clear()
  }

  /**
   * 处理位置更新
   * @param {Object} location - 新位置
   */
  handleLocationUpdate(location) {
    // 添加到缓存
    this.cache.add(location)
    this.lastLocation = location

    // 通知所有监听者
    this.callbacks.forEach(cb => {
      try {
        cb(location)
      } catch (err) {
        console.error('位置回调执行失败:', err)
      }
    })
  }

  /**
   * 添加位置变化监听器
   * @param {Function} callback - 回调函数
   */
  addListener(callback) {
    if (typeof callback === 'function') {
      this.callbacks.add(callback)
    }
  }

  /**
   * 移除位置变化监听器
   * @param {Function} callback - 回调函数
   */
  removeListener(callback) {
    this.callbacks.delete(callback)
  }

  /**
   * 获取最新位置
   * @returns {Object|null} 最新位置
   */
  getCurrentPosition() {
    return this.cache.getLatest()
  }

  /**
   * 获取位置历史
   * @param {number} count - 获取数量
   * @returns {Array} 位置历史
   */
  getLocationHistory(count = 10) {
    return this.cache.getHistory(count)
  }

  /**
   * 更新配置
   * @param {Object} newConfig - 新配置
   */
  updateConfig(newConfig) {
    Object.assign(LOCATION_CONFIG, newConfig)
  }

  /**
   * 获取当前配置
   * @returns {Object} 当前配置
   */
  getConfig() {
    return { ...LOCATION_CONFIG }
  }
}

// 创建单例实例
const locationService = new LocationService()

export default locationService
export { LOCATION_CONFIG }