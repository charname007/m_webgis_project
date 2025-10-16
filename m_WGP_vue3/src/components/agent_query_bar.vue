<template>
  <div
    ref="panelRef"
    class="agent-query-bar"
    :class="{ 'collapsed': isCollapsed }"
  >
    <!-- 查询输入区域（始终显示） -->
    <div class="query-box-wrapper">
      <div class="query-box">
        <input
          v-model="queryText"
          type="text"
          placeholder="输入自然语言查询，例如：查询浙江省的5A景区"
          @keyup.enter="handleQuery"
          class="query-input"
          :disabled="loading"
        />
        <button @click="handleQuery" class="query-button" :disabled="loading || !queryText.trim()">
          <span v-if="!loading">🔍 查询</span>
          <span v-else>⏳ 查询中...</span>
        </button>
        <button
          @click="toggleCollapse"
          class="fold-button"
          :title="isCollapsed ? '展开' : '折叠'"
        >
          {{ isCollapsed ? '▲' : '▼' }}
        </button>
      </div>
      <!-- 会话状态指示 -->
      <div v-if="currentSessionId" class="session-indicator" :title="'会话ID: ' + currentSessionId">
        💬 会话中
      </div>
    </div>

    <!-- 面板内容区域（可折叠） -->
    <div v-show="!isCollapsed" class="panel-content">
      <!-- 答案显示区域 -->
      <div v-if="answer || error" class="answer-section">
        <!-- interrupt澄清提示 -->
        <div v-if="isInterrupted" class="interrupt-content">
          <div class="interrupt-header">
            <span class="interrupt-icon">❓</span>
            <span class="interrupt-label">需要澄清：</span>
          </div>
          <p class="interrupt-text">{{ answer }}</p>
          <div v-if="interruptInfo" class="interrupt-suggestion">
            <p class="suggestion-text">{{ interruptInfo.clarity_reason || '请提供更具体的查询信息' }}</p>
          </div>
          <div class="clarification-input">
            <input
              v-model="clarifiedQuery"
              type="text"
              placeholder="请输入澄清后的查询..."
              class="clarification-input-field"
              @keyup.enter="handleResume"
            />
            <button @click="handleResume" class="resume-button" :disabled="!clarifiedQuery.trim()">
              🔄 继续查询
            </button>
          </div>
        </div>

        <!-- 成功答案 -->
        <div v-else-if="answer && !error" class="answer-content">
          <div class="answer-header">
            <span class="answer-icon">💡</span>
            <span class="answer-label">查询结果：</span>
          </div>
          <p class="answer-text">{{ answer }}</p>
          <div v-if="queryInfo" class="query-info">
            <span class="info-item">
              <strong>结果数量：</strong>{{ queryInfo.count }}
            </span>
            <span v-if="queryInfo.intent_info" class="info-item">
              <strong>查询类型：</strong>{{ getIntentTypeName(queryInfo.intent_info.intent_type) }}
            </span>
            <span v-if="queryInfo.intent_info && queryInfo.intent_info.is_spatial" class="info-item spatial">
              🌍 空间查询
            </span>
          </div>
        </div>

        <!-- 错误提示 -->
        <div v-if="error" class="error-content">
          <div class="error-header">
            <span class="error-icon">⚠️</span>
            <span class="error-label">查询失败：</span>
          </div>
          <p class="error-text">{{ error }}</p>
        </div>
      </div>

      <!-- 初始提示 -->
      <div v-if="!answer && !error && !loading" class="initial-prompt">
        <p>💬 您可以尝试这些查询：</p>
        <div class="example-queries">
          <button @click="queryText = '查询浙江省的5A景区'" class="example-btn">查询浙江省的5A景区</button>
          <button @click="queryText = '统计湖北省有多少个景区'" class="example-btn">统计湖北省有多少个景区</button>
          <button @click="queryText = '查找武汉市的景区'" class="example-btn">查找武汉市的景区</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, inject } from 'vue'
import axios from 'axios'
import API_CONFIG from '../config/api.js'

