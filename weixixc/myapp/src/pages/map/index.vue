<template>
  <view class="map-container">
    <!-- 搜索框 -->
    <view class="search-bar">
      <input v-model="searchKeyword" class="search-input" placeholder="搜索地点" @confirm="handleSearch" />
      <view class="search-btn" @tap="handleSearch">搜索</view>
    </view>

    <!-- 搜索结果 -->
    <view v-if="searchResults.length > 0" class="search-results">
      <view v-for="(item, index) in searchResults" :key="index" class="result-item" @tap="selectSearchResult(item)">
        <view class="result-title">{{ item.title }}</view>
        <view class="result-address">{{ item.address }}</view>
      </view>
    </view>

    <!-- 地图 -->
    <map id="mainMap" :longitude="center.lng" :latitude="center.lat" :scale="zoom" :markers="markers"
      :polyline="polyline" :show-location="true" @regionchange="onRegionChange" @markertap="onMarkerTap" @callouttap="onCalloutTap">

      <!-- 控件 -->
      <cover-view class="map-controls">
        <cover-view class="control-group">
          <cover-view class="control-button" @tap="handleZoomIn">
            <cover-view class="button-text">+</cover-view>
          </cover-view>
          <cover-view class="control-button" @tap="handleZoomOut">
            <cover-view class="button-text">-</cover-view>
          </cover-view>
        </cover-view>

        <cover-view class="control-group">
          <cover-view class="control-button" @tap="handleLocate">
            <cover-view class="button-text">定位</cover-view>
          </cover-view>
          <cover-view class="control-button tracking-button" :class="{ 'tracking-active': isTrackingLocation }"
            @tap="toggleLocationTracking">
            <cover-view class="button-text">
              {{ isTrackingLocation ? '停止' : '跟踪' }}
            </cover-view>
          </cover-view>
        </cover-view>

        <cover-view class="control-group">
          <cover-view class="control-button" @tap="loadSpots">
            <cover-view class="button-text">刷新</cover-view>
          </cover-view>
        </cover-view>

        <cover-view class="control-group">
          <cover-view class="control-button admin-button" @tap="goToAdmin">
            <cover-view class="button-text">管理</cover-view>
          </cover-view>
        </cover-view>

        <cover-view class="control-group">
          <cover-view class="control-button ai-button" :class="{ 'ai-active': !isAIPanelCollapsed }" @tap="toggleAIPanel">
            <cover-view class="button-text">🤖 AI</cover-view>
          </cover-view>
        </cover-view>

        <cover-view v-if="polyline.length > 0" class="control-group">
          <cover-view class="control-button clear-route-btn" @tap="clearRoute">
            <cover-view class="button-text">清除路线</cover-view>
          </cover-view>
        </cover-view>
      </cover-view>

      <!-- 地图信息 -->
      <cover-view class="map-info">
        <cover-view class="info-item">景点: {{ markers.length }}</cover-view>
        <cover-view v-if="polyline.length > 0" class="info-item route-active">
          路线已规划
        </cover-view>
      </cover-view>
    </map>

    <!-- 景点详情弹窗 -->
    <view v-if="selectedSpot" class="spot-popup" @tap="closePopup">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="spot-name">{{ selectedSpot.name }}</text>
          <text class="close-btn" @tap="closePopup">X</text>
        </view>

        <view class="popup-body">
          <!-- 图片 -->
          <view v-if="spotDetailLoading" class="image-loading">
            <text>加载详细信息中...</text>
          </view>
          <image v-else-if="selectedSpotDetail && selectedSpotDetail.imageUrl" :src="selectedSpotDetail.imageUrl"
            class="spot-image" mode="aspectFill" @error="handleImageError" />

          <!-- 基本信息(来自GeoJSON，立即显示) -->
          <view class="detail-item" v-if="selectedSpot.level">
            <text class="label">等级:</text>
            <text class="value badge" :style="{ backgroundColor: getLevelColor(selectedSpot.level) }">
              {{ selectedSpot.level }}
            </text>
          </view>

          <view class="detail-item" v-if="selectedSpot.address">
            <text class="label">地址:</text>
            <text class="value">{{ selectedSpot.address }}</text>
          </view>

          <!-- 详细信息(从API获取，延迟显示) -->
          <template v-if="selectedSpotDetail">
            <view class="detail-item" v-if="selectedSpotDetail.rating">
              <text class="label">评分:</text>
              <text class="value">{{ selectedSpotDetail.rating }} 分</text>
            </view>

            <view class="detail-item"
              v-if="selectedSpotDetail.ticketPrice !== undefined && selectedSpotDetail.ticketPrice !== null">
              <text class="label">票价:</text>
              <text class="value">
                {{ selectedSpotDetail.ticketPrice === 0 || selectedSpotDetail.ticketPrice === '0' ? '免费' :
                  `¥${selectedSpotDetail.ticketPrice}` }}
              </text>
            </view>

            <view class="detail-item" v-if="selectedSpotDetail.openTime">
              <text class="label">开放时间:</text>
              <text class="value">{{ selectedSpotDetail.openTime }}</text>
            </view>

            <view class="detail-item" v-if="selectedSpotDetail.recommendedDuration">
              <text class="label">游玩时间:</text>
              <text class="value">{{ selectedSpotDetail.recommendedDuration }}</text>
            </view>

            <view class="detail-item" v-if="selectedSpotDetail.recommendedSeason">
              <text class="label">建议季节:</text>
              <text class="value">{{ selectedSpotDetail.recommendedSeason }}</text>
            </view>

            <view class="detail-item" v-if="selectedSpotDetail.description">
              <text class="label">介绍:</text>
              <text class="value description">{{ selectedSpotDetail.description }}</text>
            </view>

            <view class="detail-item" v-if="selectedSpotDetail.tips">
              <text class="label">小贴士:</text>
              <text class="value tips">{{ selectedSpotDetail.tips }}</text>
            </view>
          </template>

          <!-- 如果没有详细信息，显示提示 -->
          <view v-else-if="!spotDetailLoading && spotDetailFailed" class="no-detail-info">
            <text>暂无更多详细信息</text>
          </view>
        </view>

        <view class="popup-footer">
          <button class="action-btn nav-btn" @tap="planRoute('walking')">步行</button>
          <button class="action-btn nav-btn" @tap="planRoute('driving')">驾车</button>
          <button class="action-btn" @tap="navigateToSpot">导航</button>
        </view>
      </view>
    </view>

    <!-- 加载提示 -->
    <view v-if="loading" class="loading">
      <text>{{ loadingText }}</text>
    </view>

    <!-- 聚合点列表弹窗 -->
    <view v-if="showClusterList" class="cluster-popup" @tap="closeClusterList">
      <view class="cluster-popup-content" @tap.stop>
        <view class="cluster-popup-header">
          <text class="cluster-title">
            该区域包含 {{ currentClusterSpots.length }} 个景点
          </text>
          <text class="close-btn" @tap="closeClusterList">X</text>
        </view>

        <scroll-view class="cluster-spot-list" scroll-y>
          <view v-for="(spot, index) in currentClusterSpots" :key="index" class="cluster-spot-item"
            @tap="viewClusterSpotDetail(spot)">
            <view v-if="spot.level" class="spot-level-badge" :style="{ backgroundColor: getLevelColor(spot.level) }">
              {{ spot.level }}
            </view>
            <view class="spot-info">
              <text class="spot-name">{{ spot.name }}</text>
              <text v-if="spot.address" class="spot-address">{{ spot.address }}</text>
            </view>
            <text class="view-detail-icon">></text>
          </view>
        </scroll-view>

        <view class="cluster-popup-footer">
          <button class="cluster-action-btn zoom-btn" @tap="zoomToCluster">
            放大查看
          </button>
        </view>
      </view>
    </view>

    <!-- AI 查询面板 -->
    <AIQueryPanel
      ref="aiQueryPanel"
      :auto-collapse="!!selectedSpot"
      @query-result="handleAIQueryResult"
      @collapse-change="handleAIPanelCollapseChange"
    />
  </view>
