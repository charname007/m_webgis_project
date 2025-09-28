import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import VectorSource from "ol/source/Vector";
import OSM from "ol/source/OSM";
import { Style, Stroke, Fill, Circle } from "ol/style";
import {
  Draw,
  Modify,
  Snap,
  defaults as defaultInteractions,
} from "ol/interaction";
import { getLength, getArea } from "ol/sphere";
import { LineString, Polygon } from "ol/geom";
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
import LayerSwitcher  from "ol-ext/control/LayerSwitcher";
import Bar from "ol-ext/control/Bar";
import Overview from "ol-ext/control/Overview";
import FeatureList from "ol-ext/control/FeatureList";
import Scale from 'ol-ext/control/Scale';
import SearchCoordinates from "ol-ext/control/SearchCoordinates";
import OverlayControl from "ol-ext/control/Overlay";
import LayerShop from "ol-ext/control/LayerShop";
import Gauge from "ol-ext/control/Gauge";
import Disable from "ol-ext/control/Disable";
import CenterPosition from "ol-ext/control/CenterPosition";
import Select from "ol-ext/control/Select";
import Notification from "ol-ext/control/Notification";
import { XYZ } from "ol/source";
import "ol-ext/dist/ol-ext.min.css";
import "ol/ol.css"
import { unByKey } from "ol/Observable";
import GeoJSON from "ol/format/GeoJSON";
// 确保 OverviewMap 不会被 tree-shaking 移除
// const ensureOverviewMap = () => {
//   if (typeof OverviewMap === 'undefined') {
//     console.warn('OverviewMap is not available');
//   }
//   return OverviewMap;
// };

// // 强制引用 OverviewMap 确保不被 tree-shaking 移除
// ensureOverviewMap();

