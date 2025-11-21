/**
 * AI 查询服务
 * 封装与 sight_server AI 查询相关的 API 调用
 */

import { get, post } from '@/utils/request'
import API_CONFIG from '@/utils/config'

/**
 * 生成新的会话ID
 */
export const generateSessionId = () => {
  const timestamp = Date.now().toString(36)
  const random = Math.random().toString(36).substr(2, 5)
  return `session_${timestamp}_${random}`
}

/**
 * 执行 AI 查询
 * @param {string} queryText - 查询文本
 * @param {string} sessionId - 会话ID
 * @returns {Promise<object>} 查询结果
 */
export const executeAIQuery = async (queryText, sessionId) => {
  try {
    console.log('[DEBUG executeAIQuery] 查询文本:', queryText)
    console.log('[DEBUG executeAIQuery] 会话ID:', sessionId)

    const url = API_CONFIG.buildURL(API_CONFIG.endpoints.aiQuery.query, true)
    console.log('[DEBUG executeAIQuery] 请求URL:', url)

    const response = await get(url, {
      q: queryText.trim(),
      include_sql: true,
      conversation_id: sessionId
    })

    console.log('[DEBUG executeAIQuery] 响应数据:', response)

    // 返回标准化的结果
    return {
      success: true,
      status: response.status || 'success',
      answer: response.answer || '',
      message: response.message || '',
      count: response.count || 0,
      data: response.data || [],
      intent_info: response.intent_info || null,
      interrupt_info: response.interrupt_info || null,
      sql: response.sql || null,
      execution_time: response.execution_time || null,
      conversation_id: response.conversation_id || sessionId
    }
  } catch (error) {
    console.error('[ERROR executeAIQuery] 查询失败:', error)
    return {
      success: false,
      status: 'error',
      error: error.message || '查询失败',
      message: error.message || '查询失败，请重试'
    }
  }
}

/**
 * 继续执行被中断的查询（clarify 后）
 * @param {string} clarifiedQuery - clarify 后的查询文本
 * @param {string} sessionId - 会话ID
 * @returns {Promise<object>} 查询结果
 */
export const resumeAIQuery = async (clarifiedQuery, sessionId) => {
  try {
    console.log('[DEBUG resumeAIQuery] clarify 后的查询:', clarifiedQuery)
    console.log('[DEBUG resumeAIQuery] 会话ID:', sessionId)

    const url = API_CONFIG.buildURL(API_CONFIG.endpoints.aiQuery.query + '/resume', true)
    console.log('[DEBUG resumeAIQuery] 请求URL:', url)

    const response = await post(url, {
      conversation_id: sessionId,
      clarified_query: clarifiedQuery.trim(),
      include_sql: true
    })

    console.log('[DEBUG resumeAIQuery] 响应数据:', response)

    return {
      success: true,
      status: response.status || 'success',
      answer: response.answer || '',
      message: response.message || '',
      count: response.count || 0,
      data: response.data || [],
      intent_info: response.intent_info || null,
      sql: response.sql || null,
      execution_time: response.execution_time || null,
      conversation_id: response.conversation_id || sessionId
    }
  } catch (error) {
    console.error('[ERROR resumeAIQuery] 继续查询失败:', error)
    return {
      success: false,
      status: 'error',
      error: error.message || '继续查询失败',
      message: error.message || '继续查询失败，请重试'
    }
  }
}

/**
 * 获取查询类型的中文名称
 * @param {string} intentType - 查询类型
 */
export const getIntentTypeName = (intentType) => {
  const typeMap = {
    'query': '数据查询',
    'summary': '统计汇总'
  }
  return typeMap[intentType] || intentType
}

export default {
  generateSessionId,
  executeAIQuery,
  resumeAIQuery,
  getIntentTypeName
}
