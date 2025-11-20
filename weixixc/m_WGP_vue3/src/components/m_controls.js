import Control from 'ol/control/Control';
import { unByKey } from 'ol/Observable';
import Overlay from 'ol/Overlay';
import Feature from 'ol/Feature';
import { Style, Stroke, Fill, Circle } from 'ol/style';
import { Draw, Snap } from 'ol/interaction';
import { getLength, getArea } from 'ol/sphere';
import { LineString, Polygon, Point } from 'ol/geom';
import CircleGeometry from 'ol/geom/Circle';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import GeoJSON from 'ol/format/GeoJSON';
import API_CONFIG from "@/config/api.js";
 
/**
 * 测量工具控制类 - 按钮式测量控件
 * 继承自 ol/control/Control
 */
export class MeasureControl extends Control {
  /**
   * 构造函数
   * @param {Object} options 配置选项
   * @param {string} [options.className='ol-measure-control'] CSS类名
   * @param {string} [options.title='测量工具'] 按钮标题
   * @param {string} [options.activeClassName='active'] 激活状态类名
   */
  constructor(options = {}) {
    const {
      className = 'ol-measure-control',
      title = '测量工具',
      activeClassName = 'active',
      eventsToSuspend = ['singleclick', 'moveend'],
      cursorWhenActive = 'crosshair',
      longPressDuration = 600,
      measureModes = null,
      defaultMeasureMode = null
    } = options;

    // 创建按钮元素
    const button = document.createElement('button');
    button.className = `${className}-button`;
    button.innerHTML = '📏';
    button.title = title;
    button.type = 'button';

    // 创建控件容器
    const element = document.createElement('div');
    element.className = `${className} ol-unselectable ol-control`;
    element.appendChild(button);

    super({
      element: element,
      target: options.target
    });

    // 初始化状态
    this.button = button;
    this.className = className;
    this.activeClassName = activeClassName;
    this.isActive = false;
    this.measureType = 'LineString'; // 默认测量类型：距离
    this.measureLayer = null;
    this.drawInteraction = null;
    this.snapInteraction = null;
    this.tooltip = null;
    this.tooltipElement = null;
    this.defaultButtonContent = button.innerHTML;
    this.eventsToSuspend = Array.isArray(eventsToSuspend)
      ? [...eventsToSuspend]
      : ['singleclick', 'moveend'];
    this.cursorWhenActive = cursorWhenActive;
    this.suspendedMapEvents = new Map();
    this.eventsSuspended = false;
    this.cursorBeforeMeasure = null;

    const defaultModeConfigs = [
      { type: 'LineString', label: '距离', icon: '📏' },

      { type: 'Polygon', label: '面积', icon: '⬜' },
      { type: 'angle', label: '角度', icon: '📐'}
    ];
    const providedModes = Array.isArray(measureModes) && measureModes.length ? measureModes : defaultModeConfigs;

    this.measureModes = providedModes
      .map((mode) => {
        if (typeof mode === 'string') {
          return { type: mode, label: this.getDefaultModeLabel(mode) };
        }
        if (mode && typeof mode === 'object' && mode.type) {
          return {
            ...mode,
            label: mode.label || this.getDefaultModeLabel(mode.type)
          };
        }
        return null;
      })
      .filter(Boolean);

    if (this.measureModes.length === 0) {
      this.measureModes = defaultModeConfigs;
    }

    this.baseTitle = title;
    this.longPressDuration = longPressDuration;
    this.longPressTimer = null;
    this.longPressTriggered = false;
    this.ignoreNextClick = false;

    const requestedMode = defaultMeasureMode || this.measureType;
    const foundIndex = this.measureModes.findIndex((mode) => mode.type === requestedMode);
    this.currentModeIndex = foundIndex !== -1 ? foundIndex : 0;
    this.measureType = this.measureModes[this.currentModeIndex]?.type || 'LineString';

    this.updateButtonDisplay();

    // 绑定事件
    button.addEventListener('click', this.handleButtonClick.bind(this));
    button.addEventListener('mousedown', this.handlePressStart.bind(this));
    button.addEventListener('touchstart', this.handlePressStart.bind(this), { passive: false });
    button.addEventListener('mouseup', this.handlePressEnd.bind(this));
    button.addEventListener('mouseleave', this.handlePressCancel.bind(this));
    button.addEventListener('touchend', this.handlePressEnd.bind(this));
    button.addEventListener('touchcancel', this.handlePressCancel.bind(this));
  }

  /**
   * 设置地图实例
   * @param {ol.Map} map 地图实例
   */
  setMap(map) {
    if (this.map && this.isActive) {
      this.deactivate();
    }
    super.setMap(map);
    this.map = map;
  }

  /**
   * 处理按钮点击事件
   */
  handleButtonClick() {
    if (this.ignoreNextClick) {
      this.ignoreNextClick = false;
      return;
    }

    if (this.isActive) {
      this.deactivate();
    } else {
      this.activate();
    }
  }

