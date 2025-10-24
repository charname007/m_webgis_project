import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import Cluster from "ol/source/Cluster";
import OSM from "ol/source/OSM";
import { Style, Stroke, Fill, Circle, Text } from "ol/style";
import {
  Draw,
  Modify,
  Snap,
  defaults as defaultInteractions,
} from "ol/interaction";
import { getLength, getArea } from "ol/sphere";
import { LineString, Polygon, Point } from "ol/geom";
import { getCenter } from "ol/extent";
import Overlay from "ol/Overlay";
import Feature from "ol/Feature";
import {
  FullScreen,
  MousePosition,
  OverviewMap,
  ScaleLine,
  ZoomToExtent,
  defaults as defaultControls,
  ZoomSlider,
} from "ol/control";
import LayerSwitcher from "ol-ext/control/LayerSwitcher";
import Bar from "ol-ext/control/Bar";
import Overview from "ol-ext/control/Overview";
import FeatureList from "ol-ext/control/FeatureList";
import Scale from "ol-ext/control/Scale";
import SearchCoordinates from "ol-ext/control/SearchCoordinates";
import SearchFeature from "ol-ext/control/SearchFeature";

import OverlayControl from "ol-ext/control/Overlay";
import LayerShop from "ol-ext/control/LayerShop";
import Gauge from "ol-ext/control/Gauge";
import Disable from "ol-ext/control/Disable";
import CenterPosition from "ol-ext/control/CenterPosition";
import Select from "ol-ext/control/Select";
import Notification from "ol-ext/control/Notification";
import { XYZ } from "ol/source";
import "ol-ext/dist/ol-ext.min.css";
import "ol/ol.css";
import { unByKey } from "ol/Observable";
import GeoJSON from "ol/format/GeoJSON";
// import 'oles/control/Measure.css';
// import 'oles/tool/Measure.css'
// import '../assets/oles.css'
// import "https://unpkg.com/oles/lib/oles.css"
// import Measure from 'oles/control/Measure';
import '../assets/map-controls.css';
// import { proj } from "oles";

// 确保 OverviewMap 不会被 tree-shaking 移除
// const ensureOverviewMap = () => {
//   if (typeof OverviewMap === 'undefined') {
//     console.warn('OverviewMap is not available');
//   }
//   return OverviewMap;
// };

// // 强制引用 OverviewMap 确保不被 tree-shaking 移除
// ensureOverviewMap();
import {MeasureControl,LocationControl,RoutePlanningControl} from "./m_controls";
import m_controls from "./m_controls";
import API_CONFIG from "../config/api.js";
export default class MapUtils {
  constructor(target) {
    this.target = target;
    this.defaultCenter = [114.305, 30.5928]; // 武汉坐标
    this.currentCenter = [...this.defaultCenter];
    this.map = null;
    this.ready = this.#initializeMap(target);
    // 状态管理    // 状态管理 - 确保所有交互状态可追踪
    this.state = {
      // 测量相关状态
      measure: {
        draw: null,
        layer: null,
        tooltip: null,
        sketch: null,
        listener: null,
        helpTooltip: null,
        helpTooltipElement: null,
        tooltipElement: null,
        type: null, // 新增：记录当前测量类型
        overlays: [], // 新增：存储测量相关的overlay
      },
      // 绘制相关状态
      draw: {
        interaction: null,
        snap: null,
      },
      // 要素高亮相关状态
      highlight: {
        currentFeature: null, // 当前高亮的要素
        originalStyle: null, // 原始样式
        highlightedLayer: null, // 高亮要素所在的图层
      },
    };
  }

  // 初始化地图（私有方法）
  async #initializeMap(target) {
    let resolvedCenter = [...this.defaultCenter];
    const geolocationAvailable = typeof navigator !== 'undefined' && navigator.geolocation;

    if (geolocationAvailable) {
      try {
        const { coordinate } = await this.getCurrentPosition({
          enableHighAccuracy: true,
          timeout: 8000,
          maximumAge: 0
        });

        if (Array.isArray(coordinate) && coordinate.length === 2 && coordinate.every((value) => Number.isFinite(value))) {
          resolvedCenter = coordinate;
        }
      } catch (error) {
        console.warn('自动定位失败，使用默认中心点:', (error && error.message) ? error.message : error);
      }
    }

    this.defaultCenter = resolvedCenter;
    this.currentCenter = [...resolvedCenter];

