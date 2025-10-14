<template>
  <div v-if="visible" class="modal-overlay" @click="handleOverlayClick">
    <div class="modal-content" @click.stop>
      <!-- 弹窗头部 -->
      <div class="modal-header">
        <h2>修改景点信息</h2>
        <button @click="close" class="close-button">×</button>
      </div>

      <!-- 弹窗内容 -->
      <div class="modal-body">
        <!-- 基本信息 -->
        <div class="form-section">
          <h3>基本信息</h3>
          <div class="form-grid">
            <div class="form-group">
              <label for="name">景点名称</label>
              <input
                id="name"
                v-model="formData.name"
                type="text"
                placeholder="请输入景点名称"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="level">景区等级</label>
              <select
                id="level"
                v-model="formData.level"
                class="form-select"
              >
                <option value="">请选择等级</option>
                <option value="5A">5A</option>
                <option value="4A">4A</option>
                <option value="3A">3A</option>
                <option value="2A">2A</option>
                <option value="1A">1A</option>
              </select>
            </div>
            <div class="form-group full-width">
              <label for="address">地址</label>
              <input
                id="address"
                v-model="formData.地址"
                type="text"
                placeholder="请输入详细地址"
                class="form-input"
              />
            </div>
          </div>
        </div>

        <!-- 坐标信息 -->
        <div class="form-section">
          <h3>坐标信息</h3>
          <div class="form-grid">
            <div class="form-group">
              <label for="lng_wgs84">经度 (WGS84)</label>
              <input
                id="lng_wgs84"
                v-model="formData.lng_wgs84"
                type="number"
                step="0.000001"
                placeholder="0.000000"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="lat_wgs84">纬度 (WGS84)</label>
              <input
                id="lat_wgs84"
                v-model="formData.lat_wgs84"
                type="number"
                step="0.000001"
                placeholder="0.000000"
                class="form-input"
              />
            </div>
            <!-- <div class="form-group">
              <label for="所属城市">所属城市</label>
              <input
                id="所属城市"
                v-model="formData.所属城市"
                type="text"
                placeholder="请输入城市名称"
                class="form-input"
              />
            </div> -->
            <!-- <div class="form-group">
              <label for="所属区县">所属区县</label>
              <input
                id="所属区县"
                v-model="formData.所属区县"
                type="text"
                placeholder="请输入区县名称"
                class="form-input"
              />
            </div> -->
          </div>
        </div>

        <!-- 详细信息 -->
        <div class="form-section">
          <h3>详细信息</h3>
          <div class="form-grid">
            <div class="form-group">
              <label for="评分">评分</label>
              <input
                id="评分"
                v-model="formData.评分"
                type="text"
                placeholder="请输入评分"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="门票">门票价格</label>
              <input
                id="门票"
                v-model="formData.门票"
                type="text"
                placeholder="请输入门票价格"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="开放时间">开放时间</label>
              <input
                id="开放时间"
                v-model="formData.开放时间"
                type="text"
                placeholder="请输入开放时间"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="建议游玩时间">建议游玩时间</label>
              <input
                id="建议游玩时间"
                v-model="formData.建议游玩时间"
                type="text"
                placeholder="请输入建议游玩时间"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="建议季节">建议季节</label>
              <input
                id="建议季节"
                v-model="formData.建议季节"
                type="text"
                placeholder="请输入建议季节"
                class="form-input"
              />
            </div>
            <div class="form-group full-width">
              <label for="小贴士">小贴士</label>
              <textarea
                id="小贴士"
                v-model="formData.小贴士"
                placeholder="请输入游玩小贴士"
                class="form-textarea"
                rows="3"
              ></textarea>
            </div>
            <div class="form-group full-width">
              <label for="介绍">景点介绍</label>
              <textarea
                id="介绍"
                v-model="formData.介绍"
                placeholder="请输入景点详细介绍"
                class="form-textarea"
                rows="4"
              ></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- 弹窗底部 -->
      <div class="modal-footer">
        <button @click="close" class="cancel-button">取消</button>
        <button @click="save" class="save-button" :disabled="loading">
          {{ loading ? '保存中...' : '保存' }}
        </button>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, computed } from 'vue'
