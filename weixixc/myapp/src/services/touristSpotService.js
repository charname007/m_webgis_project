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

    // 如果响应不是数组，使用模拟数据
    if (!Array.isArray(response)) {
      console.warn('获取景点列表返回格式不正确，使用模拟数据')
      return {
        success: true,
        data: getMockSpots()
      }
    }

    // 映射字段名（支持中英文字段名）
    const mappedSpots = response.map((spot, index) => {
      return {
        id: spot.id || spot.gid || index,
        name: spot.name || spot.名称 || spot['名称'] || '未命名景点',
        level: spot.level || spot.等级 || spot['等级'],
        address: spot.address || spot.地址 || spot['地址'],
        city: spot.city || spot.城市 || spot['城市'],
        rating: spot.rating || spot.评分 || spot['评分'],
        ticketPrice: spot.ticketPrice || spot.ticket_price || spot.门票 || spot['门票'],
        lng_wgs84: spot.lng_wgs84 || spot.longitude,
        lat_wgs84: spot.lat_wgs84 || spot.latitude,
        imageUrl: spot.imageUrl || spot.image_url || spot.图片链接 || spot['图片链接'],
        openTime: spot.openTime || spot.open_time || spot.开放时间 || spot['开放时间'],
        recommendedDuration: spot.recommendedDuration || spot.recommended_duration || spot.建议游玩时间 || spot['建议游玩时间'],
        recommendedSeason: spot.recommendedSeason || spot.recommended_season || spot.建议季节 || spot['建议季节'],
        description: spot.description || spot.介绍 || spot['介绍'],
        tips: spot.tips || spot.小贴士 || spot['小贴士']
      }
    })

    return {
      success: true,
      data: mappedSpots
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
/**
 * 从"中文名+英文名"格式中提取中文名
 * 例如: "黄鹤楼 Yellow Crane Tower" -> "黄鹤楼"
 */
const extractChineseName = (name) => {
  if (!name) return ''
  // 匹配中文字符（包括中文标点）
  const chineseMatch = name.match(/[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]+/)
  return chineseMatch ? chineseMatch[0].trim() : name
}

/**
 * 搜索景点 - 智能合并 tourist_spot 和 a_sight 两个表的数据
 * tourist_spot: 包含详细的旅游信息（介绍、门票、开放时间等）
 * a_sight: 包含空间信息（坐标、等级、地址、城市）
 *
 * @param {string} keyword - 搜索关键词
 * @returns {Promise<{success: boolean, data: Array, stats?: object, error?: string}>}
 */
export const searchSpots = async (keyword) => {
  try {
    console.log('[DEBUG searchSpots] 搜索关键词:', keyword)
    const cleanedKeyword = extractChineseName(keyword)
    console.log('[DEBUG searchSpots] 清洗后的关键词:', cleanedKeyword)

    // 并行调用两个API
    // API 1: tourist-spots 搜索 (返回详细旅游信息)
    // API 2: 获取全部景点的 GeoJSON 数据（后续在前端筛选）
    const [touristSpotsPromise, geojsonPromise] = await Promise.allSettled([
      get(API_CONFIG.endpoints.touristSpots.search, { name: keyword }),
      // 使用 geojsonByExtentAndLevel 获取全范围的数据
      get(API_CONFIG.endpoints.sights.search, {
        name: keyword,
      }),
    ]);

    let touristSpots = []
    let sightMap = new Map()

    // 处理 API 1 的结果 (tourist_spot 表 - 详细旅游信息)
    if (touristSpotsPromise.status === 'fulfilled') {
      const response = touristSpotsPromise.value
      console.log('[DEBUG searchSpots] tourist_spot 表响应:', response)

      if (Array.isArray(response)) {
        touristSpots = response
        console.log(`[DEBUG searchSpots] tourist_spot 表: ${touristSpots.length} 个景区`)
      } else {
        console.warn('[WARN searchSpots] tourist_spot 表响应不是数组格式')
      }
    } else {
      console.error('[ERROR searchSpots] tourist_spot 表调用失败:', touristSpotsPromise.reason)
    }

    // 处理 API 2 的结果 (a_sight 表 - 空间信息)
    // 转换为 Map 方便按名称查找，并在前端进行关键词筛选
    if (geojsonPromise.status === 'fulfilled') {
      const response = geojsonPromise.value
      console.log('[DEBUG searchSpots] a_sight 表原始响应:', response)
      console.log('[DEBUG searchSpots] 响应类型:', typeof response)
      console.log('[DEBUG searchSpots] response.features 存在?', !!response?.features)

      if (response && response.features && Array.isArray(response.features)) {
        console.log(`[DEBUG searchSpots] a_sight 表: ${response.features.length} 个景区（GeoJSON格式）`)

        // 遍历所有 features，筛选匹配关键词的景区
        response.features.forEach(feature => {
          const props = feature.properties || {}
          const name = props.name || props.名称
          const coords = feature.geometry?.coordinates

          if (name) {
            const cleanedFeatureName = extractChineseName(name)

            // 前端筛选：只保留匹配关键词的景区
            const matchesKeyword =
              name.includes(cleanedKeyword) ||
              cleanedFeatureName.includes(cleanedKeyword) ||
              name.includes(keyword) ||
              cleanedFeatureName.includes(keyword)

            if (matchesKeyword) {
              const hasCoordinates = !!coords && coords.length === 2
              console.log(`[DEBUG searchSpots] a_sight 匹配景区 ${name}: 坐标存在=${hasCoordinates}`, coords)

              sightMap.set(name, {
                coordinates: coords,
                lng_wgs84: coords?.[0],
                lat_wgs84: coords?.[1],
                level: props.level || props.等级,
                address: props.address || props.地址,
                city: props.city || props.城市 || props.所属城市,
                _hasCoordinates: hasCoordinates
              })
            }
          }
        })
        console.log(`[DEBUG searchSpots] sightMap 筛选后的景区数量: ${sightMap.size}`)
        console.log('[DEBUG searchSpots] sightMap 所有景区名称:', Array.from(sightMap.keys()))
      } else {
        console.warn('[WARN searchSpots] a_sight 表响应格式不正确或无数据')
        console.warn('[WARN searchSpots] 响应详情:', JSON.stringify(response))
      }
    } else {
      console.error('[ERROR searchSpots] a_sight 表调用失败:', geojsonPromise.reason)
    }

    // 合并结果 - 智能匹配两个表的数据
    const mergedResults = []
    const processedNames = new Set()

    // 第一步：处理 tourist_spot 表的结果（优先保留详细旅游信息）
    touristSpots.forEach((spot, index) => {
      const spotName = spot.name || spot.名称 || ''
      const cleanedSpotName = extractChineseName(spotName)

      // 查找匹配的关键词
      if (cleanedSpotName.includes(cleanedKeyword) || spotName.includes(keyword)) {
        // 尝试在 a_sight 中找到匹配的景区 - 使用多种匹配策略
        let sightInfo = null

        // 策略1: 使用清洗后的中文名精确匹配
        sightInfo = sightMap.get(cleanedSpotName)

        // 策略2: 使用原始名称精确匹配
        if (!sightInfo) {
          sightInfo = sightMap.get(spotName)
        }

        // 策略3: 使用包含匹配（模糊匹配）
        if (!sightInfo) {
          for (const [sightName, sightData] of sightMap.entries()) {
            const cleanedSightName = extractChineseName(sightName)
            if (sightName.includes(cleanedSpotName) ||
                cleanedSpotName.includes(sightName) ||
                cleanedSightName.includes(cleanedSpotName) ||
                cleanedSpotName.includes(cleanedSightName)) {
              sightInfo = sightData
              console.log(`[DEBUG searchSpots] 模糊匹配成功: ${cleanedSpotName} <-> ${sightName}`)
              break
            }
          }
        }

        // 构建合并后的结果
        const mergedSpot = {
          id: spot.id || spot.gid || index,
          name: spotName,
          // 旅游信息（来自 tourist_spot 表）
          // level: spot.level || spot.等级,
          rating: spot.rating || spot.评分 || spot['评分'],
          ticketPrice: spot.ticketPrice || spot.ticket_price || spot.门票 || spot['门票'],
          imageUrl: spot.imageUrl || spot.image_url || spot.图片链接 || spot['图片链接'],
          openTime: spot.openTime || spot.open_time || spot.开放时间 || spot['开放时间'],
          recommendedDuration: spot.recommendedDuration || spot.recommended_duration || spot.建议游玩时间 || spot['建议游玩时间'],
          recommendedSeason: spot.recommendedSeason || spot.recommended_season || spot.建议季节 || spot['建议季节'],
          description: spot.description || spot.介绍 || spot['介绍'],
          tips: spot.tips || spot.小贴士 || spot['小贴士'],
          // 空间信息（优先使用 a_sight 表的数据，其次使用 tourist_spot 表的）
          level: spot.level || spot.等级 || sightInfo?.level || '未知',
          address: spot.address || spot.地址 || spot['地址'] || sightInfo?.address || '暂无地址信息',
          city: spot.city || spot.城市 || spot['城市'] || sightInfo?.city,
          lng_wgs84: sightInfo?.lng_wgs84 || spot.lng_wgs84 || spot.longitude,
          lat_wgs84: sightInfo?.lat_wgs84 || spot.lat_wgs84 || spot.latitude,
          // 元信息
          _hasCoordinates: sightInfo?._hasCoordinates || !!(spot.lng_wgs84 || spot.longitude),
          _source: sightInfo ? 'merged' : 'tourist-spots'
        }

        if (sightInfo) {
          console.log(`[DEBUG searchSpots] 两个表都有数据 ${cleanedSpotName}: 坐标存在=${mergedSpot._hasCoordinates}`)
        }

        mergedResults.push(mergedSpot)
        processedNames.add(cleanedSpotName)
        processedNames.add(spotName)
      }
    })

    // 第二步：处理 a_sight 表中有但 tourist_spot 表中没有的景区
    console.log('[DEBUG searchSpots] processedNames 已处理景区:', Array.from(processedNames))

    sightMap.forEach((sightInfo, name) => {
      const cleanedSightName = extractChineseName(name)

      // 检查是否匹配关键词
      const shouldInclude =
        name.includes(cleanedKeyword) ||
        cleanedSightName.includes(cleanedKeyword) ||
        name.includes(keyword) ||
        cleanedSightName.includes(keyword)

      // 检查是否已经处理过
      const alreadyProcessed =
        processedNames.has(name) ||
        processedNames.has(cleanedSightName)

      if (shouldInclude && !alreadyProcessed) {
        console.log(`[DEBUG searchSpots] 添加 a_sight 独有景区 ${name}: 坐标存在=${sightInfo._hasCoordinates}`)

        mergedResults.push({
          id: `sight-${name}`,
          name: name,
          // 空间信息
          level: sightInfo.level || '未知',
          address: sightInfo.address || '暂无地址信息',
          city: sightInfo.city,
          lng_wgs84: sightInfo.lng_wgs84,
          lat_wgs84: sightInfo.lat_wgs84,
          // 基本信息（a_sight 表没有详细旅游信息）
          description: `${sightInfo.level || ''}级景区`,
          // 元信息
          _hasCoordinates: sightInfo._hasCoordinates,
          _source: 'geojson',
          _isBasicInfo: true
        })
      }
    })

    console.log('[DEBUG searchSpots] ========== 最终搜索结果 ==========')
    console.log('[DEBUG searchSpots] 结果数量:', mergedResults.length)
    console.log('[DEBUG searchSpots] 完整结果:', JSON.stringify(mergedResults, null, 2))
    console.log(`[DEBUG searchSpots] 统计: 共 ${mergedResults.length} 个景区 (${mergedResults.filter(r => r._hasCoordinates).length} 个有坐标, ${mergedResults.filter(r => !r._hasCoordinates).length} 个无坐标)`)

    if (mergedResults.length > 0) {
      console.log('[DEBUG searchSpots] 第一条数据示例:', mergedResults[0])
      console.log('[DEBUG searchSpots] 第一条数据的字段检查:', {
        name: mergedResults[0].name,
        level: mergedResults[0].level,
        address: mergedResults[0].address,
        rating: mergedResults[0].rating,
        ticketPrice: mergedResults[0].ticketPrice
      })
    } else {
      console.warn('[WARN searchSpots] ⚠️ 没有找到任何匹配的景区！')
      console.warn('[WARN searchSpots] touristSpots数量:', touristSpots.length)
      console.warn('[WARN searchSpots] sightMap数量:', sightMap.size)
    }
    console.log('[DEBUG searchSpots] ======================================')

    return {
      success: true,
      data: mergedResults,
      stats: {
        fromTouristSpot: touristSpots.length,
        fromASight: sightMap.size,
        merged: mergedResults.filter(r => r._source === 'merged').length,
        total: mergedResults.length,
        withCoordinates: mergedResults.filter(r => r._hasCoordinates).length
      }
    }
  } catch (error) {
    console.error('[ERROR searchSpots] 搜索景点失败:', error)
    console.error('[ERROR searchSpots] 错误详情:', error.message, error.stack)
    return {
      success: false,
      error: error.message || '搜索景点失败'
    }
  }
}

/**
 * 根据名称获取景点详情 - 智能合并 tourist_spot 和 a_sight 两个表的数据
 * @param {string} name - 景点名称
 */
export const getSpotByName = async (name) => {
  try {
    console.log('[DEBUG getSpotByName] 查询景点:', name)
    const cleanedName = extractChineseName(name)
    console.log('[DEBUG getSpotByName] 清洗后的名称:', cleanedName)

    // 并行调用两个API
    const [touristSpotPromise, geojsonPromise] = await Promise.allSettled([
      // API 1: 获取 tourist_spot 表的详细旅游信息
      get(API_CONFIG.endpoints.touristSpots.getByName(name)),
      // API 2: 获取 a_sight 表的空间信息
      // 使用清洗后的中文名搜索，提高匹配成功率
      get(API_CONFIG.endpoints.sights.search, { name: cleanedName })
    ])

    let touristSpotData = null
    let sightData = null

    // 处理 tourist_spot 表的数据
    if (touristSpotPromise.status === 'fulfilled') {
      const response = touristSpotPromise.value
      console.log('[DEBUG getSpotByName] tourist_spot 表响应:', response)

      if (Array.isArray(response) && response.length > 0) {
        touristSpotData = response[0]
      } else if (response && typeof response === 'object') {
        touristSpotData = response
      }
    } else {
      console.error('[ERROR getSpotByName] tourist_spot 表调用失败:', touristSpotPromise.reason)
    }

    // 处理 a_sight 表的数据
    if (geojsonPromise.status === 'fulfilled') {
      const response = geojsonPromise.value
      console.log('[DEBUG getSpotByName] a_sight 表响应:', response)

      // 解析 GeoJSON 数据
      if (response && response.features && Array.isArray(response.features)) {
        console.log(`[DEBUG getSpotByName] a_sight 表返回 ${response.features.length} 个景区`)

        // 尝试找到匹配的景区
        for (const feature of response.features) {
          const props = feature.properties || {}
          const featureName = props.name || props.名称
          const cleanedFeatureName = extractChineseName(featureName)

          // 多种匹配策略
          const isMatch =
            featureName === name ||
            featureName === cleanedName ||
            cleanedFeatureName === name ||
            cleanedFeatureName === cleanedName ||
            featureName.includes(cleanedName) ||
            cleanedName.includes(cleanedFeatureName)

          if (isMatch) {
            const coords = feature.geometry?.coordinates
            sightData = {
              coordinates: coords,
              lng_wgs84: coords?.[0],
              lat_wgs84: coords?.[1],
              level: props.level || props.等级,
              address: props.address || props.地址,
              city: props.city || props.城市 || props.所属城市,
              _hasCoordinates: !!(coords && coords.length === 2)
            }
            console.log(`[DEBUG getSpotByName] 找到匹配的 a_sight 数据: ${featureName}`, sightData)
            break
          }
        }
      }
    } else {
      console.error('[ERROR getSpotByName] a_sight 表调用失败:', geojsonPromise.reason)
    }

    // 如果两个表都没有数据
    if (!touristSpotData && !sightData) {
      console.error('[ERROR getSpotByName] 两个表都没有找到景点数据')
      return {
        success: false,
        error: '未找到景点信息'
      }
    }

    // 合并数据（优先使用 tourist_spot 的详细信息，用 a_sight 补充空间信息）
    const mergedData = {
      // 基础信息
      id: touristSpotData?.id,
      name: touristSpotData?.name || name,
      // 旅游详细信息（来自 tourist_spot）
      imageUrl: touristSpotData?.['图片链接'] || touristSpotData?.imageUrl || '',
      rating: touristSpotData?.['评分'] || touristSpotData?.rating || '',
      ticketPrice: touristSpotData?.['门票'] || touristSpotData?.ticketPrice || '',
      openTime: touristSpotData?.['开放时间'] || touristSpotData?.openTime || '',
      recommendedDuration: touristSpotData?.['建议游玩时间'] || touristSpotData?.recommendedDuration || '',
      recommendedSeason: touristSpotData?.['建议季节'] || touristSpotData?.recommendedSeason || '',
      description: touristSpotData?.['介绍'] || touristSpotData?.description || (sightData ? `${sightData.level || ''}级景区` : ''),
      tips: touristSpotData?.['小贴士'] || touristSpotData?.tips || '',
      link: touristSpotData?.['链接'] || touristSpotData?.link,
      page: touristSpotData?.page,
      // 空间信息（优先使用 a_sight 的数据）
      level: sightData?.level || touristSpotData?.level || touristSpotData?.等级 || '',
      address: sightData?.address || touristSpotData?.['地址'] || touristSpotData?.address || '',
      city: sightData?.city || touristSpotData?.['城市'] || touristSpotData?.city || '',
      lng_wgs84: sightData?.lng_wgs84 || touristSpotData?.lng_wgs84 || null,
      lat_wgs84: sightData?.lat_wgs84 || touristSpotData?.lat_wgs84 || null,
      // 元信息
      _hasCoordinates: sightData?._hasCoordinates || !!(touristSpotData?.lng_wgs84),
      _source: (touristSpotData && sightData) ? 'merged' : (touristSpotData ? 'tourist-spots' : 'geojson')
    }

    console.log('[DEBUG getSpotByName] 合并后的数据:', mergedData)
    console.log('[DEBUG getSpotByName] 数据来源:', mergedData._source)
    console.log('[DEBUG getSpotByName] 字段检查:', {
      name: mergedData.name,
      level: mergedData.level,
      address: mergedData.address,
      city: mergedData.city,
      lng_wgs84: mergedData.lng_wgs84,
      lat_wgs84: mergedData.lat_wgs84,
      rating: mergedData.rating,
      ticketPrice: mergedData.ticketPrice
    })

    return {
      success: true,
      data: mergedData
    }
  } catch (error) {
    console.error('[ERROR getSpotByName] 获取景点详情失败:', error)
    return {
      success: false,
      error: error.message || '获取景点详情失败'
    }
  }
}

/**
 * 添加新景点
 * @param {object} spotData - 景点数据（扁平结构）
 */
export const addSpot = async (spotData) => {
  try {
    // 将扁平数据转换为后端期望的双表结构
    const requestData = {
      tourist_spot: {
        name: spotData.name,
        地址: spotData.address || '',
        城市: spotData.city || '',
        介绍: spotData.description || '',
        开放时间: spotData.openTime || '',
        图片链接: spotData.imageUrl || '',
        评分: spotData.rating || '',
        建议游玩时间: spotData.recommendedDuration || '',
        建议季节: spotData.recommendedSeason || '',
        门票: spotData.ticketPrice || '',
        小贴士: spotData.tips || '',
        链接: ''
      },
      a_sight: {
        name: spotData.name,
        level: spotData.level || '',
        address: spotData.address || '',
        所属城市: spotData.city || '',
        lngWgs84: spotData.lng_wgs84 || null,
        latWgs84: spotData.lat_wgs84 || null
      }
    }

    console.log('[DEBUG addSpot] 转换后的请求数据:', requestData)
    const response = await post(API_CONFIG.endpoints.touristSpots.add, requestData)
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
 * @param {object} spotData - 更新的景点数据（扁平结构）
 */
export const updateSpotByName = async (name, spotData) => {
  try {
    // 将扁平数据转换为后端期望的双表结构
    const requestData = {
      tourist_spot: {
        name: spotData.name,
        地址: spotData.address || '',
        城市: spotData.city || '',
        介绍: spotData.description || '',
        开放时间: spotData.openTime || '',
        图片链接: spotData.imageUrl || '',
        评分: spotData.rating || '',
        建议游玩时间: spotData.recommendedDuration || '',
        建议季节: spotData.recommendedSeason || '',
        门票: spotData.ticketPrice || '',
        小贴士: spotData.tips || '',
        链接: ''
      },
      a_sight: {
        name: spotData.name,
        level: spotData.level || '',
        address: spotData.address || '',
        所属城市: spotData.city || '',
        lngWgs84: spotData.lng_wgs84 || null,
        latWgs84: spotData.lat_wgs84 || null
      }
    }

    console.log('[DEBUG updateSpotByName] 原始名称:', name)
    console.log('[DEBUG updateSpotByName] 转换后的请求数据:', requestData)

    const url = API_CONFIG.endpoints.touristSpots.updateByName(name)
    console.log('[DEBUG updateSpotByName] 请求URL:', url)

    const response = await put(url, requestData)
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
      // 启用点聚合
      joinCluster: true,
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
