<template>
  <div v-if="visible" class="feature-popup" :style="popupStyle">
    <!-- 标题栏 -->
    <div class="popup-header">
      <h3>{{ title }}</h3>
      <button class="close-btn" @click="handleClose" title="关闭">×</button>
    </div>

    <!-- 内容区域 -->
    <div class="popup-content">
      <!-- 属性列表 -->
      <div v-if="properties && Object.keys(validProperties).length > 0" class="properties-list">
        <div
          v-for="[key, value] in Object.entries(validProperties)"
          :key="key"
          class="property-item"
        >
          <span class="property-key">{{ key }}</span>
          <span class="property-value">{{ formatValue(value) }}</span>
        </div>
      </div>

      <!-- 无属性提示 -->
      <div v-else class="empty-message">
        暂无属性信息
      </div>

      <!-- 属性数量统计 -->
      <div class="properties-count">
        共 {{ Object.keys(validProperties).length }} 个属性
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'FeaturePopup',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    properties: {
      type: Object,
      default: () => ({})
    },
    title: {
      type: String,
      default: '要素属性'
    }
  },
  emits: ['close', 'spot-click'],
  setup(props, { emit }) {
    // 过滤内部属性
    const internalKeys = [
      // OpenLayers 内部属性
      'geometry', 'id', 'features', 'ol_uid', 'revision_', 'disposed',
      'eventTarget_', 'listeners_', 'pendingRemovals_', 'dispatching_',
      'geometryChangeKey_', 'geometryName_', 'id_', 'styleFunction_', 'style_',

      // 自定义控制属性
      'visible', 'imageLoadingStarted', 'hasImageStyle', 'cachedImageUrl',

      // 聚合相关属性
      'clusteredFeatures', 'featureCount', 'levelDistribution',
      'isSingleFeatureCluster', 'originalFeature',

      // 其他内部属性
      'values_', 'changed', 'ol_lat', 'ol_lon', 'ol_sketch', 'ol_uid',

      // 事件相关属性
      'on', 'once', 'un'
    ]

    // 计算有效属性
    const validProperties = computed(() => {
      if (!props.properties) return {}

      const filtered = {}
      Object.entries(props.properties).forEach(([key, value]) => {
        // 排除内部属性
        if (internalKeys.includes(key)) return

        // 排除以 _ 开头的属性
        if (key.startsWith('_')) return

        // 排除包含 'ol_' 的属性
        if (key.includes('ol_')) return

        filtered[key] = value
      })

      return filtered
    })

    // 格式化值的显示
    const formatValue = (value) => {
      if (value === null || value === undefined) {
        return '空值'
      }

      if (typeof value === 'object') {
        if (Array.isArray(value)) {
          return value.length > 0 ? JSON.stringify(value) : '空数组'
        }
        return JSON.stringify(value)
      }

      return value.toString()
    }

    // 处理关闭事件
    const handleClose = () => {
      emit('close')
    }

    // 计算弹窗样式
    const popupStyle = computed(() => ({
      display: props.visible ? 'block' : 'none'
    }))

    return {
      validProperties,
      formatValue,
      handleClose,
      popupStyle
    }
  }
}
</script>

<style scoped>
.feature-popup {
  position: absolute;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15), 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e0e0e0;
  max-width: 350px;
  max-height: 280px;
  overflow: hidden;
  z-index: 9999;
  color: #2c3e50;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  pointer-events: auto;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #3498db;
}

.popup-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.close-btn {
  background: #e74c3c;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  cursor: pointer;
  font-size: 18px;
  font-weight: bold;
  color: white;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #c0392b;
  transform: scale(1.1);
}

.popup-content {
  max-height: 200px;
  overflow-y: auto;
  padding-right: 5px;
  scrollbar-width: thin;
  scrollbar-color: #bdc3c7 #ecf0f1;
}

.popup-content::-webkit-scrollbar {
  width: 6px;
}

.popup-content::-webkit-scrollbar-track {
  background: #ecf0f1;
  border-radius: 3px;
}

.popup-content::-webkit-scrollbar-thumb {
  background: #bdc3c7;
  border-radius: 3px;
}

.popup-content::-webkit-scrollbar-thumb:hover {
  background: #95a5a6;
}

.properties-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.property-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #3498db;
  transition: all 0.2s ease;
  gap: 15px;
}

.property-item:hover {
  background: #e8f4fd;
  transform: translateX(2px);
}

.property-key {
  font-weight: 600;
  color: #2c3e50;
  font-size: 13px;
  min-width: 80px;
  max-width: 120px;
  flex-shrink: 0;
  word-break: break-word;
  line-height: 1.4;
}

.property-value {
  color: #34495e;
  font-size: 13px;
  word-break: break-word;
  text-align: left;
  flex: 1;
  min-width: 150px;
  line-height: 1.4;
  background: rgba(255, 255, 255, 0.7);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.empty-message {
  text-align: center;
  color: #7f8c8d;
  font-style: italic;
  padding: 20px;
}

.properties-count {
  text-align: center;
  font-size: 11px;
  color: #95a5a6;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #ecf0f1;
}
</style>