  /**
   * 处理按钮长按开始
   */
  handlePressStart(evt) {
    if (!this.measureModes || this.measureModes.length <= 1 || this.longPressDuration <= 0) return;
    if (evt && typeof evt.button === 'number' && evt.button !== 0) return;

    if (evt && evt.type === 'touchstart') {
      evt.preventDefault();
    }

    this.longPressTriggered = false;

    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer);
    }

    this.longPressTimer = setTimeout(() => {
      this.longPressTriggered = true;
      this.ignoreNextClick = true;
      this.cycleMeasureMode();
    }, this.longPressDuration);
  }

  /**
   * 处理按钮长按结束
   */
  handlePressEnd(evt) {
    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer);
      this.longPressTimer = null;
    }

    if (this.longPressTriggered) {
      if (evt) {
        if (typeof evt.preventDefault === 'function') {
          evt.preventDefault();
        }
        if (typeof evt.stopPropagation === 'function') {
          evt.stopPropagation();
        }
      }
    } else {
      this.ignoreNextClick = false;
    }

    this.longPressTriggered = false;
  }

  /**
   * 处理长按取消
   */
  handlePressCancel() {
    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer);
      this.longPressTimer = null;
    }

    this.longPressTriggered = false;
    this.ignoreNextClick = false;
  }

  /**
   * 激活测量模式
   */
  activate() {
    if (!this.map) return;

    this.isActive = true;
    this.button.classList.add(this.activeClassName);
    this.setupMeasureTool();
  }

  /**
   * 取消测量模式
   */
  deactivate() {
    this.isActive = false;
    this.button.classList.remove(this.activeClassName);
    this.cleanupMeasureTool();
  }

  /**
   * 设置测量工具
   */
  setupMeasureTool() {
    if (!this.map) return;

    this.suspendMapEvents();

    // 创建测量图层
    const measureSource = new VectorSource();
    this.measureLayer = new VectorLayer({
      name: 'measure-layer',
      source: measureSource,
      style: new Style({
        fill: new Fill({ color: 'rgba(252, 86, 49, 0.1)' }),
        stroke: new Stroke({ color: '#fc5531', lineDash: [10, 10], width: 3 }),
        image: new Circle({
          radius: 5,
          stroke: new Stroke({ color: 'rgba(0, 0, 0, 0.7)' }),
          fill: new Fill({ color: '#fc5531' })
        })
      }),
      zIndex: 100
    });
    this.map.addLayer(this.measureLayer);

    // 创建绘制交互
    const drawType = this.measureType === 'angle' ? 'LineString' : this.measureType;
    const drawOptions = {
      source: measureSource,
      type: drawType,
      style: new Style({
        fill: new Fill({ color: 'rgba(252, 86, 49, 0.1)' }),
        stroke: new Stroke({ color: '#fc5531', lineDash: [10, 10], width: 3 }),
        image: new Circle({
          radius: 5,
          stroke: new Stroke({ color: 'rgba(0, 0, 0, 0.7)' }),
          fill: new Fill({ color: '#fc5531' })
        })
      })
    };

    if (this.measureType === 'angle') {
      drawOptions.maxPoints = 3;
    }

    this.drawInteraction = new Draw(drawOptions);

    // 创建吸附交互
    this.snapInteraction = new Snap({ source: measureSource });

    // 添加交互到地图
    this.map.addInteraction(this.drawInteraction);
    this.map.addInteraction(this.snapInteraction);

    // 创建测量提示框
    this.createTooltip();

    // 绑定绘制事件
    this.bindDrawEvents();
  }

  /**
   * 创建测量提示框
   */
  createTooltip() {
    this.tooltipElement = document.createElement('div');
    this.tooltipElement.className = 'ol-tooltip ol-tooltip-measure';
    this.tooltipElement.style.cssText = `
      font-size: 14px;
      font-weight: 500;
      background: rgba(255, 255, 255, 0.9);
      color: #070707;
      padding: 6px 12px;
      border-radius: 4px;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
      border: 1px solid #fc5531;
    `;

    this.tooltip = new Overlay({
      element: this.tooltipElement,
      offset: [0, -20],
      positioning: 'bottom-center',
      stopEvent: false
    });

    this.map.addOverlay(this.tooltip);
  }

  /**
   * 绑定绘制事件
   */
  bindDrawEvents() {
    const draw = this.drawInteraction;
    let sketch;
    let listener;

    draw.on('drawstart', (evt) => {
      this.resetMeasurementForNewSketch();

      sketch = evt.feature;
      const tooltipCoord = evt.coordinate;

      listener = sketch.getGeometry().on('change', (evt) => {
        const geom = evt.target;
        const output = this.formatMeasureResult(geom, this.measureType);
        if (this.tooltipElement) {
          this.tooltipElement.innerHTML = output;
        }
        if (this.tooltip) {
          let coord;
          if (this.measureType === 'angle') {
            const coords = geom.getCoordinates();
            if (Array.isArray(coords) && coords.length >= 2) {
              coord = coords[coords.length - 2];
            } else {
              coord = geom.getLastCoordinate();
            }
          } else if (geom.getType() === 'Polygon') {
            coord = geom.getInteriorPoint().getCoordinates();
          } else {
            coord = geom.getLastCoordinate();
          }
          this.tooltip.setPosition(coord);
        }
      });
    });

    draw.on('drawend', () => {
      if (this.tooltipElement) {
        this.tooltipElement.className = 'ol-tooltip ol-tooltip-measure ol-tooltip-static';
      }
      if (listener) {
        unByKey(listener);
      }
    });
  }

  /**
   * 格式化测量结果
   * @param {ol.geom.Geometry} geometry 几何图形
   * @returns {string} 格式化后的结果
   */
  formatMeasureResult(geometry, measureType = this.measureType) {
    if (!geometry || !this.map) return '';

    if (measureType === 'angle') {
      return this.formatAngle(geometry);
    }

    const proj = this.map.getView().getProjection();

    if (geometry instanceof LineString) {
      const length = getLength(geometry, { projection: proj });
      return this.formatLength(length);
    } else if (geometry instanceof Polygon) {
      const area = getArea(geometry, { projection: proj });
      return this.formatArea(area);
    }

    return '';
  }

  /**
   * 格式化长度
   * @param {number} length 长度（米）
   * @returns {string} 格式化后的长度
   */
  formatLength(length) {
    if (length > 1000) {
      return Math.round((length / 1000) * 100) / 100 + ' 千米';
    } else {
      return Math.round(length * 100) / 100 + ' 米';
    }
  }

  /**
   * 格式化面积
   * @param {number} area 面积（平方米）
   * @returns {string} 格式化后的面积
   */
  formatArea(area) {
    if (area > 1000000) {
      return Math.round((area / 1000000) * 100) / 100 + ' 平方千米';
    } else if (area > 10000) {
      return Math.round((area / 10000) * 100) / 100 + ' 公顷';
    } else {
      return Math.round(area * 100) / 100 + ' 平方米';
    }
  }

  resetMeasurementForNewSketch() {
    const source = this.measureLayer ? this.measureLayer.getSource() : null;
    if (source) {
      source.clear();
    }

    if (this.tooltipElement) {
      this.tooltipElement.className = 'ol-tooltip ol-tooltip-measure';
      this.tooltipElement.innerHTML = '';
    }

    if (this.tooltip) {
      this.tooltip.setPosition(undefined);
    }
  }

  /**
   * 格式化角度
   * @param {ol.geom.Geometry} geometry 几何对象
   * @returns {string} 格式化后的角度
   */
  formatAngle(geometry) {
    if (!(geometry instanceof LineString)) return '';

    const coords = geometry.getCoordinates();
    if (!Array.isArray(coords)) {
      return '';
    }

    if (coords.length < 3) {
      const remaining = 3 - coords.length;
      if (remaining === 2) {
        return '请选择角的第二个点';
      }
      if (remaining === 1) {
        return '请选择角的第三个点';
      }
      return '';
    }

    const points = coords.length > 3 ? coords.slice(-3) : coords;
    const angle = this.calculateAngle(points[0], points[1], points[2]);

    if (!Number.isFinite(angle)) {
      return '';
    }

    return `${angle.toFixed(2)}°`;
  }

  /**
   * 计算三点构成的角度
   * @param {number[]} p1 第一个点
   * @param {number[]} p2 顶点
   * @param {number[]} p3 第三个点
   * @returns {number} 角度（度）
   */
  calculateAngle(p1, p2, p3) {
    if (!p1 || !p2 || !p3) return NaN;

    const v1x = p1[0] - p2[0];
    const v1y = p1[1] - p2[1];
    const v2x = p3[0] - p2[0];
    const v2y = p3[1] - p2[1];

    const dot = v1x * v2x + v1y * v2y;
    const mag1 = Math.hypot(v1x, v1y);
    const mag2 = Math.hypot(v2x, v2y);

    if (!mag1 || !mag2) return NaN;

    const cos = Math.max(-1, Math.min(1, dot / (mag1 * mag2)));
    const angleRad = Math.acos(cos);
    return (angleRad * 180) / Math.PI;
  }

  /**
  /**
   * 清理测量工具
   */
  cleanupMeasureTool() {
    // 移除交互
    if (this.drawInteraction) {
      this.map.removeInteraction(this.drawInteraction);
      this.drawInteraction = null;
    }
    if (this.snapInteraction) {
      this.map.removeInteraction(this.snapInteraction);
      this.snapInteraction = null;
    }

    // 移除图层
    if (this.measureLayer) {
      this.map.removeLayer(this.measureLayer);
      this.measureLayer = null;
    }

    // 移除提示框
    if (this.tooltip) {
      this.map.removeOverlay(this.tooltip);
      this.tooltip = null;
    }
    if (this.tooltipElement) {
      this.tooltipElement.remove();
      this.tooltipElement = null;
    }

    this.restoreMapEvents();
  }

  /**
   * 设置测量类型
   * @param {string} type 测量类型 ('LineString', 'Polygon', 'angle')
   */
  setMeasureType(type) {
    this.measureType = type;

    const foundIndex = this.measureModes.findIndex((mode) => mode.type === type);
    if (foundIndex !== -1) {
      this.currentModeIndex = foundIndex;
    }

    this.updateButtonDisplay();

    if (this.isActive) {
      this.deactivate();
      this.activate();
    }
  }

  cycleMeasureMode() {
    if (!this.measureModes || this.measureModes.length <= 1) return;

    const nextIndex = (this.currentModeIndex + 1) % this.measureModes.length;
    const nextMode = this.measureModes[nextIndex];
    if (!nextMode) return;

    this.setMeasureType(nextMode.type);
  }

  updateButtonDisplay() {
    if (!this.button) return;

    const mode = this.measureModes[this.currentModeIndex] || { type: this.measureType };
    const modeLabel = mode.label || this.getDefaultModeLabel(mode.type);

    this.button.setAttribute('data-measure-mode', mode.type || 'unknown');
    this.button.setAttribute('data-measure-label', modeLabel || '');
    this.button.title = `${this.baseTitle}（${modeLabel}） - 单击开始/停止，长按切换模式`;
    this.button.setAttribute('aria-label', `${this.baseTitle}（${modeLabel}）`);

    if (mode.icon) {
      this.button.innerHTML = mode.icon;
    } else if (typeof this.defaultButtonContent === 'string') {
      this.button.innerHTML = this.defaultButtonContent;
    }
  }

  getDefaultModeLabel(type) {
    switch (type) {
      case 'Polygon':
        return '面积';
      case 'angle':
        return '角度';
      case 'LineString':
      default:
        return '距离';
    }
  }

  /**
   * 暂停地图事件，避免与量测操作冲突
   */
  suspendMapEvents() {
    if (!this.map || this.eventsSuspended) return;

    this.suspendedMapEvents = new Map();
    const eventTypes = Array.isArray(this.eventsToSuspend)
      ? this.eventsToSuspend
      : [];

    eventTypes.forEach((type) => {
      const listeners = this.map.getListeners?.(type);
      if (!listeners || listeners.length === 0) return;

      const stored = listeners.slice();
      stored.forEach((listener) => this.map.un(type, listener));
      if (stored.length > 0) {
        this.suspendedMapEvents.set(type, stored);
      }
    });

    const viewport = this.map.getViewport?.();
    if (viewport) {
      this.cursorBeforeMeasure = viewport.style.cursor;
      viewport.style.cursor = this.cursorWhenActive;
    }

    this.map.__measureControlActive = true;
    this.eventsSuspended = true;
  }

  /**
   * 恢复先前暂停的地图事件
   */
  restoreMapEvents() {
    if (!this.map || !this.eventsSuspended) return;

    if (this.suspendedMapEvents && this.suspendedMapEvents.size > 0) {
      this.suspendedMapEvents.forEach((listeners, type) => {
        listeners.forEach((listener) => this.map.on(type, listener));
      });
      this.suspendedMapEvents.clear();
    }

    const viewport = this.map.getViewport?.();
    if (viewport) {
      viewport.style.cursor = this.cursorBeforeMeasure || '';
      this.cursorBeforeMeasure = null;
    }

    delete this.map.__measureControlActive;
    this.eventsSuspended = false;
  }
}

