<template>
  <view class="map-container">
    <!-- 搜索框 -->
    <view class="search-bar">
      <input
        v-model="searchKeyword"
        class="search-input"
        placeholder="搜索地点"
        @confirm="handleSearch"
      />
      <view class="search-btn" @tap="handleSearch">🔍</view>
    </view>

    <!-- 搜索结果 -->
    <view v-if="searchResults.length > 0" class="search-results">
      <view
        v-for="(item, index) in searchResults"
        :key="index"
        class="result-item"
        @tap="selectSearchResult(item)"
      >
        <view class="result-title">{{ item.title }}</view>
        <view class="result-address">{{ item.address }}</view>
      </view>
    </view>

    <!-- 地图 -->
    <map
      id="mainMap"
      :longitude="center.lng"
      :latitude="center.lat"
      :scale="zoom"
      :markers="markers"
      :polyline="polyline"
      :show-location="true"
      @regionchange="onRegionChange"
      @markertap="onMarkerTap"
    >
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
            <cover-view class="button-text">📍</cover-view>
          </cover-view>
        </cover-view>

        <cover-view class="control-group">
          <cover-view class="control-button" @tap="loadSpots">
            <cover-view class="button-text">🔄</cover-view>
          </cover-view>
        </cover-view>
      </cover-view>

      <!-- 地图信息 -->
      <cover-view class="map-info">
        <cover-view class="info-item">景点: {{ markers.length }}</cover-view>
      </cover-view>
    </map>

    <!-- 景点详情弹窗 -->
    <view v-if="selectedSpot" class="spot-popup" @tap="closePopup">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="spot-name">{{ selectedSpot.name }}</text>
          <text class="close-btn" @tap="closePopup">✕</text>
        </view>

        <view class="popup-body">
          <!-- 图片 -->
          <view v-if="spotDetailLoading" class="image-loading">
            <text>加载详细信息中...</text>
          </view>
          <image
            v-else-if="selectedSpotDetail && selectedSpotDetail.图片链接"
            :src="selectedSpotDetail.图片链接"
            class="spot-image"
            mode="aspectFill"
            @error="handleImageError"
          />

          <!-- 基本信息（来自GeoJSON，立即显示） -->
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

          <!-- 详细信息（从API获取，延迟显示） -->
          <template v-if="selectedSpotDetail">
            <view class="detail-item" v-if="selectedSpotDetail.评分">
              <text class="label">评分:</text>
              <text class="value">⭐ {{ selectedSpotDetail.评分 }} 分</text>
            </view>

            <view class="detail-item" v-if="selectedSpotDetail.门票 !== undefined && selectedSpotDetail.门票 !== null">
              <text class="label">票价:</text>
              <text class="value">
                {{ selectedSpotDetail.门票 === 0 || selectedSpotDetail.门票 === '0' ? '免费' : `¥${selectedSpotDetail.门票}` }}
              </text>
            </view>

            <view class="detail-item" v-if="selectedSpotDetail.开放时间">
              <text class="label">开放时间:</text>
              <text class="value">{{ selectedSpotDetail.开放时间 }}</text>
            </view>

            <view class="detail-item" v-if="selectedSpotDetail.建议游玩时间">
              <text class="label">游玩时间:</text>
              <text class="value">{{ selectedSpotDetail.建议游玩时间 }}</text>
            </view>

            <view class="detail-item" v-if="selectedSpotDetail.建议季节">
              <text class="label">建议季节:</text>
              <text class="value">{{ selectedSpotDetail.建议季节 }}</text>
            </view>

            <view class="detail-item" v-if="selectedSpotDetail.介绍">
              <text class="label">介绍:</text>
              <text class="value description">{{ selectedSpotDetail.介绍 }}</text>
            </view>

            <view class="detail-item" v-if="selectedSpotDetail.小贴士">
              <text class="label">小贴士:</text>
              <text class="value tips">{{ selectedSpotDetail.小贴士 }}</text>
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
  </view>
</template>

<script>
import { getSpotsByBounds, convertSpotsToMarkers } from '@/services/touristSpotService'
import { searchPlace, drivingRoute, walkingRoute } from '@/services/tencentMapService'

export default {
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
      // 动态加载相关
      loadedSpotIds: new Set(), // 已加载的景点ID集合，用于去重
      lastLoadTime: 0, // 上次加载时间戳
      loadThrottle: 1000, // 加载节流时间（毫秒）
      currentBounds: null, // 当前地图边界
      loadRangeFactor: 0.6, // 加载范围缩小系数（0.6表示缩小到可视区域的60%）
                           // 可调整范围：0.3-1.0
                           // 0.3=加载更少景点, 1.0=加载可视区域所有景点
      isMapReady: false, // 地图是否已准备好
      isInitialLoad: true // 是否是初始加载
    }
  },

  onLoad() {
    this.mapContext = uni.createMapContext('mainMap', this)
    this.getUserLocation()
    // 延迟加载，等待地图初始化完成
    setTimeout(() => {
      this.isMapReady = true
      this.loadSpotsInView()
    }, 1000) // 增加到1秒，确保地图完全初始化
  },

  methods: {
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

      this.loading = true
      this.loadingText = '加载附近景点...'

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

            // 转换为markers并合并到现有markers
            const newMarkers = convertSpotsToMarkers(newSpots)
            this.markers = [...this.markers, ...newMarkers]

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
      this.markers = []
      this.loadedSpotIds.clear()
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

    // 标记点击
    onMarkerTap(e) {
      const marker = this.markers.find(m => m.id === (e.detail.markerId || e.markerId))
      if (marker && marker.spotData) {
        this.selectedSpot = marker.spotData
      }
    },

    // 关闭弹窗
    closePopup() {
      this.selectedSpot = null
      this.polyline = []
    },

    // 地图控制
    handleZoomIn() {
      if (this.zoom < 20) {
        this.zoom++
        // 缩放由用户主动触发，标记为初始加载完成
        this.isInitialLoad = false
      }
    },

    handleZoomOut() {
      if (this.zoom > 3) {
        this.zoom--
        // 缩放由用户主动触发，标记为初始加载完成
        this.isInitialLoad = false
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

      // 初次加载后的第一次regionchange也忽略（通常是地图自动调整）
      if (this.isInitialLoad) {
        console.log('首次regionchange，忽略')
        this.isInitialLoad = false
        return
      }

      // e.causedBy: 'gesture' 手势, 'scale' 缩放, 'update' 方法调用
      console.log('地图区域变化，触发加载:', e.causedBy, e.type)

      // 更新中心点
      if (this.mapContext) {
        this.mapContext.getCenterLocation({
          success: (res) => {
            this.center = { lng: res.longitude, lat: res.latitude }
          }
        })

        // 地图移动或缩放结束后，加载新区域的景点
        this.loadSpotsInView()
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
  font-size: 32rpx;
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
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
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
</style>
