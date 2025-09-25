<template>
  <div class="spatial-table-fetcher">
    <div class="header">
      <h2>空间数据表管理</h2>
      <button
        @click="fetchTableNames"
        :disabled="isLoadingTables"
        class="fetch-btn"
      >
        <i class="fas fa-sync-alt" :class="{ 'fa-spin': isLoadingTables }"></i>
        {{ isLoadingTables ? "加载中..." : "获取表名称" }}
      </button>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      {{ errorMessage }}
    </div>

    <!-- 查询框 -->
    <div class="query-section">
      <h3>空间数据查询</h3>
      <div class="query-form">
        <div class="form-group">
          <label for="queryTable">选择数据表:</label>
          <select id="queryTable" v-model="queryParams.tableName" class="form-select" :disabled="tableNames.length === 0">
            <option value="">请选择表</option>
            <option v-for="table in tableNames" :key="table" :value="table">{{ table }}</option>
          </select>
          <div v-if="tableNames.length === 0" class="table-hint">
            <i class="fas fa-info-circle"></i>
            请先点击"获取表名称"按钮加载数据表列表
          </div>
        </div>

        <div class="form-group">
          <label for="queryTableCondition">表查询:</label>
          <input
            id="queryTableCondition"
            v-model="queryParams.tableCondition"
            type="text"
            placeholder="输入表名关键字（支持模糊查询）"
            class="form-input"
          >
        </div>

        <div class="form-group">
          <label for="queryName">名称查询:</label>
          <input
            id="queryName"
            v-model="queryParams.name"
            type="text"
            placeholder="输入名称关键字"
            class="form-input"
          >
        </div>

        <div class="form-group">
          <label for="queryCategories">分类查询:</label>
          <input
            id="queryCategories"
            v-model="queryParams.categories"
            type="text"
            placeholder="输入分类关键字"
            class="form-input"
          >
        </div>

        <div class="form-group">
          <label>空间范围查询:</label>
          <div class="spatial-query-options">
            <label class="radio-label">
              <input
                type="radio"
                v-model="queryParams.spatialType"
                value="point"
                class="radio-input"
              >
              点坐标
            </label>
            <label class="radio-label">
              <input
                type="radio"
                v-model="queryParams.spatialType"
                value="rectangle"
                class="radio-input"
              >
              矩形范围
            </label>
          </div>
        </div>

        <div v-if="queryParams.spatialType === 'point'" class="form-group">
          <label for="queryPoint">点坐标 (经度,纬度):</label>
          <input
            id="queryPoint"
            v-model="queryParams.point"
            type="text"
            placeholder="例如: 114.0,30.5"
            class="form-input"
          >
        </div>

        <div v-if="queryParams.spatialType === 'rectangle'" class="form-group">
          <label for="queryBounds">矩形范围 (minLon,minLat,maxLon,maxLat):</label>
          <input
            id="queryBounds"
            v-model="queryParams.bounds"
            type="text"
            placeholder="例如: 113.5,30.0,114.5,31.0"
            class="form-input"
          >
        </div>

        <div class="form-group">
          <label for="queryLimit">返回记录数:</label>
          <input
            id="queryLimit"
            v-model="queryParams.limit"
            type="number"
            min="1"
            max="1000"
            placeholder="默认100"
            class="form-input"
          >
        </div>

        <div class="query-actions">
          <button
            @click="executeQuery"
            :disabled="!queryParams.tableName || isQuerying"
            class="query-btn"
          >
            <i class="fas fa-search" :class="{ 'fa-spin': isQuerying }"></i>
            {{ isQuerying ? "查询中..." : "执行查询" }}
          </button>
          <button
            @click="resetQuery"
            class="reset-btn"
          >
            <i class="fas fa-redo"></i>
            重置条件
          </button>
        </div>
      </div>
    </div>

    <!-- 表名称列表 -->
    <div v-if="tableNames.length > 0" class="table-list">
      <div class="list-header">
        <span class="table-name-header">表名称</span>
        <span class="action-header">操作</span>
      </div>

      <div v-for="table in tableNames" :key="table" class="table-item">
        <div class="table-name">{{ table }}</div>
        <button
          @click="fetchTableGeoJSON(table)"
          :disabled="isLoadingGeoJSON[table]"
          class="geojson-btn"
        >
          <i
            class="fas fa-download"
            :class="{ 'fa-spin': isLoadingGeoJSON[table] }"
          ></i>
          {{ isLoadingGeoJSON[table] ? "获取中..." : "获取GeoJSON" }}
        </button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!isLoadingTables && !errorMessage" class="empty-state">
      <i class="fas fa-database"></i>
      <p>尚未加载任何空间数据表</p>
      <p>点击"获取表名称"按钮加载数据</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoadingTables && !errorMessage" class="loading-state">
      <div class="spinner"></div>
      <p>正在获取空间表名称...</p>
    </div>

    <!-- GeoJSON 结果区域 -->
    <div
      v-if="selectedTable && geojsonData[selectedTable]"
      class="geojson-result"
    >
      <div class="result-header">
        <h3>{{ selectedTable }} 的 GeoJSON 数据</h3>
        <button @click="clearGeoJSON(selectedTable)" class="clear-btn">
          <i class="fas fa-times"></i> 清除
        </button>
      </div>
      <pre class="geojson-pre">{{ formattedGeoJSON(selectedTable) }}</pre>
      <button @click="copyGeoJSON(selectedTable)" class="copy-btn">
        <i class="fas fa-copy"></i> 复制GeoJSON
      </button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, watch} from "vue";
