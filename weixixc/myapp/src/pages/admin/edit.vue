<template>
  <view class="edit-container">
    <!-- 顶部标题栏 -->
    <view class="header">
      <text class="header-title">{{ isEdit ? '编辑景点' : '添加景点' }}</text>
    </view>

    <!-- 表单 -->
    <view class="form">
      <!-- 基本信息 -->
      <view class="form-section">
        <view class="section-title">基本信息</view>

        <view class="form-item">
          <text class="label required">景点名称</text>
          <input
            v-model="formData.name"
            class="input"
            placeholder="请输入景点名称"
          />
        </view>

        <view class="form-item">
          <text class="label">等级</text>
          <picker
            mode="selector"
            :value="levelIndex >= 0 ? levelIndex : 0"
            :range="levelOptions"
            @change="handleLevelChange"
          >
            <view class="picker-display">
              <text :class="formData.level ? 'selected' : 'placeholder'">
                {{ formData.level || '请选择等级' }}
              </text>
            </view>
          </picker>
        </view>

        <view class="form-item">
          <text class="label required">地址</text>
          <input
            v-model="formData.address"
            class="input"
            placeholder="请输入地址"
          />
        </view>

        <view class="form-item">
          <text class="label">城市</text>
          <input
            v-model="formData.city"
            class="input"
            placeholder="请输入城市"
          />
        </view>

        <view class="form-item">
          <text class="label">评分 (0-5)</text>
          <input
            v-model="formData.rating"
            type="digit"
            class="input"
            placeholder="请输入评分"
          />
        </view>

        <view class="form-item">
          <text class="label">门票价格 (元)</text>
          <input
            v-model="formData.ticketPrice"
            type="number"
            class="input"
            placeholder="请输入门票价格，免费填0"
          />
        </view>
      </view>

      <!-- 位置信息 -->
      <view class="form-section">
        <view class="section-title">位置信息</view>

        <view class="form-item">
          <text class="label">经度 (WGS84)</text>
          <input
            v-model="formData.lng_wgs84"
            type="digit"
            class="input"
            placeholder="请输入经度"
          />
        </view>

        <view class="form-item">
          <text class="label">纬度 (WGS84)</text>
          <input
            v-model="formData.lat_wgs84"
            type="digit"
            class="input"
            placeholder="请输入纬度"
          />
        </view>
      </view>

      <!-- 详细信息 -->
      <view class="form-section">
        <view class="section-title">详细信息</view>

        <view class="form-item">
          <text class="label">图片链接</text>
          <input
            v-model="formData.imageUrl"
            class="input"
            placeholder="请输入图片URL"
          />
        </view>

        <view class="form-item">
          <text class="label">开放时间</text>
          <input
            v-model="formData.openTime"
            class="input"
            placeholder="例如：全年 08:00-18:00"
          />
        </view>

        <view class="form-item">
          <text class="label">建议游玩时间</text>
          <input
            v-model="formData.recommendedDuration"
            class="input"
            placeholder="例如：2-3小时"
          />
        </view>

        <view class="form-item">
          <text class="label">建议季节</text>
          <input
            v-model="formData.recommendedSeason"
            class="input"
            placeholder="例如：春秋季节"
          />
        </view>

        <view class="form-item">
          <text class="label">景点介绍</text>
          <textarea
            v-model="formData.description"
            class="textarea"
            placeholder="请输入景点介绍"
            :maxlength="-1"
          />
        </view>

        <view class="form-item">
          <text class="label">游玩小贴士</text>
          <textarea
            v-model="formData.tips"
            class="textarea"
            placeholder="请输入游玩小贴士"
            :maxlength="-1"
          />
        </view>
      </view>
    </view>

    <!-- 底部按钮 -->
    <view class="footer">
      <view class="btn btn-cancel" @tap="handleCancel">取消</view>
      <view class="btn btn-submit" @tap="handleSubmit">{{ isEdit ? '保存' : '添加' }}</view>
    </view>

    <!-- 加载状态 -->
    <view v-if="loading" class="loading-mask">
      <view class="loading-box">
        <text>{{ loadingText }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import { getSpotByName, addSpot, updateSpotByName } from '@/services/touristSpotService'

export default {
  data() {
    return {
      isEdit: false,
      originalName: '',
      loading: false,
      loadingText: '加载中...',

      levelOptions: ['5A', '4A', '3A', '2A', '1A'],
      levelIndex: -1,

      formData: {
        name: '',
        address: '',
        city: '',
        level: '',
        rating: '',
        ticketPrice: '',
        lng_wgs84: '',
        lat_wgs84: '',
        imageUrl: '',
        openTime: '',
        recommendedDuration: '',
        recommendedSeason: '',
        description: '',
        tips: ''
      }
    }
  },

  onLoad(options) {
    if (options.name) {
      this.isEdit = true
      this.originalName = decodeURIComponent(options.name)
      this.loadSpotDetail()
    }
  },

  methods: {
    // 加载景点详情
    async loadSpotDetail() {
      this.loading = true
      this.loadingText = '加载景点详情...'
      try {
        const result = await getSpotByName(this.originalName)
        if (result.success && result.data) {
          // 填充表单数据
          this.formData = {
            name: result.data.name || '',
            address: result.data.address || '',
            city: result.data.city || '',
            level: result.data.level || '',
            rating: result.data.rating?.toString() || '',
            ticketPrice: result.data.ticketPrice?.toString() || '',
            lng_wgs84: result.data.lng_wgs84?.toString() || '',
            lat_wgs84: result.data.lat_wgs84?.toString() || '',
            imageUrl: result.data.imageUrl || '',
            openTime: result.data.openTime || '',
            recommendedDuration: result.data.recommendedDuration || '',
            recommendedSeason: result.data.recommendedSeason || '',
            description: result.data.description || '',
            tips: result.data.tips || ''
          }

          // 设置等级选择器索引
          if (this.formData.level) {
            this.levelIndex = this.levelOptions.indexOf(this.formData.level)
          }

          console.log('景点详情加载成功:', this.formData)
        } else {
          uni.showToast({ title: '加载失败', icon: 'none' })
          setTimeout(() => {
            uni.navigateBack()
          }, 1500)
        }
      } catch (error) {
        console.error('加载景点详情失败:', error)
        uni.showToast({ title: '加载失败', icon: 'none' })
        setTimeout(() => {
          uni.navigateBack()
        }, 1500)
      } finally {
        this.loading = false
      }
    },

    // 等级选择器变化
    handleLevelChange(e) {
      console.log('[DEBUG] 等级选择器事件:', e)
      console.log('[DEBUG] e.detail.value:', e.detail.value)
      console.log('[DEBUG] levelOptions:', this.levelOptions)

      this.levelIndex = parseInt(e.detail.value)
      this.formData.level = this.levelOptions[this.levelIndex]

      console.log('[DEBUG] 更新后 levelIndex:', this.levelIndex)
      console.log('[DEBUG] 更新后 formData.level:', this.formData.level)
    },

    // 表单验证
    validateForm() {
      if (!this.formData.name.trim()) {
        uni.showToast({ title: '请输入景点名称', icon: 'none' })
        return false
      }

      if (!this.formData.address.trim()) {
        uni.showToast({ title: '请输入地址', icon: 'none' })
        return false
      }

      // 验证评分
      if (this.formData.rating && (parseFloat(this.formData.rating) < 0 || parseFloat(this.formData.rating) > 5)) {
        uni.showToast({ title: '评分范围应在0-5之间', icon: 'none' })
        return false
      }

      // 验证经纬度
      if (this.formData.lng_wgs84 && (parseFloat(this.formData.lng_wgs84) < -180 || parseFloat(this.formData.lng_wgs84) > 180)) {
        uni.showToast({ title: '经度范围应在-180到180之间', icon: 'none' })
        return false
      }

      if (this.formData.lat_wgs84 && (parseFloat(this.formData.lat_wgs84) < -90 || parseFloat(this.formData.lat_wgs84) > 90)) {
        uni.showToast({ title: '纬度范围应在-90到90之间', icon: 'none' })
        return false
      }

      return true
    },

    // 提交表单
    async handleSubmit() {
      if (!this.validateForm()) {
        return
      }

      this.loading = true
      this.loadingText = this.isEdit ? '保存中...' : '添加中...'

      try {
        // 准备提交数据，转换数据类型
        const submitData = {
          ...this.formData,
          rating: this.formData.rating ? parseFloat(this.formData.rating) : null,
          ticketPrice: this.formData.ticketPrice ? parseFloat(this.formData.ticketPrice) : null,
          lng_wgs84: this.formData.lng_wgs84 ? parseFloat(this.formData.lng_wgs84) : null,
          lat_wgs84: this.formData.lat_wgs84 ? parseFloat(this.formData.lat_wgs84) : null
        }

        let result
        if (this.isEdit) {
          // 更新景点
          result = await updateSpotByName(this.originalName, submitData)
        } else {
          // 添加景点
          result = await addSpot(submitData)
        }

        if (result.success) {
          uni.showToast({
            title: this.isEdit ? '保存成功' : '添加成功',
            icon: 'success'
          })
          setTimeout(() => {
            uni.navigateBack()
          }, 1500)
        } else {
          uni.showToast({
            title: result.error || (this.isEdit ? '保存失败' : '添加失败'),
            icon: 'none'
          })
        }
      } catch (error) {
        console.error('提交失败:', error)
        uni.showToast({
          title: this.isEdit ? '保存失败' : '添加失败',
          icon: 'none'
        })
      } finally {
        this.loading = false
      }
    },

    // 取消操作
    handleCancel() {
      uni.navigateBack()
    }
  }
}
</script>

<style scoped>
.edit-container {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 120rpx;
}

.header {
  padding: 30rpx;
  background-color: #ffffff;
  border-bottom: 1px solid #e0e0e0;
}

.header-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333333;
}