    this.map = this.#initMap(target);
    return this.map;
  }

  #initMap(target) {
    // 中国范围定义 [minLon, minLat, maxLon, maxLat]
    this.chinaExtent = [73, 18, 135, 54];
    
    const view = new View({
      center: this.currentCenter || this.defaultCenter, // 默认武汉坐标
      zoom: 15,
      projection: "EPSG:4326",
      extent: this.chinaExtent, // 中国范围限制
      constrainResolution: true, // 限制分辨率
      maxZoom: 18, // 最大缩放级别
      minZoom: 3,  // 最小缩放级别
    });

    this.overviewControl = new Overview({
      // collapsed: false,
      layers: [new TileLayer({ source: new OSM() })],
      // view: new View({
      //   projection: "EPSG:4326",
      //   center: [116.39722, 39.9096],
      //   zoom: 6,
      // }),
      projection: "EPSG:4326",
      align: "bottom-left",
      // className: "custom-overview",
    });


    this.map = new Map({
      target: target,
      layers: [],
      view: view,
      controls: defaultControls().extend([
        new MousePosition({
          className: "custom-mouse-position",
          coordinateFormat: function (coordinate) {
            // 格式化坐标，只显示小数点后2位
            return coordinate.map((coord) => coord.toFixed(2)).join(", ");
          },
        }),
        this.overviewControl,
        new ScaleLine({
          className: "custom-scale-line",
          units: "metric",
          minWidth: 100,
        }),
        new LayerSwitcher({
          show_progress: true,
          extent: true,
          trash: true,
          reordering: true,
          collapsed: false,
        }),
        new Bar({
          className: "custom-bar",
          controls: [
            new FullScreen({ className: "custom-fullscreen" }),
            new ZoomToExtent({ className: "custom-zoom-to-extent" }),
            new MeasureControl({ className: "custom-measure" }),
            new LocationControl({ className: "custom-location" }),
            new RoutePlanningControl({
              className: "custom-location",
              baseURL: API_CONFIG.baseURL
            }),
            //             new Measure({
            //   className: "custom-measure",
            // })
          ],
        }),
        // new Scale(),
        // new OverlayControl()
        new ZoomSlider(),
        // new FeatureList(),
        // new Gauge({ className: "custom-gauge" }),
        new Disable({ className: "custom-disable" }),
        new SearchCoordinates({
          className: "custom-search-coordinates",
          projection: "EPSG:4326",
        }),
        // new LayerShop({ className: "custom-layer-shop" }),
        // new Select({ className: "custom-select" }),
        new CenterPosition({ className: "custom-center-position" }),
        new Notification({ className: "custom-notification" }),
        // new Scale({
        //   className: "custom-scale",
        //   units: "metric",
        //   minWidth: 100,
        // }),
      ]),
    });

    return this.map;
  }

  // 添加底图
  addBaseLayer(type = "osm") {
    let layer;

    switch (type) {
      case "osm":
        layer = new TileLayer({
          source: new OSM(),
          title: "OpenStreetMap",
          visible: false, // 默认隐藏OSM，显示天地图
        });
        break;
      default:
        layer = new TileLayer({
          source: new OSM(),
          title: "OpenStreetMap",
          visible: false,
        });
    }

    // 天地图栅格底图（带注记）
    const TDTMapImgLyr = new TileLayer({
      source: new XYZ({
        url: "http://t0.tianditu.gov.cn/DataServer?T=img_w&x={x}&y={y}&l={z}&tk=588e8ebb68a52a948e9139d892c87051",
      }),
      title: "天地图栅格底图",
      visible: true,
    });

    const TDTMapMKLyr = new TileLayer({
      source: new XYZ({
        url: "http://t0.tianditu.gov.cn/DataServer?T=cva_w&x={x}&y={y}&l={z}&tk=588e8ebb68a52a948e9139d892c87051",
      }),
      title: "天地图注记",
      visible: true,
    });

    // 天地图矢量底图（带注记）
    const TDTMapVecLyr = new TileLayer({
      source: new XYZ({
        url: "http://t0.tianditu.gov.cn/DataServer?T=vec_w&x={x}&y={y}&l={z}&tk=588e8ebb68a52a948e9139d892c87051",
      }),
      title: "天地图矢量底图",
      visible: false,
    });

    const layers = [layer, TDTMapImgLyr, TDTMapVecLyr, TDTMapMKLyr];

    layers.forEach((layer) => {
      this.map.addLayer(layer);
      this.overviewControl.getOverviewMap().addLayer(layer);
    });

    return layers;
  }

  // 创建矢量图层
  createVectorLayer(styleOptions = {}) {
    const style = new Style({
      fill: new Fill({
        color: styleOptions.fillColor || "rgba(255, 255, 255, 0.2)",
      }),
      stroke: new Stroke({
        color: styleOptions.strokeColor || "#ffcc33",
        width: styleOptions.strokeWidth || 2,
      }),
      image: new Circle({
        radius: styleOptions.radius || 7,
        fill: new Fill({
          color: styleOptions.pointColor || "#ffcc33",
        }),
      }),
    });

    const vectorLayer = new VectorLayer({
      source: new VectorSource(),
      style: style,
    });

    return vectorLayer;
  }

  // 添加绘制交互 - 确保与测量工具完全互斥
  addDrawInteraction(layer, type) {
    // 强制清除测量状态
    this.stopMeasureTool();

    // 清除现有绘制交互
    this.#clearDrawState();

    const draw = new Draw({
      source: layer.getSource(),
      type: type,
      style: new Style({
        fill: new Fill({ color: "rgba(255, 255, 255, 0.3)" }),
        stroke: new Stroke({ color: "#4CAF50", width: 2 }),
        image: new Circle({ radius: 6, fill: new Fill({ color: "#4CAF50" }) }),
      }),
    });

    // 添加吸附交互
    const snap = new Snap({ source: layer.getSource() });
    this.map.addInteraction(snap);
    this.state.draw.snap = snap;

    this.map.addInteraction(draw);
    this.state.draw.interaction = draw;

    return draw;
  }

  // 清除绘制状态
  #clearDrawState() {
    if (this.state.draw.interaction) {
      this.map.removeInteraction(this.state.draw.interaction);
      this.state.draw.interaction = null;
    }
    if (this.state.draw.snap) {
      this.map.removeInteraction(this.state.draw.snap);
      this.state.draw.snap = null;
    }
  }

  // 添加修改交互
  addModifyInteraction(layer) {
    const modify = new Modify({
      source: layer.getSource(),
      style: new Style({
        stroke: new Stroke({ color: "#FF5722", width: 2 }),
        image: new Circle({ radius: 6, fill: new Fill({ color: "#FF5722" }) }),
      }),
    });

    // 设置修改交互的优先级低于绘制和测量
    modify.setActive(false);
    this.map.addInteraction(modify);

    // 存储修改交互引用
    this.state.modify = modify;
    return modify;
  }

  // 初始化测量工具（核心方法）
  setupMeasureTool(measureType) {
    // 1. 清除之前的测量状态和绘制状态
    this.stopMeasureTool();
    this.#clearDrawState();
    this.clearAllInteractions();

    // 强制移除所有可能的交互
    this.map.getInteractions().forEach((interaction) => {
      if (interaction instanceof Draw || interaction instanceof Snap) {
        this.map.removeInteraction(interaction);
      }
    });

    // 记录测量类型
    this.state.measure.type = measureType;

    // 2. 创建测量专用图层
    const measureSource = new VectorSource();
    const measureLayer = new VectorLayer({
      source: measureSource,
      style: new Style({
        fill: new Fill({ color: "rgba(252, 86, 49, 0.1)" }),
        stroke: new Stroke({ color: "#fc5531", lineDash: [10, 10], width: 3 }),
        image: new Circle({
          radius: 5,
          stroke: new Stroke({ color: "rgba(0, 0, 0, 0.7)" }),
          fill: new Fill({ color: "#fc5531" }),
        }),
      }),
      title: "测量图层",
      zIndex: 100, // 确保测量图层在最上层
    });
    this.map.addLayer(measureLayer);
    this.state.measure.layer = measureLayer;

    // 3. 创建测量结果提示框
    this.#createMeasureTooltip();
    // 4. 创建操作帮助提示框
    this.#createHelpTooltip();

    // 确定绘制类型
    const drawType = measureType === "angle" ? "LineString" : measureType;
    const maxPoints = measureType === "angle" ? 3 : null;

    // 5. 创建绘制交互
    const draw = new Draw({
      source: measureSource,
      type: drawType,
      maxPoints: maxPoints,
      style: new Style({
        fill: new Fill({ color: "rgba(252, 86, 49, 0.1)" }),
        stroke: new Stroke({ color: "#fc5531", lineDash: [10, 10], width: 3 }),
        image: new Circle({
          radius: 5,
          stroke: new Stroke({ color: "rgba(0, 0, 0, 0.7)" }),
          fill: new Fill({ color: "#fc5531" }),
        }),
      }),
      stopClick: true,
    });
    this.map.addInteraction(draw);
    this.state.measure.draw = draw;

    // 6. 绑定绘制事件（核心交互逻辑）
    this.#bindDrawEvents(measureType);

    // 7. 绑定鼠标移动事件（显示帮助提示）
    this.map.on("pointermove", this.#handlePointerMove.bind(this));

    return {
      draw: draw,
      layer: measureLayer,
      tooltip: this.state.measure.tooltip,
    };
  }

  // 停止测量工具 - 彻底清除所有相关元素
  // 修改mapUtils.js中的stopMeasureTool方法
  stopMeasureTool() {
    // 移除绘制交互
    if (this.state.measure.draw) {
      this.map.removeInteraction(this.state.measure.draw);
      this.state.measure.draw = null;
    }

    // 移除测量图层及内容
    if (this.state.measure.layer) {
      this.map.removeLayer(this.state.measure.layer);
      this.state.measure.layer = null;
    }

    // 移除提示框
    if (this.state.measure.tooltip) {
      this.map.removeOverlay(this.state.measure.tooltip);
      this.state.measure.tooltip = null;
    }
    if (this.state.measure.helpTooltip) {
      this.map.removeOverlay(this.state.measure.helpTooltip);
      this.state.measure.helpTooltip = null;
    }
    this.clearMeasureResults();

    // 移除DOM元素
    if (
      this.state.measure.tooltipElement &&
      this.state.measure.tooltipElement.parentNode
    ) {
      this.state.measure.tooltipElement.parentNode.removeChild(
        this.state.measure.tooltipElement
      );
      this.state.measure.tooltipElement = null;
    }
    if (
      this.state.measure.helpTooltipElement &&
      this.state.measure.helpTooltipElement.parentNode
    ) {
      this.state.measure.helpTooltipElement.parentNode.removeChild(
        this.state.measure.helpTooltipElement
      );
      this.state.measure.helpTooltipElement = null;
    }

    // 移除事件监听
    if (this.state.measure.listener) {
      unByKey(this.state.measure.listener);
      this.state.measure.listener = null;
    }
    this.map.un("pointermove", this.#handlePointerMove.bind(this));

    // 重置绘制要素
    this.state.measure.sketch = null;
  }
  // 清除测量结果但不停止测量模式
  clearMeasureResults() {
    if (this.state.measure.layer) {
      this.state.measure.layer.getSource().clear();
    }

    // 清除所有测量相关的overlay
    this.state.measure.overlays.forEach((overlay) => {
      this.map.removeOverlay(overlay);
    });
    this.state.measure.overlays = [];

    if (this.state.measure.tooltipElement) {
      this.state.measure.tooltipElement.innerHTML = "";
    }
  }

  // 删除最后一个测量结果
  deleteLastMeasure() {
    if (!this.state.measure.layer) return;
    const source = this.state.measure.layer.getSource();
    const features = source.getFeatures();

    if (features.length > 0) {
      source.removeFeature(features[features.length - 1]);
    }
  }

  // 创建测量结果提示框（私有方法）
  #createMeasureTooltip() {
    // 移除现有提示框
    if (
      this.state.measure.tooltipElement &&
      this.state.measure.tooltipElement.parentNode
    ) {
      this.state.measure.tooltipElement.parentNode.removeChild(
        this.state.measure.tooltipElement
      );
    }

    // 创建新的提示框元素
    this.state.measure.tooltipElement = document.createElement("div");
    this.state.measure.tooltipElement.className =
      "ol-tooltip ol-tooltip-measure";
    this.state.measure.tooltipElement.style.cssText = `
      font-size: 14px;
      font-weight: 500;
      background: rgba(255, 255, 255, 0.9);
      color: #070707ff;
      padding: 6px 12px;
      border-radius: 4px;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
      border: 1px solid #fc5531;
    `;

    // 创建Overlay
    this.state.measure.tooltip = new Overlay({
      element: this.state.measure.tooltipElement,
      offset: [0, -20],
      positioning: "bottom-center",
      stopEvent: false,
    });

    this.map.addOverlay(this.state.measure.tooltip);
    this.state.measure.overlays.push(this.state.measure.tooltip);
  }

  // 创建操作帮助提示框（私有方法）
  #createHelpTooltip() {
    if (
      this.state.measure.helpTooltipElement &&
      this.state.measure.helpTooltipElement.parentNode
    ) {
      this.state.measure.helpTooltipElement.parentNode.removeChild(
        this.state.measure.helpTooltipElement
      );
    }

    this.state.measure.helpTooltipElement = document.createElement("div");
    this.state.measure.helpTooltipElement.className =
      "ol-tooltip ol-tooltip-help hidden";
    this.state.measure.helpTooltipElement.style.cssText = `
      font-size: 12px;
      background: rgba(0, 0, 0, 0.7);
      color: white;
      padding: 4px 8px;
      border-radius: 3px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    `;

    this.state.measure.helpTooltip = new Overlay({
      element: this.state.measure.helpTooltipElement,
      offset: [15, 0],
      positioning: "center-left",
    });

    this.map.addOverlay(this.state.measure.helpTooltip);
    this.state.measure.overlays.push(this.state.measure.helpTooltip);
  }

  // 创建标记（新增方法）
  #createMark(markDom, txt, idstr) {
    if (markDom == null) {
      markDom = document.createElement("div");
      markDom.innerHTML = txt;
      markDom.style =
        "color:#000;width:auto;height:auto;padding:4px;border:1px solid #fc5531;font-size:12px;background-color:#fff;position:relative;font-weight:600;";
    }

    const overlay = new Overlay({
      element: markDom,
      autoPan: false,
      positioning: "bottom-center",
      id: idstr,
      stopEvent: false,
    });

    this.map.addOverlay(overlay);
    this.state.measure.overlays.push(overlay);
    return overlay;
  }

  // 绑定绘制事件（私有方法）
  #bindDrawEvents(measureType) {
    const draw = this.state.measure.draw;
    const proj = this.map.getView().getProjection();

    // 绘制开始事件
    draw.on("drawstart", (evt) => {
      this.state.measure.sketch = evt.feature;
      let tooltipCoord = evt.coordinate;

      // 角度测量时添加起点标记
      if (measureType === "angle") {
        this.#createMark(null, "起点", "start").setPosition(tooltipCoord);
      }

      // 监听几何变化（实时更新测量结果）
      this.state.measure.listener = this.state.measure.sketch
        .getGeometry()
        .on("change", (geomEvt) => {
          const geometry = geomEvt.target;
          let result = "";
          let position = tooltipCoord;

          // 根据几何类型计算测量结果
          if (geometry instanceof LineString) {
            if (measureType === "LineString") {
              // 距离测量
              const length = getLength(geometry, { projection: proj });
              result = this.#formatLength(length);
              position = geometry.getLastCoordinate();
            } else if (measureType === "angle") {
              // 角度测量
              if (geometry.getCoordinates().length >= 3) {
                result = this.#formatAngle(geometry);
                position = geometry.getCoordinates()[1]; // 顶点位置
              } else {
                result = "继续单击确定顶点";
                position = geometry.getLastCoordinate();
              }
            }
          } else if (geometry instanceof Polygon && measureType === "Polygon") {
            // 面积测量
            const area = getArea(geometry, { projection: proj });
            result = this.#formatArea(area);
            position = geometry.getInteriorPoint().getCoordinates();
          }

          // 更新提示框内容和位置
          if (this.state.measure.tooltipElement) {
            this.state.measure.tooltipElement.innerHTML = result;
          }
          if (this.state.measure.tooltip) {
            this.state.measure.tooltip.setPosition(position);
          }
        });
    });

    // 绘制结束事件
    draw.on("drawend", (evt) => {
      // 创建关闭按钮
      const closeBtn = document.createElement("span");
      closeBtn.innerHTML = "×";
      closeBtn.title = "清除测量";
      closeBtn.style =
        "color:#000;width: 16px;height:16px;line-height: 16px;text-align: center;border-radius: 50%;display: inline-block;color: #fc5531;border: 1px solid #fc5531;background-color: #fff;font-weight: bold;position: absolute;top: -8px;right: -8px;cursor: pointer;";
      closeBtn.addEventListener("click", () => {
        this.clearMeasureResults();
      });

      // 根据测量类型添加结果标记
      const geometry = evt.feature.getGeometry();
      let result = "";
      let position = [];

      if (measureType === "LineString") {
        // 距离测量结果
        result = `总长：${this.#formatLength(
          getLength(geometry, { projection: proj })
        )}`;
        position = geometry.getLastCoordinate();
      } else if (measureType === "Polygon") {
        // 面积测量结果
        result = `总面积：${this.#formatArea(
          getArea(geometry, { projection: proj })
        )}`;
        position = geometry.getInteriorPoint().getCoordinates();
      } else if (measureType === "angle") {
        // 角度测量结果
        result = `角度：${this.#formatAngle(geometry)}`;
        position = geometry.getCoordinates()[1];
      }

      // 添加结果标记和关闭按钮
      const resultOverlay = this.#createMark(null, result, "measure-result");
      resultOverlay.setPosition(position);

      const closeOverlay = this.#createMark(closeBtn, null, "measure-close");
      closeOverlay.setPosition(position);

      // 固定测量结果提示框
      if (this.state.measure.tooltipElement) {
        this.state.measure.tooltipElement.className =
          "ol-tooltip ol-tooltip-measure ol-tooltip-static";
      }
      if (this.state.measure.tooltip) {
        this.state.measure.tooltip.setOffset([0, -15]);
      }

      // 移除几何变化监听
      if (this.state.measure.listener) {
        unByKey(this.state.measure.listener);
      }
      this.state.measure.sketch = null;
      this.state.measure.listener = null;
    });

    // 绘制取消事件
    draw.on("drawabort", () => {
      if (this.state.measure.listener) {
        unByKey(this.state.measure.listener);
      }
      this.state.measure.sketch = null;
      this.state.measure.listener = null;
      if (this.state.measure.tooltipElement) {
        this.state.measure.tooltipElement.innerHTML = "";
      }
    });
  }

  // 处理鼠标移动事件（私有方法）
  #handlePointerMove(evt) {
    // 如果没有激活测量工具或正在拖拽，不处理
    if (evt.dragging || !this.state.measure.draw) return;

    let helpMsg = "";
    const sketch = this.state.measure.sketch;
    const measureType = this.state.measure.type;

    if (!sketch) {
      helpMsg = "点击开始绘制";
    } else {
      switch (measureType) {
        case "LineString":
          helpMsg = "点击继续绘制线，双击结束";
          break;
        case "Polygon":
          helpMsg = "点击继续绘制面，双击结束";
          break;
        case "angle":
          helpMsg =
            sketch.getGeometry().getCoordinates().length < 3
              ? "点击继续绘制，需要3个点"
              : "双击结束测量";
          break;
      }
    }

    // 更新帮助提示
    if (this.state.measure.helpTooltipElement) {
      this.state.measure.helpTooltipElement.innerHTML = helpMsg;
      this.state.measure.helpTooltipElement.classList.remove("hidden");
    }
    if (this.state.measure.helpTooltip) {
      this.state.measure.helpTooltip.setPosition(evt.coordinate);
    }
  }

  // 格式化长度（私有方法）
  #formatLength(length) {
    let output;
    if (length > 1000) {
      output = Math.round((length / 1000) * 100) / 100 + " 千米";
    } else {
      output = Math.round(length * 100) / 100 + " 米";
    }
    return output;
  }

  // 格式化面积（私有方法）
  #formatArea(area) {
    let output;
    if (area > 1000000) {
      output = Math.round((area / 1000000) * 100) / 100 + " 平方千米";
    } else if (area > 10000) {
      output = Math.round((area / 10000) * 100) / 100 + " 公顷";
    } else {
      output = Math.round(area * 100) / 100 + " 平方米";
    }
    return output;
  }

  // 计算角度（新增方法）
  // 计算角度（修复版）
  #formatAngle(line) {
    // 1. 先校验几何类型，确保是LineString
    if (!(line instanceof LineString)) {
      console.warn("角度测量仅支持LineString类型");
      return "0°";
    }

    // 2. 获取坐标数组，确保至少有3个点（起点、顶点、终点）
    const coordinates = line.getCoordinates();
    if (coordinates.length < 3) {
      return "需3个点完成测量"; // 明确提示，而非返回0°
    }

    // 3. 提取关键坐标（严格按「起点→顶点→终点」顺序）
    const [pointA, pointB, pointC] = coordinates; // pointB是夹角顶点
    const proj = this.map.getView().getProjection(); // 获取地图投影

    // 4. 计算三条关键边的长度（AB: 顶点到起点，BC: 顶点到终点，AC: 起点到终点）
    const lenAB = getLength(new LineString([pointA, pointB]), {
      projection: proj,
    });
    const lenBC = getLength(new LineString([pointB, pointC]), {
      projection: proj,
    });
    const lenAC = getLength(new LineString([pointA, pointC]), {
      projection: proj,
    });

    // 5. 避免除以0（防止两点重合导致边长为0）
    if (lenAB < 0.1 || lenBC < 0.1) {
      // 0.1米阈值，过滤微小距离
      return "顶点附近点重合";
    }

    // 6. 余弦定理计算夹角（修复cos值越界问题）
    let cosValue = (lenAB ** 2 + lenBC ** 2 - lenAC ** 2) / (2 * lenAB * lenBC);
    // 修正浮点数误差：将cos值强制限制在[-1, 1]范围内
    cosValue = Math.max(-1, Math.min(1, cosValue));

    // 7. 计算角度（弧度转角度，保留2位小数）
    let angle = (Math.acos(cosValue) * 180) / Math.PI;
    angle = isNaN(angle) ? 0 : angle; // 处理极端情况

    return `${angle.toFixed(2)}°`;
  }

  // 要素高亮样式定义（私有方法）
  #getHighlightStyle() {
    return new Style({
      fill: new Fill({
        color: "rgba(255, 215, 0, 0.4)", // 金色填充，透明度40%
      }),
      stroke: new Stroke({
        color: "#FFD700", // 金色边框
        width: 4, // 加粗边框
        lineDash: [5, 5], // 虚线效果
      }),
      image: new Circle({
        radius: 8, // 放大点要素
        fill: new Fill({
          color: "#FFD700", // 金色填充
        }),
        stroke: new Stroke({
          color: "#000000", // 黑色边框
          width: 2,
        }),
      }),
    });
  }

  // 高亮要素（私有方法）
  #highlightFeature(feature, layer) {
    // 先清除之前的高亮
    this.#clearHighlight();

    // 保存原始样式
    this.state.highlight.originalStyle = feature.getStyle();
    this.state.highlight.currentFeature = feature;
    this.state.highlight.highlightedLayer = layer;

    // 应用高亮样式
    feature.setStyle(this.#getHighlightStyle());

    console.log("要素高亮应用成功");
  }

  // 清除高亮（私有方法）
  #clearHighlight() {
    if (this.state.highlight.currentFeature) {
      // 如果要素有原始样式，恢复原始样式
      if (this.state.highlight.originalStyle) {
        this.state.highlight.currentFeature.setStyle(
          this.state.highlight.originalStyle
        );
      } else {
        // 如果没有保存原始样式，则清除样式（让图层样式生效）
        this.state.highlight.currentFeature.setStyle(null);
      }

      // 强制刷新要素显示
      this.state.highlight.currentFeature.changed();

      // 重置状态
      this.state.highlight.currentFeature = null;
      this.state.highlight.originalStyle = null;
      this.state.highlight.highlightedLayer = null;

      console.log("要素高亮已清除");
    }
  }

  // 清除地图上所有交互
  clearAllInteractions() {
    const interactions = this.map.getInteractions().getArray();
    interactions.forEach((interaction) => {
      // 保留基础交互（如平移缩放），只清除绘制和测量相关
      if (
        interaction instanceof Draw ||
        interaction instanceof Snap ||
        interaction instanceof Modify
      ) {
        this.map.removeInteraction(interaction);
      }
    });
    // 重置所有状态
    this.#clearDrawState();
    this.stopMeasureTool();
  }

  loadGeoJsonLayer(
    geoJson,
    styleOptions = {},
    layerName = "GeoJSON Layer",
    options = {}
  ) {
    // 默认配置选项
    const defaultOptions = {
      autoFitExtent: true, // 是否自动调整视图到图层范围
      fitPadding: 50, // 调整视图时的边距
      storeExtent: true, // 是否存储图层范围
    };

    // 合并用户配置选项
    const finalOptions = { ...defaultOptions, ...options };

    // 默认样式配置
    const defaultStyle = {
      fillColor: "rgba(255, 255, 255, 0.2)",
      strokeColor: "#4CAF50",
      strokeWidth: 2,
      pointColor: "#4CAF50",
      pointRadius: 5,
    };

    // 合并用户自定义样式
    const finalStyle = { ...defaultStyle, ...styleOptions };

    // 创建样式函数
    const styleFunction = (feature) => {
      const geometryType = feature.getGeometry().getType();
      return new Style({
        fill: new Fill({
          color: finalStyle.fillColor,
        }),
        stroke: new Stroke({
          color: finalStyle.strokeColor,
          width: finalStyle.strokeWidth,
        }),
        image: new Circle({
          radius: finalStyle.pointRadius,
          fill: new Fill({
            color: finalStyle.pointColor,
          }),
        }),
      });
    };

    // 创建矢量源
    const source = new VectorSource({
      url: typeof geoJson === "string" ? geoJson : undefined,
      format: new GeoJSON(),
      loader: () => {
        if (typeof geoJson !== "string") {
          // 如果传入的是GeoJSON对象而非URL
          const features = new GeoJSON().readFeatures(geoJson);
          // console.log(features);
          source.addFeatures(features);
        }
      },
    });

    // 创建矢量图层
    const layer = new VectorLayer({
      source: source,
      style: styleFunction,
    });

    layer.set("title", layerName);

    // 存储图层范围到图层属性中
    if (finalOptions.storeExtent) {
      layer.set("extent", null); // 初始化为null
    }

    // 添加标志跟踪是否已处理初始加载
    let isInitialLoadProcessed = false;

    // 添加监听器确保数据加载完成
    source.once("change", () => {
      if (source.getState() === "ready") {
        const features = source.getFeatures();

        // 只在第一次数据加载完成时处理范围计算和视图调整
        if (!isInitialLoadProcessed && features.length > 0) {
          console.log("实际要素数量:", features.length);

          const extent = source.getExtent();
          console.log("图层范围:", extent);

          if (finalOptions.storeExtent && extent) {
            layer.set("extent", extent);
            console.log("图层范围已存储");

            // 强制刷新LayerSwitcher ，确保zoomtoextent按钮显示
            setTimeout(() => {
              this.map.getControls().forEach((control) => {
                if (control instanceof LayerSwitcher) {
                  // 使用正确的方法刷新图层切换器
                  if (control.drawPanel) {
                    control.drawPanel();
                  } else if (control.render) {
                    control.render();
                  }
                  // 触发图层变化事件，让LayerSwitcher重新检测范围
                  this.map.dispatchEvent("change:layer");
                }
              });
            }, 100);
          }

          // 如果启用自动调整视图，则调整到图层范围
          if (finalOptions.autoFitExtent && extent) {
            this.fitToLayerExtent(layer, finalOptions.fitPadding);
          }

          // 标记为已处理，避免后续交互重复触发
          isInitialLoadProcessed = true;
        }
      }
    });

    // 手动触发加载（如果是通过URL）
    if (typeof geoJson === "string") {
      source.refresh();
    }
    this.map.addLayer(layer);

    return layer;
  }
  // 新增方法：调整视图到图层范围
  fitToLayerExtent(layer, padding = 50) {
    console.log("调整视图到图层范围");
    const source = layer.getSource();
    if (source.getFeatures().length === 0) return;

    // 获取图层的范围
    const extent = source.getExtent();

    if (
      extent &&
      !isNaN(extent[0]) &&
      !isNaN(extent[1]) &&
      !isNaN(extent[2]) &&
      !isNaN(extent[3])
    ) {
      // 使用动画效果平滑过渡到新范围
      this.map.getView().fit(extent, {
        padding: [padding, padding, padding, padding], // 上下左右边距
        duration: 800, // 动画持续时间（毫秒）
        maxZoom: 15, // 最大缩放级别限制
      });

      console.log("调整视图到图层范围:", extent);
    }
  }

  // 获取图层范围
  getLayerExtent(layer) {
    const source = layer.getSource();
    if (source.getFeatures().length === 0) return null;

    const extent = source.getExtent();
    if (
      extent &&
      !isNaN(extent[0]) &&
      !isNaN(extent[1]) &&
      !isNaN(extent[2]) &&
      !isNaN(extent[3])
    ) {
      return extent;
    }
    return null;
  }

  // 获取存储的图层范围（如果存在）
  getStoredLayerExtent(layer) {
    return layer.get("extent") || null;
  }

  // 手动跳转到图层范围
  zoomToLayerExtent(layer, padding = 50) {
    let extent = null;

    // 首先尝试获取存储的范围
    extent = this.getStoredLayerExtent(layer);

    // 如果没有存储的范围，则实时计算
    if (!extent) {
      extent = this.getLayerExtent(layer);
    }

    if (extent) {
      this.fitToLayerExtent(layer, padding);
      return true;
    }

    console.warn("无法获取图层范围，图层可能为空或范围无效");
    return false;
  }

  // 可选：新增方法获取图层中心点
  getLayerCenter(layer) {
    const source = layer.getSource();
    if (source.getFeatures().length === 0) return null;

    const extent = source.getExtent();
    if (extent) {
      return getCenter(extent);
    }
    return null;
  }

  // 在MapUtils类中添加以下方法



  /**
   * 获取用户当前位置
   * @param {Object} options - 配置选项
   * @param {number} options.timeout - 超时时间（毫秒），默认10000
   * @param {number} options.maximumAge - 位置缓存最大年龄（毫秒），默认0
   * @param {boolean} options.enableHighAccuracy - 是否启用高精度，默认false
   * @returns {Promise<Object>} 包含坐标和精度信息的Promise
   * @throws {Error} 当浏览器不支持Geolocation API或用户拒绝权限时抛出错误
   */
  getCurrentPosition(options = {}) {
    const {
      timeout = 10000,
      maximumAge = 0,
      enableHighAccuracy = false
    } = options;

    return new Promise((resolve, reject) => {
      // 检查浏览器是否支持Geolocation API
      if (!navigator.geolocation) {
        reject(new Error("浏览器不支持地理位置API"));
        return;
      }

      // 配置geolocation选项
      const geolocationOptions = {
        timeout,
        maximumAge,
        enableHighAccuracy
      };

      // 获取当前位置
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude, accuracy } = position.coords;
          const coordinate = [longitude, latitude]; // OpenLayers使用[经度, 纬度]格式
          
          resolve({
            coordinate,
            accuracy,
            timestamp: position.timestamp
          });
        },
        (error) => {
          // 处理不同的错误类型
          let errorMessage;
          switch (error.code) {
            case error.PERMISSION_DENIED:
              errorMessage = "用户拒绝了地理位置权限请求";
              break;
            case error.POSITION_UNAVAILABLE:
              errorMessage = "无法获取当前位置信息";
              break;
            case error.TIMEOUT:
              errorMessage = "获取位置信息超时";
              break;
            default:
              errorMessage = "未知错误发生";
          }
          reject(new Error(errorMessage));
        },
        geolocationOptions
      );
    });
  }

  /**
   * 设置地图中心点
   * @param {number[]} center - 中心点坐标 [经度, 纬度]
   * @param {number} [zoom] - 可选缩放级别，如果不提供则保持当前缩放级别
   * @param {Object} [options] - 可选配置选项
   * @param {number} [options.duration=800] - 动画持续时间（毫秒）
   * @param {boolean} [options.animate=true] - 是否使用动画效果
   */
  setCenter(center, zoom, options = {}) {
    const {
      duration = 800,
      animate = true
    } = options;

    const view = this.map.getView();
    
    if (zoom !== undefined && zoom !== null) {
      // 同时设置中心点和缩放级别
      if (animate) {
        view.animate({
          center: center,
          zoom: zoom,
          duration: duration
        });
      } else {
        view.setCenter(center);
        view.setZoom(zoom);
      }
    } else {
      // 只设置中心点，保持当前缩放级别
      if (animate) {
        view.animate({
          center: center,
          duration: duration
        });
      } else {
        view.setCenter(center);
      }
    }

    console.log(`地图中心已设置为: [${center[0]}, ${center[1]}]`);
  }

  /**
   * 获取当前视图的坐标范围
   * 基于当前缩放级别和地图显示区域计算
   * @param {Object} options - 配置选项
   * @param {boolean} [options.formatted=false] - 是否返回格式化对象
   * @param {number} [options.precision=6] - 坐标精度（小数位数）
   * @returns {Array|Object} 视图范围坐标
   */
  getViewExtent(options = {}) {
    const {
      formatted = false,
      precision = 6
    } = options;

    // 检查地图是否已初始化
    if (!this.map || !this.map.getView()) {
      console.warn("地图未初始化，无法获取视图范围");
      return formatted ? {} : [];
    }

    const view = this.map.getView();
    const mapSize = this.map.getSize();

    // 检查地图尺寸是否有效
    if (!mapSize || mapSize[0] === 0 || mapSize[1] === 0) {
      console.warn("地图尺寸无效，无法计算视图范围");
      return formatted ? {} : [];
    }

    try {
      // 计算当前视图范围
      const extent = view.calculateExtent(mapSize);
      
      // 格式化坐标精度
      const formatCoordinate = (coord) => {
        return parseFloat(coord.toFixed(precision));
      };

      const [minLon, minLat, maxLon, maxLat] = extent.map(formatCoordinate);

      if (formatted) {
        // 返回格式化对象
        return {
          minLon: minLon,
          minLat: minLat,
          maxLon: maxLon,
          maxLat: maxLat,
          center: [
            formatCoordinate((minLon + maxLon) / 2),
            formatCoordinate((minLat + maxLat) / 2)
          ],
          width: formatCoordinate(maxLon - minLon),
          height: formatCoordinate(maxLat - minLat),
          zoom: view.getZoom(),
          projection: view.getProjection().getCode()
        };
      } else {
        // 返回原始范围数组
        return [minLon, minLat, maxLon, maxLat];
      }
    } catch (error) {
      console.error("计算视图范围时发生错误:", error);
      return formatted ? {} : [];
    }
  }

  /**
   * 比较几何图形是否相等（私有方法）
   * @param {Geometry} geom1 - 几何图形1
   * @param {Geometry} geom2 - 几何图形2
   * @param {number} tolerance - 容差，默认0.000001
   * @returns {boolean} 是否相等
   * @private
   */
  #areGeometriesEqual(geom1, geom2, tolerance = 0.000001) {
    if (!geom1 || !geom2) return false;
    
    const type1 = geom1.getType();
    const type2 = geom2.getType();
    
    if (type1 !== type2) return false;
    
    const coords1 = this.#getGeometryCoordinates(geom1);
    const coords2 = this.#getGeometryCoordinates(geom2);
    
    return this.#areCoordinatesEqual(coords1, coords2, tolerance);
  }

  /**
   * 添加 GeoJSON 数据到图层
   * @param {VectorLayer} targetLayer - 目标图层
   * @param {Object|string} geoJson - GeoJSON 数据对象或 URL
   * @param {Object} options - 配置选项
   * @returns {Promise<Object>} 添加结果
   */
  async addGeoJsonToLayer(targetLayer, geoJson, options = {}) {
    try {
      // 1. 验证目标图层
      if (!targetLayer) {
        throw new Error('目标图层不能为空');
      }
      
      // 检查 targetLayer 是否有 getSource 方法
      if (typeof targetLayer.getSource !== 'function') {
        throw new Error('目标图层不是有效的 OpenLayers 图层对象');
      }
      
      // 2. 获取数据源（可能是 VectorSource 或 Cluster）
      let source = targetLayer.getSource();

      // 检查 source 是否存在且是有效的 VectorSource
      if (!source) {
        throw new Error('目标图层没有有效的数据源');
      }

      // 关键修复：对于基于缩放级别的图层，必须添加到 allFeaturesSource
      // 不能直接添加到聚合源的内部源(visibleFeaturesSource)
      const allFeaturesSource = targetLayer.get('allFeaturesSource');
      if (allFeaturesSource && allFeaturesSource instanceof VectorSource) {
        console.log('[addGeoJsonToLayer] 检测到基于缩放级别的图层，添加到 allFeaturesSource');
        source = allFeaturesSource;
      } else if (source instanceof Cluster) {
        // 如果是普通聚合源（非缩放级别图层），获取其内部的矢量源
        console.log('[addGeoJsonToLayer] 检测到普通聚合图层，获取内部矢量源');
        source = source.getSource();
      }

      // 检查是否是有效的 VectorSource
      if (!(source instanceof VectorSource)) {
        throw new Error('目标图层必须包含有效的 VectorSource');
      }

      // 2. GeoJSON 数据验证
      if (!geoJson) {
        throw new Error('GeoJSON 数据不能为空');
      }

      // 3. 配置默认选项
      const defaultOptions = {
        clearExisting: false,  // 默认不清除现有要素，避免意外数据丢失
        autoFitExtent: false,
        fitPadding: 50,
        skipInvalidFeatures: true,
        skipDuplicates: true,
        uniqueFields: null,
        styleFunction: null
      };
      const finalOptions = { ...defaultOptions, ...options };

      // 4. 数据加载和解析
      let features = [];
      if (typeof geoJson === 'string') {
        // URL 加载处理
        features = await this._loadGeoJsonFromUrl(geoJson);
      } else {
        // 对象解析处理
        features = this.#parseGeoJsonObject(geoJson);
      }

      // 5. 要素验证和过滤
      const validFeatures = features.filter(feature => {
        try {
          if (!feature || !feature.getGeometry) {
            console.warn('跳过无效要素：缺少几何图形');
            return false;
          }
          
          const geometry = feature.getGeometry();
          if (!geometry) {
            console.warn('跳过无效要素：几何图形为空');
            return false;
          }

          // 应用自定义样式（如果提供）
          if (finalOptions.styleFunction) {
            feature.setStyle(finalOptions.styleFunction(feature));
          }

          return true;
        } catch (error) {
          console.warn('跳过无效要素:', error.message);
          return false;
        }
      });

      // 6. 重复要素检测和过滤
      let uniqueFeatures = validFeatures;
      let duplicateCount = 0;
      
      if (finalOptions.skipDuplicates && validFeatures.length > 0) {
        const existingFeatures = source.getFeatures();
        uniqueFeatures = [];
        
        for (const newFeature of validFeatures) {
          if (!this.#isFeatureDuplicate(newFeature, existingFeatures, finalOptions.uniqueFields)) {
            uniqueFeatures.push(newFeature);
          } else {
            duplicateCount++;
            console.log('跳过重复要素:', this.#getFeatureIdentifier(newFeature, finalOptions.uniqueFields));
          }
        }
      }

      // 7. 执行添加操作
      if (finalOptions.clearExisting) {
        source.clear();
      }
      
      source.addFeatures(uniqueFeatures);

      // 8. 可选：自动调整视图到新要素范围
      if (finalOptions.autoFitExtent && uniqueFeatures.length > 0) {
        const extent = source.getExtent();
        if (extent && extent[0] !== Infinity && extent[1] !== Infinity && 
            extent[2] !== Infinity && extent[3] !== Infinity) {
          this.map.getView().fit(extent, {
            padding: [finalOptions.fitPadding, finalOptions.fitPadding, 
                     finalOptions.fitPadding, finalOptions.fitPadding],
            duration: 800,
            maxZoom: 15
          });
        }
      }

      // 9. 返回结果
      const result = {
        success: true,
        addedCount: uniqueFeatures.length,
        skippedCount: features.length - validFeatures.length,
        duplicateCount: duplicateCount,
        totalFeatures: features.length
      };

      console.log(`GeoJSON 要素添加成功: ${result.addedCount} 个要素已添加, ${result.skippedCount} 个无效要素被跳过, ${result.duplicateCount} 个重复要素被跳过`);
      return result;

    } catch (error) {
      console.error('添加 GeoJSON 到图层失败:', error);
      return {
        success: false,
        error: error.message,
        addedCount: 0,
        skippedCount: 0,
        duplicateCount: 0,
        totalFeatures: 0
      };
    }
  }

  /**
   * 从 URL 加载 GeoJSON 数据
   * @param {string} url - GeoJSON URL
   * @returns {Promise<Array>} 要素数组
   * @private
   */
  async _loadGeoJsonFromUrl(url) {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const geoJsonData = await response.json();
      // 使用 bind 确保 this 上下文正确
      const parseGeoJsonObjectBound = this.#parseGeoJsonObject.bind(this);
      return parseGeoJsonObjectBound(geoJsonData);
    } catch (error) {
      throw new Error(`加载 GeoJSON URL 失败: ${error.message}`);
    }
  }

  /**
   * 解析 GeoJSON 对象（私有方法）
   * @param {Object} geoJsonData - GeoJSON 数据对象
   * @returns {Array} 要素数组
   * @private
   */
  #parseGeoJsonObject(geoJsonData) {
    try {
      // 验证 GeoJSON 结构
      if (!geoJsonData || typeof geoJsonData !== 'object') {
        throw new Error('GeoJSON 数据必须是有效的对象');
      }

      // 检查 type 属性是否存在
      if (!geoJsonData.type) {
        throw new Error('GeoJSON 数据缺少 type 属性');
      }

      if (geoJsonData.type !== 'FeatureCollection' && geoJsonData.type !== 'Feature') {
        throw new Error(`GeoJSON 类型必须是 FeatureCollection 或 Feature，当前类型: ${geoJsonData.type}`);
      }

      // 对于 FeatureCollection，检查 features 数组
      if (geoJsonData.type === 'FeatureCollection') {
        if (!geoJsonData.features) {
          console.warn('FeatureCollection 缺少 features 数组，返回空数组');
          return [];
        }

        if (!Array.isArray(geoJsonData.features)) {
          throw new Error('FeatureCollection 的 features 必须是数组');
        }

        if (geoJsonData.features.length === 0) {
          console.warn('FeatureCollection 的 features 数组为空');
          return [];
        }
      }

      // 使用 OpenLayers GeoJSON 格式解析器
      const geoJsonFormat = new GeoJSON();
      let features = [];

      if (geoJsonData.type === 'FeatureCollection') {
        features = geoJsonFormat.readFeatures(geoJsonData);
      } else if (geoJsonData.type === 'Feature') {
        features = [geoJsonFormat.readFeature(geoJsonData)];
      }

      // 验证解析结果
      if (!features || !Array.isArray(features)) {
        console.warn('GeoJSON 解析结果无效，返回空数组');
        return [];
      }

      if (features.length === 0) {
        console.warn('GeoJSON 数据中没有找到有效要素');
      }

      return features;
    } catch (error) {
      // 记录详细的错误信息以便调试
      console.error('GeoJSON 解析详细错误:', {
        error: error.message,
        stack: error.stack,
        data: geoJsonData
      });
      throw new Error(`解析 GeoJSON 数据失败: ${error.message}`);
    }
  }

  /**
   * 检查要素是否重复（私有方法）
   * @param {Feature} newFeature - 新要素
   * @param {Array<Feature>} existingFeatures - 现有要素数组
   * @param {string[]} uniqueFields - 用于判断重复的唯一字段列表
   * @returns {boolean} 是否重复
   * @private
   */
  #isFeatureDuplicate(newFeature, existingFeatures, uniqueFields) {
    if (!newFeature || !existingFeatures || existingFeatures.length === 0) {
      return false;
    }

    // 如果提供了唯一字段，则使用字段值比较
    if (uniqueFields && uniqueFields.length > 0) {
      return this.#isDuplicateByFields(newFeature, existingFeatures, uniqueFields);
    }

    // 否则使用几何图形比较
    return this.#isDuplicateByGeometry(newFeature, existingFeatures);
  }

  /**
   * 通过字段值判断要素是否重复（私有方法）
   * @param {Feature} newFeature - 新要素
   * @param {Array<Feature>} existingFeatures - 现有要素数组
   * @param {string[]} uniqueFields - 唯一字段列表
   * @returns {boolean} 是否重复
   * @private
   */
  #isDuplicateByFields(newFeature, existingFeatures, uniqueFields) {
    const newProperties = newFeature.getProperties();
    
    for (const existingFeature of existingFeatures) {
      const existingProperties = existingFeature.getProperties();
      let isMatch = true;
      
      // 检查所有唯一字段是否匹配
      for (const field of uniqueFields) {
        const newValue = newProperties[field];
        const existingValue = existingProperties[field];
        
        // 如果字段值不匹配，则不是重复要素
        if (newValue !== existingValue) {
          isMatch = false;
          break;
        }
      }
      
      // 如果所有字段都匹配，则是重复要素
      if (isMatch) {
        return true;
      }
    }
    
    return false;
  }

  /**
   * 通过几何图形判断要素是否重复（私有方法）
   * @param {Feature} newFeature - 新要素
   * @param {Array<Feature>} existingFeatures - 现有要素数组
   * @returns {boolean} 是否重复
   * @private
   */
  #isDuplicateByGeometry(newFeature, existingFeatures) {
    const newGeometry = newFeature.getGeometry();
    if (!newGeometry) return false;

    const newCoordinates = this.#getGeometryCoordinates(newGeometry);
    
    for (const existingFeature of existingFeatures) {
      const existingGeometry = existingFeature.getGeometry();
      if (!existingGeometry) continue;

      const existingCoordinates = this.#getGeometryCoordinates(existingGeometry);
      
      // 比较坐标是否相同（考虑浮点数精度）
      if (this.#areCoordinatesEqual(newCoordinates, existingCoordinates)) {
        return true;
      }
    }
    
    return false;
  }

  /**
   * 获取几何图形的坐标数组（私有方法）
   * @param {Geometry} geometry - 几何图形
   * @returns {Array} 坐标数组
   * @private
   */
  #getGeometryCoordinates(geometry) {
    const geometryType = geometry.getType();
    
    switch (geometryType) {
      case 'Point':
        return [geometry.getCoordinates()];
      case 'LineString':
        return geometry.getCoordinates();
      case 'Polygon':
        return geometry.getCoordinates()[0]; // 只比较外环
      case 'MultiPoint':
        return geometry.getCoordinates();
      case 'MultiLineString':
        return geometry.getCoordinates().flat();
      case 'MultiPolygon':
        return geometry.getCoordinates().flat().flat();
      default:
        return [];
    }
  }

  /**
   * 比较坐标数组是否相等（私有方法）
   * @param {Array} coords1 - 坐标数组1
   * @param {Array} coords2 - 坐标数组2
   * @param {number} tolerance - 容差，默认0.000001
   * @returns {boolean} 是否相等
   * @private
   */
  #areCoordinatesEqual(coords1, coords2, tolerance = 0.000001) {
    if (!Array.isArray(coords1) || !Array.isArray(coords2)) {
      return false;
    }
    
    if (coords1.length !== coords2.length) {
      return false;
    }
    
    for (let i = 0; i < coords1.length; i++) {
      const coord1 = coords1[i];
      const coord2 = coords2[i];
      
      if (Array.isArray(coord1) && Array.isArray(coord2)) {
        // 递归比较嵌套数组
        if (!this.#areCoordinatesEqual(coord1, coord2, tolerance)) {
          return false;
        }
      } else if (typeof coord1 === 'number' && typeof coord2 === 'number') {
        // 比较数字（考虑容差）
        if (Math.abs(coord1 - coord2) > tolerance) {
          return false;
        }
      } else {
        // 类型不匹配
        return false;
      }
    }
    
    return true;
  }

  /**
   * 获取要素标识符（私有方法）
   * @param {Feature} feature - 要素
   * @param {string[]} uniqueFields - 唯一字段列表
   * @returns {string} 要素标识符
   * @private
   */
  #getFeatureIdentifier(feature, uniqueFields) {
    if (!feature) return '未知要素';
    
    const properties = feature.getProperties();
    const geometry = feature.getGeometry();
    
    // 如果有唯一字段，使用字段值作为标识符
    if (uniqueFields && uniqueFields.length > 0) {
      const fieldValues = uniqueFields.map(field => {
        const value = properties[field];
        return `${field}: ${value !== undefined ? value : '空值'}`;
      });
      return fieldValues.join(', ');
    }
    
    // 否则使用几何图形类型和坐标作为标识符
    if (geometry) {
      const geometryType = geometry.getType();
      const extent = geometry.getExtent();
      return `${geometryType} [${extent ? extent.map(coord => coord.toFixed(4)).join(', ') : '无范围'}]`;
    }
    
    return '无几何图形的要素';
  }

  // ==================== 中国范围限制相关方法 ====================

  /**
   * 设置中国范围限制
   * @param {number[]} [extent] - 可选自定义范围 [minLon, minLat, maxLon, maxLat]
   * @param {Object} [options] - 配置选项
   * @param {number} [options.minZoom=3] - 最小缩放级别
   * @param {number} [options.maxZoom=18] - 最大缩放级别
   */
  setChinaExtent(extent, options = {}) {
    const view = this.map.getView();
    const finalExtent = extent || this.chinaExtent;
    const { minZoom = 3, maxZoom = 18 } = options;

    view.setConstraints({
      extent: finalExtent,
      minZoom: minZoom,
      maxZoom: maxZoom
    });

    console.log(`中国范围限制已设置: [${finalExtent.join(', ')}]`);
  }

  /**
   * 移除范围限制
   */
  removeExtentConstraint() {
    const view = this.map.getView();
    view.setConstraints({
      extent: undefined,
      minZoom: undefined,
      maxZoom: undefined
    });

    console.log("范围限制已移除");
  }

  /**
   * 检查坐标是否在中国范围内
   * @param {number[]} coordinate - 坐标 [经度, 纬度]
   * @returns {boolean} 是否在中国范围内
   */
  isCoordinateInChina(coordinate) {
    const [lon, lat] = coordinate;
    return lon >= this.chinaExtent[0] && lon <= this.chinaExtent[2] && 
           lat >= this.chinaExtent[1] && lat <= this.chinaExtent[3];
  }

  /**
   * 重置视图到中国范围
   * @param {Object} [options] - 配置选项
   * @param {number} [options.padding=50] - 边距
   * @param {number} [options.duration=800] - 动画持续时间
   * @param {number} [options.maxZoom=15] - 最大缩放级别
   */
  resetToChinaExtent(options = {}) {
    const { padding = 50, duration = 800, maxZoom = 15 } = options;
    
    const view = this.map.getView();
    view.fit(this.chinaExtent, {
      padding: [padding, padding, padding, padding],
      duration: duration,
      maxZoom: maxZoom
    });

    console.log("视图已重置到中国范围");
  }

  /**
   * 获取中国范围信息
   * @returns {Object} 中国范围信息对象
   */
  getChinaExtentInfo() {
    const [minLon, minLat, maxLon, maxLat] = this.chinaExtent;
    return {
      extent: this.chinaExtent,
      center: [(minLon + maxLon) / 2, (minLat + maxLat) / 2],
      width: maxLon - minLon,
      height: maxLat - minLat,
      description: `中国范围: 经度 ${minLon}°E - ${maxLon}°E, 纬度 ${minLat}°N - ${maxLat}°N`
    };
  }

  /**
   * 设置自定义范围限制
   * @param {number[]} extent - 自定义范围 [minLon, minLat, maxLon, maxLat]
   * @param {Object} [options] - 配置选项
   * @param {number} [options.minZoom=1] - 最小缩放级别
   * @param {number} [options.maxZoom=20] - 最大缩放级别
   */
  setCustomExtent(extent, options = {}) {
    const view = this.map.getView();
    const { minZoom = 1, maxZoom = 20 } = options;

    if (!extent || extent.length !== 4) {
      throw new Error('范围必须是包含4个数字的数组 [minLon, minLat, maxLon, maxLat]');
    }

    view.setConstraints({
      extent: extent,
      minZoom: minZoom,
      maxZoom: maxZoom
    });

    console.log(`自定义范围限制已设置: [${extent.join(', ')}]`);
  }

  /**
   * 创建基于缩放级别的矢量图层（降序优先级）- 修复聚合要素过滤问题
   * @param {string} fieldName - 用于过滤的字段名
   * @param {Object} fieldRange - 字段范围配置
   * @param {string} layerName - 图层名称
   * @param {Object} options - 可选配置
   * @param {Function} [options.styleFunction] - 自定义样式函数
   * @param {number} [options.debounceDelay=100] - 防抖延迟时间（毫秒）
   * @param {boolean} [options.autoFitExtent=false] - 是否自动调整视图
   * @param {number} [options.fitPadding=50] - 调整视图时的边距
   * @returns {VectorLayer} 创建的矢量图层
   */
  createZoomBasedVectorLayer(fieldName, fieldRange, layerName, options = {}) {
    // 参数验证
    if (!fieldName || typeof fieldName !== 'string') {
      throw new Error('fieldName 必须是有效的字符串');
    }
    if (!fieldRange || typeof fieldRange !== 'object') {
      throw new Error('fieldRange 必须是有效的配置对象');
    }
    if (!layerName || typeof layerName !== 'string') {
      throw new Error('layerName 必须是有效的字符串');
    }

    // 配置默认选项
    const defaultOptions = {
      styleFunction: null,
      debounceDelay: 100,
      autoFitExtent: false,
      fitPadding: 50,
      enableClustering: true,  // 启用聚合
      clusterDistance: 40      // 聚合距离（像素）
    };
    const finalOptions = { ...defaultOptions, ...options };

    // 验证字段范围配置
    this.#validateFieldRangeConfig(fieldRange);

    // 创建两个矢量数据源：
    // 1. allFeaturesSource - 存储所有要素（不可见）
    // 2. visibleFeaturesSource - 只存储可见要素（用于聚合和显示）
    const allFeaturesSource = new VectorSource();
    const visibleFeaturesSource = new VectorSource();

    // 根据配置决定是否使用聚合
    let finalSource = visibleFeaturesSource;
    if (finalOptions.enableClustering) {
      finalSource = new Cluster({
        distance: finalOptions.clusterDistance,
        source: visibleFeaturesSource
      });
    }

    // 创建矢量图层
    const layer = new VectorLayer({
      source: finalSource,
      style: finalOptions.styleFunction || this.#getDefaultZoomBasedStyle(),
    });

    // 存储数据源引用
    layer.set('allFeaturesSource', allFeaturesSource);      // 所有要素
    layer.set('visibleFeaturesSource', visibleFeaturesSource); // 可见要素
    layer.set('vectorSource', allFeaturesSource);           // 向后兼容

    layer.set('title', layerName);
    layer.set('zoomBasedConfig', {
      fieldName,
      fieldRange,
      options: finalOptions
    });

    // 存储要素可见性状态
    layer.set('featureVisibility', new Map());

    // 添加图层到地图
    this.map.addLayer(layer);

    // 设置缩放级别监听
    this.#setupZoomListener(layer);

    console.log(`基于缩放级别的矢量图层已创建: ${layerName}, 字段: ${fieldName}`);
    return layer;
  }

  /**
   * 验证字段范围配置（私有方法）
   * @param {Object} fieldRange - 字段范围配置
   * @private
   */
  #validateFieldRangeConfig(fieldRange) {
    const { type } = fieldRange;

    if (type === 'discrete') {
      if (!Array.isArray(fieldRange.values) || fieldRange.values.length === 0) {
        throw new Error('离散值模式必须提供有效的 values 数组');
      }

      // 验证每个配置项
      fieldRange.values.forEach((config, index) => {
        if (config.value === undefined) {
          throw new Error(`离散值配置第 ${index + 1} 项缺少 value 属性`);
        }
        if (config.minZoom === undefined || typeof config.minZoom !== 'number') {
          throw new Error(`离散值配置第 ${index + 1} 项缺少有效的 minZoom 属性`);
        }
        if (config.minZoom < 0 || config.minZoom > 18) {
          throw new Error(`离散值配置第 ${index + 1} 项的 minZoom 必须在 0-18 范围内`);
        }
      });

      // 按 minZoom 升序排列（优先级降序）
      fieldRange.values.sort((a, b) => a.minZoom - b.minZoom);

    } else if (type === 'continuous') {
      if (!Array.isArray(fieldRange.ranges) || fieldRange.ranges.length === 0) {
        throw new Error('连续范围模式必须提供有效的 ranges 数组');
      }

      // 验证每个配置项
      fieldRange.ranges.forEach((config, index) => {
        if (config.min === undefined || typeof config.min !== 'number') {
          throw new Error(`连续范围配置第 ${index + 1} 项缺少有效的 min 属性`);
        }
        if (config.max === undefined || typeof config.max !== 'number') {
          throw new Error(`连续范围配置第 ${index + 1} 项缺少有效的 max 属性`);
        }
        if (config.minZoom === undefined || typeof config.minZoom !== 'number') {
          throw new Error(`连续范围配置第 ${index + 1} 项缺少有效的 minZoom 属性`);
        }
        if (config.minZoom < 0 || config.minZoom > 18) {
          throw new Error(`连续范围配置第 ${index + 1} 项的 minZoom 必须在 0-18 范围内`);
        }
        if (config.min >= config.max) {
          throw new Error(`连续范围配置第 ${index + 1} 项的 min 必须小于 max`);
        }
      });

      // 按 minZoom 升序排列（优先级降序）
      fieldRange.ranges.sort((a, b) => a.minZoom - b.minZoom);

    } else {
      throw new Error('fieldRange.type 必须是 "discrete" 或 "continuous"');
    }
  }

  /**
   * 获取默认的基于缩放级别的样式（私有方法）
   * @returns {Style} 默认样式
   * @private
   */
  #getDefaultZoomBasedStyle() {
    return new Style({
      fill: new Fill({
        color: 'rgba(255, 255, 255, 0.2)',
      }),
      stroke: new Stroke({
        color: '#4CAF50',
        width: 2,
      }),
      image: new Circle({
        radius: 5,
        fill: new Fill({
          color: '#4CAF50',
        }),
      }),
    });
  }

  /**
   * 设置缩放级别监听器（私有方法）
   * @param {VectorLayer} layer - 矢量图层
   * @private
   */
  #setupZoomListener(layer) {
    const config = layer.get('zoomBasedConfig');
    const { debounceDelay } = config.options;

    // 防抖函数
    let debounceTimer;
    const updateFeatureVisibility = () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        this.#updateFeatureVisibility(layer);
      }, debounceDelay);
    };

    // 监听缩放级别变化
    this.map.getView().on('change:resolution', updateFeatureVisibility);

    // 初始更新
    setTimeout(() => this.#updateFeatureVisibility(layer), 100);

    // 存储监听器引用以便后续移除
    layer.set('zoomListener', updateFeatureVisibility);
  }

  /**
   * 更新要素可见性（私有方法）- 最终修复版本
   * 彻底解决聚合要素过滤问题，确保聚合图层只包含当前缩放级别可见的要素
   * 关键修复：使用更彻底的聚合源重建机制
   * @param {VectorLayer} layer - 矢量图层
   * @private
   */
  #updateFeatureVisibility(layer) {
    console.log('[DEBUG] #updateFeatureVisibility 被调用');

    const config = layer.get('zoomBasedConfig');
    if (!config) {
      console.error('[DEBUG] 图层没有 zoomBasedConfig');
      return;
    }

    const { fieldName, fieldRange, options } = config;
    const currentZoom = this.map.getView().getZoom();

    // 获取数据源
    const allFeaturesSource = layer.get('allFeaturesSource');
    const visibleFeaturesSource = layer.get('visibleFeaturesSource');

    console.log('[DEBUG] allFeaturesSource:', allFeaturesSource);
    console.log('[DEBUG] visibleFeaturesSource:', visibleFeaturesSource);

    if (!allFeaturesSource || !visibleFeaturesSource) {
      console.error('[DEBUG] 数据源不存在');
      return;
    }

    const features = allFeaturesSource.getFeatures();

    console.log(`[缩放监听] 当前缩放级别: ${currentZoom.toFixed(2)}, 要素总数: ${features.length}`);

    if (features.length === 0) {
      console.log('[缩放监听] 图层中没有要素');
      return;
    }

    let visibleCount = 0;
    let hiddenCount = 0;
    const visibleFeatures = [];

    // 遍历所有要素，更新可见性状态
    features.forEach((feature, index) => {
      const fieldValue = feature.get(fieldName);
      const shouldBeVisible = this.#shouldFeatureBeVisible(fieldValue, fieldRange, currentZoom);

      if (index < 3) {
        console.log(`[要素${index}] 等级=${fieldValue}, 应该可见=${shouldBeVisible}`);
      }

      // 关键修复：强制设置 visible 属性，确保所有要素都有明确的可见性状态
      // 即使之前是 undefined，也要设置为 true/false
      feature.set('visible', shouldBeVisible, true); // 第三个参数 true 表示静默设置，不触发事件

      if (shouldBeVisible) {
        visibleCount++;
        visibleFeatures.push(feature);
      } else {
        hiddenCount++;
      }
    });

    // 关键修复：确保聚合图层只包含可见要素 - 完全清除后再添加
    if (visibleFeaturesSource) {
      const layerSource = layer.getSource();

      // 步骤1：完全清除可见要素源
      console.log(`[聚合更新] 清除前 visibleFeaturesSource 要素数: ${visibleFeaturesSource.getFeatures().length}`);
      visibleFeaturesSource.clear();
      console.log(`[聚合更新] 清除后 visibleFeaturesSource 要素数: ${visibleFeaturesSource.getFeatures().length}`);

      // 步骤2：如果是聚合图层，强制清除聚合缓存
      if (layerSource instanceof Cluster) {
        // 清除聚合源的内部缓存
        const clusterFeaturesBefore = layerSource.getFeatures().length;
        console.log(`[聚合更新] 清除前聚合要素数: ${clusterFeaturesBefore}`);
        layerSource.clear();
        layerSource.refresh();
        console.log(`[聚合更新] 聚合源已清除并刷新`);
      }

      // 步骤3：只添加当前缩放级别可见的要素
      if (visibleFeatures.length > 0) {
        // 关键验证：确保所有要素的 visible 属性都是 true
        const actuallyVisible = visibleFeatures.filter(f => {
          const visible = f.get('visible');
          if (visible !== true) {
            console.warn(`[聚合警告] 发现 visible 属性非 true 的要素:`, {
              name: f.get('name'),
              level: f.get(fieldName),
              visible: visible,
              visibleType: typeof visible
            });
            return false;
          }
          return true;
        });

        if (actuallyVisible.length !== visibleFeatures.length) {
          console.error(`[聚合错误] visibleFeatures 中混入了不可见要素! 预期: ${visibleFeatures.length}, 实际可见: ${actuallyVisible.length}`);
        }

        console.log(`[聚合更新] 准备添加 ${visibleFeatures.length} 个要素, 其中真正可见: ${actuallyVisible.length}`);

        // 只添加真正可见的要素
        visibleFeaturesSource.addFeatures(actuallyVisible);
        const addedCount = visibleFeaturesSource.getFeatures().length;
        console.log(`[聚合更新] 已将 ${actuallyVisible.length} 个可见要素添加到聚合源, 实际源中要素数: ${addedCount}`);

        // 步骤4：强制聚合源重新计算
        if (layerSource instanceof Cluster) {
          layerSource.refresh();
          layer.changed();

          // 等待刷新完成后验证
          setTimeout(() => {
            const clusterFeaturesAfter = layerSource.getFeatures().length;
            console.log(`[聚合更新] 刷新后聚合要素数: ${clusterFeaturesAfter}`);
            console.log('[聚合更新] 聚合源已强制刷新');

            // 验证聚合要素组成
            this.#validateClusterComposition(layerSource, fieldName, currentZoom);
          }, 100);
        }
      } else {
        console.log('[聚合更新] 没有可见要素，聚合源已清空');

        // 确保聚合源被正确清空
        if (layerSource instanceof Cluster) {
          layerSource.clear();
          layerSource.refresh();
        }
      }
    }

    console.log(`[缩放监听] 缩放级别 ${currentZoom.toFixed(2)}: ${visibleCount} 个要素可见, ${hiddenCount} 个要素隐藏`);
  }

  /**
   * 验证聚合要素组成（私有方法）
   * 确保聚合要素只包含可见要素，彻底解决聚合过滤问题
   * @param {Cluster} clusterSource - 聚合源
   * @param {string} fieldName - 字段名
   * @param {number} currentZoom - 当前缩放级别
   * @private
   */
  #validateClusterComposition(clusterSource, fieldName, currentZoom) {
    const clusterFeatures = clusterSource.getFeatures();
    
    console.log(`[聚合验证] 开始验证聚合要素组成，当前缩放级别: ${currentZoom.toFixed(2)}`);
    console.log(`[聚合验证] 聚合要素数量: ${clusterFeatures.length}`);
    
    let totalInvisibleCount = 0;
    let totalVisibleCount = 0;
    
    clusterFeatures.forEach((clusterFeature, index) => {
      const childFeatures = clusterFeature.get('features');
      if (childFeatures) {
        const visibleChildCount = childFeatures.filter(child => 
          child.get('visible') !== false
        ).length;
        
        const invisibleChildCount = childFeatures.length - visibleChildCount;
        totalInvisibleCount += invisibleChildCount;
        totalVisibleCount += visibleChildCount;
        
        if (invisibleChildCount > 0) {
          console.warn(`[聚合验证] 聚合要素 ${index} 包含 ${invisibleChildCount} 个不可见要素: ${childFeatures.length} 个子要素中 ${visibleChildCount} 个可见`);
          
          // 显示不可见要素的详细信息
          const invisibleLevels = {};
          childFeatures.forEach(child => {
            if (child.get('visible') === false) {
              const level = child.get(fieldName);
              invisibleLevels[level] = (invisibleLevels[level] || 0) + 1;
            }
          });
          console.warn(`[聚合验证] 不可见要素等级分布:`, invisibleLevels);
        } else {
          console.log(`[聚合验证] 聚合要素 ${index} 完全由可见要素组成: ${childFeatures.length} 个子要素`);
        }
      }
    });
    
    // 如果发现任何不可见要素，记录警告
    if (totalInvisibleCount > 0) {
      console.warn(`[聚合警告] 总共发现 ${totalInvisibleCount} 个不可见要素混入聚合中`);
      console.warn(`[聚合警告] 可见要素数量: ${totalVisibleCount}, 不可见要素数量: ${totalInvisibleCount}`);
    } else {
      console.log(`[聚合验证] ✅ 所有聚合要素完全由可见要素组成`);
      console.log(`[聚合验证] 可见要素总数: ${totalVisibleCount}`);
    }
    
    return totalInvisibleCount === 0;
  }

  /**
   * 判断要素是否应该可见（私有方法）
   * @param {*} fieldValue - 字段值
   * @param {Object} fieldRange - 字段范围配置
   * @param {number} currentZoom - 当前缩放级别
   * @returns {boolean} 是否可见
   * @private
   */
  #shouldFeatureBeVisible(fieldValue, fieldRange, currentZoom) {
    const { type } = fieldRange;

    if (type === 'discrete') {
      // 离散值模式：找到匹配的配置项
      const matchingConfig = fieldRange.values.find(config => 
        config.value === fieldValue
      );

      if (matchingConfig) {
        return currentZoom >= matchingConfig.minZoom;
      }

    } else if (type === 'continuous') {
      // 连续范围模式：找到包含字段值的配置项
      if (typeof fieldValue !== 'number') {
        console.warn(`连续范围模式下字段值必须是数字，当前值: ${fieldValue}`);
        return false;
      }

      const matchingConfig = fieldRange.ranges.find(config => 
        fieldValue >= config.min && fieldValue <= config.max
      );

      if (matchingConfig) {
        return currentZoom >= matchingConfig.minZoom;
      }
    }

    // 如果没有匹配的配置，默认隐藏
    return false;
  }

  /**
   * 向基于缩放级别的图层添加要素
   * @param {VectorLayer} layer - 目标图层
   * @param {Feature|Array<Feature>} features - 要添加的要素
   * @param {boolean} [updateVisibility=true] - 是否立即更新可见性
   */
  addFeaturesToZoomLayer(layer, features, updateVisibility = true) {
    if (!layer || !(layer instanceof VectorLayer)) {
      throw new Error('layer 必须是有效的 VectorLayer 实例');
    }

    const source = layer.getSource();
    const featureArray = Array.isArray(features) ? features : [features];

    source.addFeatures(featureArray);

    if (updateVisibility) {
      this.#updateFeatureVisibility(layer);
    }

    console.log(`已向图层添加 ${featureArray.length} 个要素`);
  }

  /**
   * 手动刷新基于缩放级别的图层可见性
   * @param {VectorLayer} layer - 要刷新的图层
   */
  refreshZoomBasedLayerVisibility(layer) {
    if (!layer || !(layer instanceof VectorLayer)) {
      console.error('layer 必须是有效的 VectorLayer 实例');
      return;
    }

    const config = layer.get('zoomBasedConfig');
    if (!config) {
      console.error('该图层不是基于缩放级别的图层');
      return;
    }

    this.#updateFeatureVisibility(layer);
    console.log('已手动刷新图层可见性');
  }

  /**
   * 移除基于缩放级别的图层
   * @param {VectorLayer} layer - 要移除的图层
   */
  removeZoomBasedLayer(layer) {
    if (!layer || !(layer instanceof VectorLayer)) {
      throw new Error('layer 必须是有效的 VectorLayer 实例');
    }

    // 移除缩放监听器
    const zoomListener = layer.get('zoomListener');
    if (zoomListener) {
      this.map.getView().un('change:resolution', zoomListener);
    }

    // 从地图中移除图层
    this.map.removeLayer(layer);

    console.log('基于缩放级别的图层已移除');
  }

  /**
   * 获取图层当前可见要素数量
   * @param {VectorLayer} layer - 目标图层
   * @returns {number} 可见要素数量
   */
  getVisibleFeatureCount(layer) {
    if (!layer || !(layer instanceof VectorLayer)) {
      throw new Error('layer 必须是有效的 VectorLayer 实例');
    }

    const source = layer.getSource();
    const features = source.getFeatures();
    const currentZoom = this.map.getView().getZoom();
    const config = layer.get('zoomBasedConfig');

    return features.filter(feature => {
      const fieldValue = feature.get(config.fieldName);
      return this.#shouldFeatureBeVisible(fieldValue, config.fieldRange, currentZoom);
    }).length;
  }

  // ==================== 要素聚合相关方法 ====================

  /**
   * 创建要素聚合图层
   * @param {VectorLayer} sourceLayer - 源图层
   * @param {Object} options - 聚合配置选项
   * @param {number} [options.distance=40] - 聚合距离（像素）
   * @param {number} [options.minDistance=20] - 最小聚合距离（像素）
   * @param {number} [options.maxZoom=14] - 最大聚合缩放级别
   * @param {Function} [options.styleFunction] - 聚合样式函数
   * @returns {VectorLayer} 聚合图层
   */
  createClusterLayer(sourceLayer, options = {}) {
    const {
      distance = 40,
      minDistance = 20,
      maxZoom = 14,
      styleFunction = this.#getDefaultClusterStyle.bind(this)
    } = options;

    const source = sourceLayer.getSource();
    
    // 创建聚合图层
    const clusterLayer = new VectorLayer({
      source: source,
      style: (feature) => {
        const features = feature.get('features');
        const size = features ? features.length : 1;
        
        if (size === 1) {
          // 单个要素，使用原始样式
          const originalFeature = features[0];
          return originalFeature.getStyle() || sourceLayer.getStyle()(originalFeature);
        } else {
          // 聚合要素，使用聚合样式
          return styleFunction(feature, size);
        }
      }
    });

    // 存储聚合配置
    clusterLayer.set('clusterConfig', {
      distance,
      minDistance,
      maxZoom,
      sourceLayer
    });

    // 监听缩放级别变化，动态调整聚合
    this.map.getView().on('change:resolution', () => {
      this.#updateClusterVisibility(clusterLayer);
    });

    console.log('要素聚合图层已创建');
    return clusterLayer;
  }

  /**
   * 获取默认聚合样式（私有方法）
   * @param {Feature} feature - 聚合要素
   * @param {number} size - 聚合数量
   * @returns {Style} 聚合样式
   * @private
   */
  #getDefaultClusterStyle(feature, size) {
    let radius, color, strokeWidth;
    
    if (size < 10) {
      radius = 15;
      color = 'rgba(66, 133, 244, 0.8)';
      strokeWidth = 2;
    } else if (size < 50) {
      radius = 20;
      color = 'rgba(219, 68, 55, 0.8)';
      strokeWidth = 3;
    } else {
      radius = 25;
      color = 'rgba(244, 180, 0, 0.8)';
      strokeWidth = 4;
    }

    return new Style({
      image: new Circle({
        radius: radius,
        fill: new Fill({ color: color }),
        stroke: new Stroke({
          color: '#ffffff',
          width: strokeWidth
        })
      }),
      text: new Text({
        text: size.toString(),
        fill: new Fill({ color: '#ffffff' }),
        stroke: new Stroke({
          color: 'rgba(0, 0, 0, 0.6)',
          width: 3
        }),
        font: 'bold 14px sans-serif',
        offsetY: 0
      })
    });
  }

  /**
   * 更新聚合可见性（私有方法）
   * @param {VectorLayer} clusterLayer - 聚合图层
   * @private
   */
  #updateClusterVisibility(clusterLayer) {
    const currentZoom = this.map.getView().getZoom();
    const config = clusterLayer.get('clusterConfig');
    
    if (currentZoom > config.maxZoom) {
      // 在高缩放级别时禁用聚合
      clusterLayer.setVisible(false);
      config.sourceLayer.setVisible(true);
    } else {
      // 在低缩放级别时启用聚合
      clusterLayer.setVisible(true);
      config.sourceLayer.setVisible(false);
    }
  }

  /**
   * 获取聚合要素的详细信息
   * @param {Feature} clusterFeature - 聚合要素
   * @returns {Object} 聚合详细信息
   */
  getClusterInfo(clusterFeature) {
    const features = clusterFeature.get('features');
    if (!features || features.length === 0) {
      return null;
    }

    const size = features.length;
    const extent = clusterFeature.getGeometry().getExtent();
    const center = getCenter(extent);

    // 统计要素类型
    const featureTypes = {};
    features.forEach(feature => {
      const geometryType = feature.getGeometry().getType();
      featureTypes[geometryType] = (featureTypes[geometryType] || 0) + 1;
    });

    return {
      size,
      center,
      extent,
      featureTypes,
      features: features.slice(0, 10) // 返回前10个要素用于预览
    };
  }

  /**
   * 确保聚合要素中的单个要素属性正确传递
   * 关键修复：当聚合要素中只有一个要素时，确保该要素的属性能够正确显示
   * 动态更新：在聚合源重建时自动更新属性
   * @param {Feature} clusterFeature - 聚合要素
   * @returns {Feature|null} 处理后的要素
   */
  ensureSingleClusterFeatureProperties(clusterFeature) {
    const features = clusterFeature.get('features');
    
    // 检查是否为单个要素的聚合
    if (features && features.length === 1) {
      const singleFeature = features[0];
      console.log("检测到单个要素的聚合，确保属性正确传递");
      
      // 检查原始要素是否可见
      const isOriginalFeatureVisible = singleFeature.get('visible') !== false;
      
      if (!isOriginalFeatureVisible) {
        console.warn("单个聚合要素的原始要素不可见，跳过属性传递");
        return clusterFeature;
      }
      
      // 将原始要素的属性复制到聚合要素上
      const originalProperties = singleFeature.getProperties();
      Object.keys(originalProperties).forEach(key => {
        if (!clusterFeature.get(key) && key !== 'features' && key !== 'geometry') {
          clusterFeature.set(key, originalProperties[key]);
        }
      });
      
      // 设置标记，表示这是单个要素的聚合
      clusterFeature.set('isSingleFeatureCluster', true);
      clusterFeature.set('originalFeature', singleFeature);
      clusterFeature.set('originalFeatureVisible', true);
      
      console.log("单个聚合要素属性传递完成:", clusterFeature.getProperties());
      return clusterFeature;
    } else if (features && features.length > 1) {
      // 多个要素的聚合，确保聚合信息正确
      this.#updateClusterFeatureProperties(clusterFeature);
    }
    
    return clusterFeature;
  }

  /**
   * 更新聚合要素属性（私有方法）
   * 确保聚合要素显示正确的聚合信息
   * 关键修复：只统计可见要素，确保聚合信息与当前缩放级别一致
   * @param {Feature} clusterFeature - 聚合要素
   * @private
   */
  #updateClusterFeatureProperties(clusterFeature) {
    const features = clusterFeature.get('features');
    if (!features || features.length === 0) return;
    
    // 关键修复：只统计可见要素
    const visibleFeatures = features.filter(feature => 
      feature.get('visible') !== false
    );
    const visibleCount = visibleFeatures.length;
    
    // 如果所有要素都不可见，则隐藏聚合要素
    if (visibleCount === 0) {
      console.log("聚合要素中所有子要素都不可见，隐藏聚合要素");
      clusterFeature.set('visible', false);
      return;
    }
    
    // 统计等级分布 - 只统计可见要素
    const levelDistribution = {};
    visibleFeatures.forEach(feature => {
      const level = feature.get('level') || feature.get('properties')?.level;
      if (level) {
        levelDistribution[level] = (levelDistribution[level] || 0) + 1;
      }
    });
    
    // 关键修复：更新聚合要素属性，只反映可见要素的信息
    clusterFeature.set('featureCount', visibleCount); // 只显示可见要素数量
    clusterFeature.set('visibleFeatureCount', visibleCount);
    clusterFeature.set('levelDistribution', levelDistribution);
    clusterFeature.set('isSingleFeatureCluster', false);
    
    console.log(`聚合要素属性更新: ${visibleCount} 个可见要素, 等级分布:`, levelDistribution);
  }

  /**
   * 处理聚合要素点击事件，确保属性正确显示
   * @param {Feature} clickedFeature - 点击的要素
   * @param {VectorLayer} clickedLayer - 点击的图层
   * @returns {Object} 处理结果
   */
  handleClusterFeatureClick(clickedFeature, clickedLayer) {
    // 检查是否为聚合要素
    const clusteredFeatures = clickedFeature.get('clusteredFeatures');
    const clusterFeatures = clickedFeature.get('features');
    
    if ((clusteredFeatures && clusteredFeatures.length > 0) || (clusterFeatures && clusterFeatures.length > 0)) {
      const actualFeatures = clusterFeatures || clusteredFeatures;
      const featureCount = actualFeatures.length;
      
      if (featureCount === 1) {
        // 单个要素的聚合，确保属性正确传递
        const processedFeature = this.ensureSingleClusterFeatureProperties(clickedFeature);
        
        // 获取处理后的属性
        const properties = processedFeature.getProperties();
        
        // 过滤掉内部属性
        const internalKeys = [
          'geometry', 'id', 'features', 'clusteredFeatures',
          'visible', 'imageLoadingStarted', 'hasImageStyle', 'cachedImageUrl',
          'featureCount', 'levelDistribution', 'isSingleFeatureCluster', 'originalFeature'
        ];
        
        const displayProperties = {};
        Object.keys(properties).forEach(key => {
          if (!internalKeys.includes(key)) {
            displayProperties[key] = properties[key];
          }
        });
        
        return {
          isCluster: true,
          isSingleFeature: true,
          properties: displayProperties,
          feature: processedFeature
        };
      } else {
        // 多个要素的聚合，显示聚合信息
        const levelDistribution = clickedFeature.get('levelDistribution') || {};
        
        // 统计等级分布
        actualFeatures.forEach(feature => {
          const level = feature.level || feature.properties?.level;
          if (level) {
            levelDistribution[level] = (levelDistribution[level] || 0) + 1;
          }
        });

        // 格式化等级分布
        const levelText = Object.entries(levelDistribution)
          .sort((a, b) => b[1] - a[1])
          .map(([level, count]) => `${level}: ${count}个`)
          .join(', ');

        // 格式化子要素列表 - 修复属性访问路径
        const featuresList = actualFeatures
          .slice(0, 10)
          .map((f, i) => {
            // 使用正确的 OpenLayers Feature API 访问属性
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

        return {
          isCluster: true,
          isSingleFeature: false,
          properties: clusterInfo,
          feature: clickedFeature
        };
      }
    }
    
    return {
      isCluster: false,
      isSingleFeature: false,
      properties: null,
      feature: clickedFeature
    };
  }

  // ==================== 图层管理优化相关方法 ====================

  /**
   * 图层管理器
   * @param {Object} options - 图层管理配置
   * @param {number} [options.maxLayers=10] - 最大图层数量
   * @param {boolean} [options.autoCleanup=true] - 是否自动清理
   * @param {number} [options.cleanupThreshold=1000] - 清理阈值（要素数量）
   */
  initLayerManager(options = {}) {
    const {
      maxLayers = 10,
      autoCleanup = true,
      cleanupThreshold = 1000
    } = options;

    this.layerManager = {
      maxLayers,
      autoCleanup,
      cleanupThreshold,
      layers: new Map(),
      layerOrder: []
    };

    // 监听图层添加事件
    this.map.getLayers().on('add', (event) => {
      const layer = event.element;
      this.#trackLayer(layer);
    });

    // 监听图层移除事件
    this.map.getLayers().on('remove', (event) => {
      const layer = event.element;
      this.#untrackLayer(layer);
    });

    console.log('图层管理器已初始化');
  }

  /**
   * 跟踪图层（私有方法）
   * @param {Layer} layer - 要跟踪的图层
   * @private
   */
  #trackLayer(layer) {
    if (!this.layerManager || !(layer instanceof VectorLayer)) {
      return;
    }

    const layerId = layer.get('id') || `layer_${Date.now()}`;
    const source = layer.getSource();
    
    this.layerManager.layers.set(layerId, {
      layer,
      source,
      featureCount: source ? source.getFeatures().length : 0,
      lastAccess: Date.now(),
      accessCount: 0
    });

    this.layerManager.layerOrder.push(layerId);

    // 自动清理
    if (this.layerManager.autoCleanup) {
      this.#autoCleanupLayers();
    }

    console.log(`图层已跟踪: ${layerId}, 要素数量: ${this.layerManager.layers.get(layerId).featureCount}`);
  }

  /**
   * 取消跟踪图层（私有方法）
   * @param {Layer} layer - 要取消跟踪的图层
   * @private
   */
  #untrackLayer(layer) {
    if (!this.layerManager) return;

    for (const [layerId, layerInfo] of this.layerManager.layers) {
      if (layerInfo.layer === layer) {
        this.layerManager.layers.delete(layerId);
        this.layerManager.layerOrder = this.layerManager.layerOrder.filter(id => id !== layerId);
        console.log(`图层已取消跟踪: ${layerId}`);
        break;
      }
    }
  }

  /**
   * 自动清理图层（私有方法）
   * @private
   */
  #autoCleanupLayers() {
    if (!this.layerManager || !this.layerManager.autoCleanup) return;

    const currentLayers = this.layerManager.layers.size;
    
    // 检查是否超过最大图层数量
    if (currentLayers > this.layerManager.maxLayers) {
      const layersToRemove = this.layerManager.layerOrder
        .slice(0, currentLayers - this.layerManager.maxLayers);
      
      layersToRemove.forEach(layerId => {
        const layerInfo = this.layerManager.layers.get(layerId);
        if (layerInfo && layerInfo.layer) {
          this.map.removeLayer(layerInfo.layer);
          console.log(`自动清理图层: ${layerId}`);
        }
      });
    }

    // 检查要素数量是否超过阈值
    this.layerManager.layers.forEach((layerInfo, layerId) => {
      if (layerInfo.featureCount > this.layerManager.cleanupThreshold) {
        console.warn(`图层 ${layerId} 要素数量过多: ${layerInfo.featureCount}, 建议进行要素简化`);
      }
    });
  }

  /**
   * 获取图层统计信息
   * @returns {Object} 图层统计信息
   */
  getLayerStats() {
    if (!this.layerManager) {
      return { error: '图层管理器未初始化' };
    }

    const stats = {
      totalLayers: this.layerManager.layers.size,
      totalFeatures: 0,
      layers: []
    };

    this.layerManager.layers.forEach((layerInfo, layerId) => {
      const featureCount = layerInfo.featureCount;
      stats.totalFeatures += featureCount;
      
      stats.layers.push({
        id: layerId,
        featureCount,
        lastAccess: layerInfo.lastAccess,
        accessCount: layerInfo.accessCount,
        needsOptimization: featureCount > this.layerManager.cleanupThreshold
      });
    });

    return stats;
  }

  /**
   * 优化图层性能
   * @param {string} layerId - 图层ID
   * @param {Object} options - 优化选项
   * @param {boolean} [options.simplifyGeometry=true] - 是否简化几何图形
   * @param {number} [options.simplifyTolerance=0.001] - 简化容差
   * @param {boolean} [options.enableClustering=true] - 是否启用聚合
   * @param {number} [options.clusterDistance=40] - 聚合距离
   */
  optimizeLayer(layerId, options = {}) {
    if (!this.layerManager) {
      throw new Error('图层管理器未初始化');
    }

    const layerInfo = this.layerManager.layers.get(layerId);
    if (!layerInfo) {
      throw new Error(`图层未找到: ${layerId}`);
    }

    const {
      simplifyGeometry = true,
      simplifyTolerance = 0.001,
      enableClustering = true,
      clusterDistance = 40
    } = options;

    const layer = layerInfo.layer;
    const source = layerInfo.source;

    // 要素简化
    if (simplifyGeometry && source.getFeatures().length > 100) {
      this.#simplifyLayerFeatures(layer, simplifyTolerance);
    }

    // 要素聚合
    if (enableClustering && source.getFeatures().length > 50) {
      const clusterLayer = this.createClusterLayer(layer, {
        distance: clusterDistance,
        maxZoom: 14
      });
      
      this.map.addLayer(clusterLayer);
      layer.setVisible(false); // 隐藏原始图层
      
      // 更新图层管理器
      this.#trackLayer(clusterLayer);
    }

    console.log(`图层优化完成: ${layerId}`);
  }

  // ==================== 要素简化相关方法 ====================

  /**
   * 简化图层要素（私有方法）
   * @param {VectorLayer} layer - 要简化的图层
   * @param {number} tolerance - 简化容差
   * @private
   */
  #simplifyLayerFeatures(layer, tolerance = 0.001) {
    const source = layer.getSource();
    const features = source.getFeatures();
    
    let simplifiedCount = 0;
    
    features.forEach(feature => {
      const geometry = feature.getGeometry();
      if (geometry && geometry.getType() === 'Polygon') {
        // 简化多边形（减少顶点数量）
        const simplified = this.#simplifyPolygon(geometry, tolerance);
        if (simplified) {
          feature.setGeometry(simplified);
          simplifiedCount++;
        }
      } else if (geometry && geometry.getType() === 'LineString') {
        // 简化线（减少顶点数量）
        const simplified = this.#simplifyLineString(geometry, tolerance);
        if (simplified) {
          feature.setGeometry(simplified);
          simplifiedCount++;
        }
      }
    });

    console.log(`要素简化完成: ${simplifiedCount} 个要素被简化`);
  }

  /**
   * 简化多边形（私有方法）
   * @param {Polygon} polygon - 要简化的多边形
   * @param {number} tolerance - 简化容差
   * @returns {Polygon} 简化后的多边形
   * @private
   */
  #simplifyPolygon(polygon, tolerance) {
    try {
      const coordinates = polygon.getCoordinates();
      if (!coordinates || coordinates.length === 0) return polygon;

      // 简化外环
      const simplifiedExterior = this.#simplifyCoordinates(coordinates[0], tolerance);
      if (!simplifiedExterior || simplifiedExterior.length < 3) return polygon;

      // 简化内环（如果有）
      const simplifiedInterior = coordinates.slice(1).map(ring => 
        this.#simplifyCoordinates(ring, tolerance)
      ).filter(ring => ring && ring.length >= 3);

      const simplifiedCoords = [simplifiedExterior, ...simplifiedInterior];
      return new Polygon(simplifiedCoords);
    } catch (error) {
      console.warn('简化多边形失败:', error);
      return polygon;
    }
  }

  /**
   * 简化线（私有方法）
   * @param {LineString} lineString - 要简化的线
   * @param {number} tolerance - 简化容差
   * @returns {LineString} 简化后的线
   * @private
   */
  #simplifyLineString(lineString, tolerance) {
    try {
      const coordinates = lineString.getCoordinates();
      if (!coordinates || coordinates.length < 2) return lineString;

      const simplifiedCoords = this.#simplifyCoordinates(coordinates, tolerance);
      if (!simplifiedCoords || simplifiedCoords.length < 2) return lineString;

      return new LineString(simplifiedCoords);
    } catch (error) {
      console.warn('简化线失败:', error);
      return lineString;
    }
  }

  /**
   * 简化坐标数组（私有方法）
   * @param {Array} coordinates - 坐标数组
   * @param {number} tolerance - 简化容差
   * @returns {Array} 简化后的坐标数组
   * @private
   */
  #simplifyCoordinates(coordinates, tolerance) {
    if (!coordinates || coordinates.length < 3) return coordinates;

    // 使用道格拉斯-普克算法简化坐标
    const simplified = [];
    
    // 添加第一个点
    simplified.push(coordinates[0]);
    
    // 递归简化
    this.#douglasPeucker(coordinates, 0, coordinates.length - 1, tolerance, simplified);
    
    // 添加最后一个点
    simplified.push(coordinates[coordinates.length - 1]);
    
    return simplified;
  }

  /**
   * 道格拉斯-普克算法（私有方法）
   * @param {Array} coordinates - 坐标数组
   * @param {number} start - 起始索引
   * @param {number} end - 结束索引
   * @param {number} tolerance - 容差
   * @param {Array} result - 结果数组
   * @private
   */
  #douglasPeucker(coordinates, start, end, tolerance, result) {
    if (end <= start + 1) return;

    let maxDistance = 0;
    let maxIndex = start;

    const startPoint = coordinates[start];
    const endPoint = coordinates[end];

    // 找到距离最远的点
    for (let i = start + 1; i < end; i++) {
      const distance = this.#perpendicularDistance(coordinates[i], startPoint, endPoint);
      if (distance > maxDistance) {
        maxDistance = distance;
        maxIndex = i;
      }
    }

    // 如果最大距离大于容差，则递归处理
    if (maxDistance > tolerance) {
      this.#douglasPeucker(coordinates, start, maxIndex, tolerance, result);
      result.push(coordinates[maxIndex]);
      this.#douglasPeucker(coordinates, maxIndex, end, tolerance, result);
    }
  }

  /**
   * 计算点到线的垂直距离（私有方法）
   * @param {Array} point - 点坐标
   * @param {Array} lineStart - 线起点
   * @param {Array} lineEnd - 线终点
   * @returns {number} 垂直距离
   * @private
   */
  #perpendicularDistance(point, lineStart, lineEnd) {
    const [x, y] = point;
    const [x1, y1] = lineStart;
    const [x2, y2] = lineEnd;

    // 计算点到线的垂直距离
    const numerator = Math.abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1);
    const denominator = Math.sqrt(Math.pow(y2 - y1, 2) + Math.pow(x2 - x1, 2));
    
    return denominator === 0 ? 0 : numerator / denominator;
  }

  /**
   * 获取图层性能分析报告
   * @param {string} layerId - 图层ID
   * @returns {Object} 性能分析报告
   */
  getLayerPerformanceReport(layerId) {
    if (!this.layerManager) {
      throw new Error('图层管理器未初始化');
    }

    const layerInfo = this.layerManager.layers.get(layerId);
    if (!layerInfo) {
      throw new Error(`图层未找到: ${layerId}`);
    }

    const source = layerInfo.source;
    const features = source.getFeatures();
    
    const report = {
      layerId,
      featureCount: features.length,
      geometryTypes: {},
      memoryUsage: this.#estimateMemoryUsage(features),
      optimizationRecommendations: []
    };

    // 统计几何类型
    features.forEach(feature => {
      const geometry = feature.getGeometry();
      if (geometry) {
        const type = geometry.getType();
        report.geometryTypes[type] = (report.geometryTypes[type] || 0) + 1;
      }
    });

    // 生成优化建议
    if (features.length > 1000) {
      report.optimizationRecommendations.push('要素数量过多，建议启用要素聚合');
    }
    
    if (report.geometryTypes['Polygon'] > 100) {
      report.optimizationRecommendations.push('多边形要素较多，建议进行几何简化');
    }
    
    if (report.geometryTypes['LineString'] > 500) {
      report.optimizationRecommendations.push('线要素较多，建议进行几何简化');
    }

    return report;
  }

  /**
   * 估算要素内存使用量（私有方法）
   * @param {Array} features - 要素数组
   * @returns {number} 估算的内存使用量（字节）
   * @private
   */
  #estimateMemoryUsage(features) {
    let totalBytes = 0;
    
    features.forEach(feature => {
      // 估算要素属性内存使用
      const properties = feature.getProperties();
      for (const key in properties) {
        if (properties.hasOwnProperty(key)) {
          const value = properties[key];
          totalBytes += this.#estimatePropertyMemory(key, value);
        }
      }
      
      // 估算几何图形内存使用
      const geometry = feature.getGeometry();
      if (geometry) {
        totalBytes += this.#estimateGeometryMemory(geometry);
      }
    });
    
    return totalBytes;
  }

  /**
   * 估算属性内存使用（私有方法）
   * @param {string} key - 属性键
   * @param {*} value - 属性值
   * @returns {number} 估算的内存使用量（字节）
   * @private
   */
  #estimatePropertyMemory(key, value) {
    let bytes = 0;
    
    // 键的内存使用
    bytes += key.length * 2; // UTF-16 字符串
    
    // 值的的内存使用
    if (typeof value === 'string') {
      bytes += value.length * 2;
    } else if (typeof value === 'number') {
      bytes += 8; // 64位浮点数
    } else if (typeof value === 'boolean') {
      bytes += 4;
    } else if (value === null || value === undefined) {
      bytes += 4;
    } else if (Array.isArray(value)) {
      bytes += value.reduce((sum, item) => sum + this.#estimatePropertyMemory('', item), 0);
    } else if (typeof value === 'object') {
      for (const prop in value) {
        if (value.hasOwnProperty(prop)) {
          bytes += this.#estimatePropertyMemory(prop, value[prop]);
        }
      }
    }
    
    return bytes;
  }

  /**
   * 估算几何图形内存使用（私有方法）
   * @param {Geometry} geometry - 几何图形
   * @returns {number} 估算的内存使用量（字节）
   * @private
   */
  #estimateGeometryMemory(geometry) {
    let bytes = 0;
    
    const type = geometry.getType();
    const coordinates = geometry.getCoordinates();
    
    // 基础几何图形对象开销
    bytes += 100;
    
    // 坐标数组内存使用
    if (Array.isArray(coordinates)) {
      bytes += this.#estimateCoordinatesMemory(coordinates);
    }
    
    return bytes;
  }

  /**
   * 估算坐标数组内存使用（私有方法）
   * @param {Array} coordinates - 坐标数组
   * @returns {number} 估算的内存使用量（字节）
   * @private
   */
  #estimateCoordinatesMemory(coordinates) {
    let bytes = 0;

    const countCoordinates = (coords) => {
      if (Array.isArray(coords)) {
        if (typeof coords[0] === 'number') {
          // 单个坐标点 [x, y]
          bytes += coords.length * 8; // 每个数字8字节
        } else {
          // 嵌套数组
          coords.forEach(coord => countCoordinates(coord));
        }
      }
    };

    countCoordinates(coordinates);
    return bytes;
  }

  /**
   * 预加载要素图片（用于聚合图层中的单要素显示）
   * @param {Array<Feature>} features - 要预加载图片的要素数组
   * @param {Function} fetchImageUrlFn - 获取图片URL的异步函数（参数：要素名称，返回：图片URL）
   * @param {Function} loadImageFn - 加载图片并创建样式的函数（参数：图片URL、要素，返回：样式）
   * @param {Object} options - 配置选项
   * @param {number} [options.maxConcurrent=6] - 最大并发请求数
   * @param {number} [options.batchSize=20] - 每批次加载数量
   * @param {Function} [options.onProgress] - 进度回调函数
   * @returns {Promise<Object>} 加载结果统计
   */
  async preloadFeatureImages(features, fetchImageUrlFn, loadImageFn, options = {}) {
    const {
      maxConcurrent = 6,
      batchSize = 20,
      onProgress = null
    } = options;

    console.log(`[图片预加载] 开始预加载 ${features.length} 个要素的图片`);

    // 统计信息
    const stats = {
      total: features.length,
      loaded: 0,
      cached: 0,
      failed: 0,
      skipped: 0
    };

    // 创建请求队列
    const queue = [];
    let activeRequests = 0;

    // 处理单个要素的图片加载
    const loadFeatureImage = async (feature) => {
      const spotName = feature.get('name');
      if (!spotName) {
        stats.skipped++;
        return;
      }

      // 检查是否已缓存图片URL
      const cachedImageUrl = feature.get('cachedImageUrl');
      if (cachedImageUrl) {
        stats.cached++;
        console.log(`[图片预加载] 已缓存: ${spotName}`);
        return;
      }

      try {
        // 获取图片URL
        const imageUrl = await fetchImageUrlFn(spotName);
        if (!imageUrl) {
          stats.failed++;
          return;
        }

        // 缓存图片URL到要素属性
        feature.set('cachedImageUrl', imageUrl);

        // 加载图片并创建样式
        const imageStyle = await loadImageFn(imageUrl, feature);
        if (imageStyle) {
          // 将样式应用到要素（即使要素当前不可见）
          feature.set('preloadedImageStyle', imageStyle);
          stats.loaded++;
          console.log(`[图片预加载] 成功加载: ${spotName}`);
        } else {
          stats.failed++;
        }
      } catch (error) {
        console.error(`[图片预加载] 加载失败: ${spotName}`, error);
        stats.failed++;
      }
    };

    // 执行队列中的下一个任务
    const processQueue = async () => {
      if (queue.length === 0 || activeRequests >= maxConcurrent) {
        return;
      }

      const task = queue.shift();
      activeRequests++;

      await task();

      activeRequests--;

      // 更新进度
      const completed = stats.loaded + stats.cached + stats.failed + stats.skipped;
      if (onProgress) {
        onProgress({
          completed,
          total: stats.total,
          percentage: Math.round((completed / stats.total) * 100)
        });
      }

      // 继续处理队列
      processQueue();
    };

    // 分批次处理要素
    for (let i = 0; i < features.length; i += batchSize) {
      const batch = features.slice(i, Math.min(i + batchSize, features.length));

      // 将批次中的任务加入队列
      batch.forEach(feature => {
        queue.push(() => loadFeatureImage(feature));
      });

      // 启动并发处理
      const concurrentTasks = [];
      for (let j = 0; j < maxConcurrent; j++) {
        concurrentTasks.push(processQueue());
      }

      // 等待当前批次完成
      await Promise.all(concurrentTasks);

      // 等待所有任务完成
      while (queue.length > 0 || activeRequests > 0) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    console.log(`[图片预加载] 完成统计:`, stats);
    return stats;
  }
}