</template>

<script>
import { getSpotsByBounds, convertSpotsToMarkers, getSpotByName } from '@/services/touristSpotService'
import { searchPlace, drivingRoute, walkingRoute } from '@/services/tencentMapService'
import locationService from '@/services/locationService'
import AIQueryPanel from '@/components/AIQueryPanel.vue'

export default {
  components: {
    AIQueryPanel
  },

  data() {
    return {
      center: { lng: 114.353, lat: 30.531 },
      zoom: 12,
      loading: false,
      loadingText: '加载中...',
      mapContext: null,
      markers: [],
      polyline: [],
      selectedSpot: null,
      searchKeyword: '',
      searchResults: [],
      userLocation: null,
      // 位置跟踪相关
      isTrackingLocation: false,
      userLocationMarker: null,
      isFirstLocationUpdate: true, // 标记是否是首次位置更新
      // 动态加载相关
      loadedSpotIds: new Set(), // 已加载的景点ID集合，用于去重
      lastLoadTime: 0, // 上次加载时间戳
      loadThrottle: 1000, // 加载节流时间（毫秒）
      currentBounds: null, // 当前地图边界
      loadRangeFactor: 0.6, // 加载范围缩小系数（0.6表示缩小到可视区域的60%）
      // 可调整范围：0.3-1.0
      // 0.3=加载更少景点, 1.0=加载可视区域所有景点
      isMapReady: false, // 地图是否已准备好
      isInitialLoad: true, // 是否是初始加载
      // 景点详情相关
      selectedSpotDetail: null, // 详细信息（从API获取）
      spotDetailLoading: false, // 详情加载状态
      spotDetailFailed: false, // 详情加载失败标志
      // 点聚合相关
      clusterData: {}, // 存储 clusterId -> markers 映射
      markerIdToClusterId: {}, // 存储 markerId -> clusterId 的反向映射
      isClusterEnabled: false, // 当前是否启用聚合
      clusterThreshold: 13, // 聚合阈值（scale < 13 时聚合）
      showClusterList: false, // 聚合点列表弹窗显示状态
      currentClusterSpots: [], // 当前聚合点包含的景点列表
      currentClusterCenter: null, // 当前聚合点中心坐标（用于"放大查看"）
      isAIPanelCollapsed: false // AI面板折叠状态
    }
  },

  onLoad() {
    this.mapContext = uni.createMapContext('mainMap', this)
    this.getUserLocation()

    // 延迟初始化点聚合，确保地图组件已渲染
    setTimeout(() => {
      // 先清空 markers（参考文档要求）
      if (this.mapContext && this.mapContext.addMarkers) {
        this.mapContext.addMarkers({
          markers: [],
          clear: true
        })
      }
      // 初始化点聚合功能
      this.initMarkerCluster()

      // 再延迟加载景点
      setTimeout(() => {
        this.isMapReady = true
        this.loadSpotsInView()
      }, 500)
    }, 500)

    // 添加调试日志
    console.log('🚀 准备启动缩放监听')
    this.initZoomMonitor()
  },

  onUnload() {
    // 页面卸载时停止位置跟踪
    if (this.isTrackingLocation) {
      this.stopLocationTracking()
    }
  },

  methods: {
    // ==================== 点聚合相关方法 ====================

    /**
     * 初始化点聚合功能
     */
    initMarkerCluster() {
      if (!this.mapContext) {
        console.error('地图上下文未初始化,无法初始化点聚合')
        return
      }

      try {
        // 初始化点聚合配置
        this.mapContext.initMarkerCluster({
          enableDefaultStyle: false, // 使用自定义样式
          zoomOnClick: false, // 禁用自动放大（我们自己控制）
          gridSize: 60, // 聚合范围60像素
          complete: (res) => {
            console.log('✅ 点聚合初始化成功:', res)
            // 根据当前缩放级别决定是否启用聚合
            this.isClusterEnabled = this.zoom < this.clusterThreshold
          }
        })

        // 监听聚合点创建事件
        this.mapContext.on('markerClusterCreate', (res) => {
          console.log('📍 聚合点创建事件触发:', res)
          const clusters = res.clusters

          if (!clusters || clusters.length === 0) {
            console.log('⚠️ 没有聚合点需要创建')
            return
          }

          console.log(`📍 准备创建 ${clusters.length} 个聚合点`)

          // 注意：不要清空旧数据，而是累积添加
          // this.clusterData = {} // 删除这行，改为累积添加

          // 为每个聚合点创建自定义标记
          const clusterMarkers = []

          clusters.forEach(cluster => {
            const { center, clusterId, markerIds } = cluster
            console.log(`📍 处理聚合点 ${clusterId}（类型：${typeof clusterId}），包含 ${markerIds.length} 个 markers`)
            console.log(`📍 markerIds:`, markerIds)

            // 获取聚合点包含的所有 markers
            const containedMarkers = markerIds.map(markerId => {
              // 【关键修复】同时尝试字符串、数字、原始类型匹配
              const markerIdStr = String(markerId)
              const markerIdNum = Number(markerId)

              const found = this.markers.find(m =>
                m.id === markerId ||
                m.id === markerIdStr ||
                m.id === markerIdNum
              )

              if (!found) {
                console.warn(`⚠️ 未找到 markerId=${markerId}（类型：${typeof markerId}）对应的 marker`)
                console.warn(`⚠️ this.markers 中的 id 类型示例:`, this.markers.slice(0, 3).map(m => ({ id: m.id, type: typeof m.id })))
              }
              return found
            }).filter(m => m) // 过滤掉undefined

            console.log(`📍 聚合点 ${clusterId} 找到 ${containedMarkers.length} 个有效 markers`)
            console.log(`📍 示例 marker:`, containedMarkers[0])

            // 检查 spotData
            const spotsData = containedMarkers.map(m => {
              if (!m.spotData) {
                console.warn(`⚠️ marker id=${m.id} 没有 spotData 属性，marker:`, m)
              }
              return m.spotData
            }).filter(s => s)

            console.log(`📍 聚合点 ${clusterId} 提取到 ${spotsData.length} 个 spotData`)

            // 保存聚合点到markers的映射（同时保存数字和字符串版本）
            this.clusterData[clusterId] = containedMarkers
            this.clusterData[String(clusterId)] = containedMarkers
            this.clusterData[Number(clusterId)] = containedMarkers
            console.log(`📍 已保存聚合点数据，键: ${clusterId}, ${String(clusterId)}, ${Number(clusterId)}`)

            // 分析聚合点中的最高等级
            const highestLevel = this.getHighestLevel(containedMarkers)

            // 根据等级获取边框颜色
            const colorMap = {
              '5A': '#ff6b6b',  // 红色
              '4A': '#4ecdc4',  // 青色
              '3A': '#45b7d1',  // 蓝色
              '2A': '#96ceb4',  // 绿色
              'default': '#95a5a6'  // 灰色
            }
            const borderColor = colorMap[highestLevel] || colorMap.default

            // 创建聚合点标记
            const clusterMarker = {
              ...center,
              id: clusterId, // 使用 clusterId 作为 marker 的 id，使其能被点击事件识别
              width: 60, // 增大可点击区域
              height: 60,
              clusterId: clusterId, // 标记这是一个聚合点
              isCluster: true, // 添加标识
              // 【关键修复】直接将聚合数据保存到 marker 对象中
              clusterSpots: spotsData,
              clusterMarkers: containedMarkers,
              // 使用 callout 而不是 label，提供更大的点击区域
              callout: {
                content: `${markerIds.length}`,
                color: borderColor,
                fontSize: 16,
                borderRadius: 25,
                bgColor: '#fff',
                padding: 10,
                display: 'ALWAYS',
                textAlign: 'center'
              }
            }

            clusterMarkers.push(clusterMarker)
            console.log(`📍 聚合点 ${clusterId} 创建完成，包含 ${clusterMarker.clusterSpots.length} 个景点`)
            if (clusterMarker.clusterSpots.length === 0) {
              console.error(`❌ 聚合点 ${clusterId} 的 clusterSpots 为空！containedMarkers:`, containedMarkers)
            }
          })

          // 将聚合点标记添加到地图
          if (clusterMarkers.length > 0) {
            // 【关键修复】将聚合点标记也添加到 this.markers 数组
            // 先移除旧的聚合点标记（isCluster=true的）
            this.markers = this.markers.filter(m => !m.isCluster)
            // 添加新的聚合点标记
            this.markers.push(...clusterMarkers)

            this.mapContext.addMarkers({
              markers: clusterMarkers,
              clear: false
            })
            console.log(`✅ 已添加 ${clusterMarkers.length} 个聚合点到地图和 markers 数组`)
            console.log(`✅ 当前 markers 总数: ${this.markers.length}`)
            console.log(`✅ clusterData 现在有 ${Object.keys(this.clusterData).length / 3} 个聚合点`) // 除以3是因为每个ID存了3次
          }
        })

        // 监听聚合点点击事件
        this.mapContext.on('markerClusterClick', (res) => {
          console.log('🎯 聚合点点击事件触发:', res)
          const { cluster } = res
          if (cluster && cluster.clusterId) {
            const clusterId = cluster.clusterId
            console.log('🎯 点击的聚合点 ID:', clusterId)

            // 从 clusterData 中获取聚合点包含的 markers
            const containedMarkers = this.clusterData[clusterId]
            if (containedMarkers) {
              console.log('✅ 找到聚合点数据，包含 markers:', containedMarkers.length)

              // 提取所有包含的景点数据
              this.currentClusterSpots = containedMarkers.map(m => m.spotData).filter(s => s)
              console.log('📍 有效景点数据:', this.currentClusterSpots.length)

              // 计算聚合点的中心坐标（用于"放大查看"）
              if (containedMarkers.length > 0) {
                const firstMarker = containedMarkers[0]
                this.currentClusterCenter = {
                  latitude: firstMarker.latitude,
                  longitude: firstMarker.longitude
                }
              }

              // 显示聚合点列表弹窗
              this.showClusterList = true
            } else {
              console.warn('⚠️ 未找到聚合点数据，clusterId:', clusterId)
            }
          }
        })

        console.log('✅ 点聚合事件监听器已设置')
      } catch (error) {
        console.error('❌ 初始化点聚合失败:', error)
      }
    },

    /**
     * 分析一组markers中的最高等级
     * @param {Array} markers - marker数组
     * @returns {string} 最高等级
     */
    getHighestLevel(markers) {
      if (!markers || markers.length === 0) {
        return 'default'
      }

      // 等级优先级
      const levelPriority = {
        '5A': 5,
        '4A': 4,
        '3A': 3,
        '2A': 2,
        '1A': 1,
        'default': 0
      }

      let highestLevel = 'default'
      let highestPriority = 0

      markers.forEach(marker => {
        const spotData = marker.spotData || {}
        const level = spotData.level || 'default'
        const priority = levelPriority[level] || 0

        if (priority > highestPriority) {
          highestPriority = priority
          highestLevel = level
        }
      })

      return highestLevel
    },

    /**
     * 根据等级和数量返回聚合点样式
     * @param {string} level - 景点等级
     * @param {number} count - 景点数量
     * @returns {object} label样式对象
     */
    getClusterStyle(level, count) {
      // 根据等级获取边框颜色
      const colorMap = {
        '5A': '#ff6b6b',  // 红色
        '4A': '#4ecdc4',  // 青色
        '3A': '#45b7d1',  // 蓝色
        '2A': '#96ceb4',  // 绿色
        'default': '#95a5a6'  // 灰色
      }

      const borderColor = colorMap[level] || colorMap.default

      return {
        content: count.toString(),
        fontSize: 16,
        width: 40,
        height: 40,
        borderWidth: 2,
        borderColor: borderColor,
        bgColor: '#fff',
        borderRadius: 20,
        textAlign: 'center',
        anchorX: 0,
        anchorY: -20
      }
    },

    /**
     * 根据当前缩放级别切换聚合状态
     */
    toggleClusterState() {
      const shouldEnableCluster = this.zoom < this.clusterThreshold

      if (this.isClusterEnabled === shouldEnableCluster) {
        // 状态未改变，不需要操作
        return
      }

      console.log(`🔄 切换聚合状态: zoom=${this.zoom}, threshold=${this.clusterThreshold}, enable=${shouldEnableCluster}`)
      console.log(`🔄 切换前 clusterData 键数量: ${Object.keys(this.clusterData).length}`)

      this.isClusterEnabled = shouldEnableCluster

      // 关键：状态切换时，需要重新添加所有 markers
      if (this.markers.length > 0 && this.mapContext && this.mapContext.addMarkers) {
        console.log(`🔄 重新添加所有 ${this.markers.length} 个 markers`)

        // 如果要禁用聚合，先清空 clusterData
        if (!shouldEnableCluster) {
          console.log('🔄 禁用聚合，清空 clusterData')
          this.clusterData = {}
        } else {
          console.log('🔄 启用聚合，保留 clusterData，等待新的聚合点创建')
        }

        this.mapContext.addMarkers({
          markers: this.markers,
          clear: true,
          success: () => {
            if (shouldEnableCluster) {
              console.log('📍 聚合已启用，等待 markerClusterCreate 事件填充 clusterData')
            } else {
              console.log('📍 聚合已禁用，显示所有独立景点')
            }
          }
        })
      }
    },

    /**
     * 关闭聚合点列表弹窗
     */
    closeClusterList() {
      this.showClusterList = false
      this.currentClusterSpots = []
      this.currentClusterCenter = null
    },

    /**
     * 查看聚合点中某个景点的详情
     * @param {Object} spot - 景点数据
     */
    async viewClusterSpotDetail(spot) {
      // 关闭聚合点列表
      this.closeClusterList()

      // 显示该景点的详情弹窗
      this.selectedSpot = spot

      // 异步加载详细信息
      this.spotDetailLoading = true
      this.spotDetailFailed = false
      this.selectedSpotDetail = null

      try {
        console.log(`加载景点详情: ${spot.name}`)
        const result = await getSpotByName(spot.name)

        if (result.success && result.data) {
          this.selectedSpotDetail = result.data
          console.log('[SUCCESS] 景点详情加载成功:', result.data)
        } else {
          console.warn('[WARN] 景点详情加载失败，无数据')
          this.spotDetailFailed = true
        }
      } catch (error) {
        console.error('[ERROR] 获取景点详情失败:', error)
        this.spotDetailFailed = true
      } finally {
        this.spotDetailLoading = false
      }
    },

    /**
     * 放大查看聚合点区域
     */
    zoomToCluster() {
      if (!this.currentClusterCenter || !this.currentClusterSpots.length) {
        return
      }

      // 计算所有景点的边界
      let minLat = Infinity, maxLat = -Infinity
      let minLng = Infinity, maxLng = -Infinity

      this.currentClusterSpots.forEach(spot => {
        const lat = spot.lat_wgs84 || spot.latitude
        const lng = spot.lng_wgs84 || spot.longitude

        if (lat && lng) {
          minLat = Math.min(minLat, lat)
          maxLat = Math.max(maxLat, lat)
          minLng = Math.min(minLng, lng)
          maxLng = Math.max(maxLng, lng)
        }
      })

      // 计算中心点
      const centerLat = (minLat + maxLat) / 2
      const centerLng = (minLng + maxLng) / 2

      // 更新地图中心和缩放级别
      this.center = {
        lng: centerLng,
        lat: centerLat
      }

      // 自动放大到合适的级别（通常比当前大2-3级）
      this.zoom = Math.max(this.zoom + 3, 8)

      // 关闭聚合点列表
      this.closeClusterList()

      uni.showToast({
        title: '已放大到该区域',
        icon: 'success',
        duration: 1500
      })
    },

    // ==================== 原有方法 ====================

    // 根据当前可视区域加载景点（带节流和去重）
    async loadSpotsInView() {
      // 节流：避免频繁请求
      const now = Date.now()
      if (now - this.lastLoadTime < this.loadThrottle) {
        return
      }
      this.lastLoadTime = now

      if (!this.mapContext) {
        console.warn('地图上下文未初始化')
        return
      }

      // this.loading = true
      // this.loadingText = '加载附近景点...'

      try {
        // 获取地图区域信息
        const region = await this.getMapRegion()
        if (!region) {
          console.error('无法获取地图区域')
          return
        }

        this.currentBounds = region

        // 从后端获取范围内的景点
        const result = await getSpotsByBounds(region, this.zoom)

        if (result.success && result.data.length > 0) {
          // 去重：只添加新景点
          const newSpots = result.data.filter(spot => !this.loadedSpotIds.has(spot.id))

          if (newSpots.length > 0) {
            // 记录已加载的景点ID
            newSpots.forEach(spot => this.loadedSpotIds.add(spot.id))

            // 转换为markers
            const newMarkers = convertSpotsToMarkers(newSpots)
            console.log(`📍 准备添加 ${newMarkers.length} 个 markers，joinCluster=${newMarkers[0]?.joinCluster}`)

            // 更新本地 markers 数组
            this.markers = [...this.markers, ...newMarkers]

            // 关键：如果启用了聚合，需要重新添加所有 markers 才能触发聚合
            if (this.isClusterEnabled) {
              console.log(`🔄 聚合已启用，重新添加所有 ${this.markers.length} 个 markers`)
              if (this.mapContext && this.mapContext.addMarkers) {
                this.mapContext.addMarkers({
                  markers: this.markers, // 添加所有 markers，不是只添加新的
                  clear: true, // 清空后重新添加
                  success: () => {
                    console.log(`✅ 成功重新添加所有 markers，触发聚合`)
                  },
                  fail: (err) => {
                    console.error('❌ 添加 markers 失败:', err)
                  }
                })
              }
            } else {
              // 如果未启用聚合，可以增量添加
              console.log(`📍 聚合未启用，增量添加 ${newMarkers.length} 个 markers`)
              if (this.mapContext && this.mapContext.addMarkers) {
                this.mapContext.addMarkers({
                  markers: newMarkers,
                  clear: false,
                  success: () => {
                    console.log(`✅ 成功添加 ${newMarkers.length} 个 markers`)
                  },
                  fail: (err) => {
                    console.error('❌ 添加 markers 失败:', err)
                  }
                })
              }
            }

            console.log(`新增 ${newSpots.length} 个景点，总计 ${this.markers.length} 个`)
          } else {
            console.log('当前区域景点已全部加载')
          }
        }
      } catch (error) {
        console.error('加载可视区域景点失败:', error)
      } finally {
        this.loading = false
      }
    },

    // 获取地图当前区域边界（缩小范围版本）
    getMapRegion() {
      return new Promise((resolve) => {
        this.mapContext.getRegion({
          success: (res) => {
            // res包含: southwest {latitude, longitude}, northeast {latitude, longitude}
            const originalBounds = {
              southwest: {
                lng: res.southwest.longitude,
                lat: res.southwest.latitude
              },
              northeast: {
                lng: res.northeast.longitude,
                lat: res.northeast.latitude
              }
            }

            // 计算原始范围的中心点和尺寸
            const centerLng = (originalBounds.southwest.lng + originalBounds.northeast.lng) / 2
            const centerLat = (originalBounds.southwest.lat + originalBounds.northeast.lat) / 2
            const widthLng = originalBounds.northeast.lng - originalBounds.southwest.lng
            const heightLat = originalBounds.northeast.lat - originalBounds.southwest.lat

            // 缩小到原范围的指定比例（由loadRangeFactor控制）
            const shrinkFactor = this.loadRangeFactor
            const newWidthLng = widthLng * shrinkFactor
            const newHeightLat = heightLat * shrinkFactor

            // 返回缩小后的范围
            resolve({
              southwest: {
                lng: centerLng - newWidthLng / 2,
                lat: centerLat - newHeightLat / 2
              },
              northeast: {
                lng: centerLng + newWidthLng / 2,
                lat: centerLat + newHeightLat / 2
              }
            })
          },
          fail: (err) => {
            console.error('获取地图区域失败:', err)
            // 降级：使用中心点估算更小的范围
            const delta = 0.05 // 约5.5公里（原来是0.1约11公里）
            resolve({
              southwest: {
                lng: this.center.lng - delta,
                lat: this.center.lat - delta
              },
              northeast: {
                lng: this.center.lng + delta,
                lat: this.center.lat + delta
              }
            })
          }
        })
      })
    },

    // 清除所有景点（用于刷新）
    clearAllSpots() {
      // 使用 MapContext API 清空地图上的所有 markers
      if (this.mapContext && this.mapContext.addMarkers) {
        this.mapContext.addMarkers({
          markers: [],
          clear: true
        })
      }
      // 清空本地数据
      this.markers = []
      this.loadedSpotIds.clear()
      this.clusterData = {}
      console.log('已清除所有景点')
    },

    // 旧的加载方法（保留用于手动刷新）
    async loadSpots() {
      this.clearAllSpots()
      await this.loadSpotsInView()
    },

    // 获取用户位置
    getUserLocation() {
      uni.getLocation({
        type: 'gcj02',
        success: (res) => {
          this.userLocation = { lng: res.longitude, lat: res.latitude }
        }
      })
    },

    // 搜索
    async handleSearch() {
      if (!this.searchKeyword.trim()) {
        return uni.showToast({ title: '请输入搜索关键词', icon: 'none' })
      }

      this.loading = true
      this.loadingText = '搜索中...'
      try {
        const location = `${this.center.lat},${this.center.lng}`
        const results = await searchPlace(this.searchKeyword, { location, radius: 5000 })
        this.searchResults = results || []

        // 打印搜索结果的完整数据结构，查看都有哪些字段
        if (this.searchResults.length > 0) {
          console.log('[DEBUG] 搜索结果示例:', this.searchResults[0])
          console.log('[DEBUG] 可用字段:', Object.keys(this.searchResults[0]))
        }

        if (this.searchResults.length === 0) {
          uni.showToast({ title: '未找到结果', icon: 'none' })
        }
      } catch (error) {
        console.error('搜索失败:', error)
        uni.showToast({ title: '搜索失败', icon: 'none' })
      } finally {
        this.loading = false
      }
    },

    // 选择搜索结果
    selectSearchResult(item) {
      const { location } = item
      this.center = { lng: location.lng, lat: location.lat }
      this.zoom = 15

      // 添加标记
      this.markers.push({
        id: Date.now(),
        latitude: location.lat,
        longitude: location.lng,
        iconPath: '/static/icons/spot-default.png',
        width: 32,
        height: 32,
        callout: {
          content: item.title,
          display: 'ALWAYS'
        },
        spotData: item
      })

      this.searchResults = []
      this.searchKeyword = ''
    },

    // 路线规划
    async planRoute(mode) {
      if (!this.selectedSpot || !this.userLocation) {
        return uni.showToast({ title: '请先定位', icon: 'none' })
      }

      this.loading = true
      this.loadingText = '规划路线...'

      try {
        const from = `${this.userLocation.lat},${this.userLocation.lng}`
        const to = `${this.selectedSpot.lat_wgs84},${this.selectedSpot.lng_wgs84}`

        const route = mode === 'walking'
          ? await walkingRoute(from, to)
          : await drivingRoute(from, to)

        this.polyline = [{
          points: route.polyline,
          color: '#4a90e2',
          width: 6,
          borderColor: '#2a70c2',
          borderWidth: 2
        }]

        const distance = (route.distance / 1000).toFixed(1)
        const duration = Math.ceil(route.duration / 60)
        uni.showToast({
          title: `${distance}km，约${duration}分钟`,
          icon: 'none'
        })
      } catch (error) {
        console.error('路线规划失败:', error)
        uni.showToast({ title: '路线规划失败', icon: 'none' })
      } finally {
        this.loading = false
      }
    },

    // 导航
    navigateToSpot() {
      if (!this.selectedSpot) return
      uni.openLocation({
        latitude: this.selectedSpot.lat_wgs84,
        longitude: this.selectedSpot.lng_wgs84,
        name: this.selectedSpot.name,
        address: this.selectedSpot.address || '',
        scale: 15
      })
    },

    // 标记点击（两层数据加载 + 聚合点处理）
    async onMarkerTap(e) {
      const markerId = e.detail.markerId || e.markerId
      console.log('📍 点击marker，原始事件:', e)
      console.log('📍 点击marker，markerId:', markerId, '类型:', typeof markerId)
      this.handleMarkerClick(markerId)
    },

    // Callout 点击事件（与 marker 点击使用相同逻辑）
    async onCalloutTap(e) {
      const markerId = e.detail.markerId || e.markerId
      console.log('📍 点击callout，markerId:', markerId, '类型:', typeof markerId)
      this.handleMarkerClick(markerId)
    },

    // 统一处理 marker/callout 点击的逻辑
    async handleMarkerClick(markerId) {
      console.log('📍 处理点击，markerId:', markerId, '类型:', typeof markerId)
      console.log('📍 当前 clusterData 键:', Object.keys(this.clusterData))
      console.log('📍 当前 markers 数量:', this.markers.length)
      console.log('📍 是否启用聚合:', this.isClusterEnabled)

      // 尝试将 markerId 转换为字符串和数字来匹配
      const markerIdStr = String(markerId)
      const markerIdNum = Number(markerId)

      // 【优先方案】首先尝试从 markers 数组中直接找到聚合点标记
      const marker = this.markers.find(m => m.id === markerId || m.id === markerIdStr || m.id === markerIdNum)

      if (marker && marker.isCluster && marker.clusterSpots) {
        // 这是一个聚合点，直接从 marker 对象中获取数据
        console.log('✅ 点击了聚合点（从marker获取），包含景点:', marker.clusterSpots.length)

        this.currentClusterSpots = marker.clusterSpots

        // 计算聚合点的中心坐标
        if (marker.clusterMarkers && marker.clusterMarkers.length > 0) {
          const firstMarker = marker.clusterMarkers[0]
          this.currentClusterCenter = {
            latitude: firstMarker.latitude,
            longitude: firstMarker.longitude
          }
        }

        // 显示聚合点列表弹窗
        this.showClusterList = true
        return
      }

      // 【备用方案】从 clusterData 中查找（兼容旧逻辑）
      let clusterKey = null
      if (this.clusterData[markerId]) {
        clusterKey = markerId
      } else if (this.clusterData[markerIdStr]) {
        clusterKey = markerIdStr
      } else if (this.clusterData[markerIdNum]) {
        clusterKey = markerIdNum
      }

      if (clusterKey) {
        // 这是一个聚合点（从 clusterData 获取）
        console.log('✅ 点击了聚合点（从clusterData获取），匹配键:', clusterKey)
        const containedMarkers = this.clusterData[clusterKey]
        console.log('📍 聚合点包含景点数量:', containedMarkers.length)

        // 提取所有包含的景点数据
        this.currentClusterSpots = containedMarkers.map(m => m.spotData).filter(s => s)
        console.log('📍 有效景点数据:', this.currentClusterSpots.length)

        // 计算聚合点的中心坐标（用于"放大查看"）
        if (containedMarkers.length > 0) {
          const firstMarker = containedMarkers[0]
          this.currentClusterCenter = {
            latitude: firstMarker.latitude,
            longitude: firstMarker.longitude
          }
        }

        // 显示聚合点列表弹窗
        this.showClusterList = true
        return
      }

      console.log('📍 不是聚合点，尝试作为普通 marker 处理')
      // 否则按照原有逻辑处理普通marker
      if (marker && marker.spotData) {
        console.log('✅ 找到普通景点 marker:', marker.spotData.name)
        // 第一层：立即显示基本信息（来自GeoJSON）
        this.selectedSpot = marker.spotData

        // 第二层：异步加载详细信息（从API获取）
        this.spotDetailLoading = true
        this.spotDetailFailed = false
        this.selectedSpotDetail = null

        try {
          console.log(`加载景点详情: ${marker.spotData.name}`)
          const result = await getSpotByName(marker.spotData.name)

          if (result.success && result.data) {
            this.selectedSpotDetail = result.data
            console.log('[SUCCESS] 景点详情加载成功:', result.data)
          } else {
            console.warn('[WARN] 景点详情加载失败，无数据')
            this.spotDetailFailed = true
          }
        } catch (error) {
          console.error('[ERROR] 获取景点详情失败:', error)
          this.spotDetailFailed = true
        } finally {
          this.spotDetailLoading = false
        }
      } else {
        console.warn('⚠️ 未找到对应的 marker，markerId:', markerId)
        console.warn('⚠️ clusterData 键类型:', Object.keys(this.clusterData).map(k => typeof k))
        console.warn('⚠️ markers id 列表（前10个）:', this.markers.slice(0, 10).map(m => ({ id: m.id, type: typeof m.id, isCluster: m.isCluster })))
      }
    },

    // 关闭弹窗
    closePopup() {
      this.selectedSpot = null
      this.selectedSpotDetail = null
      this.spotDetailLoading = false
      this.spotDetailFailed = false
      // 不再清除路线，让路线持久显示
    },

    // 清除路线
    clearRoute() {
      this.polyline = []
      uni.showToast({
        title: '路线已清除',
        icon: 'success',
        duration: 1500
      })
    },

    // 图片加载错误处理
    handleImageError() {
      console.warn('景点图片加载失败')
      uni.showToast({
        title: '图片加载失败',
        icon: 'none',
        duration: 2000
      })
    },
    initZoomMonitor() {
      console.log('📍 启动缩放级别监听')
      let lastScale = this.zoom

      setInterval(() => {
        // 只在地图准备好后才监听
        if (!this.isMapReady || !this.mapContext) {
          return
        }

        this.mapContext.getScale({
          success: (res) => {
            // 只有缩放级别真正变化时才处理（差异大于0.1）
            if (Math.abs(res.scale - lastScale) > 0.1) {
              console.log(`📍 缩放级别变化: ${lastScale} -> ${res.scale}`)
              lastScale = res.scale
              this.handleZoomChange(res.scale)
            }
          }
        })
      }, 500)
    },
    handleZoomChange(newScale) {
      // 更新本地缩放级别
      this.zoom = newScale

      // 切换聚合状态
      this.toggleClusterState()

      // 重新加载景点
      this.loadSpotsInView()
    },
    // 地图控制
    handleZoomIn() {
      if (this.zoom < 10) {
        this.zoom++
        // 缩放由用户主动触发，标记为初始加载完成
        this.isInitialLoad = false
        // 根据缩放级别切换聚合状态
        this.toggleClusterState()
        // 重新加载景点（因为不同zoom级别加载不同等级的景点）
        this.loadSpotsInView()
      }
    },

    handleZoomOut() {
      if (this.zoom > 8) {
        this.zoom--
        // 缩放由用户主动触发，标记为初始加载完成
        this.isInitialLoad = false
        // 根据缩放级别切换聚合状态
        this.toggleClusterState()
        // 重新加载景点（因为不同zoom级别加载不同等级的景点）
        this.loadSpotsInView()
      }
    },

    handleLocate() {
      this.loading = true
      this.loadingText = '定位中...'
      uni.getLocation({
        type: 'gcj02',
        success: (res) => {
          this.center = { lng: res.longitude, lat: res.latitude }
          this.userLocation = { lng: res.longitude, lat: res.latitude }
          uni.showToast({ title: '定位成功', icon: 'success' })
        },
        fail: () => {
          uni.showToast({ title: '定位失败', icon: 'none' })
        },
        complete: () => {
          this.loading = false
        }
      })
    },

    /**
     * 地图区域变化事件（只处理平移/移动）
     * 注意：此事件在缩放时不会触发，缩放通过 @updated 事件处理
     */
    onRegionChange(e) {
      // 地图初始化期间忽略所有regionchange事件
      if (!this.isMapReady) {
        console.log('地图初始化中，忽略regionchange事件')
        return
      }

      // 只处理移动/缩放结束事件
      if (e.type !== 'end') {
        return
      }

      // e.causedBy: 'gesture' 手势, 'scale' 缩放, 'update' 方法调用
      console.log('📍 地图平移，触发加载:', e.causedBy, e.type)

      // 更新中心点
      if (this.mapContext) {
        this.mapContext.getCenterLocation({
          success: (res) => {
            this.center = { lng: res.longitude, lat: res.latitude }
          }
        })

        // 地图平移后，加载新区域的景点（不涉及缩放变化）
        this.loadSpotsInView()
      }
    },

    /**
     * 地图更新事件（包括缩放）
     * 注意：regionchange 在缩放时不触发，只能通过 updated 事件监听缩放
     */
    onMapUpdated(e) {
      if (!this.isMapReady) {
        console.log('地图初始化中，忽略 updated 事件')
        return
      }

      console.log('📍 地图更新事件:', e)

      if (this.mapContext) {
        // 关键：通过 getScale() 获取真实缩放级别
        this.mapContext.getScale({
          success: (res) => {
            const newZoom = res.scale

            // 只在缩放级别真正改变时才处理
            if (newZoom !== this.zoom) {
              console.log(`📍 缩放级别变化: ${this.zoom} -> ${newZoom}`)
              this.zoom = newZoom

              // 更新中心点
              this.mapContext.getCenterLocation({
                success: (res) => {
                  this.center = { lng: res.longitude, lat: res.latitude }
                }
              })

              // 根据新的缩放级别切换聚合状态
              this.toggleClusterState()

              // 重新加载景点（因为不同zoom级别加载不同等级的景点）
              this.loadSpotsInView()
            }
          },
          fail: (err) => {
            console.error('❌ 获取缩放级别失败:', err)
          }
        })
      }
    },

    getLevelColor(level) {
      const colors = {
        '5A': '#ff6b6b',
        '4A': '#4ecdc4',
        '3A': '#45b7d1',
        '2A': '#96ceb4'
      }
      return colors[level] || '#95a5a6'
    },

    // 跳转到景点管理页面
    goToAdmin() {
      uni.navigateTo({
        url: '/pages/admin/index'
      })
    },

    // ==================== 位置跟踪相关方法 ====================

    /**
     * 开始位置跟踪
     */
    async startLocationTracking() {
      if (this.isTrackingLocation) {
        uni.showToast({ title: '位置跟踪已开启', icon: 'none' })
        return
      }

      try {
        this.loading = true
        this.loadingText = '启动位置跟踪...'

        // 重置首次位置更新标记
        this.isFirstLocationUpdate = true

        // 启动位置监听
        await locationService.startWatching(this.onLocationUpdate)

        this.isTrackingLocation = true
        uni.showToast({
          title: '位置跟踪已开启',
          icon: 'success'
        })

        console.log('位置跟踪已启动')
      } catch (error) {
        console.error('启动位置跟踪失败:', error)
        uni.showToast({
          title: error.message || '启动位置跟踪失败',
          icon: 'none'
        })
      } finally {
        this.loading = false
      }
    },

    /**
     * 停止位置跟踪
     */
    stopLocationTracking() {
      if (!this.isTrackingLocation) {
        return
      }

      locationService.stopWatching()
      this.isTrackingLocation = false
      this.isFirstLocationUpdate = true // 重置标记

      // 移除用户位置标记
      if (this.userLocationMarker) {
        this.markers = this.markers.filter(m => m.id !== this.userLocationMarker.id)
        this.userLocationMarker = null

        // 使用 MapContext API 更新地图（移除用户位置标记）
        if (this.mapContext && this.mapContext.addMarkers) {
          this.mapContext.addMarkers({
            markers: this.markers,
            clear: true,
            success: () => {
              console.log('✅ 用户位置标记已从地图移除')
            }
          })
        }
      }

      uni.showToast({
        title: '位置跟踪已关闭',
        icon: 'success'
      })

      console.log('位置跟踪已停止')
    },

    /**
     * 切换位置跟踪状态
     */
    async toggleLocationTracking() {
      if (this.isTrackingLocation) {
        this.stopLocationTracking()
      } else {
        await this.startLocationTracking()
      }
    },

    /**
     * 位置更新回调
     * @param {Object} location - 新的位置信息
     */
    onLocationUpdate(location) {
      console.log('位置更新:', location)

      // 更新用户位置
      this.userLocation = {
        lng: location.longitude,
        lat: location.latitude
      }

      // 更新或创建用户位置标记
      this.updateUserLocationMarker(location)

      // 首次位置更新时，自动居中到用户位置
      if (this.isFirstLocationUpdate) {
        this.centerToUserLocation()
        this.isFirstLocationUpdate = false
        console.log('✅ 首次位置更新，已自动居中到用户位置')
      }
    },

    /**
     * 更新用户位置标记
     * @param {Object} location - 位置信息
     */
    updateUserLocationMarker(location) {
      const newMarker = {
        id: 'user-location', // 固定ID
        latitude: location.latitude,
        longitude: location.longitude,
        // 使用自定义图标(需要在 static/icons 目录下放置 user-location.png)
        // 如果没有图标文件,标记会使用默认样式
        iconPath: '/static/icons/user-location.png',
        width: 36,
        height: 36,
        // 添加标注
        label: {
          content: '📍',
          fontSize: 24,
          color: '#4a90e2',
          bgColor: '#ffffff',
          borderRadius: 20,
          padding: 5,
          anchorX: 0,
          anchorY: -20
        },
        callout: {
          content: '我的位置',
          display: 'BYCLICK',
          padding: 10,
          borderRadius: 5,
          bgColor: '#ffffff',
          color: '#333333'
        }
      }

      // 如果已有用户位置标记，更新它
      if (this.userLocationMarker) {
        this.markers = this.markers.map(m =>
          m.id === 'user-location' ? newMarker : m
        )
      } else {
        // 否则添加新标记
        this.markers.push(newMarker)
      }

      this.userLocationMarker = newMarker

      // 关键修复：使用 MapContext API 在地图上显示用户位置标记
      if (this.mapContext && this.mapContext.addMarkers) {
        this.mapContext.addMarkers({
          markers: this.markers,
          clear: true, // 清空后重新添加所有标记，确保用户位置标记被显示
          success: () => {
            console.log('✅ 用户位置标记已更新到地图')
          },
          fail: (err) => {
            console.error('❌ 更新用户位置标记失败:', err)
          }
        })
      }
    },

    /**
     * 地图居中到用户位置
     */
    centerToUserLocation() {
      if (this.userLocation) {
        this.center = { ...this.userLocation }
        this.zoom = 15
      }
    },

    // ==================== AI 查询结果处理 ====================

    /**
     * 处理 AI 查询结果
     * @param {Object} result - AI 查询返回的结果
     */
    handleAIQueryResult(result) {
      console.log('📥 收到 AI 查询结果:', result)

      if (!result.data || result.data.length === 0) {
        console.warn('AI 查询结果为空')
        uni.showToast({ title: '未找到景点', icon: 'none' })
        return
      }

      // 清空现有数据
      this.clearAllSpots()

      // 将 AI 查询结果转换为 markers
      const newMarkers = convertSpotsToMarkers(result.data)

      // 更新本地数据
      this.markers = newMarkers

      // 记录已加载的景点ID
      result.data.forEach(spot => {
        if (spot.id) {
          this.loadedSpotIds.add(spot.id)
        }
      })

      // 使用 MapContext API 添加到地图（无论是否启用聚合，都重新添加所有 markers）
      if (this.mapContext && this.mapContext.addMarkers) {
        this.mapContext.addMarkers({
          markers: newMarkers,
          clear: true, // AI 查询结果总是清空后添加
          success: () => {
            console.log(`✅ 已显示 ${this.markers.length} 个 AI 查询结果`)
          },
          fail: (err) => {
            console.error('❌ 添加 AI 查询结果失败:', err)
          }
        })
      }

      // 如果有结果，自动居中到第一个景点
      if (result.data.length > 0 && result.data[0].lng_wgs84 && result.data[0].lat_wgs84) {
        this.center = {
          lng: result.data[0].lng_wgs84,
          lat: result.data[0].lat_wgs84
        }
        this.zoom = 13

        uni.showToast({
          title: `已显示 ${result.data.length} 个景点`,
          icon: 'success',
          duration: 2000
        })
      }
    },

    // ==================== AI面板控制相关方法 ====================

    /**
     * 切换AI面板显示/隐藏状态
     */
    toggleAIPanel() {
      // 获取AI面板组件引用
      const aiPanel = this.$refs.aiQueryPanel
      if (!aiPanel) {
        console.warn('AI面板组件引用未找到')
        return
      }

      // 切换面板状态
      this.isAIPanelCollapsed = !this.isAIPanelCollapsed
      aiPanel.isCollapsed = this.isAIPanelCollapsed

      console.log(`🤖 AI面板${this.isAIPanelCollapsed ? '隐藏' : '显示'}`)
    },

    /**
     * 同步AI面板状态
     * 当AI面板内部状态变化时调用此方法
     */
    syncAIPanelState(isCollapsed) {
      this.isAIPanelCollapsed = isCollapsed
    },

    /**
     * 处理AI面板折叠状态变化
     * @param {boolean} isCollapsed - 是否折叠
     */
    handleAIPanelCollapseChange(isCollapsed) {
      this.isAIPanelCollapsed = isCollapsed
      console.log(`🤖 AI面板状态变化通知: ${isCollapsed ? '折叠' : '展开'}`)
    }
  }
}
</script>

