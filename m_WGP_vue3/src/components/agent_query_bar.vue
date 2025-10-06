<template>
  <div
    ref="panelRef"
    class="agent-query-bar"
    :class="{ 'collapsed': isCollapsed }"
  >
    <!-- 面板标题栏 -->
    <div class="panel-header">
      <div class="header-left" @click="toggleCollapse" style="cursor: pointer;">
        <span class="panel-icon">🤖</span>
        <h3 class="panel-title">AI 智能查询助手</h3>
      </div>
      <div class="header-right">
        <span v-if="executionTime" class="execution-time">{{ executionTime }}s</span>
        <button
          @click="toggleCollapse"
          class="toggle-button"
          :title="isCollapsed ? '展开' : '折叠'"
        >
          {{ isCollapsed ? '▲' : '▼' }}
        </button>
      </div>
    </div>

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
      </div>
    </div>

    <!-- 面板内容区域（可折叠） -->
    <div v-show="!isCollapsed" class="panel-content">
      <!-- 答案显示区域 -->
      <div v-if="answer || error" class="answer-section">
        <!-- 成功答案 -->
        <div v-if="answer && !error" class="answer-content">
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
    const isCollapsed = ref(false)      // 折叠状态
    const panelRef = ref(null)          // 面板引用

    // 注入设置查询结果的方法（由 OlMap 提供）
    const setAgentQueryResult = inject('setAgentQueryResult', null)

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

        // 发送 GET 请求到 sight_server
        const response = await axios.get(queryUrl, {
          params: {
            q: queryText.value.trim(),
            include_sql: true  // 请求包含 SQL 语句
          },
          timeout: 600000  // 30秒超时
        })

        console.log('✅ AI查询成功:', response.data)

        // 检查响应状态
        if (response.data.status === 'success') {
          // 提取答案和数据
          answer.value = response.data.answer || '查询成功，但未返回答案'
          executionTime.value = response.data.execution_time || null

          // 保存查询信息
          queryInfo.value = {
            count: response.data.count || 0,
            intent_info: response.data.intent_info || null,
            sql: response.data.sql || null
          }

          // 将数据传递给 TouristSpotSearch 组件（通过 OlMap 的 provide）
          if (setAgentQueryResult && response.data.data) {
            console.log('📤 传递数据给 TouristSpotSearch，数量:', response.data.data.length)
            setAgentQueryResult({
              data: response.data.data,
              query: queryText.value,
              count: response.data.count
              
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
      // 方法
      handleQuery,
      toggleCollapse,
      getIntentTypeName
    }
  }
}
</script>

<style scoped>
/* ==================== 主面板样式 ==================== */
.agent-query-bar {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 800px;
  max-width: 90vw;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  z-index: 1500;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.3s ease;
}

.agent-query-bar:hover {
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.4);
}

.agent-query-bar.collapsed {
  max-height: 120px; /* 调整折叠状态高度，容纳标题栏和输入框 */
}

/* ==================== 面板头部 ==================== */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  user-select: none;
}

.panel-header:hover {
  background: rgba(255, 255, 255, 0.2);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-icon {
  font-size: 20px;
}

.panel-title {
  margin: 0;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.execution-time {
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 10px;
  border-radius: 12px;
}

.toggle-button {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  border-radius: 6px;
  width: 32px;
  height: 32px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  transition: all 0.2s ease;
}

.toggle-button:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

/* ==================== 查询输入框包装器（始终显示） ==================== */
.query-box-wrapper {
  padding: 16px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

/* ==================== 面板内容 ==================== */
.panel-content {
  padding: 16px;
  background: white;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 350px; /* 限制最大高度 */
  overflow-y: auto; /* 启用垂直滚动 */
}

/* ==================== 查询输入框 ==================== */
.query-box {
  display: flex;
  gap: 10px;
}

.query-input {
  flex: 1;
  padding: 10px 14px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s ease;
}

.query-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.query-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

.query-button {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  white-space: nowrap;
  min-width: 100px;
}

.query-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.query-button:active:not(:disabled) {
  transform: translateY(0);
}

.query-button:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
}

/* ==================== 答案显示区域 ==================== */
.answer-section {
  margin-top: 8px;
}

.answer-content {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border-left: 4px solid #4caf50;
  border-radius: 8px;
  padding: 12px;
}

.answer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.answer-icon {
  font-size: 20px;
}

.answer-label {
  font-weight: 600;
  color: #2e7d32;
  font-size: 14px;
}

.answer-text {
  margin: 8px 0;
  color: #1b5e20;
  font-size: 14px;
  line-height: 1.6;
  max-height: 120px; /* 限制答案文本最大高度 */
  overflow-y: auto; /* 答案过长时可滚动 */
  padding-right: 8px; /* 为滚动条留出空间 */
}

.query-info {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(76, 175, 80, 0.3);
}

.info-item {
  font-size: 12px;
  color: #2e7d32;
}

.info-item strong {
  font-weight: 600;
  margin-right: 4px;
}

.info-item.spatial {
  background: rgba(33, 150, 243, 0.2);
  padding: 4px 10px;
  border-radius: 12px;
  color: #1565c0;
}

/* ==================== 错误显示区域 ==================== */
.error-content {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  border-left: 4px solid #f44336;
  border-radius: 8px;
  padding: 12px;
}

.error-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.error-icon {
  font-size: 20px;
}

.error-label {
  font-weight: 600;
  color: #c62828;
  font-size: 14px;
}

.error-text {
  margin: 8px 0 0 0;
  color: #b71c1c;
  font-size: 14px;
  line-height: 1.6;
}

/* ==================== 初始提示 ==================== */
.initial-prompt {
  text-align: center;
  padding: 16px;
  color: #666;
}

.initial-prompt p {
  margin: 0 0 16px 0;
  font-size: 14px;
}

.example-queries {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.example-btn {
  padding: 8px 12px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #555;
  transition: all 0.2s ease;
}

.example-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
  transform: translateX(4px);
}

/* ==================== 滚动条样式 ==================== */
.panel-content::-webkit-scrollbar,
.answer-text::-webkit-scrollbar {
  width: 8px;
}

.panel-content::-webkit-scrollbar-track,
.answer-text::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.panel-content::-webkit-scrollbar-thumb,
.answer-text::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

.panel-content::-webkit-scrollbar-thumb:hover,
.answer-text::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}
</style>