import { getCurrentInstance } from "vue";
import { provide } from 'vue';
import { inject } from 'vue';

export default {
  name: "SpatialTableFetcher",
  props: {
    // 用于获取表名称的API地址
    tableNamesUrl: {
      type: String,
      required: true,
    },
    // 用于获取GeoJSON的API地址，需包含{tableName}占位符
    geojsonUrl: {
      type: String,
      required: true,
    },
    // 请求超时时间(毫秒)
    timeout: {
      type: Number,
      default: 10000,
    },
  },
  setup(props) {
    // 状态管理
    const tableNames = ref([]);
    const isLoadingTables = ref(false);
    const errorMessage = ref("");
    const geojsonData = reactive({});
    const isLoadingGeoJSON = reactive({});
    const selectedTable = ref("");
    const copySuccess = ref(false);
    
    // 查询相关状态
    const queryParams = reactive({
      tableName: "",
      tableCondition: "", // 表查询条件
      name: "",
      categories: "",
      spatialType: "point", // point 或 rectangle
      point: "", // 点坐标：经度,纬度
      bounds: "", // 矩形范围：minLon,minLat,maxLon,maxLat
      limit: 100
    });
    const isQuerying = ref(false);
    const queryResults = reactive({});
  // 修改为显式注入
  const mapUtilsContainer = inject('mapUtilsInstance', null);
  const mapUtils = ref(null);
  const isMapUtilsReady = ref(false);
  // 监听 mapUtilsContainer 实例的变化
  watch(
    () => mapUtilsContainer?.instance,
    (newInstance) => {
      if (newInstance) {
        mapUtils.value = newInstance;
        // 验证实例有效性
        if (mapUtils.value && mapUtils.value.map) {
          isMapUtilsReady.value = true;
          console.log("mapUtils 实例准备就绪");
        } else {
          errorMessage.value = "mapUtils 实例无效，地图未初始化";
        }
      }
    },
    { immediate: true }
  );

    onMounted(() => {
  // 组件挂载后检查 mapUtils 是否存在
  if (!mapUtils) {
    console.error('无法获取 mapUtils，请检查组件层级或注入逻辑');
    return;
  }
  // 验证 mapUtils 是否有效（例如检查是否有 map 实例）
  if (mapUtils.map) {
    isMapUtilsReady.value = true;
    console.log('mapUtils 初始化成功');
  } else {
    console.error('mapUtils 实例无效，地图未正确初始化');
  }
});
    // 获取表名称列表
    const fetchTableNames = async () => {
      // 重置状态
      tableNames.value = [];
      isLoadingTables.value = true;
      errorMessage.value = "";

      try {
        // 创建超时控制
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), props.timeout);

        const response = await fetch(props.tableNamesUrl, {
          signal: controller.signal,
          method: "GET",
          headers: {
            Accept: "application/json",
          },
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(
            `请求失败: ${response.status} ${response.statusText}`
          );
        }

        const data = await response.json();

        // 验证返回数据格式
        if (Array.isArray(data)) {
          tableNames.value = data;
          // 初始化加载状态
          data.forEach((table) => {
            isLoadingGeoJSON[table] = false;
          });
        } else {
          throw new Error("返回的数据不是有效的数组");
        }
      } catch (error) {
        if (error.name === "AbortError") {
          errorMessage.value = `请求超时（${props.timeout / 1000}秒）`;
        } else {
          errorMessage.value = `获取表名称失败: ${error.message}`;
        }
        console.error("获取表名称错误:", error);
      } finally {
        isLoadingTables.value = false;
      }
    };

    // 获取指定表的GeoJSON数据
    const fetchTableGeoJSON = async (tableName) => {
      if (!tableName) return;
        if (!isMapUtilsReady.value) {
    errorMessage.value = '地图工具未准备好，请稍后再试';
    return;}

      

      // 重置状态
      errorMessage.value = "";
      isLoadingGeoJSON[tableName] = true;

      try {
        // 替换URL中的占位符
        const url = props.geojsonUrl.replace(
          "{tableName}",
          encodeURIComponent(tableName)
        );

        // 创建超时控制
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), props.timeout);

        const response = await fetch(url, {
          signal: controller.signal,
          method: "GET",
          headers: {
            Accept: "application/json",
          },
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(
            `请求失败: ${response.status} ${response.statusText}`
          );
        }

        const data = await response.json();
        geojsonData[tableName] = data;
        selectedTable.value = tableName;
            // 加载GeoJSON到地图
    if (mapUtils) {
      // 可自定义样式
      const styleOptions = {
        fillColor: "rgba(0, 0, 255, 0.2)",
        strokeColor: "#0000FF",
        strokeWidth: 2,
        pointColor: "#FF0000",
        pointRadius: 6
      };
      
      // 调用mapUtils的方法加载图层
      const layer = mapUtils.value.loadGeoJsonLayer(
        data,                // GeoJSON对象
        styleOptions,        // 样式配置
        `${tableName}图层`   // 图层名称
      );
      
      console.log(`成功加载图层: ${tableName}`, layer);
    }
    else {

      console.error("mapUtils实例未找到");

    }
      } catch (error) {
        if (error.name === "AbortError") {
          errorMessage.value = `请求超时（${props.timeout / 1000}秒）`;
        } else {
          errorMessage.value = `获取${tableName}的GeoJSON失败: ${error.message}`;
        }
        console.error(`获取${tableName}的GeoJSON错误:`, error);
      } finally {
        isLoadingGeoJSON[tableName] = false;
      }
    };

    // 清除指定表的GeoJSON数据
    const clearGeoJSON = (tableName) => {
      if (geojsonData[tableName]) {
        delete geojsonData[tableName];
        if (selectedTable.value === tableName) {
          selectedTable.value = "";
        }
      }
    };

    // 格式化GeoJSON数据用于展示
    const formattedGeoJSON = (tableName) => {
      if (geojsonData[tableName]) {
        return JSON.stringify(geojsonData[tableName], null, 2);
      }
      return "";
    };

    // 复制GeoJSON到剪贴板
    const copyGeoJSON = (tableName) => {
      if (geojsonData[tableName]) {
        const text = JSON.stringify(geojsonData[tableName], null, 2);
        navigator.clipboard
          .writeText(text)
          .then(() => {
            copySuccess.value = true;
            setTimeout(() => (copySuccess.value = false), 2000);
          })
          .catch((err) => {
            console.error("复制失败:", err);
            errorMessage.value = "复制到剪贴板失败，请手动复制";
            setTimeout(() => (errorMessage.value = ""), 3000);
          });
      }
    };

    // 执行查询
    const executeQuery = async () => {
      if (!queryParams.tableName) {
        errorMessage.value = "请选择要查询的数据表";
        return;
      }

      if (!isMapUtilsReady.value) {
        errorMessage.value = "地图工具未准备好，请稍后再试";
        return;
      }

      isQuerying.value = true;
      errorMessage.value = "";

      try {
        // 构建查询参数
        const params = new URLSearchParams();
        
        // 添加查询条件
        if (queryParams.tableCondition) {
          params.append('table', queryParams.tableCondition);
        }
        if (queryParams.name) {
          params.append('name', queryParams.name);
        }
        if (queryParams.categories) {
          params.append('categories', queryParams.categories);
        }
        if (queryParams.limit) {
          params.append('limit', queryParams.limit.toString());
        }

        // 添加空间查询条件
        if (queryParams.spatialType === 'point' && queryParams.point) {
          const [lng, lat] = queryParams.point.split(',').map(coord => coord.trim());
          if (lng && lat) {
            params.append('lng', lng);
            params.append('lat', lat);
            params.append('radius', '1000'); // 默认1公里半径
          }
        } else if (queryParams.spatialType === 'rectangle' && queryParams.bounds) {
          const [minLng, minLat, maxLng, maxLat] = queryParams.bounds.split(',').map(coord => coord.trim());
          if (minLng && minLat && maxLng && maxLat) {
            params.append('bounds', `${minLng},${minLat},${maxLng},${maxLat}`);
          }
        }

        // 构建查询URL - 使用自然语言查询API
        const queryText = buildNaturalLanguageQuery();
        const url = `http://localhost:8001/nlq/${encodeURIComponent(queryText)}?${params.toString()}`;

        // 创建超时控制
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), props.timeout);

        const response = await fetch(url, {
          signal: controller.signal,
          method: "GET",
          headers: {
            Accept: "application/json",
          },
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`查询失败: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (data.status === 'success' && data.geojson) {
          // 存储查询结果
          queryResults[queryParams.tableName] = data;
          selectedTable.value = queryParams.tableName;
          
          // 加载GeoJSON到地图
          const styleOptions = {
            fillColor: "rgba(255, 165, 0, 0.3)", // 橙色，区别于普通加载
            strokeColor: "#FF8C00",
            strokeWidth: 2,
            pointColor: "#FF4500",
            pointRadius: 8
          };
          
          const layer = mapUtils.value.loadGeoJsonLayer(
            data.geojson,
            styleOptions,
            `${queryParams.tableName}查询结果`
          );
          
          console.log(`查询结果加载成功: ${queryParams.tableName}`, layer);
        } else {
          throw new Error(data.error || "查询返回的数据格式不正确");
        }
      } catch (error) {
        if (error.name === "AbortError") {
          errorMessage.value = `查询超时（${props.timeout / 1000}秒）`;
        } else {
          errorMessage.value = `查询失败: ${error.message}`;
        }
        console.error("查询错误:", error);
      } finally {
        isQuerying.value = false;
      }
    };

    // 构建自然语言查询
    const buildNaturalLanguageQuery = () => {
      let query = `查询${queryParams.tableName}表中的数据`;
      
      if (queryParams.tableCondition) {
        query += `，表名包含"${queryParams.tableCondition}"`;
      }
      if (queryParams.name) {
        query += `，名称包含"${queryParams.name}"`;
      }
      if (queryParams.categories) {
        query += `，分类包含"${queryParams.categories}"`;
      }
      if (queryParams.spatialType === 'point' && queryParams.point) {
        query += `，在点${queryParams.point}附近`;
      } else if (queryParams.spatialType === 'rectangle' && queryParams.bounds) {
        query += `，在矩形范围${queryParams.bounds}内`;
      }
      if (queryParams.limit) {
        query += `，返回${queryParams.limit}条记录`;
      }
      
      return query;
    };

    // 重置查询条件
    const resetQuery = () => {
      queryParams.tableName = "";
      queryParams.tableCondition = "";
      queryParams.name = "";
      queryParams.categories = "";
      queryParams.spatialType = "point";
      queryParams.point = "";
      queryParams.bounds = "";
      queryParams.limit = 100;
      errorMessage.value = "";
    };

    return {
      tableNames,
      isLoadingTables,
      errorMessage,
      geojsonData,
      isLoadingGeoJSON,
      selectedTable,
      copySuccess,
      queryParams,
      isQuerying,
      queryResults,
      fetchTableNames,
      fetchTableGeoJSON,
      clearGeoJSON,
      formattedGeoJSON,
      copyGeoJSON,
      executeQuery,
      resetQuery,
    };
  },
};
</script>

<style scoped>
.spatial-table-fetcher {
  position: absolute; 
  top: 30px; 
  left: 0px; /* 保持靠右显示 */
  z-index: 2000; 
  width: 400px; /* 增加宽度以适应查询框 */
  padding: 20px;
  background-color: rgba(255, 255, 255, 0.95); /* 轻微透明，增强悬浮感 */
  border-radius: 8px; /* 圆角更明显 */
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15); /* 增强阴影，突出悬浮效果 */
  max-height: calc(100vh - 100px);
  overflow-y: auto;
  transition: all 0.3s ease; /* 平滑过渡效果 */
  backdrop-filter: blur(5px); /* 背景模糊（可选，增强层次感） */
}

/* 鼠标悬停时的强化效果 */
.spatial-table-fetcher:hover {
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2); /* 阴影加深 */
  transform: translateY(-2px); /* 轻微上浮 */
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

.fetch-btn {
  background-color: #42b983;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.3s;
}

.fetch-btn:hover:not(:disabled) {
  background-color: #359e75;
}

.fetch-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.error-message {
  background-color: #fff0f0;
  border-left: 4px solid #ff4d4f;
  padding: 10px 15px;
  margin-bottom: 20px;
  color: #ff4d4f;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 查询框样式 */
.query-section {
  margin-bottom: 25px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.query-section h3 {
  margin: 0 0 15px 0;
  color: #495057;
  font-size: 1.2rem;
  font-weight: 600;
}

.query-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-weight: 500;
  color: #495057;
  font-size: 0.9rem;
}

.form-input,
.form-select {
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: #42b983;
  box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.1);
}

.table-hint {
  font-size: 0.8rem;
  color: #666;
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  background-color: #f8f9fa;
  padding: 8px;
  border-radius: 4px;
  border-left: 3px solid #42b983;
}

.table-hint i {
  color: #42b983;
}

.spatial-query-options {
  display: flex;
  gap: 15px;
  margin-top: 5px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-weight: normal;
}

.radio-input {
  margin: 0;
}

.query-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.query-btn {
  background-color: #ff6b35;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.3s;
  flex: 1;
  justify-content: center;
}

.query-btn:hover:not(:disabled) {
  background-color: #e55a2b;
}

.query-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.reset-btn {
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.3s;
}

.reset-btn:hover {
  background-color: #545b62;
}

.table-list {
  margin-bottom: 30px;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.list-header {
  display: flex;
  background-color: #f5f5f5;
  padding: 12px 15px;
  font-weight: 600;
  color: #555;
  border-bottom: 1px solid #eee;
}

.table-name-header {
  flex: 1;
}

.action-header {
  width: 140px;
  text-align: center;
}

.table-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  border-bottom: 1px solid #eee;
  transition: background-color 0.2s;
}

.table-item:last-child {
  border-bottom: none;
}

.table-item:hover {
  background-color: #fafafa;
}

.table-name {
  flex: 1;
  color: #333;
}

.geojson-btn {
  background-color: #2196f3;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.3s;
  width: 140px;
  justify-content: center;
}

.geojson-btn:hover:not(:disabled) {
  background-color: #0c7cd5;
}

.geojson-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #888;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 15px;
  color: #ddd;
}

.empty-state p {
  margin: 5px 0;
}

.loading-state {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 15px;
  border: 4px solid rgba(66, 185, 131, 0.2);
  border-left-color: #42b983;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.geojson-result {
  margin-top: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 6px;
  border: 1px solid #eee;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.result-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.2rem;
}

.clear-btn {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: color 0.2s, background-color 0.2s;
}

.clear-btn:hover {
  color: #ff4d4f;
  background-color: #fff0f0;
}

.geojson-pre {
  max-height: 400px;
  overflow: auto;
  padding: 15px;
  background-color: #2d2d2d;
  color: #f8f8f2;
  border-radius: 4px;
  font-family: "Consolas", "Monaco", monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.copy-btn {
  margin-top: 10px;
  background-color: #673ab7;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.3s;
}

.copy-btn:hover {
  background-color: #512da8;
}

.copy-btn.copied {
  background-color: #4caf50;
}
</style>
