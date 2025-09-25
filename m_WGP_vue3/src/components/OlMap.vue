<template>
  <div class="map-container">

        <!-- 属性信息弹窗 -->
    <!-- <div v-if="showFeatureInfo" class="feature-info-popup" :style="{ top: `${popupTop}px`, left: `${popupLeft}px` }">
      <div class="popup-header">
        <h3>要素属性</h3>
        <button @click="closeFeatureInfo">×</button>
      </div>
      <div class="popup-content">
        <table>
          <tr v-for="(value, key) in featureProperties" :key="key">
            <td>{{ key }}</td>
            <td>{{ value }}</td>
          </tr>
        </table>
      </div>
    </div> -->
    <!-- <div ref="featurepopup">    </div> -->
    <div ref="mapElement" class="map"></div>

    <div class="map-controls">
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
    </div>

    <slot></slot>

  </div>

</template>

<script>
import { onMounted, ref, onUnmounted, reactive, watch } from "vue";
import MapUtils from "./mapUtils";
import { provide } from "vue";

export default {
  name: "OlMap",
  setup() {
    const mapElement = ref(null);
    let mapUtilsInstance = null;

    // 1. 创建响应式对象用于传递 mapUtils 实例
    const mapUtilsContainer = reactive({
      instance: null
    });
    // 2. 提前在 setup 阶段提供，确保子组件能获取到响应式对象
    provide("mapUtilsInstance", mapUtilsContainer);



    const featurepopup = ref(null)
    const featurePopupElement=ref(null)

    const baseLayers = ref([]);
    const vectorLayer = ref(null);
    const modifyInteraction = ref(null);
    const activeDrawType = ref(null);
    const activeMeasureType = ref(null);
    const mapUtils = new MapUtils(mapElement.value);

    // 可绘制的几何类型
    const drawTypes = ["Point", "LineString", "Polygon", "Circle"];

    // 初始化地图
    const initMap = () => {
      if (!mapElement.value) return;

      // 创建地图实例
      mapUtilsInstance = new MapUtils(mapElement.value);
      mapUtilsContainer.instance = mapUtilsInstance;

      featurePopupElement.value=mapUtilsInstance.featurePopupElement

      // 添加底图
      baseLayers.value = mapUtilsInstance.addBaseLayer();

      // 创建矢量图层（用于绘制）
      vectorLayer.value = mapUtilsInstance.createVectorLayer({
        fillColor: "rgba(255, 255, 255, 0.2)",
        strokeColor: "#4CAF50",
        strokeWidth: 2,
        pointColor: "#4CAF50",
      });

      vectorLayer.value.set("title", "绘制图层");
      mapUtilsInstance.map.addLayer(vectorLayer.value);
      mapUtilsInstance.initFeatureClick()
      // 添加修改交互
      modifyInteraction.value = mapUtilsInstance.addModifyInteraction(
        vectorLayer.value
      );
     
     
      // 新增：添加要素点击监听
    // // 定义 showFeatureInfo 和相关变量
    // const showFeatureInfo = ref(false);
    // const featureProperties = ref({});
    // const popupLeft = ref(0);
    // const popupTop = ref(0);
      // addFeatureClickListener();
    };

    // 新增：要素点击监听方法
    const addFeatureClickListener = () => {
      if (!mapUtilsInstance || !mapUtilsInstance.map) 
      {console.log("mapUtilsInstance or mapUtilsInstance.map is null");
        return;}

      // 使用OpenLayers的点击事件
      mapUtilsInstance.map.on('singleclick', (event) => {
        // 只在没有激活绘制/测量工具时响应点击（可选）
        console.log("地图单击事件触发", event);
        if (activeDrawType.value || activeMeasureType.value)
        { console.log("有激活的绘制/测量工具，不响应单击事件");
          return;}

        // 检测点击位置的要素
        const features = [];
        mapUtilsInstance.map.forEachFeatureAtPixel(
          event.pixel,
          (feature) => {
            console.log("feature", feature);
            features.push(feature);
          },
          // { layerFilter: (layer) => layer === vectorLayer.value } 
        );

        if (features.length > 0) {
          // 获取第一个要素的属性
          console.log("features", features);
          const properties = features[0].getProperties();
          // 过滤OpenLayers内部属性（如id、geometry）
          const filteredProps = {};
          Object.keys(properties).forEach(key => {
            if (!['id', 'geometry'].includes(key)) {
              filteredProps[key] = properties[key];
            }
          });

          // 更新弹窗状态
          featureProperties.value = filteredProps;
          // 设置弹窗位置（基于点击坐标，确保在视口内）
          const { clientX, clientY } = event.originalEvent;
          const popupWidth = 300; // 弹窗宽度
          const popupHeight = 200; // 弹窗高度
          const windowWidth = window.innerWidth;
          const windowHeight = window.innerHeight;

          // 计算弹窗位置，避免超出视口
          popupLeft.value = clientX + popupWidth > windowWidth 
            ? windowWidth - popupWidth - 10 
            : clientX + 10;
          popupTop.value = clientY + popupHeight > windowHeight 
            ? windowHeight - popupHeight - 10 
            : clientY + 10;
          showFeatureInfo.value = true;
          
          // 调试日志
          console.log('弹窗状态:', showFeatureInfo.value);
          console.log('弹窗位置:', popupLeft.value, popupTop.value);
          console.log('检测到的要素属性:', filteredProps);

        } else {
          // 点击空白处关闭弹窗
          showFeatureInfo.value = false;
        }
      });

    };
    // 新增：关闭属性弹窗
    const closeFeatureInfo = () => {
      showFeatureInfo.value = false;
    };

    // 激活绘制工具
    // 修改activateDrawTool方法
    const activateDrawTool = (type) => {
      // 在 OlMap.vue 的 activateDrawTool 中添加
      if (modifyInteraction.value) {
        modifyInteraction.value.setActive(false);
      }

      // 在 activateMeasureTool 中添加
      if (modifyInteraction.value) {
        modifyInteraction.value.setActive(false);
      }
      if (!mapUtilsInstance || !vectorLayer.value) return;

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
      mapUtilsInstance.clearAllInteractions();

      // 激活新的绘制工具
      const draw = mapUtilsInstance.addDrawInteraction(vectorLayer.value, type);
      activeDrawType.value = type;
      activeMeasureType.value = null;
    };

    // 停用绘制工具
    const deactivateDrawTool = () => {
      if (mapUtilsInstance) {
        // 调用工具类方法清除绘制状态
        mapUtilsInstance._clearDrawState();
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
      if (!mapUtilsInstance) return;

      // 如果已经激活了同类型的测量工具，则取消激活
      if (activeMeasureType.value === type) {
        deactivateMeasureTool();
        return;
      }

      // 激活新的测量工具
      mapUtilsInstance.setupMeasureTool(type);
      activeMeasureType.value = type;
      activeDrawType.value = null;
    };

    // 停用测量工具
    const deactivateMeasureTool = () => {
      if (mapUtilsInstance) {
        // 调用工具类方法彻底清除测量状态
        mapUtilsInstance.stopMeasureTool();
      }
      activeMeasureType.value = null;
    };

    // 清除测量结果
    const clearMeasureResults = () => {
      if (mapUtilsInstance) {
        mapUtilsInstance.clearMeasureResults();
      }
    };

    // 删除最后一个测量结果
    const deleteLastMeasure = () => {
      if (mapUtilsInstance) {
        mapUtilsInstance.deleteLastMeasure();
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

    // 监听 featurePopupElement 的变化
    // watch(featurePopupElement, (newVal) => {
    //   console.log("featurePopupElement", newVal);
    //   if (featurepopup.value && newVal instanceof Node) {
    //     console.log("featurePopupElement", newVal);
    //     featurepopup.value.appendChild(newVal);
    //   }
    // });

    // 组件挂载时初始化地图
    onMounted(() => {
      initMap();
    });

    // 组件卸载时清理资源
    onUnmounted(() => {
      if (mapUtilsInstance && mapUtilsInstance.map) {
        mapUtilsInstance.map.setTarget(null);
        mapUtilsInstance = null;
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
      // featurePopupElement,
      // featurepopup,
      // // 添加弹窗相关的变量和方法
      // showFeatureInfo,
      // popupTop,
      // popupLeft,
      // featureProperties,
      // closeFeatureInfo,
    };
  }
}
</script>
<style scoped>
.map-container {
  position: relative;
  width: 100%;
  height: 100vh;
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

.spatial-table-fetcher {
  position: absolute;
  top: 20px;
  right: 20px;
  /* 保持靠右显示 */
  z-index: 2000;
  width: 350px;
  padding: 20px;
  background-color: rgba(255, 255, 255, 0.95);
  /* 轻微透明，增强悬浮感 */
  border-radius: 8px;
  /* 圆角更明显 */
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  /* 增强阴影，突出悬浮效果 */
  max-height: calc(100vh - 100px);
  overflow-y: auto;
  transition: all 0.3s ease;
  /* 平滑过渡效果 */
  backdrop-filter: blur(5px);
  /* 背景模糊（可选，增强层次感） */
}

/* 鼠标悬停时的强化效果 */
.spatial-table-fetcher:hover {
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
  /* 阴影加深 */
  transform: translateY(-2px);
  /* 轻微上浮 */
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

.spatial-table-fetcher {
  position: relative;
  /* 确保在流中显示 */
  z-index: 1000;
  /* 避免被地图图层覆盖 */
  max-width: 1000px;
  margin: 20px;
  /* 改用固定边距，避免在地图容器内居中失败 */
  padding: 20px;
  background-color: #fff;
  /* ... 其他样式 */
}
</style>