/**
 * 定位工具控制类 - 按钮式定位控件
 * 继承自 ol/control/Control
 */
export class LocationControl extends Control {
  /**
   * 构造函数
   * @param {Object} options 配置选项
   * @param {string} [options.className='ol-location-control'] CSS类名
   * @param {string} [options.title='定位'] 按钮标题
   * @param {number} [options.targetZoom=16] 目标缩放级别
   * @param {number} [options.animationDuration=800] 动画持续时间（毫秒）
   */
  constructor(options = {}) {
    const {
      className = 'ol-location-control',
      title = '定位',
      targetZoom = 16,
      animationDuration = 800
    } = options;

    // 创建按钮元素
    const button = document.createElement('button');
    button.className = `${className}-button`;
    button.innerHTML = '📍';
    button.title = title;
    button.type = 'button';

    // 创建控件容器
    const element = document.createElement('div');
    element.className = `${className} ol-unselectable ol-control`;
    element.appendChild(button);

    super({
      element: element,
      target: options.target
    });

    // 初始化状态
    this.button = button;
    this.className = className;
    this.targetZoom = targetZoom;
    this.animationDuration = animationDuration;
    this.isLocating = false;
    this.locationLayer = null;
    this.locationMarker = null;

    // 绑定事件
    button.addEventListener('click', this.handleButtonClick.bind(this));
  }

