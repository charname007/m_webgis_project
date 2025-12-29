<template>
  <div class="spatial-table-fetcher" :class="{ 'collapsed': isCollapsed }" :style="positionStyle"
    @mousedown="startDrag">
    <div class="header">
      <div class="header-left">
        <h2>空间数据表管理</h2>
        <!-- <div class="drag-handle">
          <i class="fas fa-arrows-alt"></i>
        </div> -->
      </div>
      <div class="header-right">

        <button @click="fetchTableNames" :disabled="isLoadingTables" class="fetch-btn">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': isLoadingTables }"></i>
          {{ isLoadingTables ? "加载中..." : "获取表名称" }}
        </button>
        <button @click="toggleCollapse" class="collapse-btn" :title="isCollapsed ? '展开' : '折叠'">
          —— <i class="fas" :class="isCollapsed ? 'fa-chevron-down' : 'fa-chevron-up'"></i>
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMessage" class="error-message">
      <i class="fas fa-exclamation-circle"></i>
      {{ errorMessage }}
    </div>

    <!-- 地图工具状态提示 -->
    <div v-if="!isMapUtilsReady" class="map-utils-status">
      <div class="status-warning">
        <i class="fas fa-exclamation-triangle"></i>
        <span>地图工具未就绪</span>
        <button @click="enableMapUtilsManually" class="enable-btn" :disabled="isMapUtilsManuallyEnabled">
          <i class="fas fa-power-off"></i>
          {{ isMapUtilsManuallyEnabled ? "已手动启用" : "手动启用地图工具" }}
        </button>
      </div>
    </div>

    <!-- 查询框 -->
    <div class="query-section">
      <h3>空间数据查询</h3>
      <div class="query-form">
        <div class="form-group">
          <label for="queryTable">数据表:</label>
          <div class="table-input-container">
            <div class="input-with-dropdown">
              <input id="queryTable" v-model="queryParams.tableName" type="text" placeholder="直接输入表名或从下拉列表选择"
                class="table-input" @focus="showTableSuggestions = true" @blur="hideTableSuggestions">
              <i class="fas fa-chevron-down dropdown-icon" @click="toggleTableSuggestions"></i>

              <!-- 下拉建议列表 -->
              <div v-if="showTableSuggestions && tableNames.length > 0" class="table-suggestions">
                <div v-for="table in filteredTableNames" :key="table" class="suggestion-item"
                  @mousedown="selectTable(table)">
                  {{ table }}
                </div>
                <div v-if="filteredTableNames.length === 0" class="no-suggestions">
                  无匹配的表名
                </div>
              </div>
            </div>

            <!-- 表名提示信息 -->
            <div v-if="tableNames.length === 0" class="table-hint">
              <i class="fas fa-info-circle"></i>
              可手动输入表名，或点击"获取表名称"按钮加载表列表
            </div>
            <div v-if="tableNames.length > 0 && queryParams.tableName && !tableNames.includes(queryParams.tableName)"
              class="table-warning">
              <i class="fas fa-exclamation-triangle"></i>
              当前输入的表名不在已加载的列表中，但可以继续查询
            </div>
            <div v-if="tableNames.length > 0 && queryParams.tableName && tableNames.includes(queryParams.tableName)"
              class="table-success">
              <i class="fas fa-check-circle"></i>
              表名已确认
            </div>
          </div>
        </div>

        <div class="form-group">
          <label for="queryName">名称查询:</label>
          <input id="queryName" v-model="queryParams.name" type="text" placeholder="输入名称关键字" class="form-input">
        </div>

        <div class="form-group">
          <label for="queryCategories">分类查询:</label>
          <input id="queryCategories" v-model="queryParams.categories" type="text" placeholder="输入分类关键字"
            class="form-input">
        </div>

        <div class="form-group">
          <label>空间范围查询:</label>
          <div class="spatial-query-options">
            <label class="radio-label">
              <input type="radio" v-model="queryParams.spatialType" value="point" class="radio-input">
              点坐标
            </label>
            <label class="radio-label">
              <input type="radio" v-model="queryParams.spatialType" value="rectangle" class="radio-input">
              矩形范围
            </label>
          </div>
        </div>

        <div v-if="queryParams.spatialType === 'point'" class="form-group">
          <label for="queryPoint">点坐标 (经度,纬度):</label>
          <div class="coordinate-input-group">
            <input id="queryPoint" v-model="queryParams.point" type="text" placeholder="例如: 114.0,30.5"
              class="form-input">
            <button @click="startPointSelection"
              :disabled="!(isMapUtilsReady || isMapUtilsManuallyEnabled) || isSelectingPoint" class="map-select-btn">
              <i class="fas fa-map-marker-alt" :class="{ 'fa-spin': isSelectingPoint }"></i>
              {{ isSelectingPoint ? "选择中..." : "从地图选点" }}
            </button>
          </div>
        </div>

        <div v-if="queryParams.spatialType === 'rectangle'" class="form-group">
          <label for="queryBounds">矩形范围 (minLon,minLat,maxLon,maxLat):</label>
          <div class="coordinate-input-group">
            <input id="queryBounds" v-model="queryParams.bounds" type="text" placeholder="例如: 113.5,30.0,114.5,31.0"
              class="form-input">
            <button @click="startRectangleSelection"
              :disabled="!(isMapUtilsReady || isMapUtilsManuallyEnabled) || isSelectingRectangle"
              class="map-select-btn">
              <i class="fas fa-vector-square" :class="{ 'fa-spin': isSelectingRectangle }"></i>
              {{ isSelectingRectangle ? "选择中..." : "从地图选框" }}
            </button>
          </div>
        </div>

        <div class="form-group">
          <label for="queryLimit">返回记录数:</label>
          <input id="queryLimit" v-model="queryParams.limit" type="number" min="1" max="1000" placeholder="默认100"
            class="form-input">
        </div>

        <div class="query-actions">
          <button @click="executeQuery" :disabled="isQuerying" class="query-btn">
            <i class="fas fa-search" :class="{ 'fa-spin': isQuerying }"></i>
            {{ isQuerying ? "查询中..." : "执行查询" }}
          </button>
          <button @click="resetQuery" class="reset-btn">
            <i class="fas fa-redo"></i>
            重置条件
          </button>
        </div>
      </div>
    </div>

    <!-- 已加载的空间表列表 -->
    <div v-if="loadedTables.length > 0" class="loaded-tables-section">
      <div class="section-header">
        <h3>已加载的空间表</h3>
        <span class="table-count">{{ loadedTables.length }} 个表</span>
      </div>
      <div class="loaded-tables-list">
        <div v-for="tableName in loadedTables" :key="tableName" class="loaded-table-item"
          :class="{ 'active': selectedTableForFeatures === tableName }" @click="selectTableForFeatures(tableName)">
          <div class="loaded-table-info">
            <span class="loaded-table-name">{{ tableName }}</span>
            <span class="feature-count">
              {{ geojsonData[tableName]?.features?.length || 0 }} 个要素
            </span>
          </div>
          <div class="loaded-table-actions">
            <button @click.stop="clearGeoJSON(tableName)" class="remove-btn" title="移除表">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 要素属性表格 -->
    <div v-if="selectedTableForFeatures && featuresData.length > 0" class="features-table-section">
      <div class="section-header">
        <h3>{{ selectedTableForFeatures }} 的要素</h3>
        <div class="table-controls">
          <span class="feature-count-info">共 {{ featuresData.length }} 个要素</span>
          <button @click="clearFeatureDisplay" class="clear-features-btn">
            <i class="fas fa-times"></i> 关闭
          </button>
        </div>
      </div>
      <div class="features-table-container">
        <table class="features-table">
          <thead>
            <tr>
              <th>序号</th>
              <!-- <th>几何类型</th> -->
              <!-- <th>几何(WKT)</th> -->
              <th v-for="key in getAttributeKeys(featuresData[0] || {})" :key="key">
                {{ key }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="feature in featuresData" :key="feature.id" class="feature-row">
              <td class="feature-id">{{ feature.id }}</td>
              <!-- <td class="geometry-type">
                <span class="geometry-badge" :class="getGeometryTypeClass(feature.geometry_type)">
                  {{ feature.geometry_type }}
                </span>
              </td> -->
              <!-- <td class="geometry-wkt">
                <span class="wkt-text">{{ getGeometryWKT(feature.geometry) }}</span>
              </td> -->
              <td v-for="key in getAttributeKeys(feature)" :key="key" class="feature-attribute">
                <span class="attribute-value">{{ getAttributeValue(feature, key) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
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
        <button @click="fetchTableGeoJSON(table)" :disabled="isLoadingGeoJSON[table]" class="geojson-btn">
          <i class="fas fa-download" :class="{ 'fa-spin': isLoadingGeoJSON[table] }"></i>
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
    <div v-if="selectedTable && geojsonData[selectedTable]" class="geojson-result">
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
import { ref, reactive, onMounted, watchEffect, watch, computed } from "vue";
import { getCurrentInstance } from "vue";
import { provide } from 'vue';
import { inject } from 'vue';
import Feature from 'ol/Feature';
import Polygon from 'ol/geom/Polygon';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';
import Fill from 'ol/style/Fill';
import API_CONFIG from '@/config/api.js';

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
      name: "",
      categories: "",
      spatialType: "point", // point 或 rectangle
      point: "", // 点坐标：经度,纬度
      bounds: "", // 矩形范围：minLon,minLat,maxLon,maxLat
      limit: 100
    });
    const isQuerying = ref(false);
    const queryResults = reactive({});

    // 已加载表和要素展示相关状态
    const selectedTableForFeatures = ref(""); // 当前选中用于展示要素的表
    const featuresData = ref([]); // 当前展示的要素数据

    // 表搜索相关状态
    const tableSearchKeyword = ref("");
    const filteredTableNames = ref([]);
    const showTableSuggestions = ref(false);

    // 地图交互状态
    const isSelectingPoint = ref(false);
    const isSelectingRectangle = ref(false);
    // 手动启用地图工具的状态
    const isMapUtilsManuallyEnabled = ref(false);

    // 折叠和拖拽相关状态
    const isCollapsed = ref(false);
    const isDragging = ref(false);
    const dragStartX = ref(0);
    const dragStartY = ref(0);
    const currentPosition = reactive({
      x: 0,
      y: 30
    });
    // 注入 mapUtils 响应式引用
    const mapUtilsRef = inject('mapUtils', null);
    const isMapUtilsReady = ref(false);
    const mapUtils = ref(null);

    // 调试信息
    console.log("mapUtilsRef 注入状态:", mapUtilsRef ? "已注入" : "未注入");
    if (mapUtilsRef) {
      console.log("mapUtilsRef 内容:", mapUtilsRef);
      console.log("mapUtilsRef.value:", mapUtilsRef.value);
    }

    // 检查 mapUtils 是否可用
    const checkMapUtilsReady = () => {
      console.log("检查 mapUtils 可用性...");

      if (mapUtilsRef && mapUtilsRef.value) {
        console.log("mapUtilsRef.value 存在:", mapUtilsRef.value);

        // 检查是否有 map 属性
        if (mapUtilsRef.value.map) {
          mapUtils.value = mapUtilsRef.value;
          isMapUtilsReady.value = true;
          console.log("✅ mapUtils 实例准备就绪", mapUtils.value);
        } else {
          console.warn("⚠️ mapUtilsRef.value 存在，但没有 map 属性");
          isMapUtilsReady.value = false;
          mapUtils.value = null;
        }
      } else {
        console.warn("❌ mapUtils 实例未准备好", mapUtilsRef);
        isMapUtilsReady.value = false;
        mapUtils.value = null;
      }

      console.log("isMapUtilsReady 状态:", isMapUtilsReady.value);
    };

    // 监听 mapUtilsRef 的变化
    watch(
      () => mapUtilsRef?.value,
      (newValue) => {
        console.log("mapUtilsRef.value 发生变化:", newValue);
        if (newValue && newValue.map) {
          mapUtils.value = newValue;
          isMapUtilsReady.value = true;
          console.log("✅ mapUtils 实例已更新", mapUtils.value);
        } else {
          isMapUtilsReady.value = false;
          mapUtils.value = null;
          console.warn("❌ mapUtils 实例更新失败");
        }
      },
      { immediate: true }
    );

    onMounted(() => {
      console.log("组件已挂载，开始检查 mapUtils...");

      // 组件挂载后立即检查
      checkMapUtilsReady();

      // 设置定时器定期检查，直到 mapUtils 可用
      const checkInterval = setInterval(() => {
        console.log("定时检查 mapUtils 状态...");
        if (mapUtilsRef && mapUtilsRef.value && mapUtilsRef.value.map) {
          mapUtils.value = mapUtilsRef.value;
          isMapUtilsReady.value = true;
          console.log("✅ mapUtils 实例准备就绪");
          clearInterval(checkInterval);
        } else {
          console.log("⏳ 等待 mapUtils 实例初始化...", {
            hasRef: !!mapUtilsRef,
            hasValue: mapUtilsRef ? !!mapUtilsRef.value : false,
            hasMap: mapUtilsRef && mapUtilsRef.value ? !!mapUtilsRef.value.map : false
          });
        }
      }, 1000);

      // 30秒后停止检查
      setTimeout(() => {
        clearInterval(checkInterval);
        if (!isMapUtilsReady.value) {
          console.error("❌ mapUtils 实例初始化超时");
          // 添加一个备选方案：允许用户手动启用按钮
          console.warn("⚠️ 地图工具初始化失败，按钮将保持禁用状态");
        }
      }, 30000);
    });

    // 表搜索处理函数
    const handleTableSearch = () => {
      if (!tableSearchKeyword.value.trim()) {
        // 如果搜索关键词为空，显示所有表
        filteredTableNames.value = [...tableNames.value];
      } else {
        // 根据关键词过滤表名（不区分大小写）
        const keyword = tableSearchKeyword.value.toLowerCase();
        filteredTableNames.value = tableNames.value.filter(table =>
          table.toLowerCase().includes(keyword)
        );
      }
    };

    // 监听表名称变化，更新过滤后的列表
    watch(tableNames, (newTableNames) => {
      filteredTableNames.value = [...newTableNames];
      // 如果当前有搜索关键词，重新应用过滤
      if (tableSearchKeyword.value.trim()) {
        handleTableSearch();
      }
    }, { immediate: true });

    // 监听搜索关键词变化
    watch(tableSearchKeyword, () => {
      handleTableSearch();
    });

    // 计算属性：已加载的空间表列表
    const loadedTables = computed(() => {
      return Object.keys(geojsonData).filter(tableName => geojsonData[tableName]);
    });

    // 选择表展示要素
    const selectTableForFeatures = (tableName) => {
      selectedTableForFeatures.value = tableName;
      const geoJsonData = geojsonData[tableName];

      if (geoJsonData && geoJsonData.features) {
        // 提取要素的属性数据，包括几何信息
        featuresData.value = geoJsonData.features.map((feature, index) => ({
          id: index + 1,
          // geometry_type: feature.geometry.type,
          // geometry: feature.geometry, // 添加几何对象
          ...feature.properties // 展开所有属性
        }));
      } else {
        featuresData.value = [];
      }
    };

    // 清除要素展示
    const clearFeatureDisplay = () => {
      selectedTableForFeatures.value = "";
      featuresData.value = [];
    };

    // 监听表名输入变化，实时过滤建议列表
    watch(() => queryParams.tableName, (newValue) => {
      if (newValue && tableNames.value.length > 0) {
        const keyword = newValue.toLowerCase();
        filteredTableNames.value = tableNames.value.filter(table =>
          table.toLowerCase().includes(keyword)
        );
      } else {
        filteredTableNames.value = [...tableNames.value];
      }
    });

    // 表输入相关函数
    const toggleTableSuggestions = () => {
      showTableSuggestions.value = !showTableSuggestions.value;
    };

    const hideTableSuggestions = () => {
      // 延迟隐藏，以便点击建议项时有时间处理
      setTimeout(() => {
        showTableSuggestions.value = false;
      }, 200);
    };

    const selectTable = (tableName) => {
      queryParams.tableName = tableName;
      showTableSuggestions.value = false;
    };
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

        // 使用 API config 构建 URL
        const url = API_CONFIG.buildURL(API_CONFIG.endpoints.spatialTables.list);
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
        return;
      }



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
        if (mapUtils.value) {
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
            `${tableName}图层`,   // 图层名称
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
        // 如果当前选中的表被清除，也要清除要素展示
        if (selectedTableForFeatures.value === tableName) {
          selectedTableForFeatures.value = "";
          featuresData.value = [];
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
      if (!isMapUtilsReady.value) {
        errorMessage.value = "地图工具未准备好，请稍后再试";
        return;
      }

      // // 如果没有选择表，则查询所有表
      // if (!queryParams.tableName && tableNames.value.length === 0) {
      //   errorMessage.value = "请先获取表名称列表";
      //   return;
      // }

      isQuerying.value = true;
      errorMessage.value = "";

      try {
        // 构建请求体对象 - 如果没有选择表，则查询所有表
        const requestBody = {
          table: queryParams.tableName || "all", // 使用"all"表示查询所有表
          name: queryParams.name || "",
          categories: queryParams.categories || "",
          geom: ""
        };

        // 构建空间查询条件
        if (queryParams.spatialType === 'point' && queryParams.point) {
          const [lng, lat] = queryParams.point.split(',').map(coord => coord.trim());
          if (lng && lat) {
            // 构建点几何对象的 WKT 格式
            requestBody.geom = `POINT(${lng} ${lat})`;
          }
        } else if (queryParams.spatialType === 'rectangle' && queryParams.bounds) {
          const [minLng, minLat, maxLng, maxLat] = queryParams.bounds.split(',').map(coord => coord.trim());
          if (minLng && minLat && maxLng && maxLat) {
            // 构建矩形几何对象的 WKT 格式
            requestBody.geom = `POLYGON((${minLng} ${minLat}, ${maxLng} ${minLat}, ${maxLng} ${maxLat}, ${minLng} ${maxLat}, ${minLng} ${minLat}))`;
          }
        }
        console.log(requestBody)

        // 构建查询URL - 使用动态配置
        const url = API_CONFIG.buildURL(API_CONFIG.endpoints.spatialTables.geojson);

        // 创建超时控制
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), props.timeout);

        const response = await fetch(url, {
          signal: controller.signal,
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(requestBody)
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          throw new Error(`查询失败: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        // 假设后端返回的是 GeoJSON 字符串，需要解析为对象
        let geojsonData;
        try {
          geojsonData = typeof data === 'string' ? JSON.parse(data) : data;
        } catch (parseError) {
          throw new Error("返回的数据格式不正确，无法解析为 GeoJSON");
        }

        // 存储查询结果
        queryResults[queryParams.tableName] = geojsonData;
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
          geojsonData,
          styleOptions,
          `${queryParams.tableName}查询结果`
        );

        console.log(`查询结果加载成功: ${queryParams.tableName}`, layer);
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


    // 重置查询条件
    const resetQuery = () => {
      queryParams.tableName = "";
      tableSearchKeyword.value = "";
      queryParams.name = "";
      queryParams.categories = "";
      queryParams.spatialType = "point";
      queryParams.point = "";
      queryParams.bounds = "";
      queryParams.limit = 100;
      errorMessage.value = "";
    };

    // 开始选点功能
    const startPointSelection = () => {
      if (!isMapUtilsReady.value) {
        errorMessage.value = "地图工具未准备好，请稍后再试";
        return;
      }

      isSelectingPoint.value = true;
      errorMessage.value = "";

      // 清除其他交互状态和地图事件
      if (isSelectingRectangle.value) {
        isSelectingRectangle.value = false;
      }
      clearAllMapEventListeners();
      disableMapInteractions();

      let mapClickHandler = null;
      let timeoutId = null;

      // 清理函数
      const cleanup = () => {
        if (mapClickHandler) {
          mapUtils.value.map.un('singleclick', mapClickHandler);
        }
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
        isSelectingPoint.value = false;
        enableMapInteractions(); // 恢复地图交互
      };

      // 设置地图点击事件监听器
      mapClickHandler = (event) => {
        const coordinate = event.coordinate;
        const lng = coordinate[0].toFixed(6);
        const lat = coordinate[1].toFixed(6);

        // 更新点坐标输入框
        queryParams.point = `${lng},${lat}`;

        // 清理所有资源
        cleanup();

        console.log(`已选择点坐标: ${lng}, ${lat}`);
      };

      // 添加地图点击事件监听器（使用singleclick而不是click）
      mapUtils.value.map.on('singleclick', mapClickHandler);

      // 设置超时自动取消选择
      timeoutId = setTimeout(() => {
        if (isSelectingPoint.value) {
          cleanup();
          errorMessage.value = "选点操作已超时，请重新选择";
        }
      }, 30000); // 30秒超时

      console.log("选点功能已启动，请点击地图选择点坐标");
    };

    // 停止选框功能
    const stopRectangleSelection = () => {
      isSelectingRectangle.value = false;
      errorMessage.value = "";
    };


    // 清除所有地图事件监听器
    const clearAllMapEventListeners = () => {
      if (mapUtils.value && mapUtils.value.map) {
        // 清除所有可能的事件监听器
        mapUtils.value.map.getInteractions().forEach(interaction => {
          if (interaction.getActive()) {
            interaction.setActive(false);
          }
        });
      }
    };

    // 检查是否正在进行地图交互
    const isMapInteractionActive = () => {
      return isSelectingPoint.value || isSelectingRectangle.value;
    };

    // 禁用地图的默认交互（在选点/选框期间）
    const disableMapInteractions = () => {
      if (mapUtils.value && mapUtils.value.map) {
        // 禁用所有默认交互，但保留我们自己的事件监听器
        mapUtils.value.map.getInteractions().forEach(interaction => {
          // 只禁用默认的交互，不要禁用我们自己的事件监听器
          if (interaction.getActive() && !interaction.get('custom')) {
            interaction.setActive(false);
          }
        });
      }
    };

    // 恢复地图的默认交互
    const enableMapInteractions = () => {
      if (mapUtils.value && mapUtils.value.map) {
        // 恢复所有默认交互
        mapUtils.value.map.getInteractions().forEach(interaction => {
          interaction.setActive(true);
        });
      }
    };

    // 开始选框功能
    const startRectangleSelection = () => {
      if (!isMapUtilsReady.value) {
        errorMessage.value = "地图工具未准备好，请稍后再试";
        return;
      }

      isSelectingRectangle.value = true;
      errorMessage.value = "";

      // 清除其他交互状态和地图事件
      if (isSelectingPoint.value) {
        isSelectingPoint.value = false;
      }
      clearAllMapEventListeners();
      disableMapInteractions();

      // 临时禁用要素点击监听器，避免触发属性弹窗
      let originalFeatureClickHandler = null;
      if (mapUtils.value && mapUtils.value.featureClickHandler) {
        originalFeatureClickHandler = mapUtils.value.featureClickHandler;
        mapUtils.value.map.un('singleclick', mapUtils.value.featureClickHandler);
        console.log("已临时禁用要素点击监听器");
      }

      let startCoordinate = null;
      let rectangleLayer = null;
      let mapClickHandler = null;
      let pointerMoveHandler = null;
      let timeoutId = null;
      const rectangleLayerId = 'rectangle-preview-' + Date.now();

      // 清理函数 - 使用更可靠的图层移除方法
      const cleanup = () => {
        console.log("开始清理选框资源...");

        // 先移除事件监听器
        if (mapClickHandler) {
          mapUtils.value.map.un('singleclick', mapClickHandler);
          mapClickHandler = null;
          console.log("已移除点击事件监听器");
        }
        if (pointerMoveHandler) {
          mapUtils.value.map.un('pointermove', pointerMoveHandler);
          pointerMoveHandler = null;
          console.log("已移除鼠标移动事件监听器");
        }

        // 恢复要素点击监听器
        if (originalFeatureClickHandler) {
          mapUtils.value.map.on('singleclick', originalFeatureClickHandler);
          console.log("已恢复要素点击监听器");
        }

        // 移除所有矩形预览图层 - 使用最彻底的方法
        console.log("准备移除所有矩形预览图层...");

        try {
          // 获取所有图层
          const layers = mapUtils.value.map.getLayers().getArray();

          // 查找所有矩形预览图层
          const previewLayers = layers.filter(layer => {
            const layerId = layer.get('id');
            return layerId && layerId.startsWith('rectangle-preview-');
          });

          console.log(`找到 ${previewLayers.length} 个预览图层需要移除`);

          // 一次性移除所有预览图层
          previewLayers.forEach(layer => {
            try {
              // 清理图层内容
              const source = layer.getSource();
              if (source) {
                source.clear();
              }

              // 从地图移除图层
              mapUtils.value.map.removeLayer(layer);
              console.log(`已移除图层: ${layer.get('id')}`);

              // 强制释放资源
              layer.setSource(null);
              layer.setStyle(null);
            } catch (layerError) {
              console.error(`移除图层 ${layer.get('id')} 时出错:`, layerError);
            }
          });

          // 强制地图刷新
          setTimeout(() => {
            try {
              mapUtils.value.map.renderSync();
              console.log("地图已强制刷新");

              // 验证移除结果
              const finalLayers = mapUtils.value.map.getLayers().getArray();
              const remainingPreviewLayers = finalLayers.filter(layer => {
                const layerId = layer.get('id');
                return layerId && layerId.startsWith('rectangle-preview-');
              });

              console.log(`移除后剩余预览图层数量: ${remainingPreviewLayers.length}`);

              if (remainingPreviewLayers.length > 0) {
                console.warn("仍有预览图层未移除，尝试最终清理");
                // 最终清理：移除所有可能的预览图层
                remainingPreviewLayers.forEach(layer => {
                  try {
                    mapUtils.value.map.removeLayer(layer);
                    console.log(`最终清理图层: ${layer.get('id')}`);
                  } catch (finalError) {
                    console.error(`最终清理失败:`, finalError);
                  }
                });
              }

            } catch (renderError) {
              console.log("地图刷新失败:", renderError);
            }
          }, 100);

        } catch (error) {
          console.error("清理矩形图层时出错:", error);
        } finally {
          // 无论如何都要释放引用
          rectangleLayer = null;
        }

        // 清除超时定时器
        if (timeoutId) {
          clearTimeout(timeoutId);
          timeoutId = null;
          console.log("已清除超时定时器");
        }

        // 重置状态
        isSelectingRectangle.value = false;
        startCoordinate = null;

        // 恢复地图交互
        enableMapInteractions();
        console.log("选框功能清理完成");
      };

      // 设置地图点击事件监听器（开始绘制）
      mapClickHandler = (event) => {
        // 阻止事件冒泡，避免触发要素点击事件
        event.stopPropagation();

        if (!startCoordinate) {
          // 第一次点击：记录起始点
          startCoordinate = event.coordinate;
          console.log("开始绘制矩形，请再次点击确定结束点");
        } else {
          // 第二次点击：完成矩形绘制
          const endCoordinate = event.coordinate;

          // 计算矩形边界
          const minLng = Math.min(startCoordinate[0], endCoordinate[0]).toFixed(6);
          const minLat = Math.min(startCoordinate[1], endCoordinate[1]).toFixed(6);
          const maxLng = Math.max(startCoordinate[0], endCoordinate[0]).toFixed(6);
          const maxLat = Math.max(startCoordinate[1], endCoordinate[1]).toFixed(6);

          // 更新矩形范围输入框
          queryParams.bounds = `${minLng},${minLat},${maxLng},${maxLat}`;

          // 清理所有资源
          cleanup();

          console.log(`已选择矩形范围: ${minLng}, ${minLat}, ${maxLng}, ${maxLat}`);
        }
      };

      // 设置鼠标移动事件监听器（实时预览矩形）
      pointerMoveHandler = (event) => {
        if (startCoordinate && event.coordinate) {
          const endCoordinate = event.coordinate;

          // 如果矩形图层不存在，创建它
          if (!rectangleLayer) {
            // 创建临时矩形图层 - 使用更简单的方法
            const rectangleFeature = new Feature({
              geometry: new Polygon([
                [
                  startCoordinate,
                  [endCoordinate[0], startCoordinate[1]],
                  endCoordinate,
                  [startCoordinate[0], endCoordinate[1]],
                  startCoordinate
                ]
              ])
            });

            // 创建新的矢量源和图层
            const vectorSource = new VectorSource({
              features: [rectangleFeature]
            });

            rectangleLayer = new VectorLayer({
              source: vectorSource,
              style: new Style({
                stroke: new Stroke({
                  color: 'rgba(0, 123, 255, 0.8)',
                  width: 3,
                  lineDash: [5, 5]
                }),
                fill: new Fill({
                  color: 'rgba(0, 123, 255, 0.2)'
                })
              })
            });

            // 设置图层不可交互，避免触发点击事件
            rectangleLayer.set('id', 'rectangle-preview-' + Date.now());
            rectangleLayer.set('interactive', false);

            // 禁用图层中要素的交互性
            const previewFeature = rectangleLayer.getSource().getFeatures()[0];
            previewFeature.set('interactive', false);
            previewFeature.set('selectable', false);

            // 直接添加到地图
            mapUtils.value.map.addLayer(rectangleLayer);
            console.log("矩形预览图层已创建并添加到地图");
          } else {
            // 如果图层已存在，只更新几何形状
            const rectangleFeature = rectangleLayer.getSource().getFeatures()[0];
            if (rectangleFeature) {
              rectangleFeature.setGeometry(new Polygon([
                [
                  startCoordinate,
                  [endCoordinate[0], startCoordinate[1]],
                  endCoordinate,
                  [startCoordinate[0], endCoordinate[1]],
                  startCoordinate
                ]
              ]));
            }
          }
        }
      };

      // 添加事件监听器（使用singleclick而不是click）
      mapUtils.value.map.on('singleclick', mapClickHandler);
      mapUtils.value.map.on('pointermove', pointerMoveHandler);

      // 设置超时自动取消选择
      timeoutId = setTimeout(() => {
        if (isSelectingRectangle.value) {
          cleanup();
          errorMessage.value = "选框操作已超时，请重新选择";
        }
      }, 60000); // 60秒超时

      console.log("选框功能已启动，请点击地图开始绘制矩形");
    };

    // 手动启用地图工具
    const enableMapUtilsManually = () => {
      isMapUtilsManuallyEnabled.value = true;
      console.log("✅ 地图工具已手动启用");
      errorMessage.value = "地图工具已手动启用，但某些功能可能无法正常工作";
      setTimeout(() => {
        errorMessage.value = "";
      }, 3000);
    };

    // 折叠功能
    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value;
    };

    // 拖拽功能
    const startDrag = (event) => {
      // 防止在按钮等元素上触发拖拽
      if (event.target.closest('button') || event.target.closest('input') || event.target.closest('select')) {
        return;
      }
      console.log("开始拖拽")
      isDragging.value = true;
      dragStartX.value = event.clientX - currentPosition.x;
      dragStartY.value = event.clientY - currentPosition.y;
      console.log("dragStartX:", dragStartX.value);
      console.log("dragStartY:", dragStartY.value);
      console.log("currentPosition.x:", currentPosition.x);
      console.log("currentPosition.y:", currentPosition.y);
      // 添加全局事件监听器
      document.addEventListener('mousemove', handleDrag);
      document.addEventListener('mouseup', stopDrag);

      // 防止文本选择
      event.preventDefault();
    };

    const handleDrag = (event) => {
      if (!isDragging.value) return;

      const newX = event.clientX - dragStartX.value;
      const newY = event.clientY - dragStartY.value;

      // 限制在可视区域内
      const maxX = window.innerWidth - 400; // 组件宽度
      const maxY = window.innerHeight - 100; // 组件最小高度

      currentPosition.x = Math.max(0, Math.min(newX, maxX));
      currentPosition.y = Math.max(0, Math.min(newY, maxY));

      console.log("dragStartX:", dragStartX.value);
      console.log("dragStartY:", dragStartY.value);
      console.log("currentPosition.x:", currentPosition.x);
      console.log("currentPosition.y:", currentPosition.y);
      // 添加全局事件监听器
    };

    const stopDrag = () => {
      isDragging.value = false;
      document.removeEventListener('mousemove', handleDrag);
      document.removeEventListener('mouseup', stopDrag);
    };

    // 计算位置样式
    const positionStyle = computed(() => ({
      left: `${currentPosition.x}px`,
      top: `${currentPosition.y}px`,
      cursor: isDragging.value ? 'grabbing' : 'grab'
    }));

    // 辅助函数：获取要素属性键名
    const getAttributeKeys = (feature) => {
      if (!feature || typeof feature !== 'object') {
        return [];
      }
      return Object.keys(feature).filter(k => k !== 'id' && k !== 'geometry_type');
    };

    // 辅助函数：获取几何类型的CSS类名
    const getGeometryTypeClass = (geometryType) => {
      if (!geometryType || typeof geometryType !== 'string') {
        return '';
      }
      return geometryType.toLowerCase();
    };

    // 辅助函数：获取属性值，确保安全访问
    const getAttributeValue = (feature, key) => {
      if (!feature || typeof feature !== 'object' || !key) {
        return '';
      }
      const value = feature[key];
      return value !== null && value !== undefined ? String(value) : '';
    };

    // 辅助函数：将GeoJSON几何转换为WKT格式
    const getGeometryWKT = (geometry) => {
      if (!geometry || typeof geometry !== 'object') {
        return '';
      }

      const { type, coordinates } = geometry;

      try {
        switch (type) {
          case 'Point':
            return `POINT(${coordinates[0].toFixed(6)} ${coordinates[1].toFixed(6)})`;

          case 'LineString':
            const lineCoords = coordinates.map(coord =>
              `${coord[0].toFixed(6)} ${coord[1].toFixed(6)}`
            ).join(', ');
            return `LINESTRING(${lineCoords})`;

          case 'Polygon':
            const polygonCoords = coordinates[0].map(coord =>
              `${coord[0].toFixed(6)} ${coord[1].toFixed(6)}`
            ).join(', ');
            return `POLYGON((${polygonCoords}))`;

          case 'MultiPoint':
            const multiPointCoords = coordinates.map(coord =>
              `${coord[0].toFixed(6)} ${coord[1].toFixed(6)}`
            ).join(', ');
            return `MULTIPOINT(${multiPointCoords})`;

          case 'MultiLineString':
            const multiLineCoords = coordinates.map(line =>
              `(${line.map(coord => `${coord[0].toFixed(6)} ${coord[1].toFixed(6)}`).join(', ')})`
            ).join(', ');
            return `MULTILINESTRING(${multiLineCoords})`;

          case 'MultiPolygon':
            const multiPolygonCoords = coordinates.map(polygon =>
              `(${polygon[0].map(coord => `${coord[0].toFixed(6)} ${coord[1].toFixed(6)}`).join(', ')})`
            ).join(', ');
            return `MULTIPOLYGON(${multiPolygonCoords})`;

          default:
            return `UNKNOWN(${type})`;
        }
      } catch (error) {
        console.error('几何转换WKT失败:', error);
        return `ERROR: ${type}`;
      }
    };

    // watch(positionStyle, (newValue, oldValue) => {
    //   console.log("位置样式已更新:", newValue);
    // });
    return {
      isCollapsed,
      positionStyle,
      toggleCollapse,
      startDrag,
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
      isSelectingPoint,
      isSelectingRectangle,
      isMapUtilsReady,
      isMapUtilsManuallyEnabled,
      tableSearchKeyword,
      filteredTableNames,
      showTableSuggestions,
      fetchTableNames,
      fetchTableGeoJSON,
      clearGeoJSON,
      formattedGeoJSON,
      copyGeoJSON,
      executeQuery,
      resetQuery,
      startPointSelection,
      startRectangleSelection,
      enableMapUtilsManually,
      handleTableSearch,
      toggleTableSuggestions,
      hideTableSuggestions,
      selectTable,
      loadedTables,
      selectedTableForFeatures,
      featuresData,
      selectTableForFeatures,
      clearFeatureDisplay,
      getAttributeKeys,
      getGeometryTypeClass,
      getAttributeValue,
      getGeometryWKT,
    };
  },
};
</script>

<style scoped>
.spatial-table-fetcher {
  position: absolute;
  top: 30px;
  left: 0px;
  z-index: 2000;
  width: 400px;
  padding: 20px;
  background-color: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-height: calc(100vh - 100px);
  overflow-y: auto;
  transition: all 0.3s ease;
  backdrop-filter: blur(5px);
  cursor: grab;
  user-select: none;
}

/* 折叠状态 */
.spatial-table-fetcher.collapsed {
  max-height: 60px;
  overflow: hidden;
  padding-bottom: 10px;
}

/* 拖拽状态 */
.spatial-table-fetcher:active {
  cursor: grabbing;
}

/* 鼠标悬停时的强化效果 */
.spatial-table-fetcher:hover {
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
  cursor: grab;
}

.header:active {
  cursor: grabbing;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

h2 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

.drag-handle {
  color: #495057;
  font-size: 1.1rem;
  cursor: grab;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
  background-color: rgba(255, 255, 255, 0.8);
  border: 1px solid #e0e0e0;
  margin-right: 10px;
}

.drag-handle:hover {
  background-color: rgba(66, 185, 131, 0.1);
  border-color: #42b983;
  color: #42b983;
  transform: scale(1.1);
}

.collapse-btn {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid #e0e0e0;
  color: #495057;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-size: 1rem;
  font-weight: 500;
  min-width: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.collapse-btn:hover {
  background-color: rgba(66, 185, 131, 0.1);
  border-color: #42b983;
  color: #42b983;
  transform: scale(1.05);
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

/* 地图工具状态提示样式 */
.map-utils-status {
  margin-bottom: 20px;
}

.status-warning {
  background-color: #fff8e6;
  border-left: 4px solid #ffc107;
  padding: 12px 15px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #856404;
}

.status-warning i {
  color: #ffc107;
  font-size: 1.1rem;
}

.status-warning span {
  flex: 1;
  font-weight: 500;
}

.enable-btn {
  background-color: #ffc107;
  color: #212529;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.3s;
  font-size: 0.85rem;
  white-space: nowrap;
}

.enable-btn:hover:not(:disabled) {
  background-color: #e0a800;
}

.enable-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  background-color: #6c757d;
  color: white;
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

.table-warning {
  font-size: 0.8rem;
  color: #dc3545;
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  background-color: #fff0f0;
  padding: 8px;
  border-radius: 4px;
  border-left: 3px solid #dc3545;
}

.table-warning i {
  color: #dc3545;
}

.table-success {
  font-size: 0.8rem;
  color: #28a745;
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  background-color: #f0fff4;
  padding: 8px;
  border-radius: 4px;
  border-left: 3px solid #28a745;
}

.table-success i {
  color: #28a745;
}

/* 表输入容器样式 */
.table-input-container {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-with-dropdown {
  position: relative;
  display: flex;
  align-items: center;
  color: #212529
}

.table-input {
  padding: 8px 35px 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
  width: 100%;
}

.table-input:focus {
  outline: none;
  border-color: #42b983;
  box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.1);
}

.dropdown-icon {
  position: absolute;
  right: 10px;
  color: #6c757d;
  font-size: 0.9rem;
  cursor: pointer;
  z-index: 1;
  transition: color 0.2s;
}

.dropdown-icon:hover {
  color: #42b983;
}

.table-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ced4da;
  border-top: none;
  border-radius: 0 0 4px 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.suggestion-item {
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.suggestion-item:hover {
  background-color: #f8f9fa;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.no-suggestions {
  padding: 8px 12px;
  color: #6c757d;
  font-style: italic;
  text-align: center;
}

/* 表搜索容器样式 */
.table-search-container {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  padding: 8px 12px 8px 35px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
  transition: border-color 0.2s;
  width: 100%;
}

.search-input:focus {
  outline: none;
  border-color: #42b983;
  box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.1);
}

.search-icon {
  position: absolute;
  left: 10px;
  color: #6c757d;
  font-size: 0.9rem;
  z-index: 1;
}

.search-no-results {
  font-size: 0.8rem;
  color: #dc3545;
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  background-color: #fff0f0;
  padding: 8px;
  border-radius: 4px;
  border-left: 3px solid #dc3545;
}

.search-no-results i {
  color: #dc3545;
}

.search-results-info {
  font-size: 0.8rem;
  color: #28a745;
  margin-top: 5px;
  display: flex;
  align-items: center;
  gap: 5px;
  background-color: #f0fff4;
  padding: 8px;
  border-radius: 4px;
  border-left: 3px solid #28a745;
}

.search-results-info i {
  color: #28a745;
}

/* 坐标输入组样式 */
.coordinate-input-group {
  display: flex;
  gap: 8px;
  align-items: stretch;
}

.coordinate-input-group .form-input {
  flex: 1;
  min-width: 0;
}

.map-select-btn {
  background-color: #17a2b8;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background-color 0.3s;
  white-space: nowrap;
  font-size: 0.85rem;
  min-width: fit-content;
}

.map-select-btn:hover:not(:disabled) {
  background-color: #138496;
}

.map-select-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  background-color: #6c757d;
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

/* 已加载空间表列表样式 */
.loaded-tables-section {
  margin-bottom: 25px;
  padding: 15px;
  background-color: #f0f8ff;
  border-radius: 8px;
  border: 1px solid #b3d9ff;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.section-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.1rem;
  font-weight: 600;
}

.table-count {
  font-size: 0.8rem;
  color: #666;
  background-color: rgba(66, 185, 131, 0.1);
  padding: 4px 8px;
  border-radius: 12px;
  border: 1px solid #42b983;
}

.loaded-tables-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.loaded-table-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background-color: white;
  border: 1px solid #e0e7ff;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.loaded-table-item:hover {
  background-color: #f8faff;
  border-color: #42b983;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.loaded-table-item.active {
  background-color: #e6f3ff;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.2);
}

.loaded-table-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.loaded-table-name {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.95rem;
}

.feature-count {
  font-size: 0.8rem;
  color: #666;
  font-style: italic;
}

.loaded-table-actions {
  display: flex;
  align-items: center;
}

.remove-btn {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  font-size: 0.8rem;
}

.remove-btn:hover {
  background-color: #c82333;
}

/* 要素属性表格样式 */
.features-table-section {
  margin-bottom: 25px;
  padding: 15px;
  background-color: #fff5f5;
  border-radius: 8px;
  border: 1px solid #ffc9c9;
  color: #212529
}

.table-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.feature-count-info {
  font-size: 0.8rem;
  color: #666;
  background-color: rgba(255, 193, 7, 0.1);
  padding: 4px 8px;
  border-radius: 12px;
  border: 1px solid #ffc107;
}

.clear-features-btn {
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  gap: 4px;
}

.clear-features-btn:hover {
  background-color: #545b62;
}

.features-table-container {
  max-height: 400px;
  overflow: auto;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  background-color: white;
}

.features-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.features-table thead {
  background-color: #f8f9fa;
  position: sticky;
  top: 0;
  z-index: 1;
}

.features-table th {
  padding: 8px 6px;
  text-align: left;
  border-bottom: 2px solid #dee2e6;
  border-right: 1px solid #dee2e6;
  font-weight: 600;
  color: #495057;
  white-space: nowrap;
  font-size: 0.8rem;
}

.features-table th:last-child {
  border-right: none;
}

.features-table tbody tr {
  transition: background-color 0.2s ease;
}

.features-table tbody tr:hover {
  background-color: #f8f9fa;
}

.features-table tbody tr:nth-child(even) {
  background-color: #fbfbfb;
}

.features-table td {
  padding: 6px;
  border-bottom: 1px solid #dee2e6;
  border-right: 1px solid #dee2e6;
  vertical-align: top;
  max-width: 120px;
  word-wrap: break-word;
}

.features-table td:last-child {
  border-right: none;
}

.feature-id {
  font-weight: 600;
  color: #007bff;
  text-align: center;
  width: 50px;
}

.geometry-type {
  text-align: center;
  width: 80px;
}

.geometry-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  white-space: nowrap;
}

.geometry-badge.point {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.geometry-badge.linestring {
  background-color: #cce5ff;
  color: #004085;
  border: 1px solid #b3d9ff;
}

.geometry-badge.polygon {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.geometry-badge.multipoint,
.geometry-badge.multilinestring,
.geometry-badge.multipolygon {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.feature-attribute {
  max-width: 150px;
}

.attribute-value {
  display: block;
  word-break: break-word;
  max-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .features-table {
    font-size: 0.75rem;
  }

  .features-table th,
  .features-table td {
    padding: 4px;
  }

  .feature-attribute {
    max-width: 100px;
  }
}

/* 滚动条样式 */
.features-table-container::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.features-table-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.features-table-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.features-table-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