export default {
  name: 'AgentQueryBar',
  setup() {
    // ==================== 状态定义 ====================
    const queryText = ref('')           // 用户输入的查询文本
    const answer = ref('')              // AI 返回的答案
    const error = ref('')               // 错误信息
    const loading = ref(false)          // 加载状态
    const queryInfo = ref(null)         // 查询信息（count、intent_info等）
    const executionTime = ref(null)     // 执行时间
    const isCollapsed = ref(true)      // 折叠状态
    const panelRef = ref(null)          // 面板引用
    const currentSessionId = ref('')    // 当前会话ID
    const sessionHistory = ref([])      // 会话历史记录
    
    // ✅ 新增：interrupt相关状态
    const isInterrupted = ref(false)    // 是否处于interrupt状态
    const interruptInfo = ref(null)     // interrupt信息
    const clarifiedQuery = ref('')      // 澄清后的查询文本

    // 注入设置查询结果的方法（由 OlMap 提供）
    const setAgentQueryResult = inject('setAgentQueryResult', null)

    // ==================== 会话管理方法 ====================

    /**
     * 生成新的会话ID
     */
    const generateSessionId = () => {
      const timestamp = Date.now().toString(36)
      const random = Math.random().toString(36).substr(2, 5)
      return `session_${timestamp}_${random}`
    }

    /**
     * 开始新会话
     */
    const startNewSession = () => {
      currentSessionId.value = generateSessionId()
      sessionHistory.value = []
      console.log('🆕 开始新会话:', currentSessionId.value)
    }


    /**
     * 记录查询到会话历史
     */
    const addToSessionHistory = (query, result) => {
      sessionHistory.value.push({
        query,
        timestamp: new Date().toISOString(),
        result: {
          count: result.count || 0,
          status: result.status || 'unknown',
          executionTime: result.execution_time || null
        }
      })
    }

    // ==================== 核心方法 ====================

    /**
     * 处理查询请求
     * 调用 sight_server 的 /query 端点，获取 AI 查询结果
     */
    const handleQuery = async () => {
      // 验证输入
      if (!queryText.value.trim()) {
        error.value = '请输入查询内容'
        return
      }

      // 如果没有会话ID，开始新会话
      if (!currentSessionId.value) {
        startNewSession()
      }

      // 重置状态
      loading.value = true
      error.value = ''
      answer.value = ''
      queryInfo.value = null
      executionTime.value = null

      try {
        // 构建 sight_server 的查询 URL
        const queryUrl = API_CONFIG.buildSightServerURL(API_CONFIG.sightServer.endpoints.query)

        console.log('🤖 AI查询开始:', queryText.value)
        console.log('📡 请求URL:', queryUrl)
        console.log('💬 会话ID:', currentSessionId.value)

        // 发送 GET 请求到 sight_server（包含会话ID）
        const response = await axios.get(queryUrl, {
          params: {
            q: queryText.value.trim(),
            include_sql: true,  // 请求包含 SQL 语句
            conversation_id: currentSessionId.value  // 传递会话ID
          },
          timeout: 600000  // 30秒超时
        })

        console.log('✅ AI查询成功:', response.data)

        // ✅ 新增：检查interrupt状态
        if (response.data.status === 'interrupt') {
          // 处理interrupt状态
          isInterrupted.value = true
          interruptInfo.value = response.data.interrupt_info || {}
          answer.value = response.data.message || '查询需要澄清:'
          error.value = ''
          loading.value = false
          console.log('🔄 查询被中断，等待澄清:', interruptInfo.value)
          return
        }

        // 检查响应状态
        if (response.data.status === 'success') {
          // 提取答案和数据
          answer.value = response.data.answer || '查询成功，但未返回答案'
          executionTime.value = response.data.execution_time || null

          // 保存查询信息
          queryInfo.value = {
            count: response.data.count || 0,
            intent_info: response.data.intent_info || null,
            sql: response.data.sql || null,
            conversation_id: response.data.conversation_id || currentSessionId.value
          }

          // 记录到会话历史
          addToSessionHistory(queryText.value, response.data)

          // 将数据传递给 TouristSpotSearch 组件（通过 OlMap 的 provide）
          if (setAgentQueryResult && response.data.data) {
            console.log('📤 传递数据给 TouristSpotSearch，数量:', response.data.data.length)
            setAgentQueryResult({
              data: response.data.data,
              query: queryText.value,
              count: response.data.count,
              session_id: currentSessionId.value
            })
          }
        } else {
          // 查询失败
          error.value = response.data.message || '查询失败，请重试'
        }
      } catch (err) {
        console.error('❌ AI查询失败:', err)

        // 错误处理
        if (err.code === 'ECONNABORTED') {
          error.value = '查询超时，请检查 sight_server 是否正在运行'
        } else if (err.response) {
          error.value = `查询失败: ${err.response.data?.message || err.response.statusText}`
        } else if (err.request) {
          error.value = '无法连接到 AI 查询服务，请检查 sight_server 是否启动'
        } else {
          error.value = `查询失败: ${err.message}`
        }
      } finally {
        loading.value = false
      }
    }

    /**
     * 切换折叠状态
     */
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
    }

    /**
     * 获取查询类型的中文名称
     */
    const getIntentTypeName = (intentType) => {
      const typeMap = {
        'query': '数据查询',
        'summary': '统计汇总'
      }
      return typeMap[intentType] || intentType
    }

    /**
     * 处理resume查询
     * 当查询被interrupt后，使用澄清后的查询继续执行
     */
    const handleResume = async () => {
      if (!clarifiedQuery.value.trim()) {
        error.value = '请输入澄清后的查询内容'
        return
      }

      // 重置状态
      loading.value = true
      error.value = ''
      answer.value = ''

      try {
        // 构建 resume 请求的 URL
        const resumeUrl = API_CONFIG.buildSightServerURL(API_CONFIG.sightServer.endpoints.query + '/resume')

        console.log('🔄 继续查询:', clarifiedQuery.value)
        console.log('📡 请求URL:', resumeUrl)
        console.log('💬 会话ID:', currentSessionId.value)

        // 发送 POST 请求到 resume 端点
        const response = await axios.post(resumeUrl, {
          conversation_id: currentSessionId.value,
          clarified_query: clarifiedQuery.value.trim(),
          include_sql: true
        }, {
          timeout: 600000  // 30秒超时
        })

        console.log('✅ 继续查询成功:', response.data)

        // 检查响应状态
        if (response.data.status === 'success') {
          // 提取答案和数据
          answer.value = response.data.answer || '查询成功，但未返回答案'
          executionTime.value = response.data.execution_time || null

          // 保存查询信息
          queryInfo.value = {
            count: response.data.count || 0,
            intent_info: response.data.intent_info || null,
            sql: response.data.sql || null,
            conversation_id: response.data.conversation_id || currentSessionId.value
          }

          // 记录到会话历史
          addToSessionHistory(clarifiedQuery.value, response.data)

          // 将数据传递给 TouristSpotSearch 组件
          if (setAgentQueryResult && response.data.data) {
            console.log('📤 传递数据给 TouristSpotSearch，数量:', response.data.data.length)
            setAgentQueryResult({
              data: response.data.data,
              query: clarifiedQuery.value,
              count: response.data.count,
              session_id: currentSessionId.value
            })
          }

          // 重置interrupt状态
          isInterrupted.value = false
          interruptInfo.value = null
          clarifiedQuery.value = ''
        } else {
          // 查询失败
          error.value = response.data.message || '继续查询失败，请重试'
        }
      } catch (err) {
        console.error('❌ 继续查询失败:', err)

        // 错误处理
        if (err.code === 'ECONNABORTED') {
          error.value = '查询超时，请检查 sight_server 是否正在运行'
        } else if (err.response) {
          error.value = `继续查询失败: ${err.response.data?.message || err.response.statusText}`
        } else if (err.request) {
          error.value = '无法连接到 AI 查询服务，请检查 sight_server 是否启动'
        } else {
          error.value = `继续查询失败: ${err.message}`
        }
      } finally {
        loading.value = false
      }
    }

    // ==================== 返回值 ====================
    return {
      // 状态
      queryText,
      answer,
      error,
      loading,
      queryInfo,
      executionTime,
      isCollapsed,
      panelRef,
      currentSessionId,
      sessionHistory,
      // ✅ 新增：interrupt相关状态
      isInterrupted,
      interruptInfo,
      clarifiedQuery,
      // 方法
      handleQuery,
      toggleCollapse,
      getIntentTypeName,
      startNewSession,
      handleResume
    }
  }
}
</script>

