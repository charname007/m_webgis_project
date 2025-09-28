<template>
  <div class="map-container">
    <div ref="mapElement" class="map"></div>

    <!-- <div class="map-controls">
      <div class="control-group">
        <h3>绘制工具</h3>
        <button v-for="type in drawTypes" :key="type" @click="activateDrawTool(type)"
          :class="{ active: activeDrawType === type }">
          {{ getDrawTypeName(type) }}
        </button>
        <button @click="clearDrawings" class="danger" :disabled="!vectorLayer">
          清除绘制
        </button>
      </div>

      <div class="control-group">
        <h3>测量工具</h3>
        <button @click="activateMeasureTool('LineString')" :class="{ active: activeMeasureType === 'LineString' }">
          距离测量
        </button>
        <button @click="activateMeasureTool('Polygon')" :class="{ active: activeMeasureType === 'Polygon' }">
          面积测量
        </button>
        <button @click="activateMeasureTool('angle')" :class="{ active: activeMeasureType === 'angle' }">
          角度测量
        </button>
        <button @click="clearMeasureResults" :disabled="!activeMeasureType" class="danger">
          清除测量
        </button>
        <button @click="deactivateMeasureTool" :disabled="!activeMeasureType">
          停止测量
        </button>
        <button @click="deleteLastMeasure" :disabled="!activeMeasureType" class="warning">
          删除最后一个
        </button>
      </div>
    </div> -->

    <slot name="SpatialTableFetcher"></slot>
    

  </div>

</template>

<script>
import { onMounted, ref, onUnmounted } from "vue";
import MapUtils from "./mapUtils";
import { provide } from "vue";
import SpatialTableFetcher from "./SpatialTableFetcher.vue";

export default {
  name: "OlMap",
  setup() {
    const mapElement = ref(null);
    
    // 创建响应式 mapUtils 实例容器
    const mapUtilsRef = ref(null);
    
    // 提供 mapUtils 实例给子组件
    provide("mapUtils", mapUtilsRef);

    const baseLayers = ref([]);
    const vectorLayer = ref(null);
    const modifyInteraction = ref(null);
    const activeDrawType = ref(null);
    const activeMeasureType = ref(null);

    // 可绘制的几何类型
    const drawTypes = ["Point", "LineString", "Polygon", "Circle"];

    // 初始化地图
    const initMap = () => {
      if (!mapElement.value) return;

      // 创建地图实例并赋值给响应式引用
      const mapUtils = new MapUtils(mapElement.value);
      mapUtilsRef.value = mapUtils;

      // 等待地图完全初始化
      setTimeout(() => {
        if (mapUtils && mapUtils.map) {
          // 添加底图
          baseLayers.value = mapUtils.addBaseLayer();

          // 创建矢量图层（用于绘制）
          vectorLayer.value = mapUtils.createVectorLayer({
            fillColor: "rgba(255, 255, 255, 0.2)",
            strokeColor: "#4CAF50",
            strokeWidth: 2,
            pointColor: "#4CAF50",
          });

          vectorLayer.value.set("title", "绘制图层");
          mapUtils.map.addLayer(vectorLayer.value);
          mapUtils.initFeatureClick();
          
          // 添加修改交互
          modifyInteraction.value = mapUtils.addModifyInteraction(
            vectorLayer.value
          );
          
          console.log("地图初始化完成，mapUtils实例已注入");
        }
      }, 100);
    };


    // 激活绘制工具
    const activateDrawTool = (type) => {
      if (modifyInteraction.value) {
        modifyInteraction.value.setActive(false);
      }

      if (!mapUtilsRef.value || !vectorLayer.value) return;

      // 关键修复：无论当前是否有激活的测量工具，都强制停用
      if (activeMeasureType.value) {
        deactivateMeasureTool();
      }

      // 如果已经激活了同类型的绘制工具，则取消激活
      if (activeDrawType.value === type) {
        deactivateDrawTool();
        return;
      }

      // 先清除所有可能的交互
      mapUtilsRef.value.clearAllInteractions();

      // 激活新的绘制工具
      const draw = mapUtilsRef.value.addDrawInteraction(vectorLayer.value, type);
      activeDrawType.value = type;
      activeMeasureType.value = null;
    };

    // 停用绘制工具
    const deactivateDrawTool = () => {
      if (mapUtilsRef.value) {
        // 调用工具类方法清除绘制状态
        mapUtilsRef.value.clearAllInteractions();
      }
      activeDrawType.value = null;
    };

    // 清除绘制内容
    const clearDrawings = () => {
      if (vectorLayer.value && vectorLayer.value.getSource()) {
        vectorLayer.value.getSource().clear();
      }
    };

    // 激活测量工具
    const activateMeasureTool = (type) => {
      if (!mapUtilsRef.value) return;

      // 如果已经激活了同类型的测量工具，则取消激活
      if (activeMeasureType.value === type) {
        deactivateMeasureTool();
        return;
      }

      // 激活新的测量工具
      mapUtilsRef.value.setupMeasureTool(type);
      activeMeasureType.value = type;
      activeDrawType.value = null;
    };

    // 停用测量工具
    const deactivateMeasureTool = () => {
      if (mapUtilsRef.value) {
        // 调用工具类方法彻底清除测量状态
        mapUtilsRef.value.stopMeasureTool();
      }
      activeMeasureType.value = null;
    };

    // 清除测量结果
    const clearMeasureResults = () => {
      if (mapUtilsRef.value) {
        mapUtilsRef.value.clearMeasureResults();
      }
    };

    // 删除最后一个测量结果
    const deleteLastMeasure = () => {
      if (mapUtilsRef.value) {
        mapUtilsRef.value.deleteLastMeasure();
      }
    };

    // 获取绘制类型名称
    const getDrawTypeName = (type) => {
      const names = {
        Point: "点",
        LineString: "线",
        Polygon: "多边形",
        Circle: "圆",
      };
      return names[type] || type;
    };

    // 组件挂载时初始化地图
    onMounted(() => {
      initMap();
    });

    // 组件卸载时清理资源
    onUnmounted(() => {
      if (mapUtilsRef.value && mapUtilsRef.value.map) {
        mapUtilsRef.value.map.setTarget(null);
        mapUtilsRef.value = null;
      }
    });

    return {
      mapElement,
      drawTypes,
      activeDrawType,
      activeMeasureType,
      vectorLayer,
      activateDrawTool,
      clearDrawings,
      activateMeasureTool,
      deactivateMeasureTool,
      clearMeasureResults,
      deleteLastMeasure,
      getDrawTypeName,
    };
  }
}
</script>
<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: visible; /* 允许子元素溢出容器 */
  display: flex;
  flex-direction: row;
}

