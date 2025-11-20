<template>
  <view class="search-panel">
    <!-- 搜索框 -->
    <view class="search-box">
      <input 
        v-model="keyword" 
        class="search-input" 
        placeholder="搜索地点"
        @input="onInput"
        @confirm="onSearch"
      />
      <view class="search-btn" @tap="onSearch">搜索</view>
    </view>

    <!-- 搜索结果列表 -->
    <view v-if="results.length > 0" class="results-list">
      <view 
        v-for="(item, index) in results" 
        :key="index"
        class="result-item"
        @tap="selectResult(item)"
      >
        <view class="item-title">{{ item.title }}</view>
        <view class="item-address">{{ item.address }}</view>
      </view>
    </view>

    <!-- 空状态 -->
    <view v-else-if="searched && results.length === 0" class="empty-state">
      <text>未找到相关地点</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { searchPlace } from '@/services/tencentMapService'

const props = defineProps({
  location: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select'])

const keyword = ref('')
const results = ref([])
const searched = ref(false)

// 输入事件
const onInput = (e) => {
  keyword.value = e.detail.value
  if (!keyword.value) {
    results.value = []
    searched.value = false
  }
}

// 搜索
const onSearch = async () => {
  if (!keyword.value.trim()) {
    uni.showToast({ title: '请输入搜索关键词', icon: 'none' })
    return
  }

  try {
    uni.showLoading({ title: '搜索中...' })
    
    const data = await searchPlace(keyword.value, {
      location: props.location,
      radius: 5000
    })

    results.value = data || []
    searched.value = true

    if (results.value.length === 0) {
      uni.showToast({ title: '未找到结果', icon: 'none' })
    }
  } catch (error) {
    console.error('搜索失败:', error)
    uni.showToast({ title: '搜索失败', icon: 'none' })
  } finally {
    uni.hideLoading()
  }
}

// 选择结果
const selectResult = (item) => {
  emit('select', item)
  results.value = []
  keyword.value = ''
}
</script>

<style lang="scss" scoped>
.search-panel {
  background: #fff;
  border-radius: 12rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.search-box {
  display: flex;
  padding: 20rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.search-input {
  flex: 1;
  height: 70rpx;
  padding: 0 24rpx;
  background: #f5f5f5;
  border-radius: 35rpx;
  font-size: 28rpx;
}

.search-btn {
  width: 120rpx;
  height: 70rpx;
  line-height: 70rpx;
  text-align: center;
  margin-left: 20rpx;
  background: #4a90e2;
  color: #fff;
  border-radius: 35rpx;
  font-size: 28rpx;
}

.results-list {
  max-height: 600rpx;
  overflow-y: auto;
}

.result-item {
  padding: 24rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.result-item:last-child {
  border-bottom: none;
}

.item-title {
  font-size: 30rpx;
  color: #333;
  margin-bottom: 8rpx;
}

.item-address {
  font-size: 24rpx;
  color: #999;
}

.empty-state {
  padding: 80rpx;
  text-align: center;
  color: #999;
  font-size: 28rpx;
}
</style>