  /**
   * 设置地图实例
   * @param {ol.Map} map 地图实例
   */
  setMap(map) {
    super.setMap(map);
    this.map = map;
  }

  /**
   * 处理按钮点击事件
   */
  handleButtonClick() {
    if (this.isLocating) {
      this.stopLocating();
    } else {
      this.startLocating();
    }
  }

  /**
   * 开始定位
   */
  async startLocating() {
    if (!this.map || this.isLocating) return;

    this.isLocating = true;
    this.button.classList.add('locating');
    this.button.innerHTML = '⏳';
    this.button.title = '定位中...';

    try {
      const position = await this.getCurrentPosition();
      await this.centerToPosition(position);
      this.showLocationMarker(position);
      this.showSuccess();
    } catch (error) {
      this.showError(error.message);
    } finally {
      this.isLocating = false;
      this.button.classList.remove('locating');
      this.button.innerHTML = '📍';
    }
  }

  /**
   * 停止定位
   */
  stopLocating() {
    this.isLocating = false;
    this.button.classList.remove('locating');
    this.button.innerHTML = '📍';
    this.button.title = '定位';
    this.hideLocationMarker();
  }

  /**
   * 获取当前位置
   * @returns {Promise<Object>} 位置信息
   */
  getCurrentPosition() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('浏览器不支持地理位置API'));
        return;
      }

      const options = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      };

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude, accuracy } = position.coords;
          resolve({
            coordinate: [longitude, latitude],
            accuracy: accuracy,
            timestamp: position.timestamp
          });
        },
        (error) => {
          let errorMessage;
          switch (error.code) {
            case error.PERMISSION_DENIED:
              errorMessage = '用户拒绝了地理位置权限请求';
              break;
            case error.POSITION_UNAVAILABLE:
              errorMessage = '无法获取当前位置信息';
              break;
            case error.TIMEOUT:
              errorMessage = '获取位置信息超时';
              break;
            default:
              errorMessage = '未知错误发生';
          }
          reject(new Error(errorMessage));
        },
        options
      );
    });
  }

  /**
   * 将地图居中到指定位置
   * @param {Object} position 位置信息
   */
  async centerToPosition(position) {
    const view = this.map.getView();
    
    return new Promise((resolve) => {
      view.animate({
        center: position.coordinate,
        zoom: this.targetZoom,
        duration: this.animationDuration
      }, () => {
        resolve();
      });
    });
  }

  /**
   * 显示位置标记
   * @param {Object} position 位置信息
   */
  showLocationMarker(position) {

    if (!this.locationLayer) {

      const source = new VectorSource();

      this.locationLayer = new VectorLayer({
        name:'CurrentLocation',
        source: source,

        style: new Style({

          image: new Circle({

            radius: 8,

            fill: new Fill({ color: '#4285F4' }),

            stroke: new Stroke({

              color: '#FFFFFF',

              width: 2

            })

          })

        }),

        // zIndex: 1000

      });

      this.map.addLayer(this.locationLayer);

    }



    const locationSource = this.locationLayer.getSource ? this.locationLayer.getSource() : null;

    if (locationSource) {

      locationSource.clear();

    }


    //添加精度圆会导致卡顿
    // if (position.accuracy && position.accuracy > 0 && locationSource) {

    //   const accuracyFeature = new Feature({

    //     geometry: new CircleGeometry(position.coordinate, position.accuracy)

    //   });

    //   accuracyFeature.setStyle(new Style({

    //     stroke: new Stroke({

    //       color: '#4285F4',

    //       width: 1,

    //       lineDash: [5, 5]

    //     }),

    //     fill: new Fill({

    //       color: 'rgba(66, 133, 244, 0.1)'

    //     })

    //   }));

    //   locationSource.addFeature(accuracyFeature);

    // }



    this.locationMarker = new Feature({

      geometry: new Point(position.coordinate)

    });

    this.locationMarker.setStyle(new Style({

      image: new Circle({

        radius: 8,

        fill: new Fill({ color: '#4285F4' }),

        stroke: new Stroke({

          color: '#FFFFFF',

          width: 2

        })

      })

    }));



    if (locationSource) {

      locationSource.addFeature(this.locationMarker);

    }



    this.updateCenterPinPosition(position.coordinate);

  }



  updateCenterPinPosition(coordinate) {

    if (!this.map || !coordinate) return;



    const layerCollection = typeof this.map.getLayers === 'function' ? this.map.getLayers() : null;

    const layers = layerCollection && typeof layerCollection.getArray === 'function'

      ? layerCollection.getArray()

      : [];



    const pinLayer = layers.find((layer) => {

      return layer && typeof layer.get === 'function' && layer.get('title') === '当前位置';

    });



    if (!pinLayer || typeof pinLayer.getSource !== 'function') return;



    const source = pinLayer.getSource();

    if (!source || typeof source.getFeatures !== 'function') return;



    const features = source.getFeatures();

    let pinFeature = features && features.length > 0 ? features[0] : null;



    if (!pinFeature) {

      pinFeature = new Feature({ geometry: new Point(coordinate) });

      source.addFeature(pinFeature);

    } else {

      const geometry = pinFeature.getGeometry();

      if (geometry && geometry instanceof Point) {

        geometry.setCoordinates(coordinate);

      } else {

        pinFeature.setGeometry(new Point(coordinate));

      }

    }



    pinFeature.set('coordinates', coordinate);

    if (typeof pinFeature.changed === 'function') {

      pinFeature.changed();

    }

    if (typeof source.changed === 'function') {

      source.changed();

    }

  }



  hideLocationMarker() {
    if (this.locationLayer) {
      this.locationLayer.getSource().clear();
    }
  }

  /**
   * 显示成功状态
   */
  showSuccess() {
    this.button.classList.add('success');
    this.button.title = '定位成功';
    
    setTimeout(() => {
      this.button.classList.remove('success');
      this.button.title = '定位';
    }, 3000);
  }

  /**
   * 显示错误状态
   * @param {string} message 错误信息
   */
  showError(message) {
    this.button.classList.add('error');
    this.button.title = message;
    
    setTimeout(() => {
      this.button.classList.remove('error');
      this.button.title = '定位';
    }, 3000);
    
    console.error('定位失败:', message);
  }
}

