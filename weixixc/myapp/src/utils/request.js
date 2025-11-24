import API_CONFIG from './config.js'

const requestInterceptor = (config) => {
  console.log('请求:', config.url)
  return config
}

const responseInterceptor = (response) => {
  if (response.statusCode === 200) {
    return response.data
  } else {
    uni.showToast({
      title: `请求失败: ${response.statusCode}`,
      icon: 'none'
    })
    return Promise.reject(response)
  }
}

const request = (options) => {
  const config = requestInterceptor(options)

  return new Promise((resolve, reject) => {
    uni.request({
      url: config.url,
      method: config.method || 'GET',
      data: config.data,
      header: {
        'Content-Type': 'application/json',
        ...config.header
      },
      timeout: config.timeout || 600000, // 10分钟超时
      success: (res) => {
        try {
          const data = responseInterceptor(res)
          resolve(data)
        } catch (err) {
          reject(err)
        }
      },
      fail: (err) => {
        console.error('请求失败:', err)
        uni.showToast({
          title: '网络请求失败',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

export const get = (url, params = {}, useSightServer = false) => {
  const fullUrl = API_CONFIG.buildURL(url, useSightServer)
  const queryString = Object.keys(params)
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')
  const requestUrl = queryString ? `${fullUrl}?${queryString}` : fullUrl
  return request({ url: requestUrl, method: 'GET' })
}

export const post = (url, data = {}, useSightServer = false) => {
  const fullUrl = API_CONFIG.buildURL(url, useSightServer)
  return request({ url: fullUrl, method: 'POST', data })
}

export const put = (url, data = {}, useSightServer = false) => {
  const fullUrl = API_CONFIG.buildURL(url, useSightServer)
  return request({ url: fullUrl, method: 'PUT', data })
}

export const del = (url, useSightServer = false) => {
  const fullUrl = API_CONFIG.buildURL(url, useSightServer)
  return request({ url: fullUrl, method: 'DELETE' })
}

export default { get, post, put, delete: del }
