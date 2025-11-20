<template>
  <div
    ref="panelRef"
    class="tourist-spot-search"
    :class="{ 'collapsed': isCollapsed }"
    :style="{ left: position.x + 'px', top: position.y + 'px' }"
  >
    <!-- 搜索框区域（始终显示） -->
    <div
      class="search-box-wrapper"
      @mousedown="handleDragStart"
    >
      <div class="search-box">
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="输入景区名称搜索..."
          @input="handleSearchInput"
          @keyup.enter="searchTouristSpots"
          class="search-input"
        />
        <button @click="searchTouristSpots" class="search-button">搜索</button>
        <button
          @click="toggleExtentSearch"
          :class="['extent-search-button', { active: isExtentSearchActive }]"
          :title="isExtentSearchActive ? '取消范围选择' : '框选范围搜索'"
        >
          {{ isExtentSearchActive ? '取消框选' : '📦 框选' }}
        </button>
        <button
          @click.stop="toggleCollapse"
          class="fold-button"
          :title="isCollapsed ? '展开' : '折叠'"
        >
          {{ isCollapsed ? '▼' : '▲' }}
        </button>
      </div>
    </div>

    <!-- 面板内容区域（可折叠） -->
    <div v-show="!isCollapsed" class="panel-content">
      <!-- 添加景区操作区域 - 始终显示 -->
      <div class="action-section">
        <button
          @click="handleAddSpot"
          class="add-spot-button"
          title="添加新景区"
        >
          ➕ 添加新景区
        </button>
        <span class="action-tip">或使用上方搜索框查找现有景区</span>
      </div>

      <!-- 搜索结果 -->
      <div v-if="searchResults.length > 0" class="search-results">
        <div class="results-header">
          <div class="header-left">
            <h3>搜索结果 ({{ totalCount }} 条)</h3>
          </div>
        </div>

        <!-- 分页控制 -->
        <div class="pagination-controls">
          <button
            @click="prevPage"
            :disabled="currentPage === 1"
            class="pagination-button"
          >
            上一页
          </button>
          <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
          <button
            @click="nextPage"
            :disabled="currentPage === totalPages"
            class="pagination-button"
          >
            下一页
          </button>
        </div>

        <!-- 结果列表 -->
        <div class="results-list">
          <div
            v-for="spot in searchResults"
            :key="spot.id"
            @click="handleSpotClick(spot)"
            class="result-item"
          >
            <div class="spot-info">
              <!-- 图片显示区域 -->
              <div class="spot-image-container">
                <div v-if="getImageLoadingState(spot.name) === 'loading'" class="image-loading">
                  <div class="loading-spinner"></div>
                  <span>加载中...</span>
                </div>
                <div v-else-if="getImageLoadingState(spot.name) === 'loaded' && getLoadedImage(spot.name)" class="image-loaded">
                  <img
                    :src="getLoadedImage(spot.name)"
                    :alt="spot.name"
                    class="spot-image"
                    @error="handleImageError(spot.name)"
                  />
                </div>
                <div v-else-if="getImageLoadingState(spot.name) === 'error'" class="image-error">
                  <div class="error-icon">⚠️</div>
                  <span>图片加载失败</span>
                </div>
                <div v-else class="image-placeholder">
                  <div class="placeholder-icon">🏞️</div>
                  <span>暂无图片</span>
                </div>
              </div>

              <h4 class="spot-name">
                {{ spot.name }}
                <span v-if="spot._isBasicInfo" class="basic-info-badge">基本信息</span>
                <!-- 操作按钮组 -->
                <div class="action-buttons">
                  <!-- 修改按钮 -->
                  <button
                    @click.stop="handleEditSpot(spot)"
                    class="edit-button"
                    title="修改景点信息"
                  >
                    ✏️
                  </button>
                  <!-- 删除按钮 -->
                  <button
                    @click.stop="handleDeleteSpot(spot)"
                    class="delete-button"
                    title="删除景点"
                  >
                    🗑️
                  </button>
                </div>
              </h4>
              <div class="spot-details">
                <p v-if="spot.level" class="spot-level">
                  <span class="label">等级:</span> {{ spot.level }}
                </p>
                <p v-if="spot.地址" class="spot-address">
                  <span class="label">地址:</span> {{ spot.地址 }}
                </p>
                <p v-if="spot.评分" class="spot-rating">
                  <span class="label">评分:</span> {{ spot.评分 }}
                </p>
                <p v-if="spot.门票" class="spot-ticket">
                  <span class="label">门票:</span> {{ spot.门票 }}
                </p>
                <p v-if="spot.开放时间" class="spot-open-time">
                  <span class="label">开放时间:</span> {{ spot.开放时间 }}
                </p>
                <p v-if="spot.建议游玩时间" class="spot-duration">
                  <span class="label">建议游玩时间:</span> {{ spot.建议游玩时间 }}
                </p>
                <p v-if="spot.建议季节" class="spot-season">
                  <span class="label">建议季节:</span> {{ spot.建议季节 }}
                </p>
                <p v-if="spot.小贴士" class="spot-tips">
                  <span class="label">小贴士:</span> {{ spot.小贴士 }}
                </p>
                <p v-if="spot.介绍" class="spot-description">
                  <span class="label">介绍:</span> {{ spot.介绍 }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 无结果提示 -->
      <div v-else-if="hasSearched" class="no-results">
        <p>未找到相关景区的详细信息</p>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <p>搜索中...</p>
      </div>
    </div>

    <!-- 修改弹窗 -->
    <TouristSpotEditModal
      v-if="editModalVisible"
      :spot="editingSpot"
      :visible="editModalVisible"
      @close="() => editModalVisible = false"
      @save="handleSpotSave"
    />
  </div>
</template>

<script>
import { ref, inject, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
import API_CONFIG from '../config/api.js'
import TouristSpotEditModal from './TouristSpotEditModal.vue'
import { TRUE } from 'ol/functions.js'

export default {
  name: 'TouristSpotSearch',
  components: {
    TouristSpotEditModal
  },
  setup() {
    const searchKeyword = ref('')
    const searchResults = ref([])
    const allSearchResults = ref([]) // 存储所有搜索结果
    const loading = ref(false)
    const hasSearched = ref(false)
    const currentPage = ref(1)
    const pageSize = ref(10)
    const totalCount = ref(0)

    // 范围搜索相关状态
    const isExtentSearchActive = ref(false)

    // 面板UI状态
    const panelRef = ref(null)
    const isCollapsed = ref(true)
    const position = ref({ x: 80, y: 8 }) // 初始位置：左上角
    const isDragging = ref(false)
    const dragOffset = ref({ x: 0, y: 0 })

    // 注入 mapUtils 实例
    const mapUtils = inject('mapUtils')

    // 注入图片缓存系统
    const imageCache = inject('imageCache')

    // 注入地图中心标记更新函数
    const updateMapCenterMarker = inject('updateMapCenterMarker')

    // 注入选中景区信息
    const selectedSpotInfo = inject('selectedSpotInfo')
    const setSelectedSpotInfo = inject('setSelectedSpotInfo')
    const registerSpotClickCallback = inject('registerSpotClickCallback')

    // 修改弹窗相关状态
    const editModalVisible = ref(false)
    const editingSpot = ref(null)

    // 注入范围选择功能
    const activateExtentDraw = inject('activateExtentDraw', null)
    const deactivateExtentDraw = inject('deactivateExtentDraw', null)

    // ==================== AI智能查询结果接收 ====================

    // 注入 AI 查询结果（由 OlMap 提供）
    const agentQueryResult = inject('agentQueryResult', null)

    // 存储从地图点击的景区信息
    const mapClickedSpotInfo = ref(null)

    // 图片加载状态管理
    const imageLoadingStates = ref(new Map()) // 存储每个景点的图片加载状态
    const loadedImages = ref(new Map()) // 存储已加载的图片URL

    // 分批加载图片
    const batchLoadImages = async (spots) => {
      const batchSize = 3 // 每批加载的图片数量
      const maxConcurrent = 2 // 最大并发数
      
      for (let i = 0; i < spots.length; i += batchSize) {
        const batch = spots.slice(i, i + batchSize)
        
        // 使用 Promise.all 控制并发
        const promises = batch.map(async (spot) => {
          if (loadedImages.value.has(spot.name)) {
            return // 已加载，跳过
          }
          
          // 设置加载状态
          imageLoadingStates.value.set(spot.name, 'loading')
          
          try {
            // 使用共享的图片缓存系统获取图片URL
            const imageUrl = await imageCache.fetchTouristSpotImageUrl(spot.name)
            
            if (imageUrl) {
              // 使用共享的图片缓存系统加载图片
              await imageCache.loadImageAndCreateIcon(imageUrl)
              loadedImages.value.set(spot.name, imageUrl)
              imageLoadingStates.value.set(spot.name, 'loaded')
            } else {
              imageLoadingStates.value.set(spot.name, 'error')
            }
          } catch (error) {
            console.error(`加载图片失败: ${spot.name}`, error)
            imageLoadingStates.value.set(spot.name, 'error')
          }
        })
        
        // 控制并发数
        const concurrentPromises = []
        for (let j = 0; j < promises.length; j += maxConcurrent) {
          const concurrentBatch = promises.slice(j, j + maxConcurrent)
          await Promise.all(concurrentBatch)
          // 添加延迟避免请求过于频繁
          await new Promise(resolve => setTimeout(resolve, 100))
        }
      }
    }

    // 获取图片加载状态
    const getImageLoadingState = (spotName) => {
      return imageLoadingStates.value.get(spotName) || 'idle'
    }

    // 获取已加载的图片URL
    const getLoadedImage = (spotName) => {
      return loadedImages.value.get(spotName)
    }

    // 处理图片加载错误
    const handleImageError = (spotName) => {
      console.warn(`图片加载失败: ${spotName}`)
      imageLoadingStates.value.set(spotName, 'error')
    }

    // 计算总页数
    const totalPages = ref(0)

    // 防抖搜索
    let searchTimeout = null

    const handleSearchInput = () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout)
      }
      searchTimeout = setTimeout(() => {
        if (searchKeyword.value.trim()) {
          currentPage.value = 1
          searchTouristSpots()
        }
      }, 500)
    }

    // 搜索景区（同时查询两个表）
    const searchTouristSpots = async () => {
      if (!searchKeyword.value.trim()) {
        searchResults.value = []
        hasSearched.value = false
        return
      }

      loading.value = true
      hasSearched.value = true

      try {
        const keyword = searchKeyword.value.trim()
        const cleanedKeyword = extractChineseName(keyword)

        // 并发查询两个表
        const [touristSpotResponse, sightResponse] = await Promise.all([
          // 1. 查询 tourist_spot 表（详细信息）
          axios.get(API_CONFIG.buildURL(API_CONFIG.endpoints.touristSpots.search), {
            params: { name: keyword }
          }).catch(err => {
            console.error('查询tourist_spot表失败:', err)
            return { data: [] }
          }),

          // 2. 查询 a_sight 表（空间信息）
          axios.post(API_CONFIG.buildURL(API_CONFIG.endpoints.sights.geojsonByExtentAndLevel), {
            minLon: -180,
            minLat: -90,
            maxLon: 180,
            maxLat: 90,
            levels: ['5A', '4A', '3A', '2A', '1A']
          }).catch(err => {
            console.error('查询a_sight表失败:', err)
            return { data: { features: [] } }
          })
        ])

        // 处理 tourist_spot 表结果
        const touristSpots = touristSpotResponse.data || []
        console.log(`tourist_spot 表查询结果: ${touristSpots.length} 个景区`)

        // 处理 a_sight 表结果，转换为Map方便查找
        const sightMap = new Map()
        if (sightResponse.data && sightResponse.data.features) {
          console.log(`a_sight 表查询结果: ${sightResponse.data.features.length} 个景区`)
          sightResponse.data.features.forEach(feature => {
            const name = feature.properties?.name
            if (name) {
              const hasCoordinates = !!feature.geometry?.coordinates
              console.log(`景区 ${name}: 坐标存在 = ${hasCoordinates}`, { 
                geometry: feature.geometry,
                coordinates: feature.geometry?.coordinates 
              })
              sightMap.set(name, {
                coordinates: feature.geometry?.coordinates,
                level: feature.properties?.level,
                address: feature.properties?.address
              })
            }
          })
        }

        // 合并结果 - 新的搜索策略：允许无坐标的景区显示
        const mergedResults = []
        const processedNames = new Set()

        // 1. 处理 tourist_spot 表的结果
        touristSpots.forEach(spot => {
          const cleanedSpotName = extractChineseName(spot.name)

          // 查找匹配的关键词
          if (cleanedSpotName.includes(cleanedKeyword) || spot.name.includes(keyword)) {
            // 尝试在 a_sight 中找到匹配的景区 - 使用多种匹配策略
            let sightInfo = sightMap.get(cleanedSpotName)
            if (!sightInfo) {
              // 尝试使用原始名称匹配
              sightInfo = sightMap.get(spot.name)
            }
            if (!sightInfo) {
              // 尝试使用包含匹配
              for (const [sightName, sightData] of sightMap.entries()) {
                if (sightName.includes(cleanedSpotName) || cleanedSpotName.includes(sightName)) {
                  sightInfo = sightData
                  break
                }
              }
            }

            if (sightInfo) {
              // 两个表都有数据，合并
              const hasCoordinates = !!sightInfo.coordinates
              console.log(`两个表都有数据 ${cleanedSpotName}: 坐标存在 = ${hasCoordinates}`, sightInfo)
              mergedResults.push({
                ...spot,
                coordinates: sightInfo.coordinates, // 添加坐标
                level: spot.level || sightInfo.level, // 优先使用tourist_spot的等级
                地址: spot.地址 || sightInfo.address,
                _hasCoordinates: hasCoordinates  // 动态判断是否有坐标
              })
              processedNames.add(cleanedSpotName)
            } else {
              // 只有 tourist_spot 数据
              mergedResults.push({
                ...spot,
                _hasCoordinates: false
              })
              processedNames.add(cleanedSpotName)
            }
          }
        })

        // 2. 处理 a_sight 表中有但 tourist_spot 表中没有的景区
        // 即使没有坐标信息，也包含该景区的基本信息
        console.log('sightMap 所有景区名称:', Array.from(sightMap.keys()))
        console.log('processedNames 已处理景区:', Array.from(processedNames))
        console.log('搜索关键词 - 原始:', keyword, '清洗后:', cleanedKeyword)
        console.log('处理 a_sight 表中独有的景区:', Array.from(sightMap.keys()).filter(name => {
          const cleanedSightName = extractChineseName(name)
          const shouldInclude = 
            name.includes(cleanedKeyword) || 
            cleanedSightName.includes(cleanedKeyword) ||
            name.includes(keyword) ||
            cleanedSightName.includes(keyword)
          return shouldInclude && !processedNames.has(name) && !processedNames.has(cleanedSightName)
        }))
        
        sightMap.forEach((sightInfo, name) => {
          // 使用更宽松的匹配策略
          const cleanedSightName = extractChineseName(name)
          const shouldInclude = 
            name.includes(cleanedKeyword) || 
            cleanedSightName.includes(cleanedKeyword) ||
            name.includes(keyword) ||
            cleanedSightName.includes(keyword)
          
          if (shouldInclude && !processedNames.has(name) && !processedNames.has(cleanedSightName)) {
            const hasCoordinates = !!sightInfo.coordinates
            console.log(`添加景区 ${name}: 坐标存在 = ${hasCoordinates}`, sightInfo)
            mergedResults.push({
              name: name,
              level: sightInfo.level || '未知',
              地址: sightInfo.address || '暂无地址信息',
              介绍: `${sightInfo.level || ''}级景区`,
              coordinates: sightInfo.coordinates,
              _isBasicInfo: true,
              _hasCoordinates: hasCoordinates  // 根据是否有坐标设置标记
            })
          }
        })

        // 保存所有搜索结果用于分页
        allSearchResults.value = mergedResults
        totalCount.value = mergedResults.length
        totalPages.value = Math.ceil(totalCount.value / pageSize.value)

        console.log('最终搜索结果:', mergedResults)
        console.log(`搜索完成: 共找到 ${mergedResults.length} 个景区 (${mergedResults.filter(r => r._hasCoordinates).length} 个有坐标, ${mergedResults.filter(r => !r._hasCoordinates).length} 个无坐标)`)

        // 应用分页
        applyPagination()
      } catch (error) {
        console.error('搜索景区失败:', error)
        searchResults.value = []
        totalCount.value = 0
        totalPages.value = 0
      } finally {
        loading.value = false
      }
    }

    // 应用分页
    const applyPagination = () => {
      const startIndex = (currentPage.value - 1) * pageSize.value
      const endIndex = startIndex + pageSize.value
      searchResults.value = allSearchResults.value.slice(startIndex, endIndex)
      
      // 分页后自动加载当前页的图片
      if (searchResults.value.length > 0) {
        batchLoadImages(searchResults.value)
      }
    }

    // 分页控制
    const prevPage = () => {
      if (currentPage.value > 1) {
        currentPage.value--
        applyPagination()
      }
    }

    const nextPage = () => {
      if (currentPage.value < totalPages.value) {
        currentPage.value++
        applyPagination()
      }
    }

    // 从混合名称中提取中文部分
    const extractChineseName = (mixedName) => {
      if (!mixedName) return ''
      
      // 匹配中文字符（包括中文标点符号）
      const chineseRegex = /[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+/g
      const chineseMatches = mixedName.match(chineseRegex)
      
      if (chineseMatches && chineseMatches.length > 0) {
        // 返回所有中文字符的组合
        return chineseMatches.join('')
      }
      
      // 如果没有找到中文，返回原名称
      return mixedName
    }

    // 处理从地图点击的景区信息
    const handleSpotClickFromMap = async (spotInfo) => {
      console.log('收到地图点击的景区信息:', spotInfo)
      mapClickedSpotInfo.value = spotInfo

      // 处理聚合要素 - 多个景区
      if (spotInfo.isCluster && spotInfo.names && spotInfo.names.length > 0) {
        console.log(`聚合要素包含 ${spotInfo.names.length} 个景区`)

        // 清空之前的搜索结果
        allSearchResults.value = []
        searchResults.value = []

        // 为每个景区名称发起搜索请求，并保存原始要素信息和坐标
        const searchPromises = spotInfo.names.map(async (name, index) => {
          try {
            const cleanedName = extractChineseName(name.trim())
            const searchUrl = API_CONFIG.buildURL(API_CONFIG.endpoints.touristSpots.search)
            const response = await axios.get(searchUrl, {
              params: { name: cleanedName }
            })

            // 获取要素的坐标信息
            const feature = spotInfo.features && spotInfo.features[index]
            const properties = feature?.get ? feature.getProperties() : (feature?.properties || {})
            const geometry = feature?.getGeometry ? feature.getGeometry() : feature?.geometry
            const coordinates = geometry?.getCoordinates ? geometry.getCoordinates() : geometry?.coordinates

            // 如果找到详细信息，返回并添加坐标
            if (response.data && response.data.length > 0) {
              return response.data.map(spot => ({
                ...spot,
                coordinates: coordinates, // 保存坐标
                _hasCoordinates: !!coordinates
              }))
            }

            // 如果没有详细信息，从要素中提取基本信息并保存坐标
            return [{
              name: name,
              level: properties.level || '未知',
              地址: properties.address || '暂无地址信息',
              介绍: `${properties.level || ''}级景区`,
              coordinates: coordinates, // 保存坐标
              _isBasicInfo: true,
              _hasCoordinates: !!coordinates
            }]
          } catch (error) {
            console.error(`搜索景区 ${name} 失败:`, error)
            // 出错时也返回基本信息和坐标
            const feature = spotInfo.features && spotInfo.features[index]
            const properties = feature?.get ? feature.getProperties() : (feature?.properties || {})
            const geometry = feature?.getGeometry ? feature.getGeometry() : feature?.geometry
            const coordinates = geometry?.getCoordinates ? geometry.getCoordinates() : geometry?.coordinates

            return [{
              name: name,
              level: properties.level || '未知',
              地址: properties.address || '暂无地址信息',
              介绍: `${properties.level || ''}级景区`,
              coordinates: coordinates, // 保存坐标
              _isBasicInfo: true,
              _hasCoordinates: !!coordinates
            }]
          }
        })

        // 等待所有搜索完成
        const results = await Promise.all(searchPromises)

        // 合并所有结果并去重（根据景区名称）
        const mergedResults = results.flat()
        const uniqueResults = mergedResults.filter((result, index, self) =>
          index === self.findIndex(r => r.name === result.name)
        )

        // 更新搜索结果
        allSearchResults.value = uniqueResults
        totalCount.value = uniqueResults.length
        totalPages.value = Math.ceil(totalCount.value / pageSize.value)
        currentPage.value = 1

        // 设置搜索关键词为聚合信息
        searchKeyword.value = `聚合要素 (${spotInfo.count}个景区)`
        hasSearched.value = true

        // 应用分页
        applyPagination()

        console.log(`聚合要素搜索完成，找到 ${uniqueResults.length} 个景区详情`)

        // 自动滚动到搜索结果
        setTimeout(() => {
          const searchResultsElement = document.querySelector('.search-results')
          if (searchResultsElement) {
            searchResultsElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        }, 100)

        return
      }

      // 处理单个景区
      if (!spotInfo || !spotInfo.name) {
        console.warn('地图点击的景区缺少名称，无法触发搜索')
        return
      }

      // 提取纯中文名称，优先使用中文名称进行搜索
      const originalName = spotInfo.name.trim()
      const cleanedName = extractChineseName(originalName)

      const candidateNames = [cleanedName, originalName]
        .map(name => name && name.trim())
        .filter((name, index, self) => name && self.indexOf(name) === index)

      let matched = false

      for (const name of candidateNames) {
        searchKeyword.value = name
        await searchTouristSpots()

        if (searchResults.value.length > 0) {
          matched = true

          // 将完全匹配的景区放到列表首位，方便查看详情
          const exactMatchIndex = searchResults.value.findIndex(result => result.name === name)
          if (exactMatchIndex > 0) {
            const [exactMatch] = searchResults.value.splice(exactMatchIndex, 1)
            searchResults.value.unshift(exactMatch)

            const fullMatchIndex = allSearchResults.value.findIndex(result => result.name === name)
            if (fullMatchIndex > 0) {
              const [fullMatch] = allSearchResults.value.splice(fullMatchIndex, 1)
              allSearchResults.value.unshift(fullMatch)
            }
          }

          console.log(`找到匹配景区，使用关键词: ${name}`)

          // 自动滚动到第一个匹配的结果并高亮显示
          setTimeout(() => {
            const firstResultElement = document.querySelector('.result-item')
            if (firstResultElement) {
              firstResultElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
              firstResultElement.classList.add('highlighted')
              setTimeout(() => {
                firstResultElement.classList.remove('highlighted')
              }, 3000)
            }
          }, 100)

          break
        }
      }

      // 如果没有找到详细信息，显示基本信息并保存坐标
      if (!matched) {
        console.log(`未找到景区详细信息，显示基本信息`)

        const properties = spotInfo.properties || {}
        const coordinates = spotInfo.coordinates // 从地图点击信息中获取坐标

        allSearchResults.value = [{
          name: spotInfo.name,
          level: properties.level || spotInfo.level || '未知',
          地址: properties.address || '暂无地址信息',
          介绍: `${properties.level || spotInfo.level || ''}级景区`,
          coordinates: coordinates, // 保存坐标
          _isBasicInfo: true,
          _hasCoordinates: !!coordinates
        }]

        totalCount.value = 1
        totalPages.value = 1
        currentPage.value = 1
        searchKeyword.value = spotInfo.name
        hasSearched.value = true

        applyPagination()

        // 自动滚动到搜索结果
        setTimeout(() => {
          const firstResultElement = document.querySelector('.result-item')
          if (firstResultElement) {
            firstResultElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
            firstResultElement.classList.add('highlighted')
            setTimeout(() => {
              firstResultElement.classList.remove('highlighted')
            }, 3000)
          }
        }, 100)
      }
    }

    // 处理景区点击（从搜索结果列表）
    const handleSpotClick = async (spot) => {
      if (!mapUtils || !mapUtils.value) {
        console.error('地图工具未初始化')
        return
      }

      try {
        // 如果景区已有坐标，直接使用
        if (spot._hasCoordinates && spot.coordinates) {
          console.log(`使用已保存的坐标跳转到景区: ${spot.name}`, { coordinates: spot.coordinates })

          // 跳转到该点为中心
          mapUtils.value.map.getView().setCenter(spot.coordinates)
          mapUtils.value.map.getView().setZoom(15)

          // 更新地图中心标记位置
          if (updateMapCenterMarker) {
            updateMapCenterMarker()
          }

          // 触发地图移动事件，让智能景区图层重新加载数据
          setTimeout(() => {
            mapUtils.value.map.dispatchEvent('moveend')
          }, 100)

          return
        }

        // 如果没有坐标，查询 a_sight 表获取坐标
        console.log(`景区 ${spot.name} 没有坐标，查询 a_sight 表`)
        const chineseName = extractChineseName(spot.name)

        const sightQueryRequest = {
          minLon: -180,
          minLat: -90,
          maxLon: 180,
          maxLat: 90,
          levels: ['5A', '4A', '3A', '2A', '1A']
        }

        const sightUrl = API_CONFIG.buildURL(API_CONFIG.endpoints.sights.geojsonByExtentAndLevel)
        const response = await axios.post(sightUrl, sightQueryRequest)

        if (response.data) {
          const geojson = typeof response.data === 'string' ? JSON.parse(response.data) : response.data

          // 在 GeoJSON 中查找匹配的景区
          const matchingFeature = geojson.features.find(feature =>
            feature.properties && feature.properties.name === chineseName
          )

          if (matchingFeature && matchingFeature.geometry && matchingFeature.geometry.coordinates) {
            const coordinates = matchingFeature.geometry.coordinates

            mapUtils.value.map.getView().setCenter(coordinates)
            mapUtils.value.map.getView().setZoom(15)

            console.log(`已跳转到景区: ${chineseName}`, { coordinates })

            if (updateMapCenterMarker) {
              updateMapCenterMarker()
            }

            setTimeout(() => {
              mapUtils.value.map.dispatchEvent('moveend')
            }, 100)
          } else {
            console.warn(`未找到景区 ${chineseName} 的坐标信息`)
            // 尝试使用原始名称匹配
            const fallbackFeature = geojson.features.find(feature =>
              feature.properties && feature.properties.name === spot.name
            )

            if (fallbackFeature && fallbackFeature.geometry && fallbackFeature.geometry.coordinates) {
              const coordinates = fallbackFeature.geometry.coordinates
              mapUtils.value.map.getView().setCenter(coordinates)
              mapUtils.value.map.getView().setZoom(15)

              if (updateMapCenterMarker) {
                updateMapCenterMarker()
              }

              setTimeout(() => {
                mapUtils.value.map.dispatchEvent('moveend')
              }, 100)

              console.log(`使用原始名称跳转到景区: ${spot.name}`, { coordinates })
            } else {
              console.warn(`使用原始名称也未找到景区 ${spot.name} 的坐标信息`)
              alert(`未找到景区"${spot.name}"的位置信息`)
            }
          }
        } else {
          console.warn(`查询景区 ${chineseName} 坐标失败`)
          alert(`未找到景区"${spot.name}"的位置信息`)
        }
      } catch (error) {
        console.error(`获取景区 ${spot.name} 坐标失败:`, error)
        alert(`获取景区位置失败: ${error.message}`)
      }
    }

    // 切换范围搜索模式
    const toggleExtentSearch = () => {
      if (!activateExtentDraw || !deactivateExtentDraw) {
        console.error('范围选择功能未注入')
        alert('范围选择功能不可用')
        return
      }

      if (isExtentSearchActive.value) {
        // 取消范围搜索
        deactivateExtentDraw()
        isExtentSearchActive.value = false
        console.log('范围搜索已取消')
      } else {
        // 激活范围搜索
        activateExtentDraw(handleExtentSelected)
        isExtentSearchActive.value = true
        console.log('范围搜索已激活，请在地图上绘制矩形框选范围')
      }
    }

    // 处理范围选择完成
    const handleExtentSelected = async (extent) => {
      console.log('范围选择完成:', extent)
      isExtentSearchActive.value = false

      // 设置加载状态
      loading.value = true
      hasSearched.value = true
      searchKeyword.value = '范围搜索'

      try {
        // 1. 先查询 a_sight 表获取范围内的景区
        const sightQueryRequest = {
          minLon: extent[0],
          minLat: extent[1],
          maxLon: extent[2],
          maxLat: extent[3],
          levels: ['5A', '4A', '3A', '2A', '1A'] // 查询所有等级
        }

        const sightUrl = API_CONFIG.buildURL(API_CONFIG.endpoints.sights.geojsonByExtentAndLevel)
        const sightResponse = await axios.post(sightUrl, sightQueryRequest)

        if (!sightResponse.data || !sightResponse.data.features || sightResponse.data.features.length === 0) {
          console.log('范围内没有找到景区')
          searchResults.value = []
          allSearchResults.value = []
          totalCount.value = 0
          totalPages.value = 0
          loading.value = false
          return
        }

        // 提取景区信息（包括名称、属性和坐标）
        const sightFeatures = sightResponse.data.features.map(feature => ({
          name: feature.properties?.name,
          properties: feature.properties,
          coordinates: feature.geometry?.coordinates // 保存坐标信息
        })).filter(item => item.name)

        console.log(`范围内找到 ${sightFeatures.length} 个景区`)

        // 2. 根据景区名称查询详细信息，如果没有详细信息则使用基本属性
        const searchPromises = sightFeatures.map(async (sightFeature) => {
          try {
            const cleanedName = extractChineseName(sightFeature.name.trim())
            const searchUrl = API_CONFIG.buildURL(API_CONFIG.endpoints.touristSpots.search)
            const response = await axios.get(searchUrl, {
              params: { name: cleanedName }
            })

            // 如果找到详细信息，返回详细信息并添加坐标
            if (response.data && response.data.length > 0) {
              return response.data.map(spot => ({
                ...spot,
                coordinates: sightFeature.coordinates, // 保存坐标
                _hasCoordinates: !!sightFeature.coordinates  // 根据是否有坐标设置标记
              }))
            }

            // 如果没有详细信息，返回基本属性并添加坐标
            return [{
              name: sightFeature.name,
              level: sightFeature.properties.level || '未知',
              地址: sightFeature.properties.address || '暂无地址信息',
              介绍: `${sightFeature.properties.level || ''}级景区`,
              coordinates: sightFeature.coordinates, // 保存坐标
              _isBasicInfo: true, // 标记这是基本信息
              _hasCoordinates: !!sightFeature.coordinates  // 根据是否有坐标设置标记
            }]
          } catch (error) {
            console.error(`查询景区 ${sightFeature.name} 详细信息失败:`, error)
            // 查询失败也返回基本信息并添加坐标
            return [{
              name: sightFeature.name,
              level: sightFeature.properties.level || '未知',
              地址: sightFeature.properties.address || '暂无地址信息',
              介绍: `${sightFeature.properties.level || ''}级景区`,
              coordinates: sightFeature.coordinates, // 保存坐标
              _isBasicInfo: true,
              _hasCoordinates: !!sightFeature.coordinates  // 根据是否有坐标设置标记
            }]
          }
        })

        // 等待所有查询完成
        const results = await Promise.all(searchPromises)

        // 合并结果并去重
        const mergedResults = results.flat()
        const uniqueResults = mergedResults.filter((result, index, self) =>
          index === self.findIndex(r => r.name === result.name)
        )

        // 更新搜索结果
        allSearchResults.value = uniqueResults
        totalCount.value = uniqueResults.length
        totalPages.value = Math.ceil(totalCount.value / pageSize.value)
        currentPage.value = 1

        // 应用分页
        applyPagination()

        console.log(`范围搜索完成，找到 ${uniqueResults.length} 个景区详情`)

        // 自动滚动到搜索结果
        setTimeout(() => {
          const searchResultsElement = document.querySelector('.search-results')
          if (searchResultsElement) {
            searchResultsElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        }, 100)

      } catch (error) {
        console.error('范围搜索失败:', error)
        searchResults.value = []
        allSearchResults.value = []
        totalCount.value = 0
        totalPages.value = 0
      } finally {
        loading.value = false
      }
    }

    // ==================== 面板UI控制函数 ====================

    // 切换折叠状态
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
    }

    // 开始拖拽
    const handleDragStart = (e) => {
      // 检查点击目标是否为输入框，如果是则阻止拖拽
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON') {
        return
      }

      // 阻止文本选择
      e.preventDefault()

      isDragging.value = true

      // 计算鼠标相对于面板的偏移量
      const rect = panelRef.value.getBoundingClientRect()
      dragOffset.value = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      }

      // 添加全局事件监听器
      document.addEventListener('mousemove', onDrag)
      document.addEventListener('mouseup', stopDrag)
    }

    // 拖拽中
    const onDrag = (e) => {
      if (!isDragging.value) return

      // 计算新位置
      let newX = e.clientX - dragOffset.value.x
      let newY = e.clientY - dragOffset.value.y

      // 限制面板不超出视口边界
      const panel = panelRef.value
      if (panel) {
        const maxX = window.innerWidth - panel.offsetWidth
        const maxY = window.innerHeight - panel.offsetHeight

        newX = Math.max(0, Math.min(newX, maxX))
        newY = Math.max(0, Math.min(newY, maxY))
      }

      position.value = { x: newX, y: newY }
    }

    // 停止拖拽
    const stopDrag = () => {
      isDragging.value = false

      // 移除全局事件监听器
      document.removeEventListener('mousemove', onDrag)
      document.removeEventListener('mouseup', stopDrag)
    }

    // ==================== 监听 AI 查询结果 ====================

    /**
     * 处理 AI 查询结果
     * 当 agent_query_bar 查询成功后，将数据显示在搜索结果列表中
     */
    const handleAgentQueryResult = (result) => {
      if (!result || !result.data) {
        console.warn('TouristSpotSearch: AI 查询结果为空')
        return
      }

      console.log('TouristSpotSearch: 处理 AI 查询结果，数量:', result.data.length)

      // 清空当前搜索结果
      allSearchResults.value = []
      searchResults.value = []

      // 设置搜索关键词为 AI 查询
      searchKeyword.value = `AI 查询: ${result.query || '未知'}`
      hasSearched.value = true

      // 将 AI 返回的数据赋值给搜索结果，并进行字段名映射
      // 为每条数据添加标记，表示这是从 AI 查询获得的
      const processedData = result.data.map(item => {
        // 字段名映射：将 AI 返回的字段名映射为前端模板期望的字段名
        const mappedItem = {
          ...item,
          // 映射字段名 - 正确处理 null 值
          地址: item.address !== undefined ? item.address : item.地址,
          评分: item.rating !== undefined ? item.rating : item.评分,
          门票: item.ticket_price !== undefined ? item.ticket_price : item.门票,
          开放时间: item.opening_hours !== undefined ? item.opening_hours : item.开放时间,
          建议游玩时间: item.suggested_duration !== undefined ? item.suggested_duration : item.建议游玩时间,
          建议季节: item.suggested_season !== undefined ? item.suggested_season : item.建议季节,
          小贴士: item.tips !== undefined ? item.tips : item.小贴士,
          介绍: item.introduction !== undefined ? item.introduction : item.介绍,
          // 添加标记
          _fromAI: true,          // 标记来源为 AI
          _hasCoordinates: !!item.coordinates  // 标记是否有坐标
        }

        // 删除重复的字段，避免数据冗余
        delete mappedItem.address
        delete mappedItem.rating
        delete mappedItem.ticket_price
        delete mappedItem.opening_hours
        delete mappedItem.suggested_duration
        delete mappedItem.suggested_season
        delete mappedItem.tips
        delete mappedItem.introduction

        return mappedItem
      })

      allSearchResults.value = processedData
      totalCount.value = result.count || processedData.length
      totalPages.value = Math.ceil(totalCount.value / pageSize.value)
      currentPage.value = 1

      // 应用分页
      applyPagination()

      console.log('TouristSpotSearch: AI 查询结果已显示，总数:', totalCount.value)
      console.log('TouristSpotSearch: 处理后的第一条数据:', processedData[0])
    }

    // 监听 AI 查询结果的变化
    if (agentQueryResult) {
      watch(agentQueryResult, (newResult) => {
        if (newResult) {
          console.log('TouristSpotSearch: 检测到新的 AI 查询结果')
          handleAgentQueryResult(newResult)
        }
      })
    }

    onMounted(() => {
      console.log('TouristSpotSearch 组件已挂载')

      // 注册景区点击回调
      if (registerSpotClickCallback) {
        registerSpotClickCallback(handleSpotClickFromMap)
        console.log('景区点击回调已注册')
      } else {
        console.warn('registerSpotClickCallback 未注入')
      }
    })

    // 处理景点修改
    const handleEditSpot = (spot) => {
      console.log('开始修改景点:', spot)
      console.log('景点ID:', spot.id)
      console.log('景点名称:', spot.name)
      
      // 检查景点数据是否有效
      // if (!spot || !spot.id) {
      //   console.error('景点数据无效，缺少ID:', spot)
      //   alert('无法编辑该景点：缺少必要数据')
      //   return
      // }
      
      editingSpot.value = spot
      editModalVisible.value = true
      
      console.log('弹窗状态已更新:', {
        editModalVisible: editModalVisible.value,
        editingSpot: editingSpot.value
      })
    }

    // 处理景点保存
    const handleSpotSave = (updatedSpot) => {
      console.log('景点保存成功:', updatedSpot)

      // 判断是否为新增操作（原始editedSpot没有id）
      const isAddOperation = !editingSpot.value.id

      if (isAddOperation) {
        // 新增操作：添加到搜索结果列表
        console.log('新增景区，添加到搜索结果')
        allSearchResults.value.unshift(updatedSpot)
        totalCount.value = allSearchResults.value.length
        totalPages.value = Math.ceil(totalCount.value / pageSize.value)
        currentPage.value = 1 // 跳转到第一页显示新增的景区
      } else {
        // 编辑操作：更新搜索结果列表中的景点信息
        const index = allSearchResults.value.findIndex(s => s.id === updatedSpot.id)
        if (index !== -1) {
          allSearchResults.value[index] = { ...allSearchResults.value[index], ...updatedSpot }
        }
      }

      applyPagination() // 重新应用分页以更新显示
      editModalVisible.value = false
    }

    // 处理添加景点
    const handleAddSpot = () => {
      console.log('开始添加新景点')
      // 创建空的景点对象
      const newSpot = {
        id: null, // null表示新增模式
        name: '',
        level: '',
        地址: '',
        介绍: '',
        评分: '',
        门票: '',
        开放时间: '',
        建议游玩时间: '',
        建议季节: '',
        小贴士: '',
        图片链接: '',
        lng_wgs84: '',
        lat_wgs84: '',
        _isBasicInfo: false,
        _hasCoordinates: false
      }

      editingSpot.value = newSpot
      editModalVisible.value = true

      console.log('添加弹窗状态已更新:', {
        editModalVisible: editModalVisible.value,
        editingSpot: editingSpot.value
      })
    }

    // 处理删除景点
    const handleDeleteSpot = async (spot) => {
      // 确认删除
      const confirmMessage = `确定要删除景区"${spot.name}"吗？此操作不可撤销。`
      if (!confirm(confirmMessage)) {
        console.log('用户取消删除操作')
        return
      }

      console.log('开始删除景区:', spot.name)

      try {
        // 使用景点名称删除，支持中英文混合
        const spotName = spot.name.trim()
        const encodedName = encodeURIComponent(spotName)
        const deleteUrl = API_CONFIG.buildURL(API_CONFIG.endpoints.touristSpots.deleteByName(encodedName))

        console.log(`删除景区 URL: ${deleteUrl}`)

        const response = await axios.delete(deleteUrl)
        console.log('删除景区成功:', response.data)

        // 从本地搜索结果中移除
        const index = allSearchResults.value.findIndex(s => s.name === spot.name)
        if (index !== -1) {
          allSearchResults.value.splice(index, 1)
          totalCount.value = allSearchResults.value.length
          totalPages.value = Math.ceil(totalCount.value / pageSize.value)

          // 如果当前页没有数据了，返回上一页
          if (currentPage.value > totalPages.value && currentPage.value > 1) {
            currentPage.value = totalPages.value
          }

          applyPagination()
        }

        alert(`景区"${spot.name}"删除成功`)

      } catch (error) {
        console.error(`删除景区 "${spot.name}" 失败:`, error)
        const errorMessage = error.response?.data?.message || error.message || '删除失败'
        alert(`删除景区失败: ${errorMessage}`)
      }
    }

    // 组件卸载时清理事件监听器
    onUnmounted(() => {
      document.removeEventListener('mousemove', onDrag)
      document.removeEventListener('mouseup', stopDrag)
    })

    return {
      // 面板UI
      panelRef,
      isCollapsed,
      position,
      toggleCollapse,
      handleDragStart,
      // 搜索相关
      searchKeyword,
      searchResults,
      loading,
      hasSearched,
      currentPage,
      pageSize,
      totalCount,
      totalPages,
      handleSearchInput,
      searchTouristSpots,
      prevPage,
      nextPage,
      handleSpotClick,
      getImageLoadingState,
      getLoadedImage,
      handleImageError,
      isExtentSearchActive,
      toggleExtentSearch,
      // 修改相关
      editModalVisible,
      editingSpot,
      handleEditSpot,
      handleSpotSave,
      // 添加和删除相关
      handleAddSpot,
      handleDeleteSpot
    }
  }
}
</script>