/**
 * 路线规划控制类 - 按钮式路线规划控件
 * 继承自 ol/control/Control
 * 功能：点击按钮，在地图上选取2点（或选取要素），向后端route端点发送请求，
 * 得到返回的多个geojson，将它们分别加载为路线图层
 */
export class RoutePlanningControl extends Control {
  /**
   * 构造函数
   * @param {Object} options 配置选项
   * @param {string} [options.className='ol-route-planning-control'] CSS类名
   * @param {string} [options.title='路线规划'] 按钮标题
   * @param {string} [options.activeClassName='active'] 激活状态类名
  //  * @param {string} [options.baseURL=''] API基础URL
   */
  constructor(options = {}) {
    const {
      className = 'ol-route-planning-control',
      title = '路线规划',
      activeClassName = 'active',
      // baseURL = '',
      eventsToSuspend = ['singleclick', 'moveend'],
      cursorWhenActive = 'crosshair',
      longPressDuration = 600
    } = options;

    // 创建按钮元素
    const button = document.createElement('button');
    button.className = `${className}-button`;
    button.innerHTML = '🛣️';
    button.title = title;
    button.type = 'button';

    // 创建控件容器
    const element = document.createElement('div');
    element.className = `${className} ol-unselectable ol-control`;
    element.appendChild(button);

    super({
      element: element,
      target: options.target
    });

    // 初始化状态
    this.button = button;
    this.className = className;
    this.activeClassName = activeClassName;
    // this.baseURL = baseURL;
    this.isActive = false;
    this.isSelecting = false;
    this.selectedPoints = []; // 存储选中的点 [起点, 终点]
    this.routeMode = 'driving'; // 默认路线模式：驾车
    this.routeLayers = []; // 存储创建的路线图层
    this.eventsToSuspend = Array.isArray(eventsToSuspend)
      ? [...eventsToSuspend]
      : ['singleclick', 'moveend'];
    this.cursorWhenActive = cursorWhenActive;
    this.suspendedMapEvents = new Map();
    this.eventsSuspended = false;
    this.cursorBeforePlanning = null;
    this.baseTitle = title;
    this.longPressDuration = longPressDuration;
    this.longPressTimer = null;
    this.longPressTriggered = false;
    this.ignoreNextClick = false;

    // 定义路线规划模式
    this.routeModes = [
      { type: 'driving', label: '驾车', icon: '🚗' },
      { type: 'walking', label: '步行', icon: '🚶' },
      { type: 'bicycling', label: '骑行', icon: '🚲' }
    ];
    this.currentModeIndex = 0;

    this.updateButtonDisplay();

    // 绑定事件
    button.addEventListener('click', this.handleButtonClick.bind(this));
    button.addEventListener('mousedown', this.handlePressStart.bind(this));
    button.addEventListener('touchstart', this.handlePressStart.bind(this), { passive: false });
    button.addEventListener('mouseup', this.handlePressEnd.bind(this));
    button.addEventListener('mouseleave', this.handlePressCancel.bind(this));
    button.addEventListener('touchend', this.handlePressEnd.bind(this));
    button.addEventListener('touchcancel', this.handlePressCancel.bind(this));
  }

