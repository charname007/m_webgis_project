/**
 * 错误处理工具模块
 * 统一处理各类API错误
 */

/**
 * 位置错误码映射
 */
const LOCATION_ERROR_MAP = {
  1: '位置权限被拒绝',
  2: '获取位置失败',
  3: '请求位置超时',
  'fail:auth deny': '用户拒绝授权位置权限',
  'fail:unauthorized': '未授权使用位置功能,请在设置中开启',
  'fail:timeout': '获取位置超时,请检查网络连接'
}

/**
 * 处理位置相关错误
 * @param {Object|Error} error - 错误对象
 * @returns {Error} 标准化的错误对象
 */
export function handleLocationError(error) {
  if (!error) {
    return new Error('未知位置错误')
  }

  // 如果已经是Error对象
  if (error instanceof Error) {
    return error
  }

  // 处理微信小程序错误对象
  const errMsg = error.errMsg || error.message || ''
  const errCode = error.errCode || error.errno

  // 根据错误码或错误消息获取友好提示
  let message = LOCATION_ERROR_MAP[errCode] ||
                LOCATION_ERROR_MAP[errMsg] ||
                errMsg ||
                '获取位置失败'

  const err = new Error(message)
  err.code = errCode
  err.originalError = error

  return err
}

/**
 * 处理网络请求错误
 * @param {Object|Error} error - 错误对象
 * @returns {Error} 标准化的错误对象
 */
export function handleNetworkError(error) {
  if (!error) {
    return new Error('网络请求失败')
  }

  if (error instanceof Error) {
    return error
  }

  const errMsg = error.errMsg || error.message || '网络请求失败'
  const err = new Error(errMsg)
  err.originalError = error

  return err
}

/**
 * 显示错误提示
 * @param {Error|string} error - 错误对象或错误消息
 * @param {number} duration - 提示持续时间(毫秒)
 */
export function showError(error, duration = 2000) {
  const message = error instanceof Error ? error.message : error

  uni.showToast({
    title: message,
    icon: 'none',
    duration
  })
}

/**
 * 统一的错误处理函数
 * @param {Error|string} error - 错误对象或错误消息
 * @param {Object} options - 配置选项
 * @param {boolean} options.showToast - 是否显示toast提示
 * @param {boolean} options.logError - 是否打印错误日志
 * @param {Function} options.callback - 错误处理回调
 */
export function handleError(error, options = {}) {
  const {
    showToast = true,
    logError = true,
    callback
  } = options

  // 打印错误日志
  if (logError) {
    console.error('[ErrorHandler]', error)
  }

  // 显示错误提示
  if (showToast) {
    showError(error)
  }

  // 执行回调
  if (callback && typeof callback === 'function') {
    callback(error)
  }
}