<style scoped>
/* ==================== 简约风格主面板 ==================== */
.agent-query-bar {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  max-width: 90vw;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.1);
  z-index: 1500;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.2s ease;
  border: 1px solid #f0f0f0;
}

.agent-query-bar:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
}

.agent-query-bar.collapsed {
  max-height: 80px;
}

/* ==================== 查询输入框包装器 ==================== */
.query-box-wrapper {
  padding: 12px 16px;
  background: white;
  position: relative;
}

.session-indicator {
  font-size: 11px;
  color: #666;
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 400;
  margin-top: 6px;
  display: inline-block;
}

/* ==================== 简化面板内容 ==================== */
.panel-content {
  padding: 0 16px 16px 16px;
  background: white;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

/* ==================== 简化查询输入框 ==================== */
.query-box {
  display: flex;
  gap: 8px;
}

.query-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s ease;
  background: #ffffff;
}

.query-input:focus {
  outline: none;
  border-color: #666;
}

.query-input:disabled {
  background: #fafafa;
  cursor: not-allowed;
}

.query-button {
  padding: 8px 16px;
  background: #333;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 400;
  transition: background-color 0.2s ease;
  white-space: nowrap;
  min-width: 80px;
}

.query-button:hover:not(:disabled) {
  background: #555;
}