  /**
   * 设置地图实例
   * @param {ol.Map} map 地图实例
   */
  setMap(map) {
    if (this.map && this.isActive) {
      this.deactivate();
    }
    super.setMap(map);
    this.map = map;
  }

  /**
   * 处理按钮点击事件
   */
  handleButtonClick() {
    if (this.ignoreNextClick) {
      this.ignoreNextClick = false;
      return;
    }

    if (this.isActive) {
      if (this.isSelecting) {
        // 如果正在选点，则取消选点
        this.cancelPointSelection();
      } else {
        // 如果已激活但不在选点状态，则取消整个路线规划
        this.deactivate();
      }
    } else {
      // 激活路线规划模式
      this.activate();
    }
  }

  /**
   * 处理按钮长按开始
   */
  handlePressStart(evt) {
    if (this.routeModes.length <= 1 || this.longPressDuration <= 0) return;
    if (evt && typeof evt.button === 'number' && evt.button !== 0) return;

    if (evt && evt.type === 'touchstart') {
      evt.preventDefault();
    }

    this.longPressTriggered = false;

    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer);
    }

    this.longPressTimer = setTimeout(() => {
      this.longPressTriggered = true;
      this.ignoreNextClick = true;
      this.cycleRouteMode();
    }, this.longPressDuration);
  }

  /**
   * 处理按钮长按结束
   */
  handlePressEnd(evt) {
    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer);
      this.longPressTimer = null;
    }

    if (this.longPressTriggered) {
      if (evt) {
        if (typeof evt.preventDefault === 'function') {
          evt.preventDefault();
        }
        if (typeof evt.stopPropagation === 'function') {
          evt.stopPropagation();
        }
      }
    } else {
      this.ignoreNextClick = false;
    }

    this.longPressTriggered = false;
  }

  /**
   * 处理长按取消
   */
  handlePressCancel() {
    if (this.longPressTimer) {
      clearTimeout(this.longPressTimer);
      this.longPressTimer = null;
    }

    this.longPressTriggered = false;
    this.ignoreNextClick = false;
  }

  /**
   * 激活路线规划模式
   */
  activate() {
    if (!this.map) return;

    this.isActive = true;
    this.button.classList.add(this.activeClassName);
    this.startPointSelection();
  }

  /**
   * 取消路线规划模式
   */
  deactivate() {
    this.isActive = false;
    this.isSelecting = false;
    this.selectedPoints = [];
    this.button.classList.remove(this.activeClassName);
    this.cleanupPlanningTool();
  }

  /**
   * 开始选点
   */
  startPointSelection() {
    if (!this.map) return;

    this.isSelecting = true;
    this.selectedPoints = [];
    this.suspendMapEvents();

    // 绑定地图点击事件
    this.mapClickHandler = this.map.on('singleclick', this.handleMapClick.bind(this));

    // 更新按钮状态
    this.updateButtonState('请选择起点');
  }

  /**
   * 取消选点
   */
  cancelPointSelection() {
    this.isSelecting = false;
    this.selectedPoints = [];
    this.restoreMapEvents();

    // 移除地图点击事件
    if (this.map && this.mapClickHandler) {
      unByKey(this.mapClickHandler);
      this.mapClickHandler = null;
    }

    // 更新按钮状态
    this.updateButtonState('路线规划');
  }

  /**
   * 处理地图点击事件 - 智能选点机制
   * @param {ol.MapBrowserEvent} evt 地图点击事件
   */
  handleMapClick(evt) {
    if (!this.isSelecting || !this.map) return;

    const coordinate = evt.coordinate;
    const pixel = evt.pixel;

    // 智能选点：检查是否点击了要素
    const clickedFeature = this.detectClickedFeature(pixel);

    let selectedPoint;
    if (clickedFeature) {
      // 点击了要素，使用要素的几何中心点
      selectedPoint = this.getFeatureCenter(clickedFeature);
      console.log('点击了要素，使用要素中心点:', selectedPoint);
    } else {
      // 点击了空白处，使用坐标点
      selectedPoint = coordinate;
      console.log('点击了空白处，使用坐标点:', selectedPoint);
    }

    this.selectedPoints.push(selectedPoint);

    // 根据已选点数更新状态
    if (this.selectedPoints.length === 1) {
      this.updateButtonState('请选择终点');
    } else if (this.selectedPoints.length === 2) {
      this.updateButtonState('正在规划路线...');
      this.requestRoutePlanning();
    }
  }

  /**
   * 检测点击的要素
   * @param {Array} pixel 像素坐标
   * @returns {ol.Feature|null} 点击的要素或null
   */
  detectClickedFeature(pixel) {
    if (!this.map) return null;

    let clickedFeature = null;
    this.map.forEachFeatureAtPixel(pixel, (feature, layer) => {
      // 只返回第一个找到的要素
      if (!clickedFeature && feature && feature.getGeometry()) {
        clickedFeature = feature;
      }
      return clickedFeature ? true : false; // 找到要素后停止遍历
    });

    return clickedFeature;
  }

  /**
   * 获取要素的几何中心点
   * @param {ol.Feature} feature 要素
   * @returns {Array} 中心点坐标
   */
  getFeatureCenter(feature) {
    const geometry = feature.getGeometry();
    if (!geometry) return null;

    const extent = geometry.getExtent();
    if (!extent) return null;

    // 计算要素包围盒的中心点
    const centerX = (extent[0] + extent[2]) / 2;
    const centerY = (extent[1] + extent[3]) / 2;

    return [centerX, centerY];
  }

  /**
   * 请求路线规划
   */
  async requestRoutePlanning() {
    if (this.selectedPoints.length !== 2) {
      console.error('需要选择起点和终点');
      return;
    }

    const [startPoint, endPoint] = this.selectedPoints;

    try {
      // 构建请求参数 - 高德地图API要求"经度,纬度"格式
      // 同时确保坐标精度符合高德地图API要求（小数点后最多6位）
      const params = {
        origin: this.formatCoordinateForAMap(startPoint), // 经度,纬度
        destination: this.formatCoordinateForAMap(endPoint), // 经度,纬度
        mode: this.routeMode
      };
      console.log('请求参数',params)

      // 发送请求到后端API
      const response = await this.sendRouteRequest(params);

      // 处理响应数据
      this.handleRouteResponse(response);

    } catch (error) {
      console.error('路线规划请求失败:', error);
      this.updateButtonState('路线规划失败');

      // 延迟后恢复状态
      setTimeout(() => {
        this.updateButtonState('路线规划');
      }, 2000);
    } finally {
      // 完成选点，准备下一次规划
      this.isSelecting = false;
      this.selectedPoints = [];
      this.restoreMapEvents();

      // 移除地图点击事件
      if (this.map && this.mapClickHandler) {
        unByKey(this.mapClickHandler);
        this.mapClickHandler = null;
      }
    }
  }

  /**
   * 格式化坐标以符合高德地图API要求
   * 确保坐标精度不超过6位小数
   * @param {Array} coordinate 坐标数组 [经度, 纬度]
   * @returns {string} 格式化后的坐标字符串 "经度,纬度"
   */
  formatCoordinateForAMap(coordinate) {
    if (!Array.isArray(coordinate) || coordinate.length !== 2) {
      console.error('坐标格式错误:', coordinate);
      return '';
    }

    // 确保坐标精度不超过6位小数
    const lng = parseFloat(coordinate[0].toFixed(6));
    const lat = parseFloat(coordinate[1].toFixed(6));

    // 返回"经度,纬度"格式
    return `${lng},${lat}`;
  }

  /**
   * 发送路线规划请求
   * @param {Object} params 请求参数
   * @returns {Promise<Object>} 响应数据
   */
  async sendRouteRequest(params) {
    // 这里需要根据实际的后端API进行调整
    // const endpoint = `${this.baseURL}/route/${this.routeMode}`;
    const endpoint = API_CONFIG.buildURL(
      API_CONFIG.endpoints.routes[this.routeMode]
    );
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  /**
   * 处理路线规划响应
   * @param {Object} response 响应数据
   */
  handleRouteResponse(response) {
    if (!response || !response.paths || !Array.isArray(response.paths)) {
      console.error('无效的路线规划响应');
      return;
    }

    // 清理之前的路线图层
    this.clearRouteLayers();

    // 为每条路径创建图层
    response.paths.forEach((path, index) => {
      if (path && path.type === 'FeatureCollection' && Array.isArray(path.features)) {
        this.createRouteLayer(path, index);
      }
    });

    this.updateButtonState('路线规划完成');

    // 延迟后恢复状态
    setTimeout(() => {
      this.updateButtonState('路线规划');
    }, 2000);
  }

  /**
   * 创建路线图层
   * @param {Object} geojson GeoJSON数据
   * @param {number} index 路径索引
   */
  createRouteLayer(geojson, index) {
    if (!this.map) return;

    // 创建矢量源
    const source = new VectorSource({
      features: new GeoJSON().readFeatures(geojson, {
        featureProjection: this.map.getView().getProjection()
      })
    });

    // 创建图层样式
    const style = this.createRouteStyle(index);

    // 创建图层
    const layer = new VectorLayer({
      name: this.generateLayerName(index),
      source: source,
      style: style,
      zIndex: 100
    });

    // 添加到地图
    this.map.addLayer(layer);
    this.routeLayers.push(layer);
  }

  /**
   * 创建路线样式
   * @param {number} index 路径索引
   * @returns {ol.style.Style} 样式对象
   */
  createRouteStyle(index) {
    // 定义不同路径的颜色
    const colors = [
      '#ff0000', // 红色
      '#0000ff', // 蓝色
      '#00ff00', // 绿色
      '#ffff00', // 黄色
      '#ff00ff', // 紫色
      '#00ffff'  // 青色
    ];

    const color = colors[index % colors.length];

    return new Style({
      stroke: new Stroke({
        color: color,
        width: 4,
        lineDash: index === 0 ? null : [10, 5] // 第一条路径实线，其他虚线
      })
    });
  }

  /**
   * 生成图层名称
   * @param {number} index 路径索引
   * @returns {string} 图层名称
   */
  generateLayerName(index) {
    const [startPoint, endPoint] = this.selectedPoints;
    const modeLabel = this.getModeLabel(this.routeMode);

    // 这里可以添加更智能的起点终点名称获取逻辑
    const startName = `起点`;
    const endName = `终点`;

    return `${startName}->${endName}_${index + 1}_${modeLabel}`;
  }

  /**
   * 清理路线图层
   */
  clearRouteLayers() {
    if (!this.map) return;

    this.routeLayers.forEach(layer => {
      this.map.removeLayer(layer);
    });
    this.routeLayers = [];
  }

  /**
   * 清理规划工具
   */
  cleanupPlanningTool() {
    this.clearRouteLayers();
    this.restoreMapEvents();

    // 移除地图点击事件
    if (this.map && this.mapClickHandler) {
      unByKey(this.mapClickHandler);
      this.mapClickHandler = null;
    }
  }

  /**
   * 切换路线模式
   */
  cycleRouteMode() {
    if (this.routeModes.length <= 1) return;

    const nextIndex = (this.currentModeIndex + 1) % this.routeModes.length;
    const nextMode = this.routeModes[nextIndex];
    if (!nextMode) return;

    this.setRouteMode(nextMode.type);
  }

  /**
   * 设置路线模式
   * @param {string} mode 路线模式
   */
  setRouteMode(mode) {
    this.routeMode = mode;

    const foundIndex = this.routeModes.findIndex((routeMode) => routeMode.type === mode);
    if (foundIndex !== -1) {
      this.currentModeIndex = foundIndex;
    }

    this.updateButtonDisplay();
  }

  /**
   * 更新按钮显示
   */
  updateButtonDisplay() {
    if (!this.button) return;

    const mode = this.routeModes[this.currentModeIndex] || { type: this.routeMode };
    const modeLabel = mode.label || this.getModeLabel(mode.type);

    this.button.setAttribute('data-route-mode', mode.type || 'unknown');
    this.button.setAttribute('data-route-label', modeLabel || '');
    this.button.title = `${this.baseTitle}（${modeLabel}） - 单击开始/停止，长按切换模式`;
    this.button.setAttribute('aria-label', `${this.baseTitle}（${modeLabel}）`);

    if (mode.icon) {
      this.button.innerHTML = mode.icon;
    }
  }

  /**
   * 更新按钮状态
   * @param {string} status 状态文本
   */
  updateButtonState(status) {
    if (!this.button) return;

    const mode = this.routeModes[this.currentModeIndex] || { type: this.routeMode };
    const modeLabel = mode.label || this.getModeLabel(mode.type);

    this.button.title = `${status}（${modeLabel}）`;
  }

  /**
   * 获取模式标签
   * @param {string} mode 模式类型
   * @returns {string} 模式标签
   */
  getModeLabel(mode) {
    switch (mode) {
      case 'walking':
        return '步行';
      case 'bicycling':
        return '骑行';
      case 'driving':
      default:
        return '驾车';
    }
  }

  /**
   * 暂停地图事件，避免与路线规划操作冲突
   */
  suspendMapEvents() {
    if (!this.map || this.eventsSuspended) return;

    this.suspendedMapEvents = new Map();
    const eventTypes = Array.isArray(this.eventsToSuspend)
      ? this.eventsToSuspend
      : [];

    eventTypes.forEach((type) => {
      const listeners = this.map.getListeners?.(type);
      if (!listeners || listeners.length === 0) return;

      const stored = listeners.slice();
      stored.forEach((listener) => this.map.un(type, listener));
      if (stored.length > 0) {
        this.suspendedMapEvents.set(type, stored);
      }
    });

    const viewport = this.map.getViewport?.();
    if (viewport) {
      this.cursorBeforePlanning = viewport.style.cursor;
      viewport.style.cursor = this.cursorWhenActive;
    }

    this.map.__routePlanningActive = true;
    this.eventsSuspended = true;
  }

  /**
   * 恢复先前暂停的地图事件
   */
  restoreMapEvents() {
    if (!this.map || !this.eventsSuspended) return;

    if (this.suspendedMapEvents && this.suspendedMapEvents.size > 0) {
      this.suspendedMapEvents.forEach((listeners, type) => {
        listeners.forEach((listener) => this.map.on(type, listener));
      });
      this.suspendedMapEvents.clear();
    }

    const viewport = this.map.getViewport?.();
    if (viewport) {
      viewport.style.cursor = this.cursorBeforePlanning || '';
      this.cursorBeforePlanning = null;
    }

    delete this.map.__routePlanningActive;
    this.eventsSuspended = false;
  }
}

// 导出默认对象，包含所有控件类
export default {
  MeasureControl,
  LocationControl,
  RoutePlanningControl
};