import axios from 'axios'
import API_CONFIG from '../config/api.js'

export default {
  name: 'TouristSpotEditModal',
  props: {
    visible: {
      type: Boolean,
      required: true
    },
    spot: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const formData = ref({})
    const loading = ref(false)
    const error = ref('')

    // 初始化表单数据
    const initializeFormData = () => {
      // 优先从 a_sight 或根对象的 coordinates 数组获取坐标
      const spotCoordinates = props.spot.a_sight?.coordinates || props.spot.coordinates;

      let lng = props.spot.lng_wgs84;
      let lat = props.spot.lat_wgs84;

      if (Array.isArray(spotCoordinates) && spotCoordinates.length >= 2) {
        lng = spotCoordinates[0];
        lat = spotCoordinates[1];
      }

      formData.value = {
        // tourist_spot 表字段
        name: props.spot.name || '',
        地址: props.spot.地址 || '',
        介绍: props.spot.介绍 || '',
        开放时间: props.spot.开放时间 || '',
        评分: props.spot.评分 || '',
        门票: props.spot.门票 || '',
        建议游玩时间: props.spot.建议游玩时间 || '',
        建议季节: props.spot.建议季节 || '',
        小贴士: props.spot.小贴士 || '',

        // a_sight 表字段
        level: props.spot.level || '',
        lng_wgs84: lng || '',
        lat_wgs84: lat || '',
      }
    }

    // 监听景点数据变化
    watch(() => props.spot, () => {
      if (props.visible) {
        initializeFormData()
        error.value = ''
      }
    }, { immediate: true })

    // 验证表单
    const validateForm = () => {
      if (!formData.value.name?.trim()) {
        error.value = '景点名称不能为空'
        return false
      }
      if (!formData.value.地址?.trim()) {
        error.value = '地址不能为空'
        return false
      }
      if (formData.value.lng_wgs84 && isNaN(parseFloat(formData.value.lng_wgs84))) {
        error.value = '经度必须是有效数字'
        return false
      }
      if (formData.value.lat_wgs84 && isNaN(parseFloat(formData.value.lat_wgs84))) {
        error.value = '纬度必须是有效数字'
        return false
      }
      return true
    }

    // 保存景点信息
    const save = async () => {
      if (!validateForm()) {
        return
      }

      loading.value = true
      error.value = ''

      try {
        // 构建请求数据
        const requestData = {
          // tourist_spot 表数据
          tourist_spot: {
            name: formData.value.name.trim(),
            地址: formData.value.地址.trim(),
            介绍: formData.value.介绍?.trim() || null,
            开放时间: formData.value.开放时间?.trim() || null,
            评分: formData.value.评分?.trim() || null,
            门票: formData.value.门票?.trim() || null,
            建议游玩时间: formData.value.建议游玩时间?.trim() || null,
            建议季节: formData.value.建议季节?.trim() || null,
            小贴士: formData.value.小贴士?.trim() || null
          },
          // a_sight 表数据
          a_sight: {
            name: formData.value.name.trim(),
            level: formData.value.level || null,
            lngWgs84: formData.value.lng_wgs84 ? parseFloat(formData.value.lng_wgs84) : null,
            latWgs84: formData.value.lat_wgs84 ? parseFloat(formData.value.lat_wgs84) : null,
            // 所属城市: formData.value.所属城市?.trim() || null,
            // 所属区县: formData.value.所属区县?.trim() || null
          }
        }

        console.log('发送更新请求:', requestData)

        // 发送更新请求 - 处理没有ID的情况（通过名称更新）
        let updateUrl;
        // 确保 props.spot.id 存在且为字符串再调用 startsWith
        if (props.spot.id && typeof props.spot.id === 'string' && props.spot.id.startsWith('name_')) {
            // 虚拟ID，通过名称更新
            const spotName = props.spot.id.substring(5);
            console.log('通过名称更新景点:', spotName);
            const encodedName = encodeURIComponent(spotName);
            updateUrl = API_CONFIG.buildURL(API_CONFIG.endpoints.touristSpots.updateByName(encodedName));
        } else if (props.spot.id) {
            // 有真实ID（数字类型），使用ID更新
            updateUrl = API_CONFIG.buildURL(API_CONFIG.endpoints.touristSpots.update(props.spot.id));
        } else {
            // 没有ID，通过名称更新
            const spotName = props.spot.name;
            console.log('通过名称更新景点 (无ID):', spotName);
            const encodedName = encodeURIComponent(spotName);
            updateUrl = API_CONFIG.buildURL(API_CONFIG.endpoints.touristSpots.updateByName(encodedName));
        }

        console.log('更新URL:', updateUrl)

        console.log('发送PUT请求到:', updateUrl)
        console.log('请求数据:', JSON.stringify(requestData, null, 2))

        const response = await axios.put(updateUrl, requestData)

        console.log('响应状态:', response.status)
        console.log('响应数据:', response.data)

        if (response.status === 200) {
          console.log('景点更新成功:', response.data)
          emit('save', { ...props.spot, ...formData.value })
          close()
        } else {
          error.value = response.data.message || '保存失败'
        }
      } catch (err) {
        console.error('保存景点失败:', err)
        error.value = err.response?.data?.detail || err.message || '保存失败，请重试'
      } finally {
        loading.value = false
      }
    }

    // 关闭弹窗
    const close = () => {
      emit('close')
    }

    // 点击遮罩层关闭
    const handleOverlayClick = (event) => {
      if (event.target.classList.contains('modal-overlay')) {
        close()
      }
    }

    return {
      formData,
      loading,
      error,
      save,
      close,
      handleOverlayClick
    }
  }
}
</script>