.query-button:disabled {
  background: #ddd;
  cursor: not-allowed;
}

.fold-button {
  background: transparent;
  color: #888;
  border: none;
  border-radius: 4px;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: color 0.2s ease;
}

.fold-button:hover {
  color: #333;
}

/* ==================== 简化答案显示区域 ==================== */
.answer-section {
  margin-top: 4px;
}

.answer-content {
  background: #f9f9f9;
  border-radius: 6px;
  padding: 12px;
  border: 1px solid #e5e5e5;
}

.answer-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.answer-icon {
  font-size: 16px;
}

.answer-label {
  font-weight: 500;
  color: #333;
  font-size: 13px;
}

.answer-text {
  margin: 6px 0;
  color: #555;
  font-size: 13px;
  line-height: 1.5;
  max-height: 100px;
  overflow-y: auto;
  padding-right: 4px;
}

.query-info {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #e5e5e5;
}

.info-item {
  font-size: 11px;
  color: #666;
}

.info-item strong {
  font-weight: 500;
  margin-right: 2px;
}

.info-item.spatial {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 8px;
  color: #555;
}

/* ==================== 简化错误显示区域 ==================== */
.error-content {
  background: #fafafa;
  border-radius: 6px;
  padding: 12px;
  border: 1px solid #e5e5e5;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.error-icon {
  font-size: 16px;
}

.error-label {
  font-weight: 500;
  color: #666;
  font-size: 13px;
}

.error-text {
  margin: 6px 0 0 0;
  color: #666;
  font-size: 13px;
  line-height: 1.5;
}

/* ==================== interrupt澄清提示样式 ==================== */
.interrupt-content {
  background: #fff8e1;
  border-radius: 6px;
  padding: 12px;
  border: 1px solid #ffd54f;
}

.interrupt-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.interrupt-icon {
  font-size: 16px;
}

.interrupt-label {
  font-weight: 500;
  color: #f57c00;
  font-size: 13px;
}

.interrupt-text {
  margin: 6px 0;
  color: #666;
  font-size: 13px;
  line-height: 1.5;
}

.interrupt-suggestion {
  background: #fff3e0;
  border-radius: 4px;
  padding: 8px;
  margin: 8px 0;
  border-left: 3px solid #ff9800;
}

.suggestion-text {
  margin: 0;
  color: #666;
  font-size: 12px;
  line-height: 1.4;
}

.clarification-input {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.clarification-input-field {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  font-size: 13px;
  background: white;
}

.clarification-input-field:focus {
  outline: none;
  border-color: #666;
}

.resume-button {
  padding: 6px 12px;
  background: #ff9800;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 400;
  transition: background-color 0.2s ease;
  white-space: nowrap;
}

.resume-button:hover:not(:disabled) {
  background: #f57c00;
}

.resume-button:disabled {
  background: #ddd;
  cursor: not-allowed;
}

/* ==================== 简化初始提示 ==================== */
.initial-prompt {
  text-align: center;
  padding: 12px;
  color: #888;
}

.initial-prompt p {
  margin: 0 0 12px 0;
  font-size: 13px;
}

.example-queries {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.example-btn {
  padding: 6px 10px;
  background: #f9f9f9;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  color: #666;
  transition: all 0.2s ease;
}

.example-btn:hover {
  background: #333;
  color: white;
  border-color: #333;
}

/* ==================== 简化滚动条样式 ==================== */
.panel-content::-webkit-scrollbar,
.answer-text::-webkit-scrollbar {
  width: 4px;
}

.panel-content::-webkit-scrollbar-track,
.answer-text::-webkit-scrollbar-track {
  background: transparent;
}

.panel-content::-webkit-scrollbar-thumb,
.answer-text::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 2px;
}

.panel-content::-webkit-scrollbar-thumb:hover,
.answer-text::-webkit-scrollbar-thumb:hover {
  background: #ccc;
}
</style>