<style lang="scss" scoped>
.map-container {
  width: 100%;
  height: 100vh;
  position: relative;
}

#mainMap {
  width: 100%;
  height: 100%;
}

.search-bar {
  position: absolute;
  top: 20rpx;
  left: 20rpx;
  right: 20rpx;
  display: flex;
  gap: 16rpx;
  z-index: 10;
}

.search-input {
  flex: 1;
  height: 70rpx;
  padding: 0 24rpx;
  background: #fff;
  border-radius: 35rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.search-btn {
  width: 70rpx;
  height: 70rpx;
  line-height: 70rpx;
  text-align: center;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
  font-size: 24rpx;
  color: #333;
}

.search-results {
  position: absolute;
  top: 100rpx;
  left: 20rpx;
  right: 20rpx;
  max-height: 400rpx;
  background: #fff;
  border-radius: 12rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  z-index: 10;
}

.result-item {
  padding: 24rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.result-title {
  font-size: 30rpx;
  color: #333;
  margin-bottom: 8rpx;
}

.result-address {
  font-size: 24rpx;
  color: #999;
}

.map-controls {
  position: absolute;
  right: 20rpx;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 2rpx;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.15);
}

.control-button {
  width: 70rpx;
  height: 70rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.95);
}

.control-button:active {
  background: rgba(240, 240, 240, 0.95);
}

