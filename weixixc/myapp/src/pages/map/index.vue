<template>
  <view class="map-container">
    <!-- 地图组件 -->
    <map
      id="mainMap"
      :longitude="center.lng"
      :latitude="center.lat"
      :scale="zoom"
      :markers="markers"
      :show-location="true"
      :enable-zoom="true"
      :enable-scroll="true"
      :enable-rotate="false"
      :enable-overlooking="false"
      :enable-satellite="false"
      :enable-traffic="false"
      @regionchange="onRegionChange"
      @tap="onMapTap"
      @markertap="onMarkerTap"
    >
      <!-- 地图控件 - 使用 cover-view -->
      <cover-view class="map-controls">
        <!-- 缩放控件 -->
        <cover-view class="control-group zoom-controls">
          <cover-view class="control-button zoom-in" @tap="handleZoomIn">
            <cover-view class="button-text">+</cover-view>
          </cover-view>
          <cover-view class="control-button zoom-out" @tap="handleZoomOut">
            <cover-view class="button-text">-</cover-view>
          </cover-view>
        </cover-view>

        <!-- 定位按钮 -->
        <cover-view class="control-group location-control">
          <cover-view class="control-button location-button" @tap="handleLocate">
            <cover-view class="button-text">📍</cover-view>
          </cover-view>
        </cover-view>

        <!-- 刷新景点按钮 -->
        <cover-view class="control-group refresh-control">
          <cover-view class="control-button refresh-button" @tap="loadSpots">
            <cover-view class="button-text">🔄</cover-view>
          </cover-view>
        </cover-view>
      </cover-view>

      <!-- 地图信息显示 -->
      <cover-view class="map-info">
        <cover-view class="info-item">缩放: {{ zoom }}</cover-view>
        <cover-view class="info-item">
          中心: {{ center.lng.toFixed(4) }}, {{ center.lat.toFixed(4) }}
        </cover-view>
        <cover-view class="info-item">景点: {{ markers.length }}</cover-view>
      </cover-view>
    </map>

    <!-- 加载提示 -->
    <view v-if="loading" class="loading-overlay">
      <view class="loading-content">
        <text class="loading-text">{{ loadingText }}</text>
      </view>
    </view>

    <!-- 景点详情弹窗 -->
    <view v-if="selectedSpot" class="spot-detail-popup" @tap="closeSpotDetail">
      <view class="popup-content" @tap.stop>
        <view class="popup-header">
          <text class="spot-name">{{ selectedSpot.name }}</text>
          <text class="close-btn" @tap="closeSpotDetail">✕</text>
        </view>

        <view class="popup-body">
          <view class="detail-item" v-if="selectedSpot.level">
            <text class="item-label">等级:</text>
            <text class="item-value level-badge" :style="{ backgroundColor: getLevelColor(selectedSpot.level) }">
              {{ selectedSpot.level }}
            </text>
          </view>

          <view class="detail-item" v-if="selectedSpot.address">
            <text class="item-label">地址:</text>
            <text class="item-value">{{ selectedSpot.address }}</text>
          </view>

          <view class="detail-item" v-if="selectedSpot.rating">
            <text class="item-label">评分:</text>
            <text class="item-value">{{ selectedSpot.rating }} 分</text>
          </view>

          <view class="detail-item" v-if="selectedSpot.ticket_price !== undefined">
            <text class="item-label">票价:</text>
            <text class="item-value">
              {{ selectedSpot.ticket_price === 0 ? '免费' : `¥${selectedSpot.ticket_price}` }}
            </text>
          </view>

          <view class="detail-item">
            <text class="item-label">坐标:</text>
            <text class="item-value">{{ selectedSpot.lng_wgs84?.toFixed(6) }}, {{ selectedSpot.lat_wgs84?.toFixed(6) }}</text>
          </view>
        </view>

        <view class="popup-footer">
          <button class="action-btn navigate-btn" @tap="navigateToSpot">导航</button>
          <button class="action-btn detail-btn" @tap="viewMoreDetail">详情</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getAllSpots, convertSpotsToMarkers } from '@/services/touristSpotService'