<style scoped>
/* ==================== 主面板样式 ==================== */
.tourist-spot-search {
  position: fixed;
  width: 420px;
  max-height: 80vh;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  z-index: 2000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: box-shadow 0.3s ease;
  border: 1px solid #e0e0e0;
  
}

.tourist-spot-search:hover {
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.15);
}

.tourist-spot-search.collapsed {
  max-height: 130px; /* 调整折叠状态高度，容纳标题栏和搜索框 */
  height: auto;
}

/* ==================== 搜索框包装器（可拖拽） ==================== */
/* .search-box-wrapper {
  padding: 12px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  cursor: move;
  user-select: none;
} */

/* .search-box-wrapper:hover {
  background: #f0f1f3;
} */

/* ==================== 搜索框包装器（始终显示） ==================== */
.search-box-wrapper {
  padding: 8px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  cursor: move;
  user-select: none;
  /* left: 150px; */
}

/* ==================== 面板内容 ==================== */
.panel-content {
  padding: 16px;
  background: white;
  overflow-y: auto;
  max-height: calc(80vh - 60px);
}

/* ==================== 搜索框样式 ==================== */
.search-box {
  display: flex;
  gap: 8px;
}

.fold-button {
  background: #ffffff;
  color: #666;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  width: 28px;
  height: 38px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.fold-button:hover {
  background: #f0f0f0;
  border-color: #999;
}

.search-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.2s ease;
  background: #ffffff;
}

