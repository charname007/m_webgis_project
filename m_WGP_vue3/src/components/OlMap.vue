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

    <!-- <slot name="SpatialTableFetcher"></slot> -->
    <slot name="TouristSpotSearch"></slot>

    <!-- AI智能查询组件 -->
    <slot name="AgentQueryBar"></slot>

    <!-- 要素属性弹窗组件 -->
    <FeaturePopup
      ref="featurePopupRef"
      :visible="popupVisible"
      :properties="popupProperties"
      :title="popupTitle"
      @close="closePopup"
    />

  </div>

</template>

<script>
import { onMounted, ref, onUnmounted, shallowRef, nextTick } from "vue";
import MapUtils from "./mapUtils";
import { provide } from "vue";
import SpatialTableFetcher from "./SpatialTableFetcher.vue";
import FeaturePopup from "./FeaturePopup.vue";
import API_CONFIG from "../config/api.js";
import { Style, Fill, Stroke, Circle, Icon, Text } from "ol/style";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import Cluster from "ol/source/Cluster";
import Feature from "ol/Feature";
import Point from "ol/geom/Point";
import Polygon from "ol/geom/Polygon";
import Overlay from "ol/Overlay";
import Draw, { createBox } from "ol/interaction/Draw";
import DragPan from "ol/interaction/DragPan";
import DragBox from "ol/interaction/DragBox";
import { platformModifierKeyOnly } from "ol/events/condition";

