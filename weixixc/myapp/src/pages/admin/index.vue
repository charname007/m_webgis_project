<template>
  <view class="admin-container">
    <!-- 顶部工具栏 -->
    <view class="toolbar">
      <view class="title">景点管理</view>
      <view class="add-btn" @tap="handleAdd">+ 添加景点</view>
    </view>

    <!-- 搜索框 -->
    <view class="search-box">
      <input
        v-model="searchKeyword"
        class="search-input"
        placeholder="搜索景点名称"
        @confirm="handleSearch"
      />
      <view class="search-btn" @tap="handleSearch">搜索</view>
    </view>

    <!-- 景点列表 -->
    <view v-if="!loading && filteredSpots.length > 0" class="spot-list">
      <view
        v-for="spot in filteredSpots"
        :key="spot.id"
        class="spot-item"
      >
        <view class="spot-info">
          <view class="spot-header">
            <text class="spot-name">{{ spot.name }}</text>
            <text v-if="spot.level" class="spot-level" :style="{ backgroundColor: getLevelColor(spot.level) }">
              {{ spot.level }}
            </text>
          </view>
          <view class="spot-address">{{ spot.address || '暂无地址' }}</view>
          <view class="spot-meta">
            <text v-if="spot.rating" class="meta-item">评分: {{ spot.rating }}</text>
            <text v-if="spot.ticketPrice !== undefined" class="meta-item">
              票价: {{ spot.ticketPrice === 0 ? '免费' : `¥${spot.ticketPrice}` }}
            </text>
          </view>
        </view>

        <view class="spot-actions">
          <view class="action-btn edit-btn" @tap="handleEdit(spot)">编辑</view>
          <view class="action-btn delete-btn" @tap="handleDelete(spot)">删除</view>
        </view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-if="!loading && filteredSpots.length === 0" class="empty-state">
      <text class="empty-text">
        {{ searchKeyword ? '未找到匹配的景点' : '请使用搜索功能查找景点' }}
      </text>
      <view v-if="searchKeyword" class="empty-action" @tap="handleClearSearch()">
        清空搜索
      </view>
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>
  </view>
</template>

<script>
import { getAllSpots, deleteSpotByName, searchSpots } from '@/services/touristSpotService'

export default {
  data() {
    return {
      spots: [],
      filteredSpots: [],
      searchKeyword: '',
      loading: false,
      isSearchMode: false, // 标记是否在搜索模式
      hasLoadedOnce: false // 标记是否已经加载过一次数据
    }
  },

  onLoad() {
    console.log('[DEBUG onLoad] 页面首次加载，不自动加载数据，等待用户搜索')
    // 不自动加载数据，用户需要通过搜索来查找景点
  },

  onShow() {
    // 当页面显示时（包括从其他页面返回）
    console.log('[DEBUG onShow] 页面显示, isSearchMode:', this.isSearchMode, ', hasLoadedOnce:', this.hasLoadedOnce)

    // 完全不自动加载，保持搜索结果和空状态
  },

  methods: {
    // 加载景点列表（限制数量，避免加载过多）
    async loadSpots() {
      // 添加调用堆栈追踪
      console.log('[DEBUG loadSpots] 被调用，调用堆栈:')
      console.trace()

      this.loading = true
      this.isSearchMode = false
      this.hasLoadedOnce = true
      try {
        const result = await getAllSpots()
        if (result.success) {
          // 只显示前100条，避免性能问题
          this.spots = (result.data || []).slice(0, 100)
          this.filteredSpots = this.spots
          console.log(`景点列表加载成功: 显示前 ${this.spots.length} 条（共 ${result.data?.length || 0} 条）`)

          if (result.data && result.data.length > 100) {
            uni.showToast({
              title: `已加载前100条，请使用搜索功能查找更多景点`,
              icon: 'none',
              duration: 3000
            })
          }
        } else {
          uni.showToast({ title: '加载失败', icon: 'none' })
        }
      } catch (error) {
        console.error('加载景点失败:', error)
        uni.showToast({ title: '加载失败', icon: 'none' })
      } finally {
        this.loading = false
      }
    },

    // 搜索景点（使用后端API）
    async handleSearch() {
      console.log('[DEBUG handleSearch] 开始搜索, 关键词:', this.searchKeyword)

      if (!this.searchKeyword.trim()) {
        // 清空搜索，回到空状态
        console.log('[DEBUG handleSearch] 关键词为空，清空结果')
        this.isSearchMode = false
        this.filteredSpots = []  // 不自动加载，回到空状态
        return
      }

      this.loading = true
      this.isSearchMode = true
      try {
        const result = await searchSpots(this.searchKeyword)

        if (result.success) {
          this.filteredSpots = result.data || []
          console.log(`[DEBUG handleSearch] 搜索 "${this.searchKeyword}" 找到 ${this.filteredSpots.length} 个结果`)

          if (this.filteredSpots.length === 0) {
            uni.showToast({ title: '未找到匹配的景点', icon: 'none' })
          }
        } else {
          console.error('[ERROR handleSearch] 搜索失败:', result.error)
          uni.showToast({ title: '搜索失败', icon: 'none' })
          this.filteredSpots = []
        }
      } catch (error) {
        console.error('[ERROR handleSearch] 搜索异常:', error)
        uni.showToast({ title: '搜索失败', icon: 'none' })
        this.filteredSpots = []
      } finally {
        this.loading = false
      }
    },

    // 清空搜索
    async handleClearSearch() {
      console.log('[DEBUG handleClearSearch] 清空搜索')
      this.searchKeyword = ''
      this.isSearchMode = false
      this.filteredSpots = []  // 清空结果，回到初始空状态
      // 不再自动加载数据
    },

    // 添加景点
    handleAdd() {
      uni.navigateTo({
        url: '/pages/admin/edit'
      })
    },

    // 编辑景点
    handleEdit(spot) {
      console.log('[DEBUG handleEdit] 准备编辑景点:', spot.name)
      uni.navigateTo({
        url: `/pages/admin/edit?name=${encodeURIComponent(spot.name)}`
      })
    },

    // 删除景点
    handleDelete(spot) {
      uni.showModal({
        title: '确认删除',
        content: `确定要删除景点 "${spot.name}" 吗？`,
        success: async (res) => {
          if (res.confirm) {
            await this.deleteSpot(spot.name)
          }
        }
      })
    },

    // 执行删除
    async deleteSpot(name) {
      console.log('[DEBUG deleteSpot] 删除景点:', name)
      uni.showLoading({ title: '删除中...' })
      try {
        const result = await deleteSpotByName(name)
        if (result.success) {
          uni.showToast({ title: '删除成功', icon: 'success' })

          // 删除后重新执行搜索以更新结果
          if (this.isSearchMode && this.searchKeyword) {
            console.log('[DEBUG deleteSpot] 重新执行搜索以更新结果')
            await this.handleSearch()
          } else {
            // 如果没有搜索关键词，直接从列表中移除该项
            console.log('[DEBUG deleteSpot] 从列表中移除该项')
            this.filteredSpots = this.filteredSpots.filter(spot => spot.name !== name)
          }
        } else {
          uni.showToast({ title: result.error || '删除失败', icon: 'none' })
        }
      } catch (error) {
        console.error('[ERROR deleteSpot] 删除景点失败:', error)
        uni.showToast({ title: '删除失败', icon: 'none' })
      } finally {
        uni.hideLoading()
      }
    },

    // 获取等级颜色
    getLevelColor(level) {
      const colorMap = {
        '5A': '#ff6b6b',
        '4A': '#4ecdc4',
        '3A': '#45b7d1',
        '2A': '#96ceb4',
        'default': '#95a5a6'
      }
      return colorMap[level] || colorMap.default
    }
  }
}
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  background-color: #ffffff;
  border-bottom: 1px solid #e0e0e0;
}