.form {
  padding: 20rpx;
}

.form-section {
  margin-bottom: 30rpx;
  background-color: #ffffff;
  border-radius: 12rpx;
  padding: 30rpx;
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333333;
  margin-bottom: 30rpx;
  padding-bottom: 20rpx;
  border-bottom: 2rpx solid #f0f0f0;
}

.form-item {
  margin-bottom: 30rpx;
}

.label {
  display: block;
  font-size: 28rpx;
  color: #666666;
  margin-bottom: 16rpx;
}

.required::before {
  content: '* ';
  color: #ff6b6b;
}

.input,
.picker-display {
  width: 100%;
  padding: 20rpx;
  background-color: #f5f5f5;
  border-radius: 8rpx;
  font-size: 28rpx;
}

.picker-display .placeholder {
  color: #999999;
}

.picker-display .selected {
  color: #333333;
  font-weight: 500;
}

.textarea {
  width: 100%;
  padding: 20rpx;
  background-color: #f5f5f5;
  border-radius: 8rpx;
  font-size: 28rpx;
  color: #333333;
  min-height: 200rpx;
}

.footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  padding: 20rpx;
  background-color: #ffffff;
  border-top: 1px solid #e0e0e0;
  gap: 20rpx;
}

.btn {
  flex: 1;
  padding: 24rpx;
  text-align: center;
  border-radius: 8rpx;
  font-size: 32rpx;
}

.btn-cancel {
  background-color: #e0e0e0;
  color: #666666;
}

.btn-submit {
  background-color: #4ecdc4;
  color: #ffffff;
}

.loading-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-box {
  padding: 40rpx 60rpx;
  background-color: #ffffff;
  border-radius: 12rpx;
  color: #333333;
  font-size: 28rpx;
}
</style>
