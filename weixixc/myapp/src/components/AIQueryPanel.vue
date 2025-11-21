<template>
  <view class="ai-query-panel" :class="{ 'collapsed': isCollapsed }">
    <!-- 查询输入区域（始终显示） -->
    <view class="query-box-wrapper">
      <view class="query-box">
        <input
          v-model="queryText"
          class="query-input"
          placeholder="输入自然语言查询"
          :disabled="loading"
          @confirm="handleQuery"
        />
        <view
          class="query-button"
          :class="{ 'disabled': loading || !queryText.trim() }"
          @tap="handleQuery"
        >
          <text v-if="!loading">🔍 查询</text>
          <text v-else>⏳ 查询中...</text>
        </view>
        <view
          class="fold-button"
          @tap="toggleCollapse"
        >
          <text>{{ isCollapsed ? '▲' : '▼' }}</text>
        </view>
      </view>

      <!-- 会话状态指示 -->
      <view v-if="currentSessionId" class="session-indicator">
        💬 会话中
      </view>
    </view>

    <!-- 面板内容区域（可折叠） -->
    <view v-show="!isCollapsed" class="panel-content">
      <!-- 答案显示区域 -->
      <view v-if="answer || error" class="answer-section">
        <!-- interrupt clarify提示 -->
        <view v-if="isInterrupted" class="interrupt-content">
          <view class="interrupt-header">
            <text class="interrupt-icon">❓</text>
            <text class="interrupt-label">需要clarify：</text>
          </view>
          <text class="interrupt-text">{{ answer }}</text>

          <view v-if="interruptInfo" class="interrupt-suggestion">
            <text class="suggestion-text">
              {{ interruptInfo.clarity_reason || '请提供更具体的查询信息' }}
            </text>
          </view>

          <view class="clarification-input">
            <input
              v-model="clarifiedQuery"
              class="clarification-input-field"
              placeholder="请输入clarify后的查询..."
              @confirm="handleResume"
            />
            <view
              class="resume-button"
              :class="{ 'disabled': !clarifiedQuery.trim() }"
              @tap="handleResume"
            >
              <text>🔄 继续查询</text>
            </view>
          </view>
        </view>

        <!-- 成功答案 -->
        <view v-else-if="answer && !error" class="answer-content">
          <view class="answer-header">
            <text class="answer-icon">💡</text>
            <text class="answer-label">查询结果：</text>
          </view>
          <text class="answer-text">{{ answer }}</text>

          <view v-if="queryInfo" class="query-info">
            <text class="info-item">
              <text class="info-label">结果数量：</text>{{ queryInfo.count }}
            </text>
            <text v-if="queryInfo.intent_info" class="info-item">
              <text class="info-label">查询类型：</text>
              {{ getIntentTypeName(queryInfo.intent_info.intent_type) }}
            </text>
            <text
              v-if="queryInfo.intent_info && queryInfo.intent_info.is_spatial"
              class="info-item spatial"
            >
              🌍 空间查询
            </text>
          </view>
        </view>

        <!-- 错误提示 -->
        <view v-if="error" class="error-content">
          <view class="error-header">
            <text class="error-icon">⚠️</text>
            <text class="error-label">查询失败：</text>
          </view>
          <text class="error-text">{{ error }}</text>
        </view>
      </view>

      <!-- 初始提示 -->
      <view v-if="!answer && !error && !loading" class="initial-prompt">

      </view>
    </view>
  </view>
</template>

<script>
import { generateSessionId, executeAIQuery, resumeAIQuery, getIntentTypeName } from '@/services/aiQueryService'

