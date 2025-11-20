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

          <view class="detail-item" v-if="selectedSpot.rating">
            <text class="label">评分:</text>
            <text class="value">{{ selectedSpot.rating }} 分</text>
          </view>

          <view class="detail-item" v-if="selectedSpot.ticket_price !== undefined">
            <text class="label">票价:</text>
            <text class="value">
              {{ selectedSpot.ticket_price === 0 ? '免费' : `¥${selectedSpot.ticket_price}` }}
            </text>
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
import { getAllSpots, convertSpotsToMarkers } from '@/services/touristSpotService'
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
      userLocation: null
    }
  },

  onLoad() {
    this.mapContext = uni.createMapContext('mainMap', this)
    this.loadSpots()
    this.getUserLocation()
  },

  methods: {
    // 加载景点
    async loadSpots() {
      this.loading = true
      this.loadingText = '加载景点...'
      try {
        const result = await getAllSpots()
        if (result.success) {
          this.markers = convertSpotsToMarkers(result.data)
          if (this.markers.length > 0) {
            this.center = {
              lng: this.markers[0].longitude,
              lat: this.markers[0].latitude
            }
          }
          uni.showToast({ title: `加载了 ${this.markers.length} 个景点`, icon: 'success' })
        }
      } catch (error) {
        console.error('加载失败:', error)
      } finally {
        this.loading = false
      }
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
      if (this.zoom < 20) this.zoom++
    },

    handleZoomOut() {
      if (this.zoom > 3) this.zoom--
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
      if (e.type === 'end' && this.mapContext) {
        this.mapContext.getCenterLocation({
          success: (res) => {
            this.center = { lng: res.longitude, lat: res.latitude }
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