// 响应式数据
const center = ref({
  lng: 114.353,  // 武汉大学经度
  lat: 30.531    // 武汉大学纬度
})

const zoom = ref(12)  // 缩放级别 (3-20)
const loading = ref(false)
const loadingText = ref('加载中...')
const mapContext = ref(null)
const markers = ref([])  // 地图标记数组
const selectedSpot = ref(null)  // 当前选中的景点
const allSpots = ref([])  // 所有景点数据

// 地图上下文
onMounted(() => {
  // 获取地图上下文
  mapContext.value = uni.createMapContext('mainMap')

  // 请求位置权限
  requestLocationPermission()

  // 加载景点数据
  loadSpots()

  console.log('地图页面加载完成')
})

// 加载景点数据
const loadSpots = async () => {
  loading.value = true
  loadingText.value = '加载景点数据...'

  try {
    const result = await getAllSpots()

    if (result.success) {
      console.log('景点数据加载成功:', result.data)
      allSpots.value = result.data

      // 转换为markers格式
      markers.value = convertSpotsToMarkers(result.data)

      console.log('生成标记数量:', markers.value.length)

      // 如果有景点数据,将地图中心移到第一个景点
      if (markers.value.length > 0 && markers.value[0].latitude && markers.value[0].longitude) {
        center.value = {
          lng: markers.value[0].longitude,
          lat: markers.value[0].latitude
        }
      }

      uni.showToast({
        title: `加载了 ${markers.value.length} 个景点`,
        icon: 'success'
      })
    } else {
      console.error('加载景点失败:', result.error)
      uni.showToast({
        title: result.error || '加载景点失败',
        icon: 'none'
      })
    }
  } catch (error) {
    console.error('加载景点异常:', error)
    uni.showToast({
      title: '加载景点异常',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

// 请求位置权限
const requestLocationPermission = () => {
  uni.authorize({
    scope: 'scope.userLocation',
    success() {
      console.log('位置权限已授予')
    },
    fail() {
      console.log('位置权限被拒绝')
      uni.showModal({
        title: '提示',
        content: '需要获取您的位置信息来显示附近景点',
        success(res) {
          if (res.confirm) {
            uni.openSetting()
          }
        }
      })
    }
  })
}

// 地图区域变化事件
const onRegionChange = (e) => {
  if (e.type === 'end' && e.causedBy === 'drag') {
    // 拖动结束,更新中心点
    mapContext.value.getCenterLocation({
      success: (res) => {
        center.value = {
          lng: res.longitude,
          lat: res.latitude
        }
      }
    })
  }

  if (e.type === 'end' && e.causedBy === 'scale') {
    // 缩放结束,更新缩放级别
    mapContext.value.getScale({
      success: (res) => {
        zoom.value = res.scale
      }
    })
  }
}

// 地图点击事件
const onMapTap = (e) => {
  console.log('地图点击:', e)
  // 点击地图空白处关闭详情弹窗
  if (selectedSpot.value) {
    closeSpotDetail()
  }
}

// 标记点击事件
const onMarkerTap = (e) => {
  console.log('标记点击:', e)
  const markerId = e.detail.markerId || e.markerId

  // 查找对应的景点数据
  const marker = markers.value.find(m => m.id === markerId)
  if (marker && marker.spotData) {
    selectedSpot.value = marker.spotData
    console.log('选中景点:', selectedSpot.value)
  }
}

// 关闭景点详情
const closeSpotDetail = () => {
  selectedSpot.value = null
}

// 导航到景点
const navigateToSpot = () => {
  if (!selectedSpot.value) return

  const lat = selectedSpot.value.lat_wgs84
  const lng = selectedSpot.value.lng_wgs84

  uni.openLocation({
    latitude: lat,
    longitude: lng,
    name: selectedSpot.value.name,
    address: selectedSpot.value.address || '',
    scale: 15
  })
}

// 查看更多详情
const viewMoreDetail = () => {
  // 这里可以跳转到详情页面
  uni.showToast({
    title: '详情页面开发中',
    icon: 'none'
  })
}

// 获取等级颜色
const getLevelColor = (level) => {
  const colorMap = {
    '5A': '#ff6b6b',
    '4A': '#4ecdc4',
    '3A': '#45b7d1',
    '2A': '#96ceb4'
  }
  return colorMap[level] || '#95a5a6'
}

// 放大地图
const handleZoomIn = () => {
  if (zoom.value < 20) {
    zoom.value += 1
    mapContext.value.moveToLocation({
      longitude: center.value.lng,
      latitude: center.value.lat
    })
  }
}

// 缩小地图
const handleZoomOut = () => {
  if (zoom.value > 3) {
    zoom.value -= 1
    mapContext.value.moveToLocation({
      longitude: center.value.lng,
      latitude: center.value.lat
    })
  }
}

// 定位到当前位置
const handleLocate = () => {
  loading.value = true
  loadingText.value = '正在定位...'

  uni.getLocation({
    type: 'gcj02',
    success: (res) => {
      center.value = {
        lng: res.longitude,
        lat: res.latitude
      }

      mapContext.value.moveToLocation({
        longitude: res.longitude,
        latitude: res.latitude
      })

      uni.showToast({
        title: '定位成功',
        icon: 'success'
      })
    },
    fail: (err) => {
      console.error('定位失败:', err)
      uni.showToast({
        title: '定位失败',
        icon: 'none'
      })
    },
    complete: () => {
      loading.value = false
    }
  })
}

onUnmounted(() => {
  console.log('地图页面卸载')
})
</script>

<style lang="scss" scoped>
.map-container {
  width: 100%;
  height: 100vh;
  position: relative;
  overflow: hidden;
}

/* 地图组件 */
#mainMap {
  width: 100%;
  height: 100%;
}

/* 地图控件容器 */
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
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 8rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.15);
}

.control-button {
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.95);
  cursor: pointer;
  transition: all 0.2s;
}