export default {
  name: 'AIQueryPanel',

  props: {
    // 是否需要自动折叠（例如当景点弹窗打开时）
    autoCollapse: {
      type: Boolean,
      default: false
    }
  },

  mounted() {
    console.log('✅ AIQueryPanel 组件已加载')
    console.log('初始状态 - isCollapsed:', this.isCollapsed)
  },

  watch: {
    // 监听 autoCollapse 变化，自动折叠/展开
    autoCollapse(shouldCollapse) {
      if (shouldCollapse) {
        // 需要折叠时，自动折叠
        this.isCollapsed = true
        console.log('🔽 AI面板自动隐藏（景点详情打开）')
      } else {
        // 景点详情关闭后，自动恢复显示
        this.isCollapsed = false
        console.log('✅ AI面板自动恢复显示（景点详情关闭）')
      }
    }
  },

  data() {
    return {
      // 状态
      queryText: '',
      answer: '',
      error: '',
      loading: false,
      queryInfo: null,
      isCollapsed: false,  // 改为默认展开，方便看到
      currentSessionId: '',

      // interrupt相关状态
      isInterrupted: false,
      interruptInfo: null,
      clarifiedQuery: ''
    }
  },

  methods: {
    /**
     * 处理查询请求
     */
    async handleQuery() {
      // 验证输入
      if (!this.queryText.trim()) {
        uni.showToast({ title: '请输入查询内容', icon: 'none' })
        return
      }

      if (this.loading) {
        return
      }

      // 如果没有会话ID，开始新会话
      if (!this.currentSessionId) {
        this.currentSessionId = generateSessionId()
        console.log('🆕 开始新会话:', this.currentSessionId)
      }

      // 重置状态
      this.loading = true
      this.error = ''
      this.answer = ''
      this.queryInfo = null
      this.isInterrupted = false
      this.interruptInfo = null

      try {
        console.log('🤖 AI查询开始:', this.queryText)

        // 调用 AI 查询服务
        const result = await executeAIQuery(this.queryText, this.currentSessionId)

        console.log('✅ AI查询结果:', result)

        if (!result.success) {
          this.error = result.message || '查询失败，请重试'
          this.loading = false
          return
        }

        // 检查 interrupt 状态
        if (result.status === 'interrupt') {
          this.isInterrupted = true
          this.interruptInfo = result.interrupt_info || {}
          this.answer = result.message || '查询需要clarify'
          this.loading = false
          console.log('🔄 查询被中断，等待clarify:', this.interruptInfo)
          return
        }

        // 检查响应状态
        if (result.status === 'success') {
          this.answer = result.answer || '查询成功，但未返回答案'

          // 保存查询信息
          this.queryInfo = {
            count: result.count || 0,
            intent_info: result.intent_info || null,
            sql: result.sql || null,
            conversation_id: result.conversation_id || this.currentSessionId
          }

          // 触发事件，通知父组件有新的查询结果
          if (result.data && result.data.length > 0) {
            console.log('📤 触发查询结果事件，数据量:', result.data.length)
            this.$emit('query-result', {
              data: result.data,
              query: this.queryText,
              count: result.count,
              session_id: this.currentSessionId
            })
          }
        } else {
          this.error = result.message || '查询失败，请重试'
        }
      } catch (err) {
        console.error('❌ AI查询失败:', err)
        this.error = err.message || '查询失败，请重试'
      } finally {
        this.loading = false
      }
    },

    /**
     * 处理 resume 查询
     */
    async handleResume() {
      if (!this.clarifiedQuery.trim()) {
        uni.showToast({ title: '请输入clarify后的查询内容', icon: 'none' })
        return
      }

      if (this.loading) {
        return
      }

      // 重置状态
      this.loading = true
      this.error = ''
      this.answer = ''

      try {
        console.log('🔄 继续查询:', this.clarifiedQuery)

        // 调用 resume 服务
        const result = await resumeAIQuery(this.clarifiedQuery, this.currentSessionId)

        console.log('✅ 继续查询结果:', result)

        if (!result.success) {
          this.error = result.message || '继续查询失败，请重试'
          this.loading = false
          return
        }

        // 检查响应状态
        if (result.status === 'success') {
          this.answer = result.answer || '查询成功，但未返回答案'

          // 保存查询信息
          this.queryInfo = {
            count: result.count || 0,
            intent_info: result.intent_info || null,
            sql: result.sql || null,
            conversation_id: result.conversation_id || this.currentSessionId
          }

          // 重置 interrupt 状态
          this.isInterrupted = false
          this.interruptInfo = null
          this.clarifiedQuery = ''

          // 触发事件
          if (result.data && result.data.length > 0) {
            console.log('📤 触发查询结果事件，数据量:', result.data.length)
            this.$emit('query-result', {
              data: result.data,
              query: this.clarifiedQuery,
              count: result.count,
              session_id: this.currentSessionId
            })
          }
        } else {
          this.error = result.message || '继续查询失败，请重试'
        }
      } catch (err) {
        console.error('❌ 继续查询失败:', err)
        this.error = err.message || '继续查询失败，请重试'
      } finally {
        this.loading = false
      }
    },

    /**
     * 切换折叠状态
     */
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed
    },

    /**
     * 设置示例查询
     */
    setExample(text) {
      this.queryText = text
    },

    /**
     * 获取查询类型的中文名称
     */
    getIntentTypeName
  }
}
</script>

<style scoped>
/* ==================== 主面板 ==================== */
.ai-query-panel {
  position: fixed;
  bottom: 40rpx;
  left: 50%;
  transform: translateX(-50%);
  width: 680rpx;
  max-width: 90vw;
  background: #ffffff;
  border-radius: 16rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.15);
  z-index: 9999;  /* 提高 z-index，确保在最上层 */
  transition: all 0.3s ease;
  opacity: 1;
  pointer-events: auto;
}

.ai-query-panel.collapsed {
  /* 完全隐藏面板，避免与景点详情弹窗的底部按钮重合 */
  opacity: 0;
  pointer-events: none;
  transform: translateX(-50%) translateY(100rpx);
}

/* ==================== 查询输入框包装器 ==================== */
.query-box-wrapper {
  padding: 24rpx 32rpx;
  background: white;
  border-radius: 16rpx 16rpx 0 0;
}

