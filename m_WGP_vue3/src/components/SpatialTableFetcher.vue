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

    <!-- 地图工具状态提示 -->
    <div v-if="!isMapUtilsReady" class="map-utils-status">
      <div class="status-warning">
        <i class="fas fa-exclamation-triangle"></i>
        <span>地图工具未就绪</span>
        <button 
          @click="enableMapUtilsManually" 
          class="enable-btn"
          :disabled="isMapUtilsManuallyEnabled"
        >
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
          <div class="coordinate-input-group">
            <input
              id="queryPoint"
              v-model="queryParams.point"
              type="text"
              placeholder="例如: 114.0,30.5"
              class="form-input"
            >
            <button
              @click="startPointSelection"
              :disabled="!(isMapUtilsReady || isMapUtilsManuallyEnabled) || isSelectingPoint"
              class="map-select-btn"
            >
              <i class="fas fa-map-marker-alt" :class="{ 'fa-spin': isSelectingPoint }"></i>
              {{ isSelectingPoint ? "选择中..." : "从地图选点" }}
            </button>
          </div>
        </div>

        <div v-if="queryParams.spatialType === 'rectangle'" class="form-group">
          <label for="queryBounds">矩形范围 (minLon,minLat,maxLon,maxLat):</label>
          <div class="coordinate-input-group">
            <input
              id="queryBounds"
              v-model="queryParams.bounds"
              type="text"
              placeholder="例如: 113.5,30.0,114.5,31.0"
              class="form-input"
            >
            <button
              @click="startRectangleSelection"
              :disabled="!(isMapUtilsReady || isMapUtilsManuallyEnabled) || isSelectingRectangle"
              class="map-select-btn"
            >
              <i class="fas fa-vector-square" :class="{ 'fa-spin': isSelectingRectangle }"></i>
              {{ isSelectingRectangle ? "选择中..." : "从地图选框" }}
            </button>
          </div>
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
            :disabled="isQuerying"
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
import Feature from 'ol/Feature';
import Polygon from 'ol/geom/Polygon';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import Style from 'ol/style/Style';
import Stroke from 'ol/style/Stroke';
import Fill from 'ol/style/Fill';

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
    
    // 地图交互状态
    const isSelectingPoint = ref(false);
    const isSelectingRectangle = ref(false);
    // 手动启用地图工具的状态
    const isMapUtilsManuallyEnabled = ref(false);
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

      // 如果没有选择表，则查询所有表
      if (!queryParams.tableName && tableNames.value.length === 0) {
        errorMessage.value = "请先获取表名称列表";
        return;
      }

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

        // 构建查询URL - 使用后端提供的 POST API
        const url = "http://localhost:8080/postgis/WGP_db/tables/SpatialTables/geojson";

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
      queryParams.tableCondition = "";
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
      isSelectingPoint,
      isSelectingRectangle,
      isMapUtilsReady,
      isMapUtilsManuallyEnabled,
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
</style>