export default {
  name: "OlMap",
  components: {
    FeaturePopup
  },
  setup() {
    const mapElement = ref(null);

    // 使用 shallowRef 避免深度代理（防止私有字段访问失败）
    const mapUtilsRef = shallowRef(null);

    const baseLayers = ref([]);
    const vectorLayer = ref(null);
    const modifyInteraction = ref(null);
    const activeDrawType = ref(null);
    const activeMeasureType = ref(null);
    const sightLayerRef = shallowRef(null); // 景区图层引用
    const mapCenterLayer = ref(null); // 地图中心标记图层
    const extentData = ref(null); // 存储获取的景区数据
    const isLoading = ref(false); // 加载状态

    // 范围选择相关状态
    const extentDrawLayer = ref(null); // 范围选择图层
    const extentDrawInteraction = ref(null); // 范围选择交互
    const extentSelectCallback = ref(null); // 范围选择完成回调
    const savedDragPanInteraction = ref(null); // 保存被禁用的DragPan交互
    const singleClickListenerKey = ref(null); // 保存singleclick事件监听器的key
    const moveendListenerKey = ref(null); // 保存moveend事件监听器的key

    // 手动范围选择相关状态
    const isDrawing = ref(false); // 是否正在绘制
    const startPixel = ref(null); // 开始像素坐标
    const endPixel = ref(null); // 结束像素坐标
    const drawFeature = ref(null); // 绘制的要素

    // 弹窗相关状态
    const featurePopupRef = ref(null);
    const popupVisible = ref(false);
    const popupProperties = ref({});
    const popupTitle = ref('要素属性');
    const popupOverlay = ref(null);
    const currentHighlightedFeature = ref(null);
    const currentHighlightedLayer = ref(null);
    const originalFeatureStyle = ref(null);
    
    // 图片缓存和加载状态
    const imageCache = ref(new Map()); // 图片样式缓存
    const imageUrlCache = ref(new Map()); // 景点名称 -> 图片URL 缓存
    const loadingImages = ref(new Set()); // 正在加载的图片

    // 请求队列管理
    const requestQueue = [];
    let activeRequests = 0;
    const MAX_CONCURRENT_REQUESTS = 6; // 最大并发请求数

    // 执行队列中的下一个请求
    const processQueue = () => {
      if (requestQueue.length === 0 || activeRequests >= MAX_CONCURRENT_REQUESTS) {
        return;
      }

      const nextRequest = requestQueue.shift();
      activeRequests++;

      nextRequest().finally(() => {
        activeRequests--;
        processQueue(); // 继续处理队列
      });
    };

    // 将请求加入队列
    const queueRequest = (requestFn) => {
      return new Promise((resolve, reject) => {
        requestQueue.push(() => requestFn().then(resolve).catch(reject));
        processQueue();
      });
    };

    // 根据要素名称查询旅游景点图片链接（带缓存和队列控制）
    const fetchTouristSpotImageUrl = async (spotName) => {
      if (!spotName) return null;

      // 检查URL缓存
      if (imageUrlCache.value.has(spotName)) {
        return imageUrlCache.value.get(spotName);
      }

      // 使用队列控制并发
      return queueRequest(async () => {
        try {
          const response = await fetch(API_CONFIG.buildURL(API_CONFIG.endpoints.touristSpots.byName(encodeURIComponent(spotName))));

          if (response.ok) {
            const touristSpots = await response.json();
            if (touristSpots && touristSpots.length > 0) {
              const imageUrl = touristSpots[0].图片链接;
              // 缓存URL映射
              imageUrlCache.value.set(spotName, imageUrl);
              return imageUrl;
            }
          }
          // 缓存null结果，避免重复请求失败的景点
          imageUrlCache.value.set(spotName, null);
          return null;
        } catch (error) {
          console.error(`查询景点 "${spotName}" 图片链接失败:`, error);
          imageUrlCache.value.set(spotName, null);
          return null;
        }
      });
    };

    // 加载图片并创建Icon样式
    const loadImageAndCreateIcon = async (imageUrl, feature) => {
      if (!imageUrl) return null;

      // 检查缓存
      if (imageCache.value.has(imageUrl)) {
        return imageCache.value.get(imageUrl);
      }

      // 检查是否正在加载
      if (loadingImages.value.has(imageUrl)) {
        return null; // 返回null表示正在加载,稍后会重新触发样式更新
      }

      loadingImages.value.add(imageUrl);

      try {
        return new Promise((resolve) => {
          const img = new Image();
          img.onload = () => {
            const iconStyle = new Style({
              image: new Icon({
                src: imageUrl,
                scale: 0.2, // 调整图标大小
                anchor: [0.5, 1], // 图标锚点（底部中心）
                anchorXUnits: 'fraction',
                anchorYUnits: 'fraction'
              })
            });

            // 缓存样式
            imageCache.value.set(imageUrl, iconStyle);
            loadingImages.value.delete(imageUrl);

            // 强制刷新要素样式
            if (feature) {
              feature.setStyle(iconStyle);
              feature.changed();
            }

            resolve(iconStyle);
          };

          img.onerror = () => {
            console.warn(`图片加载失败: ${imageUrl}`);
            loadingImages.value.delete(imageUrl);
            resolve(null);
          };

          img.src = imageUrl;
        });
      } catch (error) {
        console.error(`创建图片Icon失败:`, error);
        loadingImages.value.delete(imageUrl);
        return null;
      }
    };

    // 创建地图中心标记图层
    const createMapCenterLayer = () => {
      if (!mapUtilsRef.value || !mapUtilsRef.value.map) return;

      // 获取当前地图中心
      const view = mapUtilsRef.value.map.getView();
      const center = view.getCenter();

      // 创建地图钉要素
      const pinFeature = new Feature({
        geometry: new Point(center),
        name: '当前位置',
        coordinates: center
      });

      // 创建SVG地图钉样式
      const createMapPinSvg = () => {
        const svg = `<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
          <path d="M16 2C10.477 2 6 6.477 6 12c0 8 10 18 10 18s10-10 10-18c0-5.523-4.477-10-10-10z" 
                fill="#FF5722" stroke="#FFFFFF" stroke-width="2"/>
          <circle cx="16" cy="12" r="4" fill="#FFFFFF"/>
        </svg>`;
        return `data:image/svg+xml;base64,${btoa(svg)}`;
      };

      const pinStyle = new Style({
        image: new Icon({
          src: createMapPinSvg(),
          scale: 0.8,
          anchor: [0.5, 1],
          anchorXUnits: 'fraction',
          anchorYUnits: 'fraction'
        })
      });

      pinFeature.setStyle(pinStyle);

      // 创建矢量数据源并添加要素
      const centerSource = new VectorSource({
        features: [pinFeature]
      });

      // 创建矢量图层
      const centerLayer = new VectorLayer({
        source: centerSource,
        zIndex: 1000 // 确保图层在最上层
      });

      centerLayer.set('title', '当前位置');

      // 添加到地图
      mapUtilsRef.value.map.addLayer(centerLayer);

      // 保存图层引用
      mapCenterLayer.value = centerLayer;

      console.log('地图中心标记图层已创建');
    };

    // 更新地图中心标记位置
    const updateMapCenterMarker = () => {
      if (!mapCenterLayer.value || !mapUtilsRef.value) return;

      const view = mapUtilsRef.value.map.getView();
      const center = view.getCenter();

      // 获取图层中的要素
      const source = mapCenterLayer.value.getSource();
      const features = source.getFeatures();

      if (features.length > 0) {
        const pinFeature = features[0];
        // 更新要素的几何位置和属性
        pinFeature.setGeometry(new Point(center));
        pinFeature.set('coordinates', center);
      }
    };

    // 提供 mapUtils 实例给子组件
    provide("mapUtils", mapUtilsRef);

    // 提供图片缓存系统给子组件
    provide("imageCache", {
      imageCache,
      imageUrlCache,
      loadingImages,
      fetchTouristSpotImageUrl,
      loadImageAndCreateIcon
    });

    // 提供地图中心标记更新函数给子组件
    provide("updateMapCenterMarker", updateMapCenterMarker);

    // 提供选中景区信息给子组件
    const selectedSpotInfo = ref(null);
    provide("selectedSpotInfo", selectedSpotInfo);

    // 提供设置选中景区信息的函数给子组件
    const setSelectedSpotInfo = (spotInfo) => {
      selectedSpotInfo.value = spotInfo;
    };
    provide("setSelectedSpotInfo", setSelectedSpotInfo);

    // 提供景区点击事件回调注册函数
    const spotClickCallbacks = ref([]);
    const registerSpotClickCallback = (callback) => {
      spotClickCallbacks.value.push(callback);
      console.log('景区点击回调已注册，当前回调数量:', spotClickCallbacks.value.length);
    };
    provide("registerSpotClickCallback", registerSpotClickCallback);

    // 触发所有注册的景区点击回调
    const triggerSpotClickCallbacks = (spotInfo) => {
      console.log('触发景区点击回调，spotInfo:', spotInfo);
      spotClickCallbacks.value.forEach(callback => {
        try {
          callback(spotInfo);
        } catch (error) {
          console.error('景区点击回调执行失败:', error);
        }
      });
    };

    // 处理从地图点击的景区信息
    const handleSpotClickFromMap = (spotInfo) => {
      console.log('收到地图点击的景区信息:', spotInfo);
      
      // 设置选中的景区信息
      setSelectedSpotInfo(spotInfo);
      
      // 触发所有注册的回调函数
      triggerSpotClickCallbacks(spotInfo);
      
      console.log('景区信息已传递给搜索组件:', spotInfo.name);
    };
    
    // 智能数据缓存
    const dataCache = ref({
      cachedExtent: null,      // 已缓存数据的范围 [minLon, minLat, maxLon, maxLat]
      cachedZoomLevel: null,   // 缓存时的缩放级别
      cachedData: null,        // 缓存的数据
      cachedLevels: [],        // 缓存时请求的景区等级
      lastRequestTime: null    // 最后请求时间
    });

    // 可绘制的几何类型
    const drawTypes = ["Point", "LineString", "Polygon", "Circle"];

    // 初始化地图
    const initMap = () => {
      if (!mapElement.value) return;

      // 创建地图实例并赋值给响应式引用
      const mapUtils = new MapUtils(mapElement.value);
      mapUtilsRef.value = mapUtils;

      // 等待地图完全初始化
      mapUtils.ready

        .then(() => {

          if (!mapUtils || !mapUtils.map) {

            throw new Error('Map instance unavailable after initialization');

          }



          // 添加底图

          baseLayers.value = mapUtils.addBaseLayer();



          // 根据当前缩放级别加载景区图层

          const sightLayer = mapUtils.createZoomBasedVectorLayer(

            'level',

            {

              type: 'discrete',

              values: [

                { value: '5A', minZoom: 0 },

                { value: '4A', minZoom: 8 },

                { value: '3A', minZoom: 10 },

                { value: '2A', minZoom: 12 },

                { value: '1A', minZoom: 14 }

              ]

            },

            '景区',

            {

              styleFunction: getSightStyle,

              debounceDelay: 300

            }

          );



          sightLayerRef.value = sightLayer;



          // vectorLayer.value = mapUtils.createVectorLayer({

          //   fillColor: "rgba(255, 255, 255, 0.2)",

          //   strokeColor: "#4CAF50",

          //   strokeWidth: 2,

          //   pointColor: "#4CAF50",

          // });



          // vectorLayer.value.set("title", "绘制图层");

          // mapUtils.map.addLayer(vectorLayer.value);



          // modifyInteraction.value = mapUtils.addModifyInteraction(vectorLayer.value);



          setupMapListeners();

          createMapCenterLayer();



          setTimeout(() => {

            createPopupOverlay();

          }, 200);



          setTimeout(() => {

            fetchGeoJsonByExtent();

          }, 500);



          console.log('地图初始化完成，MapUtils 实例已注入');

        })

        .catch((error) => {

          console.error('地图初始化失败:', error);

        });

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

    // ==================== 范围选择功能 ====================

    // 激活范围选择
    const activateExtentDraw = (callback) => {
      if (!mapUtilsRef.value || !mapUtilsRef.value.map) {
        console.error('地图未初始化');
        return;
      }

      // 保存回调函数
      extentSelectCallback.value = callback;

      // 创建范围选择图层
      if (!extentDrawLayer.value) {
        extentDrawLayer.value = new VectorLayer({
          source: new VectorSource(),
          style: new Style({
            fill: new Fill({
              color: 'rgba(33, 150, 243, 0.2)'
            }),
            stroke: new Stroke({
              color: '#2196F3',
              width: 2,
              lineDash: [5, 5]
            })
          }),
          zIndex: 1000
        });
        extentDrawLayer.value.set('title', '范围选择图层');
        mapUtilsRef.value.map.addLayer(extentDrawLayer.value);
      }

      // 清除之前的范围
      extentDrawLayer.value.getSource().clear();

      // 禁用地图拖拽和其他可能干扰的交互
      const map = mapUtilsRef.value.map;

      // 打印所有交互类型以便调试
      console.log('当前所有交互:');
      map.getInteractions().forEach((interaction, index) => {
        console.log(`交互 ${index}:`, interaction.constructor.name, '- active:', interaction.getActive());
      });

      // 禁用**所有**可能干扰绘制的交互（除了必要的缩放）
      const interactionsToDisable = [];
      map.getInteractions().forEach((interaction) => {
        const name = interaction.constructor.name;
        // 只保留缩放相关的交互，禁用所有其他交互
        if (name !== 'MouseWheelZoom' && name !== 'PinchZoom' && name !== 'KeyboardZoom') {
          if (interaction.getActive()) {
            interaction.setActive(false);
            interactionsToDisable.push({ interaction, name });
            console.log(`已临时禁用 ${name} 交互`);
          }
        }
      });

      // 保存被禁用的交互以便恢复
      savedDragPanInteraction.value = interactionsToDisable;

      // 临时移除singleclick和moveend事件监听器，避免干扰绘制
      if (singleClickListenerKey.value) {
        map.un('singleclick', handleFeatureClick);
        console.log('已临时移除点击事件监听器');
      }

      if (moveendListenerKey.value) {
        map.un('moveend', handleMapMoveEnd);
        console.log('已临时移除moveend事件监听器');
      }

      // 🎯 使用手动事件监听实现范围选择（最可靠的方法）
      console.log('🎯 准备手动监听地图事件实现范围选择');

      // 手动监听鼠标事件
      const handlePointerDown = (evt) => {
        isDrawing.value = true;
        startPixel.value = evt.pixel;
        console.log('🖱️ 开始绘制，起始点:', evt.pixel);

        // 清除之前的绘制
        extentDrawLayer.value.getSource().clear();
      };

      const handlePointerMove = (evt) => {
        if (!isDrawing.value) return;

        endPixel.value = evt.pixel;

        // 计算范围的四个角点（像素坐标）
        const minX = Math.min(startPixel.value[0], endPixel.value[0]);
        const minY = Math.min(startPixel.value[1], endPixel.value[1]);
        const maxX = Math.max(startPixel.value[0], endPixel.value[0]);
        const maxY = Math.max(startPixel.value[1], endPixel.value[1]);

        // 转换为地图坐标
        const coords = [
          map.getCoordinateFromPixel([minX, minY]),
          map.getCoordinateFromPixel([maxX, minY]),
          map.getCoordinateFromPixel([maxX, maxY]),
          map.getCoordinateFromPixel([minX, maxY]),
          map.getCoordinateFromPixel([minX, minY])
        ];

        // 更新或创建绘制要素
        if (drawFeature.value) {
          drawFeature.value.getGeometry().setCoordinates([coords]);
        } else {
          drawFeature.value = new Feature({
            geometry: new Polygon([coords])
          });
          extentDrawLayer.value.getSource().addFeature(drawFeature.value);
        }
      };

      const handlePointerUp = (evt) => {
        if (!isDrawing.value) return;

        isDrawing.value = false;
        endPixel.value = evt.pixel;

        console.log('✅ 绘制完成，结束点:', evt.pixel);

        // 计算最终范围
        const minX = Math.min(startPixel.value[0], endPixel.value[0]);
        const minY = Math.min(startPixel.value[1], endPixel.value[1]);
        const maxX = Math.max(startPixel.value[0], endPixel.value[0]);
        const maxY = Math.max(startPixel.value[1], endPixel.value[1]);

        const minCoord = map.getCoordinateFromPixel([minX, minY]);
        const maxCoord = map.getCoordinateFromPixel([maxX, maxY]);

        const extent = [minCoord[0], minCoord[1], maxCoord[0], maxCoord[1]];
        console.log('📍 选择的范围:', extent);

        // 调用回调函数
        if (extentSelectCallback.value) {
          extentSelectCallback.value(extent);
        }

        // 延迟清除
        setTimeout(() => {
          deactivateExtentDraw();
        }, 1000);
      };

      // 绑定事件
      map.on('pointerdown', handlePointerDown);
      map.on('pointermove', handlePointerMove);
      map.on('pointerup', handlePointerUp);

      // 保存事件处理器引用以便移除
      extentDrawInteraction.value = {
        handlePointerDown,
        handlePointerMove,
        handlePointerUp
      };

      console.log('✨ 范围选择已激活，请在地图上拖拽绘制矩形');
    };

    // 停用范围选择
    const deactivateExtentDraw = () => {
      if (!mapUtilsRef.value || !mapUtilsRef.value.map) return;

      const map = mapUtilsRef.value.map;

      // 移除手动绑定的事件监听器
      if (extentDrawInteraction.value) {
        map.un('pointerdown', extentDrawInteraction.value.handlePointerDown);
        map.un('pointermove', extentDrawInteraction.value.handlePointerMove);
        map.un('pointerup', extentDrawInteraction.value.handlePointerUp);
        extentDrawInteraction.value = null;
        console.log('已移除范围选择事件监听器');
      }

      // 重置绘制状态
      isDrawing.value = false;
      startPixel.value = null;
      endPixel.value = null;
      drawFeature.value = null;

      // 清除范围选择图层内容
      if (extentDrawLayer.value) {
        const layer = extentDrawLayer.value;
        const source = layer.getSource ? layer.getSource() : null;
        if (source) {
          source.clear();
        }
        if (map && typeof map.removeLayer === 'function') {
          const layers = map.getLayers()?.getArray?.();
          if (Array.isArray(layers) && layers.includes(layer)) {
            map.removeLayer(layer);
          }
        }
        extentDrawLayer.value = null;
      }

      // 恢复被禁用的交互
      if (savedDragPanInteraction.value && Array.isArray(savedDragPanInteraction.value)) {
        savedDragPanInteraction.value.forEach(({ interaction, name }) => {
          interaction.setActive(true);
          console.log(`已恢复 ${name} 交互`);
        });
        savedDragPanInteraction.value = null;
      }

      // 恢复singleclick事件监听器
      if (singleClickListenerKey.value && mapUtilsRef.value && mapUtilsRef.value.map) {
        singleClickListenerKey.value = mapUtilsRef.value.map.on('singleclick', handleFeatureClick);
        console.log('已恢复点击事件监听器');
      }

      // 恢复moveend事件监听器
      if (moveendListenerKey.value && mapUtilsRef.value && mapUtilsRef.value.map) {
        moveendListenerKey.value = mapUtilsRef.value.map.on('moveend', handleMapMoveEnd);
        console.log('已恢复moveend事件监听器');
      }

      // 清除回调
      extentSelectCallback.value = null;

      console.log('范围选择已停用');
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

    // 防抖函数
    const debounce = (func, wait) => {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    };

    // 异步获取要素的图片样式
    const getFeatureImageStyle = async (feature) => {
      const spotName = feature.get('name'); // 获取要素名称
      if (!spotName) return null;
      
      // 先尝试从缓存中获取图片URL
      const cachedImageUrl = feature.get('cachedImageUrl');
      if (cachedImageUrl) {
        const cachedStyle = imageCache.value.get(cachedImageUrl);
        if (cachedStyle) return cachedStyle;
      }
      
      // 查询图片链接
      const imageUrl = await fetchTouristSpotImageUrl(spotName);
      if (!imageUrl) return null;
      
      // 缓存图片URL到要素属性
      feature.set('cachedImageUrl', imageUrl);
      
      // 加载图片并创建样式
      return await loadImageAndCreateIcon(imageUrl, feature);
    };

    // 根据景区等级设置不同样式（支持图片icon和聚合）
    const getSightStyle = (feature) => {
      // 检查是否为聚合要素
      const features = feature.get('features');
      if (features && features.length > 1) {
        // 关键修复：只统计可见要素，过滤掉 visible=false 的要素
        const visibleFeatures = features.filter(f => f.get('visible') !== false);
        const size = visibleFeatures.length;

        // 如果没有可见要素，返回空样式隐藏聚合点
        if (size === 0) {
          return [];
        }

        // 收集可见子要素的属性
        const childFeatures = visibleFeatures.map(f => ({
          name: f.get('name'),
          level: f.get('level'),
          id: f.getId(),
          properties: f.getProperties()
        }));

        // 设置聚合要素的属性（只包含可见要素）
        feature.set('clusteredFeatures', childFeatures);
        feature.set('featureCount', size);

        // 统计等级分布（只统计可见要素）
        const levelCounts = {};
        visibleFeatures.forEach(f => {
          const level = f.get('level');
          levelCounts[level] = (levelCounts[level] || 0) + 1;
        });
        feature.set('levelDistribution', levelCounts);

        // 根据主要等级决定颜色
        const mainLevel = Object.keys(levelCounts).sort((a, b) =>
          levelCounts[b] - levelCounts[a]
        )[0];

        let clusterColor;
        switch(mainLevel) {
          case '5A': clusterColor = 'rgba(255, 87, 34, 0.8)'; break;  // 红色
          case '4A': clusterColor = 'rgba(76, 175, 80, 0.8)'; break;  // 绿色
          case '3A': clusterColor = 'rgba(33, 150, 243, 0.8)'; break; // 蓝色
          case '2A': clusterColor = 'rgba(156, 39, 176, 0.8)'; break; // 紫色
          case '1A': clusterColor = 'rgba(255, 152, 0, 0.8)'; break;  // 橙色
          default: clusterColor = 'rgba(158, 158, 158, 0.8)';         // 灰色
        }

        return new Style({
          image: new Circle({
            radius: Math.min(10 + size / 5, 30), // 根据数量调整大小
            fill: new Fill({ color: clusterColor }),
            stroke: new Stroke({
              color: '#fff',
              width: 2
            })
          }),
          text: new Text({
            text: size.toString(),
            fill: new Fill({ color: '#fff' }),
            font: 'bold 12px sans-serif'
          })
        });
      }

      // 单个要素
      const singleFeature = features && features.length === 1 ? features[0] : feature;

      // 关键修复：如果是聚合要素中的单个要素，确保属性正确传递
      if (features && features.length === 1) {
        // 将原始要素的属性复制到聚合要素上，确保点击时能获取到完整属性
        const originalProperties = singleFeature.getProperties();
        Object.keys(originalProperties).forEach(key => {
          if (!feature.get(key) && key !== 'features' && key !== 'geometry') {
            feature.set(key, originalProperties[key]);
          }
        });

        // 设置标记，表示这是单个要素的聚合
        feature.set('isSingleFeatureCluster', true);
        feature.set('originalFeature', singleFeature);
      }

      // 检查要素是否应该可见
      const isVisible = singleFeature.get('visible');
      if (isVisible === false) {
        // 要素不可见，清除图片样式标记，返回空样式数组
        singleFeature.unset('hasImageStyle');
        return [];
      }

      // 关键优化：优先使用预加载的图片样式
      const preloadedStyle = singleFeature.get('preloadedImageStyle');
      if (preloadedStyle) {
        console.log(`[单要素聚合] 使用预加载图片: ${singleFeature.get('name')}`);
        return preloadedStyle;
      }

      // 检查要素是否已经有图片样式（通过检查自定义样式）
      const customStyle = singleFeature.getStyle();
      if (customStyle && customStyle !== getSightStyle) {
        // 已经有自定义图片样式，返回 undefined 让要素使用自己的样式
        return undefined;
      }

      // 检查缓存的图片URL
      const cachedImageUrl = singleFeature.get('cachedImageUrl');
      if (cachedImageUrl && imageCache.value.has(cachedImageUrl)) {
        // 图片已缓存，直接返回缓存的样式
        const cachedStyle = imageCache.value.get(cachedImageUrl);
        console.log(`[单要素聚合] 使用缓存图片: ${singleFeature.get('name')}`);
        return cachedStyle;
      }

      // 兜底策略：异步加载图片（预加载未完成或失败的情况）
      // 使用标记避免重复触发
      if (!singleFeature.get('imageLoadingStarted')) {
        singleFeature.set('imageLoadingStarted', true);

        console.log(`[单要素聚合] 异步加载图片: ${singleFeature.get('name')}`);

        getFeatureImageStyle(singleFeature).then(imageStyle => {
          if (imageStyle) {
            // 再次检查要素是否应该可见（防止异步加载期间状态变化）
            const isStillVisible = singleFeature.get('visible');
            if (isStillVisible !== false) {
              // 只有在要素可见时才应用图片样式
              singleFeature.setStyle(imageStyle);
              singleFeature.set('preloadedImageStyle', imageStyle); // 缓存到预加载属性
              singleFeature.changed(); // 强制刷新要素显示
              console.log(`[单要素聚合] 异步加载成功: ${singleFeature.get('name')}`);
            }
          }
        }).catch(error => {
          console.error('[单要素聚合] 获取图片样式失败:', error);
        });
      }

      // 返回默认的圆形样式作为临时样式（仅当要素可见时）
      const level = singleFeature.get('level'); // 获取景区等级
      let color, radius, strokeWidth;
      
      switch(level) {
        case '5A':
          color = '#FF5722'; // 红色 - 最高等级
          radius = 10;
          strokeWidth = 3;
          break;
        case '4A':
          color = '#4CAF50'; // 绿色
          radius = 8;
          strokeWidth = 2.5;
          break;
        case '3A':
          color = '#2196F3'; // 蓝色
          radius = 6;
          strokeWidth = 2;
          break;
        case '2A':
          color = '#9C27B0'; // 紫色
          radius = 5;
          strokeWidth = 1.5;
          break;
        case '1A':
          color = '#FF9800'; // 橙色
          radius = 4;
          strokeWidth = 1;
          break;
        default:
          color = '#9E9E9E'; // 灰色
          radius = 4;
          strokeWidth = 1;
      }
      
      return new Style({
        image: new Circle({
          radius: radius,
          fill: new Fill({ color: color }),
          stroke: new Stroke({
            color: '#FFFFFF',
            width: strokeWidth
          })
        })
      });
    };

    // 根据当前缩放级别确定要请求的景区等级
    const getLevelsByZoom = (zoom) => {
      if (zoom >= 14) {
        return ['5A', '4A', '3A', '2A', '1A']; // 显示所有等级
      } else if (zoom >= 12) {
        return ['5A', '4A', '3A', '2A']; // 显示5A-2A
      } else if (zoom >= 10) {
        return ['5A', '4A', '3A']; // 显示5A-3A
      } else if (zoom >= 8) {
        return ['5A', '4A']; // 显示5A-4A
      } else {
        return ['5A']; // 缩放级别低于8时只显示5A景区
      }
    };

    // 检查当前范围是否在缓存范围内
    const isExtentWithinCache = (currentExtent, cachedExtent) => {
      if (!cachedExtent) return false;
      
      const [currentMinLon, currentMinLat, currentMaxLon, currentMaxLat] = currentExtent;
      const [cachedMinLon, cachedMinLat, cachedMaxLon, cachedMaxLat] = cachedExtent;
      
      // 检查当前范围是否完全在缓存范围内
      return currentMinLon >= cachedMinLon && 
             currentMinLat >= cachedMinLat && 
             currentMaxLon <= cachedMaxLon && 
             currentMaxLat <= cachedMaxLat;
    };

    // 检查是否需要重新请求数据
    const shouldRequestData = (currentExtent, currentZoom, currentLevels) => {
      const cache = dataCache.value;
      
      // 如果没有缓存数据，需要请求
      if (!cache.cachedExtent || !cache.cachedData) {
        console.log('无缓存数据，需要请求');
        return true;
      }
      
      // 检查缩放级别变化
      const zoomDiff = Math.abs(currentZoom - cache.cachedZoomLevel);
      
      // 如果缩放级别变化超过2级，需要重新请求
      if (zoomDiff > 2) {
        console.log(`缩放级别变化超过阈值 (${zoomDiff.toFixed(1)}级)，需要重新请求`);
        return true;
      }
      
      // 检查缓存的等级是否包含当前需要的所有等级
      const cachedLevelsSet = new Set(cache.cachedLevels || []);
      const hasAllLevels = currentLevels.every(level => cachedLevelsSet.has(level));

      // 如果缓存不包含所有需要的等级，必须重新请求
      if (!hasAllLevels) {
        const missingLevels = currentLevels.filter(level => !cachedLevelsSet.has(level));
        console.log(`缓存缺少等级 [${missingLevels.join(', ')}]，需要重新请求`);
        return true;
      }

      // 检查当前范围是否在缓存范围内
      const isWithinCache = isExtentWithinCache(currentExtent, cache.cachedExtent);
      if (isWithinCache) {
        console.log(`当前范围在缓存范围内且缓存包含所有需要的等级 (缓存: ${cache.cachedLevels?.join(',')}, 需要: ${currentLevels.join(',')})，使用缓存数据`);
        return false;
      }
      
      // 如果当前范围超出缓存范围，需要重新请求
      console.log('当前范围超出缓存范围，需要重新请求');
      return true;
    };

    // 更新缓存
    const updateDataCache = (extent, zoom, levels, data) => {
      dataCache.value = {
        cachedExtent: [extent.minLon, extent.minLat, extent.maxLon, extent.maxLat],
        cachedZoomLevel: zoom,
        cachedData: data,
        cachedLevels: [...levels],
        lastRequestTime: Date.now()
      };
      console.log('数据缓存已更新');
    };

    // ==================== 弹窗和高亮相关函数 ====================

    // 创建弹窗 Overlay
    const createPopupOverlay = () => {
      if (!featurePopupRef.value || !mapUtilsRef.value) return;

      // 安全地获取 popup 元素
      const popupElement = featurePopupRef.value.$el || featurePopupRef.value;
      
      // 验证 popupElement 是否为有效的 DOM 元素
      if (!popupElement || typeof popupElement !== 'object' || !popupElement.nodeType) {
        console.warn('无效的弹窗元素，无法创建 Overlay');
        return;
      }

      try {
        popupOverlay.value = new Overlay({
          element: popupElement,
          positioning: 'bottom-center',
          stopEvent: true,
          offset: [0, -15],
          autoPan: false, // 禁用自动平移以避免DOM元素问题
        });

        mapUtilsRef.value.map.addOverlay(popupOverlay.value);
        console.log('弹窗 Overlay 已创建');
      } catch (error) {
        console.error('创建弹窗 Overlay 失败:', error);
      }
    };

    // 显示弹窗
    const showPopup = (properties, coordinate) => {
      // 确保弹窗 Overlay 已创建
      if (!popupOverlay.value) {
        createPopupOverlay();
      }

      // 再次检查 Overlay 是否成功创建
      if (!popupOverlay.value) {
        console.warn('弹窗 Overlay 创建失败，跳过显示');
        return;
      }

      popupProperties.value = properties;
      popupVisible.value = true;

      // 使用 nextTick 确保 DOM 更新完成后再设置位置
      nextTick(() => {
        // 再次验证元素是否已挂载到DOM
        const popupElement = featurePopupRef.value?.$el || featurePopupRef.value;
        if (popupOverlay.value && popupElement && popupElement.parentNode) {
          popupOverlay.value.setPosition(coordinate);
        } else {
          console.warn('弹窗元素未正确挂载到DOM，延迟设置位置');
          setTimeout(() => {
            if (popupOverlay.value) {
              popupOverlay.value.setPosition(coordinate);
            }
          }, 100);
        }
      });

      console.log('显示弹窗:', properties);
    };

    // 关闭弹窗
    const closePopup = () => {
      popupVisible.value = false;
      if (popupOverlay.value) {
        popupOverlay.value.setPosition(undefined);
      }
      clearHighlight();
      console.log('弹窗已关闭');
    };

    // 高亮要素
    const highlightFeature = (feature, layer) => {
      // 先清除之前的高亮
      clearHighlight();

      if (!feature) return;

      // 保存原始样式
      originalFeatureStyle.value = feature.getStyle();
      currentHighlightedFeature.value = feature;
      currentHighlightedLayer.value = layer;

      // 创建高亮样式
      const highlightStyle = new Style({
        fill: new Fill({
          color: 'rgba(255, 215, 0, 0.4)'
        }),
        stroke: new Stroke({
          color: '#FFD700',
          width: 4,
          lineDash: [5, 5]
        }),
        image: new Circle({
          radius: 8,
          fill: new Fill({
            color: '#FFD700'
          }),
          stroke: new Stroke({
            color: '#000000',
            width: 2
          })
        })
      });

      // 应用高亮样式
      feature.setStyle(highlightStyle);
      console.log('要素已高亮');
    };

    // 清除高亮
    const clearHighlight = () => {
      if (currentHighlightedFeature.value) {
        // 恢复原始样式
        if (originalFeatureStyle.value) {
          currentHighlightedFeature.value.setStyle(originalFeatureStyle.value);
        } else {
          currentHighlightedFeature.value.setStyle(null);
        }

        // 强制刷新要素显示
        currentHighlightedFeature.value.changed();

        // 重置状态
        currentHighlightedFeature.value = null;
        originalFeatureStyle.value = null;
        currentHighlightedLayer.value = null;

        console.log('高亮已清除');
      }
    };

    // 处理要素点击事件
    const handleFeatureClick = (evt) => {
      if (!mapUtilsRef.value) return;

      console.log('=== 地图点击事件触发 ===');
      console.log('点击坐标:', evt.coordinate);
      console.log('点击像素:', evt.pixel);

      const map = mapUtilsRef.value.map;
      let clickedFeature = null;
      let clickedLayer = null;

      // 查找点击到的要素
      map.forEachFeatureAtPixel(evt.pixel, (feature, layer) => {
        if (!clickedFeature) {
          clickedFeature = feature;
          clickedLayer = layer;
          console.log('找到要素:', feature);
          console.log('图层:', layer?.get?.('title'));
        }
      });

      if (!clickedFeature) {
        closePopup();
        console.log('没有点击到要素');
        return;
      }

      // 检查是否为聚合要素
      const clusteredFeatures = clickedFeature.get('clusteredFeatures');
      const clusterFeatures = clickedFeature.get('features');

      if ((clusteredFeatures && clusteredFeatures.length > 0) || (clusterFeatures && clusterFeatures.length > 0)) {
        // 处理聚合要素
        handleClusterFeatureClick(clickedFeature, clusteredFeatures || clusterFeatures, evt.coordinate, clickedLayer);
      } else {
        // 处理普通要素
        handleSingleFeatureClick(clickedFeature, evt.coordinate, clickedLayer);
      }
    };

    // 处理聚合要素点击
    const handleClusterFeatureClick = (clusterFeature, features, coordinate, layer) => {
      // 过滤可见要素
      const visibleFeatures = features.filter(f => {
        if (f.get) {
          return f.get('visible') !== false;
        }
        return true;
      });

      const featureCount = visibleFeatures.length;

      if (featureCount === 0) {
        closePopup();
        console.log('聚合要素中没有可见要素');
        return;
      }

      if (featureCount === 1) {
        // 单个要素的聚合
        const singleFeature = visibleFeatures[0];
        let properties = {};

        if (singleFeature.getProperties) {
          properties = singleFeature.getProperties();
        } else if (typeof singleFeature === 'object' && singleFeature.properties) {
          properties = { ...singleFeature.properties };
        } else if (typeof singleFeature === 'object') {
          properties = { ...singleFeature };
        }

        highlightFeature(clusterFeature, layer);
        showPopup(properties, coordinate);

        // 调用景区点击回调
        if (properties.name) {
          handleSpotClickFromMap({
            name: properties.name,
            level: properties.level,
            coordinates: coordinate,
            properties: properties
          });
        }

        console.log('显示单个聚合要素属性:', properties);
      } else {
        // 多个要素的聚合
        const levelDistribution = {};

        visibleFeatures.forEach(feature => {
          const level = feature.get ? feature.get('level') : (feature.level || feature.properties?.level);
          if (level) {
            levelDistribution[level] = (levelDistribution[level] || 0) + 1;
          }
        });

        const levelText = Object.entries(levelDistribution)
          .sort((a, b) => b[1] - a[1])
          .map(([level, count]) => `${level}: ${count}个`)
          .join(', ');

        const featuresList = visibleFeatures
          .slice(0, 10)
          .map((f, i) => {
            const name = f.get ? f.get('name') : (f.name || f.properties?.name || '未知');
            const level = f.get ? f.get('level') : (f.level || f.properties?.level || '未知');
            return `${i + 1}. ${name} (${level})`;
          })
          .join('\n');

        const clusterInfo = {
          '📍 类型': '聚合要素',
          '🔢 总数': `${featureCount} 个景区`,
          '📊 等级分布': levelText,
          '📋 包含景区': featuresList + (featureCount > 10 ? `\n... 还有 ${featureCount - 10} 个景区` : '')
        };

        showPopup(clusterInfo, coordinate);
        console.log('显示聚合要素信息:', clusterInfo);

        // 触发景区点击回调，传递多个景区信息
        const spotNames = visibleFeatures
          .map(f => f.get ? f.get('name') : (f.name || f.properties?.name))
          .filter(name => name);

        if (spotNames.length > 0) {
          handleSpotClickFromMap({
            isCluster: true,
            count: featureCount,
            names: spotNames,
            levelDistribution: levelDistribution,
            coordinates: coordinate,
            features: visibleFeatures
          });
        }
      }
    };

    // 处理单个要素点击
    const handleSingleFeatureClick = (feature, coordinate, layer) => {
      highlightFeature(feature, layer);
      const properties = feature.getProperties();

      console.log('=== 普通要素属性 ===');
      console.log('属性:', properties);

      showPopup(properties, coordinate);

      // 调用景区点击回调
      if (properties.name) {
        handleSpotClickFromMap({
          name: properties.name,
          level: properties.level,
          coordinates: coordinate,
          properties: properties
        });
      }

      console.log('要素高亮并显示属性弹窗');
    };

    // ==================== 地图事件监听 ====================

    // 设置地图事件监听
    const setupMapListeners = () => {
      if (!mapUtilsRef.value || !mapUtilsRef.value.map) return;

      const map = mapUtilsRef.value.map;
      const view = map.getView();

      // 监听移动结束事件 - 当用户拖拽地图结束时触发，并保存key
      moveendListenerKey.value = map.on('moveend', handleMapMoveEnd);

      // 监听缩放结束事件 - 当用户缩放地图结束时触发
      view.on('change:resolution', debounce(handleZoomEnd, 300));

      // 绑定要素点击事件，并保存监听器key以便后续移除
      singleClickListenerKey.value = map.on('singleclick', handleFeatureClick);

      console.log('地图事件监听已设置，包括要素点击事件');
    };

    // 处理地图移动结束事件
    const handleMapMoveEnd = debounce(() => {
      console.log('地图移动结束，请求当前视图范围内的景区数据');
      fetchGeoJsonByExtent();
    }, 300);

    // 处理缩放结束事件
    const handleZoomEnd = () => {
      console.log('地图缩放结束，请求当前视图范围内的景区数据');
      fetchGeoJsonByExtent();
    };

    // 获取当前视图范围内的景区数据
    const fetchGeoJsonByExtent = async () => {
      if (!mapUtilsRef.value || !sightLayerRef.value) return;
      
      isLoading.value = true;
      
      try {
        // 获取当前视图范围和缩放级别
        const extent = mapUtilsRef.value.getViewExtent({ formatted: true });
        const currentZoom = mapUtilsRef.value.map.getView().getZoom();
        
        // 根据当前缩放级别确定要请求的景区等级
        const levelsToRequest = getLevelsByZoom(currentZoom);
        
        // 构建当前范围数组用于缓存判断
        const currentExtent = [extent.minLon, extent.minLat, extent.maxLon, extent.maxLat];
        
        // 智能判断是否需要重新请求数据
        const needRequest = shouldRequestData(currentExtent, currentZoom, levelsToRequest);
        
        if (!needRequest) {
          // 使用缓存数据
          console.log('使用缓存数据，跳过网络请求');
          const cache = dataCache.value;

          // 验证缓存数据有效性
          if (!cache.cachedData) {
            console.warn('缓存数据为空，跳过添加');
            isLoading.value = false;
            return;
          }

          // 将缓存数据添加到景区图层
          const mapUtils = mapUtilsRef.value;
          if (mapUtils && mapUtils.addGeoJsonToLayer) {
            try {
              const result = await mapUtils.addGeoJsonToLayer(
                sightLayerRef.value,
                cache.cachedData,
                {
                  clearExisting: false,
                  autoFitExtent: false,
                  skipDuplicates: true
                }
              );

              console.log(`使用缓存数据成功添加 ${result.addedCount} 个景区要素`);

              // 刷新可见性
              mapUtils.refreshZoomBasedLayerVisibility(sightLayerRef.value);
            } catch (error) {
              console.error('使用缓存数据失败:', error);
            }
          }

          isLoading.value = false;
          return;
        }
        
        // 需要重新请求数据
        console.log(`缩放级别 ${currentZoom.toFixed(1)}，请求等级: ${levelsToRequest.join(', ')}`);
        
        // 构建请求参数
        const requestData = {
          minLon: extent.minLon,
          minLat: extent.minLat,
          maxLon: extent.maxLon,
          maxLat: extent.maxLat,
          levels: levelsToRequest // 动态请求的等级
        };
        
        // 发送请求
        const response = await fetch(API_CONFIG.buildURL(API_CONFIG.endpoints.sights.geojsonByExtentAndLevel), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestData)
        });
        
        if (response.ok) {
          const geoJson = await response.json();

          // 验证响应数据的有效性
          if (!geoJson || typeof geoJson !== 'object') {
            console.error('响应数据无效或为空:', geoJson);
            isLoading.value = false;
            return;
          }

          // 验证GeoJSON结构
          if (!geoJson.type || (geoJson.type !== 'FeatureCollection' && geoJson.type !== 'Feature')) {
            console.error('响应数据不是有效的GeoJSON格式:', geoJson);
            isLoading.value = false;
            return;
          }

          // 验证features数组（对于FeatureCollection），如果缺失则初始化为空数组
          if (geoJson.type === 'FeatureCollection') {
            if (!Array.isArray(geoJson.features)) {
              console.warn('FeatureCollection缺少features数组，已初始化为空数组:', geoJson);
              geoJson.features = [];
            }
          }

          extentData.value = geoJson;

          // 更新缓存
          updateDataCache(extent, currentZoom, levelsToRequest, geoJson);

          // 检查GeoJSON数据是否有效
          if (geoJson && geoJson.features && geoJson.features.length > 0) {
          // 将 GeoJSON 数据添加到景区图层
          const mapUtils = mapUtilsRef.value;
          if (mapUtils && mapUtils.addGeoJsonToLayer) {
            // 直接调用实例方法
            const result = await mapUtils.addGeoJsonToLayer(
              sightLayerRef.value,
              geoJson,
              {
                clearExisting: false, // 不清除现有要素，避免数据丢失
                autoFitExtent: false,
                skipDuplicates: true
              }
            );

            console.log(`成功添加 ${result.addedCount} 个景区要素到景区图层`);

            // 添加数据后，刷新可见性以确保正确应用缩放级别过滤
            console.log('[DEBUG] 准备刷新图层可见性, 当前缩放级别:', mapUtils.map.getView().getZoom());
            console.log('[DEBUG] 景区图层:', sightLayerRef.value);
            console.log('[DEBUG] allFeaturesSource 要素数:', sightLayerRef.value.get('allFeaturesSource')?.getFeatures().length);

            mapUtils.refreshZoomBasedLayerVisibility(sightLayerRef.value);

            console.log('[DEBUG] 刷新完成后 visibleFeaturesSource 要素数:', sightLayerRef.value.get('visibleFeaturesSource')?.getFeatures().length);

            // 关键优化：预加载要素图片，确保聚合中的单要素可以显示图片icon
            const allFeatures = sightLayerRef.value.get('allFeaturesSource')?.getFeatures() || [];
            if (allFeatures.length > 0) {
              console.log(`[图片预加载] 开始预加载 ${allFeatures.length} 个要素的图片`);

              // 异步预加载，不阻塞主流程
              mapUtils.preloadFeatureImages(
                allFeatures,
                fetchTouristSpotImageUrl,  // 图片URL获取函数
                loadImageAndCreateIcon,    // 图片加载函数
                {
                  maxConcurrent: 6,
                  batchSize: 20,
                  onProgress: (progress) => {
                    if (progress.percentage % 20 === 0) {
                      console.log(`[图片预加载] 进度: ${progress.percentage}% (${progress.completed}/${progress.total})`);
                    }
                  }
                }
              ).then(stats => {
                console.log(`[图片预加载] 完成! 成功: ${stats.loaded}, 缓存: ${stats.cached}, 失败: ${stats.failed}, 跳过: ${stats.skipped}`);
              }).catch(error => {
                console.error('[图片预加载] 失败:', error);
              });
            }

          } else {
            console.error('MapUtils实例不可用或缺少addGeoJsonToLayer方法');
          }
          } else {
            // 如果没有数据，清除图层
            if (sightLayerRef.value && sightLayerRef.value.getSource()) {
              sightLayerRef.value.getSource().clear();
            }
            console.log('当前视图范围内没有景区数据');
          }
        }
      } catch (error) {
        console.error('获取景区 GeoJSON 数据失败:', error);
      } finally {
        isLoading.value = false;
      }
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

    // 提供范围选择功能给子组件（必须在函数定义之后）
    provide("activateExtentDraw", activateExtentDraw);
    provide("deactivateExtentDraw", deactivateExtentDraw);

    // ==================== AI智能查询结果 Provide ====================

    // AI查询结果状态（用于传递给 TouristSpotSearch 组件）
    const agentQueryResult = ref(null);

    /**
     * 设置 AI 查询结果
     * 由 agent_query_bar 组件调用，用于传递查询结果给 TouristSpotSearch
     */
    const setAgentQueryResult = (result) => {
      console.log('OlMap: 接收到 AI 查询结果:', result);
      agentQueryResult.value = result;
    };

    // 将 AI 查询结果和设置函数提供给子组件
    provide("agentQueryResult", agentQueryResult);
    provide("setAgentQueryResult", setAgentQueryResult);

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
      // 弹窗相关
      featurePopupRef,
      popupVisible,
      popupProperties,
      popupTitle,
      closePopup,
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