.control-button:active {
  background-color: rgba(240, 240, 240, 0.95);
}

.button-text {
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
  line-height: 1;
}

/* 缩放控件 */
.zoom-controls {
  .zoom-in {
    border-bottom: 2rpx solid #e0e0e0;
  }
}

/* 定位控件 */
.location-control {
  margin-top: 20rpx;
}

.location-button .button-text {
  font-size: 36rpx;
}

/* 刷新控件 */
.refresh-control {
  margin-top: 20rpx;
}

.refresh-button .button-text {
  font-size: 32rpx;
}

/* 地图信息显示 */
.map-info {
  position: absolute;
  top: 20rpx;
  left: 20rpx;
  background-color: rgba(255, 255, 255, 0.9);
  padding: 16rpx 24rpx;
  border-radius: 8rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.info-item {
  font-size: 24rpx;
  color: #666;
  line-height: 1.5;
  margin-bottom: 8rpx;
}

.info-item:last-child {
  margin-bottom: 0;
}

/* 加载提示 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-content {
  background-color: rgba(255, 255, 255, 0.95);
  padding: 40rpx 60rpx;
  border-radius: 12rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.loading-text {
  font-size: 28rpx;
  color: #333;
  margin-top: 20rpx;
}

/* 景点详情弹窗 */
.spot-detail-popup {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  z-index: 1000;
  animation: fadeIn 0.3s;
}

.popup-content {
  width: 100%;
  background-color: #ffffff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 32rpx;
  max-height: 70vh;
  overflow-y: auto;
  animation: slideUp 0.3s;
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
  cursor: pointer;
}

.popup-body {
  margin-bottom: 32rpx;
}

.detail-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 20rpx;
  font-size: 28rpx;
}

.item-label {
  color: #666;
  min-width: 120rpx;
  margin-right: 16rpx;
}

.item-value {
  color: #333;
  flex: 1;
  word-break: break-all;
}

.level-badge {
  display: inline-block;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: bold;
}

.popup-footer {
  display: flex;
  gap: 24rpx;
}

.action-btn {
  flex: 1;
  height: 80rpx;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: bold;
  border: none;
}

.navigate-btn {
  background-color: #4a90e2;
  color: #ffffff;
}

.detail-btn {
  background-color: #f0f0f0;
  color: #333;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}
</style>
