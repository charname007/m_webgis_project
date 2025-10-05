import Control from 'ol/control/Control';
import { unByKey } from 'ol/Observable';
import Overlay from 'ol/Overlay';
import Feature from 'ol/Feature';
import { Style, Stroke, Fill, Circle } from 'ol/style';
import { Draw, Snap } from 'ol/interaction';
import { getLength, getArea } from 'ol/sphere';
import { LineString, Polygon } from 'ol/geom';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';

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
      activeClassName = 'active'
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
    if (this.isActive) {
      this.deactivate();
    } else {
      this.activate();
    }
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
    // 创建测量图层
    const measureSource = new VectorSource();
    this.measureLayer = new VectorLayer({
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
    this.drawInteraction = new Draw({
      source: measureSource,
      type: this.measureType,
      style: new Style({
        fill: new Fill({ color: 'rgba(252, 86, 49, 0.1)' }),
        stroke: new Stroke({ color: '#fc5531', lineDash: [10, 10], width: 3 }),
        image: new Circle({
          radius: 5,
          stroke: new Stroke({ color: 'rgba(0, 0, 0, 0.7)' }),
          fill: new Fill({ color: '#fc5531' })
        })
      })
    });

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
      sketch = evt.feature;
      const tooltipCoord = evt.coordinate;

      listener = sketch.getGeometry().on('change', (evt) => {
        const geom = evt.target;
        const output = this.formatMeasureResult(geom);
        if (this.tooltipElement) {
          this.tooltipElement.innerHTML = output;
        }
        if (this.tooltip) {
          const coord = geom.getType() === 'Polygon' 
            ? geom.getInteriorPoint().getCoordinates()
            : geom.getLastCoordinate();
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
  formatMeasureResult(geometry) {
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
  }

  /**
   * 设置测量类型
   * @param {string} type 测量类型 ('LineString', 'Polygon', 'angle')
   */
  setMeasureType(type) {
    this.measureType = type;
    if (this.isActive) {
      this.deactivate();
      this.activate();
    }
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
    // 创建定位图层（如果不存在）
    if (!this.locationLayer) {
      const source = new VectorSource();
      this.locationLayer = new VectorLayer({
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
        zIndex: 1000
      });
      this.map.addLayer(this.locationLayer);
    }

    // 创建精度圆圈
    if (position.accuracy && position.accuracy > 0) {
      const accuracyFeature = new Feature({
        geometry: new Circle(position.coordinate, position.accuracy)
      });
      accuracyFeature.setStyle(new Style({
        stroke: new Stroke({
          color: '#4285F4',
          width: 1,
          lineDash: [5, 5]
        }),
        fill: new Fill({
          color: 'rgba(66, 133, 244, 0.1)'
        })
      }));
      this.locationLayer.getSource().addFeature(accuracyFeature);
    }

    // 创建位置标记
    this.locationMarker = new Feature({
      geometry: new Circle(position.coordinate, 8)
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
    this.locationLayer.getSource().addFeature(this.locationMarker);
  }

  /**
   * 隐藏位置标记
   */
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

// 导出默认对象，包含所有控件类
export default {
  MeasureControl,
  LocationControl
};