.session-indicator {
  font-size: 22rpx;
  color: #666666;
  background: #f5f5f5;
  padding: 8rpx 16rpx;
  border-radius: 20rpx;
  margin-top: 12rpx;
  display: inline-block;
}

/* ==================== 查询输入框 ==================== */
.query-box {
  display: flex;
  gap: 16rpx;
  align-items: center;
}

.query-input {
  flex: 1;
  padding: 20rpx 24rpx;
  border: 2rpx solid #e5e5e5;
  border-radius: 12rpx;
  font-size: 28rpx;
  background: #ffffff;
}

.query-button {
  padding: 20rpx 32rpx;
  background: #4a90e2;
  color: white;
  border-radius: 12rpx;
  font-size: 26rpx;
  white-space: nowrap;
  min-width: 120rpx;
  text-align: center;
}

.query-button.disabled {
  background: #ddd;
  color: #999;
}

.fold-button {
  width: 60rpx;
  height: 60rpx;
  background: transparent;
  color: #888;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
}

/* ==================== 面板内容 ==================== */
.panel-content {
  padding: 0 32rpx 32rpx 32rpx;
  background: white;
  border-radius: 0 0 16rpx 16rpx;
  max-height: 600rpx;
  overflow-y: auto;
}

/* ==================== 答案显示区域 ==================== */
.answer-section {
  margin-top: 8rpx;
}

.answer-content {
  background: #f9f9f9;
  border-radius: 12rpx;
  padding: 24rpx;
  border: 2rpx solid #e5e5e5;
}

.answer-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 12rpx;
}

.answer-icon {
  font-size: 32rpx;
}

.answer-label {
  font-weight: 500;
  color: #333333;
  font-size: 26rpx;
}

.answer-text {
  margin: 12rpx 0;
  color: #555555;
  font-size: 26rpx;
  line-height: 1.6;
  display: block;
}

.query-info {
  display: flex;
  flex-wrap: wrap;
  gap: 24rpx;
  margin-top: 16rpx;
  padding-top: 16rpx;
  border-top: 2rpx solid #e5e5e5;
}

.info-item {
  font-size: 22rpx;
  color: #666666;
  display: block;
}

.info-label {
  font-weight: 500;
  margin-right: 8rpx;
}

.info-item.spatial {
  background: #e3f2fd;
  padding: 8rpx 16rpx;
  border-radius: 16rpx;
  color: #1976d2;
}

/* ==================== 错误显示 ==================== */
.error-content {
  background: #fff3e0;
  border-radius: 12rpx;
  padding: 24rpx;
  border: 2rpx solid #ffb74d;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 12rpx;
}

.error-icon {
  font-size: 32rpx;
}

.error-label {
  font-weight: 500;
  color: #f57c00;
  font-size: 26rpx;
}

.error-text {
  margin: 0;
  color: #666666;
  font-size: 26rpx;
  line-height: 1.6;
  display: block;
}

/* ==================== interrupt clarify提示 ==================== */
.interrupt-content {
  background: #fff8e1;
  border-radius: 12rpx;
  padding: 24rpx;
  border: 2rpx solid #ffd54f;
}

.interrupt-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 12rpx;
}

.interrupt-icon {
  font-size: 32rpx;
}

.interrupt-label {
  font-weight: 500;
  color: #f57c00;
  font-size: 26rpx;
}

.interrupt-text {
  margin: 12rpx 0;
  color: #666666;
  font-size: 26rpx;
  line-height: 1.6;
  display: block;
}

.interrupt-suggestion {
  background: #fff3e0;
  border-radius: 8rpx;
  padding: 16rpx;
  margin: 16rpx 0;
  border-left: 6rpx solid #ff9800;
}

.suggestion-text {
  margin: 0;
  color: #666666;
  font-size: 24rpx;
  line-height: 1.5;
  display: block;
}

.clarification-input {
  display: flex;
  gap: 16rpx;
  margin-top: 24rpx;
}

.clarification-input-field {
  flex: 1;
  padding: 16rpx 20rpx;
  border: 2rpx solid #e5e5e5;
  border-radius: 8rpx;
  font-size: 26rpx;
  background: white;
}

.resume-button {
  padding: 16rpx 24rpx;
  background: #ff9800;
  color: white;
  border-radius: 8rpx;
  font-size: 24rpx;
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
}

.resume-button.disabled {
  background: #ddd;
  color: #999;
}

/* ==================== 初始提示 ==================== */
.initial-prompt {
  text-align: center;
  padding: 24rpx;
}

.prompt-text {
  margin-bottom: 24rpx;
  font-size: 26rpx;
  color: #888888;
  display: block;
}

.example-queries {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.example-btn {
  padding: 16rpx 20rpx;
  background: #f9f9f9;
  border: 2rpx solid #e5e5e5;
  border-radius: 12rpx;
  font-size: 24rpx;
  color: #666666;
}
</style>