<style scoped>
/* ==================== 弹窗样式 ==================== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.2);
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

/* ==================== 弹窗头部 ==================== */
.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f8f9fa;
  border-radius: 8px 8px 0 0;
}

.modal-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
  font-weight: 600;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  color: #666;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.close-button:hover {
  background: #f0f0f0;
  color: #333;
}

/* ==================== 弹窗内容 ==================== */
.modal-body {
  padding: 24px;
  flex: 1;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 32px;
}

.form-section h3 {
  margin: 0 0 16px 0;
  color: #2c3e50;
  font-size: 16px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 2px solid #4a90e2;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  margin-bottom: 6px;
  color: #555;
  font-size: 14px;
  font-weight: 500;
}

.form-input,
.form-select,
.form-textarea {
  padding: 10px 12px;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.2s ease;
  background: white;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
}

/* ==================== 弹窗底部 ==================== */
.modal-footer {
  padding: 20px 24px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #f8f9fa;
  border-radius: 0 0 8px 8px;
}

.cancel-button {
  padding: 10px 20px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.cancel-button:hover {
  background: #5a6268;
}

.save-button {
  padding: 10px 20px;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.save-button:hover:not(:disabled) {
  background: #357abd;
}

.save-button:disabled {
  background: #a0a0a0;
  cursor: not-allowed;
}

/* ==================== 错误提示 ==================== */
.error-message {
  background: #f8d7da;
  color: #721c24;
  padding: 12px 16px;
  border-radius: 4px;
  margin: 16px 24px;
  border: 1px solid #f5c6cb;
  font-size: 14px;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    margin: 20px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .modal-body {
    padding: 16px;
  }

  .modal-footer {
    padding: 16px;
    flex-direction: column;
  }

  .cancel-button,
  .save-button {
    width: 100%;
  }
}

/* ==================== 滚动条样式 ==================== */
.modal-content::-webkit-scrollbar {
  width: 6px;
}

.modal-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.modal-content::-webkit-scrollbar-thumb {
  background: #4a90e2;
  border-radius: 3px;
}

.modal-content::-webkit-scrollbar-thumb:hover {
  background: #357abd;
}
</style>