.search-input:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}

.search-button {
  padding: 10px 16px;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.search-button:hover {
  background: #357abd;
}

.search-button:active {
  background: #2c5aa0;
}

.extent-search-button {
  padding: 10px 12px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.extent-search-button:hover {
  background: #5a6268;
}

.extent-search-button.active {
  background: #dc3545;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

/* ==================== 搜索结果样式 ==================== */
.search-results {
  margin-top: 16px;
}

.results-header {
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  flex: 1;
}

.header-left h3 {
  margin: 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.header-right {
  display: flex;
  gap: 8px;
}

.add-spot-button {
  padding: 6px 12px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.add-spot-button:hover {
  background: #218838;
}

.add-spot-button:active {
  background: #1e7e34;
}

/* ==================== 操作区域样式 ==================== */
.action-section {
  margin: 16px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e8eaed;
  text-align: center;
}

.action-tip {
  display: block;
  margin-top: 8px;
  font-size: 12px;
  color: #6c757d;
  font-style: italic;
}

/* ==================== 分页控制 ==================== */
.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.pagination-button {
  padding: 6px 12px;
  background: #ffffff;
  color: #4a90e2;
  border: 1px solid #4a90e2;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.pagination-button:disabled {
  background: #f8f9fa;
  color: #999;
  border-color: #d0d0d0;
  cursor: not-allowed;
}

.pagination-button:hover:not(:disabled) {
  background: #4a90e2;
  color: white;
}

.page-info {
  font-size: 13px;
  color: #555;
  font-weight: 500;
}

/* ==================== 结果列表 ==================== */
.results-list {
  max-height: 450px;
  overflow-y: auto;
}

.result-item {
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #ffffff;
}

.result-item:hover {
  background: #f8f9fa;
  border-color: #4a90e2;
  box-shadow: 0 2px 8px rgba(74, 144, 226, 0.1);
}

.result-item.highlighted {
  background: #e8f5e9;
  border-color: #28a745;
}

/* ==================== 景区信息样式 ==================== */
.spot-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.spot-name {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 8px;
}

.basic-info-badge {
  display: inline-block;
  padding: 3px 8px;
  background: #ffc107;
  color: #212529;
  font-size: 11px;
  border-radius: 3px;
  font-weight: 500;
}

/* ==================== 操作按钮组样式 ==================== */
.action-buttons {
  display: flex;
  gap: 4px;
  margin-left: auto;
}

/* ==================== 修改按钮样式 ==================== */
.edit-button {
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.2s ease;
}

.edit-button:hover {
  background: #357abd;
  transform: scale(1.1);
}

.edit-button:active {
  background: #2c5aa0;
  transform: scale(0.95);
}

/* ==================== 删除按钮样式 ==================== */
.delete-button {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.2s ease;
}

.delete-button:hover {
  background: #c82333;
  transform: scale(1.1);
}

.delete-button:active {
  background: #bd2130;
  transform: scale(0.95);
}

.spot-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.spot-details p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
}

.label {
  font-weight: 600;
  color: #555;
  margin-right: 6px;
}

.spot-level { color: #ff5722; font-weight: 600; }
.spot-address { color: #666; }
.spot-rating { color: #ff9800; }
.spot-ticket { color: #e91e63; }
.spot-open-time { color: #2196f3; }
.spot-duration { color: #9c27b0; }
.spot-season { color: #4caf50; }
.spot-tips { color: #795548; font-style: italic; }
.spot-description { color: #333; line-height: 1.6; }

/* ==================== 图片样式 ==================== */
.spot-image-container {
  width: 100%;
  height: 160px;
  margin-bottom: 12px;
  border-radius: 4px;
  overflow: hidden;
  background: #f8f9fa;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e0e0e0;
}

.image-loading,
.image-error,
.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #6c757d;
  font-size: 13px;
  gap: 8px;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #e0e0e0;
  border-top: 2px solid #4a90e2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon,
.placeholder-icon {
  font-size: 32px;
}

.spot-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s ease;
}

.spot-image:hover {
  transform: scale(1.02);
}

/* ==================== 其他状态样式 ==================== */
.no-results {
  text-align: center;
  padding: 30px 20px;
  color: #666;
  font-size: 14px;
}

.loading {
  text-align: center;
  padding: 24px 20px;
  color: #4a90e2;
  font-weight: 500;
}

/* ==================== 滚动条样式 ==================== */
.results-list::-webkit-scrollbar,
.panel-content::-webkit-scrollbar {
  width: 6px;
}

.results-list::-webkit-scrollbar-track,
.panel-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.results-list::-webkit-scrollbar-thumb,
.panel-content::-webkit-scrollbar-thumb {
  background: #4a90e2;
  border-radius: 3px;
}

.results-list::-webkit-scrollbar-thumb:hover,
.panel-content::-webkit-scrollbar-thumb:hover {
  background: #357abd;
}
</style>