.title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333333;
}

.add-btn {
  padding: 12rpx 24rpx;
  background-color: #4ecdc4;
  color: #ffffff;
  border-radius: 8rpx;
  font-size: 28rpx;
}

.search-box {
  display: flex;
  padding: 20rpx;
  background-color: #ffffff;
  margin-bottom: 20rpx;
}

.search-input {
  flex: 1;
  padding: 20rpx;
  background-color: #f5f5f5;
  border-radius: 8rpx;
  font-size: 28rpx;
}

.search-btn {
  margin-left: 20rpx;
  padding: 20rpx 40rpx;
  background-color: #4ecdc4;
  color: #ffffff;
  border-radius: 8rpx;
  font-size: 28rpx;
}

.spot-list {
  padding: 0 20rpx;
}

.spot-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  margin-bottom: 20rpx;
  background-color: #ffffff;
  border-radius: 12rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.spot-info {
  flex: 1;
}

.spot-header {
  display: flex;
  align-items: center;
  margin-bottom: 16rpx;
}

.spot-name {
  font-size: 32rpx;
  font-weight: bold;
  color: #333333;
  margin-right: 16rpx;
}

.spot-level {
  padding: 4rpx 12rpx;
  color: #ffffff;
  font-size: 22rpx;
  border-radius: 6rpx;
}

.spot-address {
  font-size: 26rpx;
  color: #666666;
  margin-bottom: 12rpx;
}

.spot-meta {
  display: flex;
  gap: 20rpx;
}

.meta-item {
  font-size: 24rpx;
  color: #999999;
}

.spot-actions {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.action-btn {
  padding: 12rpx 24rpx;
  border-radius: 8rpx;
  font-size: 24rpx;
  text-align: center;
  min-width: 100rpx;
}

.edit-btn {
  background-color: #45b7d1;
  color: #ffffff;
}

.delete-btn {
  background-color: #ff6b6b;
  color: #ffffff;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 200rpx 0;
}

.empty-text {
  font-size: 28rpx;
  color: #999999;
  margin-bottom: 40rpx;
}

.empty-action {
  padding: 20rpx 60rpx;
  background-color: #4ecdc4;
  color: #ffffff;
  border-radius: 8rpx;
  font-size: 28rpx;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 40rpx;
  color: #999999;
}
</style>