.button-text {
  font-size: 24rpx;
  font-weight: bold;
  color: #333;
}

.clear-route-btn {
  background: rgba(255, 107, 107, 0.95) !important;
}

.clear-route-btn .button-text {
  color: #fff;
}

.tracking-button {
  transition: all 0.3s ease;
}

.tracking-active {
  background: rgba(74, 144, 226, 0.95) !important;
}

.tracking-active .button-text {
  color: #fff;
}

.ai-button {
  transition: all 0.3s ease;
}

.ai-active {
  background: rgba(74, 144, 226, 0.95) !important;
}

.ai-active .button-text {
  color: #fff;
}

.map-info {
  position: absolute;
  bottom: 150rpx;
  left: 20rpx;
  background: rgba(255, 255, 255, 0.9);
  padding: 12rpx 20rpx;
  border-radius: 8rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.info-item {
  font-size: 24rpx;
  color: #666;
}

.route-active {
  color: #4a90e2;
  font-weight: bold;
  margin-top: 8rpx;
}

.spot-popup {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  top: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  z-index: 100;
}

.popup-content {
  width: 100%;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 32rpx;
  max-height: 70vh;
  overflow-y: auto;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
  padding-bottom: 24rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.spot-name {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
  flex: 1;
}

.close-btn {
  font-size: 48rpx;
  color: #999;
  padding: 0 16rpx;
}

.popup-body {
  margin-bottom: 32rpx;
}

/* 图片相关 */
.spot-image {
  width: 100%;
  height: 300rpx;
  border-radius: 12rpx;
  margin-bottom: 24rpx;
  background: #f5f5f5;
}

.image-loading {
  width: 100%;
  height: 300rpx;
  border-radius: 12rpx;
  margin-bottom: 24rpx;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-size: 28rpx;
}

.no-detail-info {
  padding: 32rpx;
  text-align: center;
  color: #999;
  font-size: 28rpx;
}

.detail-item {
  display: flex;
  margin-bottom: 20rpx;
  font-size: 28rpx;
}

.label {
  color: #666;
  min-width: 120rpx;
  margin-right: 16rpx;
}

.value {
  color: #333;
  flex: 1;
}

/* 描述和小贴士样式 */
.value.description,
.value.tips {
  line-height: 1.6;
  text-align: justify;
}

.value.tips {
  color: #ff6b6b;
  background: #fff5f5;
  padding: 12rpx;
  border-radius: 8rpx;
  border-left: 4rpx solid #ff6b6b;
}

.badge {
  display: inline-block;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
  color: #fff;
  font-size: 24rpx;
  font-weight: bold;
}

.popup-footer {
  display: flex;
  gap: 16rpx;
}

.action-btn {
  flex: 1;
  height: 80rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: bold;
  border: none;
  background: #f0f0f0;
  color: #333;
}

.nav-btn {
  background: #4a90e2;
  color: #fff;
}

.loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 32rpx 48rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
  z-index: 999;
}

/* 聚合点列表弹窗样式 */
.cluster-popup {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  top: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  z-index: 100;
}

.cluster-popup-content {
  width: 100%;
  background: #fff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 32rpx;
  max-height: 60vh;
  display: flex;
  flex-direction: column;
}

.cluster-popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
  padding-bottom: 24rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.cluster-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  flex: 1;
}

.cluster-spot-list {
  flex: 1;
  overflow-y: auto;
  max-height: 40vh;
}

.cluster-spot-item {
  display: flex;
  align-items: center;
  padding: 24rpx 16rpx;
  border-bottom: 1rpx solid #f5f5f5;
  transition: background 0.2s;
}

.cluster-spot-item:active {
  background: #f5f5f5;
}

.spot-level-badge {
  display: inline-block;
  padding: 6rpx 12rpx;
  border-radius: 8rpx;
  color: #fff;
  font-size: 20rpx;
  font-weight: bold;
  margin-right: 16rpx;
  flex-shrink: 0;
}

.spot-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.spot-name {
  font-size: 28rpx;
  color: #333;
  font-weight: 500;
}

.spot-address {
  font-size: 24rpx;
  color: #999;
}

.view-detail-icon {
  font-size: 32rpx;
  color: #999;
  flex-shrink: 0;
}

.cluster-popup-footer {
  padding-top: 24rpx;
  border-top: 1rpx solid #f0f0f0;
}

.cluster-action-btn {
  width: 100%;
  height: 80rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: bold;
  border: none;
}

.zoom-btn {
  background: #4a90e2;
  color: #fff;
}
</style>