.map {
  width: 100%;
  height: 100%;
  z-index: 100;
}

.map-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  background: white;
  padding: 10px;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  max-width: 200px;
  
}

.control-group {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.control-group:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.control-group h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
  text-align: center;
  padding: 5px;
  background: #f5f5f5;
  border-radius: 3px;
}

button {
  display: block;
  width: 100%;
  padding: 8px 10px;
  margin-bottom: 6px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 3px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

button:hover {
  background: #e5e5e5;
  border-color: #ccc;
}

button.active {
  background: #4caf50;
  color: white;
  border-color: #45a049;
}

button.danger {
  background: #f44336;
  color: white;
  border-color: #d32f2f;
}

button.danger:hover {
  background: #d32f2f;
}

button.warning {
  background: #ff9800;
  color: white;
  border-color: #e65100;
}

button.warning:hover {
  background: #f57c00;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.layer-item {
  display: flex;
  align-items: center;
  margin-bottom: 5px;
  font-size: 12px;
}

.layer-item input {
  margin-right: 8px;
}

</style>

<style>
/* 测量提示框样式 */
.ol-tooltip {
  position: relative;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 4px;
  color: white;
  padding: 4px 8px;
  pointer-events: none;
  white-space: nowrap;
}

.ol-tooltip-measure {
  background-color: rgba(255, 255, 255, 0.9);
  color: #333;
  border: 1px solid #ddd;
}

.ol-tooltip-static {
  background-color: #ff9800;
  color: white;
  border: 1px solid #e65100;
  font-weight: bold;
  padding: 6px 12px;
}

.ol-tooltip-hidden {
  display: none;
}

.ol-tooltip::before {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
}

/* 属性弹窗样式 */
.feature-info-popup {
  position: fixed;
  z-index: 10000; /* 提高z-index确保在最上层 */
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  max-width: 300px;
  max-height: 200px;
  overflow: auto;
  color: black; /* 设置字体颜色为黑色 */
  pointer-events: auto; /* 确保可以交互 */
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding-bottom: 5px;
  border-bottom: 1px solid #eee;
}

.popup-header h3 {
  margin: 0;
  font-size: 16px;
}

.popup-header button {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #999;
}

.popup-header button:hover {
  color: #333;
}

.popup-content table {
  width: 100%;
  border-collapse: collapse;
}

.popup-content td {
  padding: 5px;
  border-bottom: 1px solid #eee;
}

.popup-content td:first-child {
  font-weight: bold;
  color: #555;


  border-style: solid;
  border-color: rgba(0, 0, 0, 0.5) transparent transparent transparent;
}

.ol-tooltip-measure::before {
  border-top-color: rgba(255, 255, 255, 0.9);
}

.ol-tooltip-static::before {
  border-top-color: #ff9800;
}

.map .custom-fullscreen {
  right: 5px;
  top: 5px;
  position: absolute;
}


.map .custom-zoom-to-extent {
  top: 60px;
  left: 10px;
  position: absolute;
  color: #000;
}

.map .custom-wms-capabilities {
  top: 100px;
  left: 10px;
  position: absolute;
  color: #000;
}

.map .custom-zoom-slider {
  top: 140px;
  left: 10px;
  position: absolute;
  color: #000;
}

</style>
