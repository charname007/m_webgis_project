<template>
  <div>
    <slot :loading="loading" :error="error" :data="geoJsonData">
      <!-- 默认插槽内容 -->
      <button @click="fetchGeoJson" :disabled="loading">
        {{ loading ? '加载中...' : '获取GeoJSON数据' }}
      </button>
      <div v-if="error" class="error-message">{{ error }}</div>
    </slot>
  </div>
</template>

<script>
import { ref } from 'vue';

export default {
  name: 'GeoJSONFetcher',
  props: {
    url: {
      type: String,
      required: true,
      validator: value => {
        try {
          new URL(value);
          return true;
        } catch {
          return false;
        }
      }
    },
    requestOptions: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    const loading = ref(false);
    const error = ref(null);
    const geoJsonData = ref(null);

    const fetchGeoJson = async () => {
      loading.value = true;
      error.value = null;
      
      try {
        const response = await fetch(props.url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...props.requestOptions.headers
          },
          ...props.requestOptions
        });

        if (!response.ok) {
          throw new Error(`请求失败: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        
        // 验证是否为有效的GeoJSON
        if (!data.type || !data.features) {
          throw new Error('返回的数据不是有效的GeoJSON格式');
        }

        geoJsonData.value = data;
      } catch (err) {
        error.value = err.message;
        console.error('获取GeoJSON数据失败:', err);
      } finally {
        loading.value = false;
      }
    };

    return {
      loading,
      error,
      geoJsonData,
      fetchGeoJson
    };
  }
};
</script>

<style scoped>
.error-message {
  color: red;
  margin-top: 8px;
}

button {
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>