export default class MapUtils {
  constructor(target) {
    this.map = this.#initMap(target);
  // 状态管理 - 确保所有交互状态可追踪
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
  #initMap(target) {
    const view = new View({
      center: [116.39722, 39.9096], // 默认北京坐标
      zoom: 12,
      projection: "EPSG:4326",
    });

    this.overviewControl = new OverviewMap({
      collapsed: false,
      layers: [new TileLayer({ source: new OSM() })],
      view: new View({
        projection: "EPSG:4326",
        center: [116.39722, 39.9096],
        zoom: 6,
      }),
    });

    this.map = new Map({
      target: target,
      layers: [],
      view: view,
      controls: defaultControls().extend([
        new MousePosition({
          className: "custom-mouse-position",
          coordinateFormat: function(coordinate) {
            // 格式化坐标，只显示小数点后2位
            return coordinate.map(coord => coord.toFixed(2)).join(', ');
          },
        }),
        this.overviewControl,
        new ScaleLine({
          className: "custom-scale-line",
          units: "metric",
          minWidth: 100,
        }),
        new LayerSwitcher ({
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

          ],
        }),
        // new Scale(),
        // new OverlayControl()
        new ZoomSlider(),
        new FeatureList(),
            // new Gauge({ className: "custom-gauge" }),
            new Disable({ className: "custom-disable" }),
            new SearchCoordinates({ className: "custom-search-coordinates" }),
            // new LayerShop({ className: "custom-layer-shop" }),
            new Select({ className: "custom-select" }),
            new CenterPosition({ className: "custom-center-position" }),
            new Notification({ className: "custom-notification" }),
//          new Measure({
//   type: 'LineString', // 初始测量类型：LineString(距离)、Polygon(面积)、Angle(角度)
//   units: 'kilometers', // 单位：kilometers、meters、miles等
//   decimals: 2, // 小数位数
//   label: true, // 在图形上显示测量结果
//   tooltip: true, // 显示鼠标跟随提示
//   style: null, // 使用默认样式，可自定义
//   activeColor: '#ff0000', // 激活状态颜色
//   drawStyle: { // 绘制时样式
//     stroke: {
//       color: '#ff0000',
//       width: 2
//     },
//     fill: {
//       color: 'rgba(255, 0, 0, 0.1)'
//     }
//   }
// })
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
    this.clearMeasureResults()


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
        this.state.highlight.currentFeature.setStyle(this.state.highlight.originalStyle);
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

  loadGeoJsonLayer(geoJson, styleOptions = {}, layerName = "GeoJSON Layer", options = {}) {
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
              this.map.getControls().forEach(control => {
                if (control instanceof LayerSwitcher ) {
                  // 使用正确的方法刷新图层切换器
                  if (control.drawPanel) {
                    control.drawPanel();
                  } else if (control.render) {
                    control.render();
                  }
                  // 触发图层变化事件，让LayerSwitcher重新检测范围
                  this.map.dispatchEvent('change:layer');
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
    if (extent && 
        !isNaN(extent[0]) && 
        !isNaN(extent[1]) && 
        !isNaN(extent[2]) && 
        !isNaN(extent[3])) {
      return extent;
    }
    return null;
  }

  // 获取存储的图层范围（如果存在）
  getStoredLayerExtent(layer) {
    return layer.get('extent') || null;
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
   * 初始化要素点击事件监听，显示属性信息并高亮要素
   * @param {VectorLayer} layer - 要监听的矢量图层
   * @param {Object} options - 弹窗配置选项
   * @param {string} [options.className='feature-info-popup'] - 弹窗CSS类名
   * @param {number[]} [options.offset=[0, -10]] - 弹窗偏移量
   */
  initFeatureClick(options = {}) {
    // 移除已有的点击事件，避免重复绑定
    if (this.featureClickHandler) {
      this.map.un("singleclick", this.featureClickHandler);
    }

    // 配置默认参数
    const config = {
      className: "feature-info-popup",
      offset: [0, -10],
      ...options,
    };

    // 创建属性弹窗元素
    this.createFeaturePopup(config.className, config.offset);

    // 弹窗状态管理
    this.isPopupVisible = false;

    // 绑定点击事件处理函数
    this.featureClickHandler = (evt) => {
      // 如果弹窗已经显示，则忽略点击（必须关闭当前弹窗才能显示新的）
      if (this.isPopupVisible) {
        console.log("弹窗已显示，忽略点击");
        return;
      }

      // 查找点击到的要素
      const features = [];
      let clickedFeature = null;
      let clickedLayer = null;

      this.map.forEachFeatureAtPixel(
        evt.pixel,
        (feature, layer) => {
          console.log("点击到要素:", feature);
          features.push(feature);
          clickedFeature = feature;
          clickedLayer = layer;
        }
      );
      
      if (features.length > 0) {
        // 高亮点击的要素
        this.#highlightFeature(clickedFeature, clickedLayer);
        
        // 显示属性弹窗
        const properties = clickedFeature.getProperties();
        this.showFeaturePopup(properties, evt.coordinate);
        
        console.log("要素高亮并显示属性弹窗");
      } else {
        // 未点击到要素，清除高亮并隐藏弹窗
        this.#clearHighlight();
        this.hideFeaturePopup();
        console.log("未点击到要素，清除高亮");
      }
    };

    this.map.on("singleclick", this.featureClickHandler);
  }

  /**
   * 创建要素属性弹窗DOM元素
   * @param {string} className - 弹窗CSS类名
   */
  createFeaturePopup(className) {
    // 移除已有的弹窗元素
    if (this.featurePopupElement) {
      this.featurePopupElement.remove();
    }

    // 创建弹窗容器
    this.featurePopupElement = document.createElement("div");
    this.featurePopupElement.className = className;
    this.featurePopupElement.style.cssText = `
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
      display: none;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      backdrop-filter: blur(10px);
      transition: all 0.3s ease;
    `;

    // 创建标题栏
    const header = document.createElement("div");
    header.style.cssText = `
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 2px solid #3498db;
    `;

    const title = document.createElement("h3");
    title.textContent = "要素属性";
    title.style.cssText = `
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #2c3e50;
    `;

    // 创建关闭按钮
    const closeBtn = document.createElement("button");
    closeBtn.innerHTML = "×";
    closeBtn.title = "关闭";
    closeBtn.style.cssText = `
      background: #e74c3c;
      border: none;
      border-radius: 50%;
      width: 24px;
      height: 24px;
      line-height: 24px;
      text-align: center;
      cursor: pointer;
      font-size: 14px;
      font-weight: bold;
      color: white;
      transition: all 0.2s ease;
    `;
    closeBtn.onmouseover = () => {
      closeBtn.style.background = '#c0392b';
      closeBtn.style.transform = 'scale(1.1)';
    };
    closeBtn.onmouseout = () => {
      closeBtn.style.background = '#e74c3c';
      closeBtn.style.transform = 'scale(1)';
    };
    closeBtn.onclick = () => this.hideFeaturePopup();

    header.appendChild(title);
    header.appendChild(closeBtn);
    this.featurePopupElement.appendChild(header);

    // 创建内容容器
    this.featurePopupContent = document.createElement("div");
    this.featurePopupContent.style.cssText = `
      max-height: 200px;
      overflow-y: auto;
      padding-right: 5px;
    `;

    // 自定义滚动条样式
    this.featurePopupContent.style.cssText += `
      scrollbar-width: thin;
      scrollbar-color: #bdc3c7 #ecf0f1;
    `;

    // Webkit浏览器滚动条样式
    const scrollbarStyle = document.createElement('style');
    scrollbarStyle.textContent = `
      .${className} div::-webkit-scrollbar {
        width: 6px;
      }
      .${className} div::-webkit-scrollbar-track {
        background: #ecf0f1;
        border-radius: 3px;
      }
      .${className} div::-webkit-scrollbar-thumb {
        background: #bdc3c7;
        border-radius: 3px;
      }
      .${className} div::-webkit-scrollbar-thumb:hover {
        background: #95a5a6;
      }
    `;
    document.head.appendChild(scrollbarStyle);

    this.featurePopupElement.appendChild(this.featurePopupContent);

    // 创建弹窗Overlay
    this.featurePopup = new Overlay({
      element: this.featurePopupElement,
      positioning: "bottom-center",
      stopEvent: false,
      offset: [0, -15]
    });
    this.map.addOverlay(this.featurePopup);
    
    console.log("要素弹窗创建完成 - 优化版");
  }

  /**
   * 显示要素属性弹窗
   * @param {Object} properties - 要素属性对象
   * @param {number[]} coordinate - 弹窗显示的坐标位置
   * @param {number[]} offset - 弹窗偏移量
   */
  showFeaturePopup(properties, coordinate, offset) {
    // 检查弹窗是否已创建
    if (!this.featurePopup || !this.featurePopupElement) {
      console.warn("要素弹窗未初始化，请先调用 createFeaturePopup 方法");
      return;
    }
    
    // 如果弹窗已经显示，则忽略（必须关闭当前弹窗才能显示新的）
    if (this.isPopupVisible) {
      console.log("弹窗已显示，忽略新的显示请求");
      return;
    }
    
    // 清空之前的内容
    if (!coordinate || !Array.isArray(coordinate)) {
      console.warn("坐标为空，无法显示弹窗");
      return;
    }
    this.featurePopupContent.innerHTML = "";

    // 创建属性列表容器
    const propertiesList = document.createElement("div");
    propertiesList.style.cssText = `
      display: flex;
      flex-direction: column;
      gap: 8px;
    `;

    // 统计有效属性数量
    const validProperties = Object.entries(properties).filter(([key]) => 
      !['geometry', 'id'].includes(key)
    );

    if (validProperties.length === 0) {
      const emptyMessage = document.createElement("div");
      emptyMessage.textContent = "暂无属性信息";
      emptyMessage.style.cssText = `
        text-align: center;
        color: #7f8c8d;
        font-style: italic;
        padding: 20px;
      `;
      this.featurePopupContent.appendChild(emptyMessage);
    } else {
      // 遍历属性并创建卡片式布局
      validProperties.forEach(([key, value], index) => {
        const propertyItem = document.createElement("div");
        propertyItem.style.cssText = `
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          padding: 8px 12px;
          background: #f8f9fa;
          border-radius: 6px;
          border-left: 3px solid #3498db;
          transition: all 0.2s ease;
          gap: 15px;
        `;

        propertyItem.onmouseover = () => {
          propertyItem.style.background = '#e8f4fd';
          propertyItem.style.transform = 'translateX(2px)';
        };
        propertyItem.onmouseout = () => {
          propertyItem.style.background = '#f8f9fa';
          propertyItem.style.transform = 'translateX(0)';
        };

        const keySpan = document.createElement("span");
        keySpan.textContent = key;
        keySpan.style.cssText = `
          font-weight: 600;
          color: #2c3e50;
          font-size: 13px;
          min-width: 80px;
          max-width: 120px;
          flex-shrink: 0;
          word-break: break-word;
          line-height: 1.4;
        `;

        const valueSpan = document.createElement("span");
        valueSpan.textContent = value !== null && value !== undefined ? value.toString() : '空值';
        valueSpan.style.cssText = `
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
        `;

        propertyItem.appendChild(keySpan);
        propertyItem.appendChild(valueSpan);
        propertiesList.appendChild(propertyItem);
      });

      this.featurePopupContent.appendChild(propertiesList);
    }

    // 添加属性数量统计
    const countInfo = document.createElement("div");
    countInfo.textContent = `共 ${validProperties.length} 个属性`;
    countInfo.style.cssText = `
      text-align: center;
      font-size: 11px;
      color: #95a5a6;
      margin-top: 10px;
      padding-top: 8px;
      border-top: 1px solid #ecf0f1;
    `;
    this.featurePopupContent.appendChild(countInfo);

    // 设置弹窗位置和显示（添加动画效果）
    this.featurePopup.setPosition(coordinate);
    this.featurePopupElement.style.display = "block";
    
    // 更新弹窗状态
    this.isPopupVisible = true;
    
    // 添加显示动画
    this.featurePopupElement.style.opacity = "0";
    this.featurePopupElement.style.transform = "translateY(10px) scale(0.95)";
    
    setTimeout(() => {
      this.featurePopupElement.style.opacity = "1";
      this.featurePopupElement.style.transform = "translateY(0) scale(1)";
    }, 10);
    
    console.log("要素弹窗显示:", properties, "属性数量:", validProperties.length);
  }

  /**
   * 隐藏要素属性弹窗
   */
  hideFeaturePopup() {
    if (this.featurePopupElement) {
      // 添加隐藏动画
      this.featurePopupElement.style.opacity = "0";
      this.featurePopupElement.style.transform = "translateY(10px) scale(0.95)";
      
      setTimeout(() => {
        this.featurePopupElement.style.display = "none";
        // 更新弹窗状态
        this.isPopupVisible = false;
        // 清除要素高亮
        this.#clearHighlight();
      }, 300);
    }
  }

  /**
   * 移除要素点击监听
   */
  removeFeatureClick() {
    if (this.featureClickHandler) {
      this.map.un("singleclick", this.featureClickHandler);
      this.featureClickHandler = null;
    }
    this.hideFeaturePopup();
  }
}
