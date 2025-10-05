// 要素属性显示功能验证脚本
console.log('=== 要素属性显示功能验证 ===');

// 检查关键组件是否正常加载
function verifyComponents() {
    console.log('1. 检查 Vue 组件加载状态...');
    
    // 检查 OlMap 组件
    if (typeof OlMap !== 'undefined') {
        console.log('✅ OlMap 组件已加载');
    } else {
        console.log('❌ OlMap 组件未找到');
        return false;
    }
    
    // 检查 MapUtils 类
    if (typeof MapUtils !== 'undefined') {
        console.log('✅ MapUtils 类已加载');
    } else {
        console.log('❌ MapUtils 类未找到');
        return false;
    }
    
    return true;
}

// 检查地图初始化状态
function verifyMapInitialization() {
    console.log('2. 检查地图初始化状态...');
    
    // 等待地图初始化完成
    setTimeout(() => {
        const mapElement = document.querySelector('.map');
        if (mapElement) {
            console.log('✅ 地图容器元素存在');
            
            // 检查是否有 OpenLayers 地图实例
            const map = mapElement._ol_map;
            if (map) {
                console.log('✅ OpenLayers 地图实例已创建');
                
                // 检查图层
                const layers = map.getLayers().getArray();
                console.log(`✅ 地图图层数量: ${layers.length}`);
                
                // 检查景区图层
                const sightLayer = layers.find(layer => 
                    layer.get('title') === '景区' || 
                    layer.get('title')?.includes('景区')
                );
                
                if (sightLayer) {
                    console.log('✅ 景区图层已找到');
                    
                    // 检查要素数量
                    const source = sightLayer.getSource();
                    if (source) {
                        const features = source.getFeatures();
                        console.log(`✅ 景区要素数量: ${features.length}`);
                        
                        if (features.length > 0) {
                            console.log('✅ 景区数据加载成功');
                            
                            // 检查第一个要素的属性
                            const firstFeature = features[0];
                            const properties = firstFeature.getProperties();
                            console.log('✅ 要素属性示例:', properties);
                            
                            // 检查是否有景区相关属性
                            const sightKeys = Object.keys(properties).filter(key => 
                                key.toLowerCase().includes('name') || 
                                key.toLowerCase().includes('level') ||
                                key.toLowerCase().includes('景区') ||
                                key.toLowerCase().includes('景点')
                            );
                            
                            if (sightKeys.length > 0) {
                                console.log('✅ 景区相关属性存在:', sightKeys);
                            } else {
                                console.log('⚠️ 未找到景区相关属性');
                            }
                        } else {
                            console.log('⚠️ 景区图层中没有要素');
                        }
                    }
                } else {
                    console.log('❌ 未找到景区图层');
                }
            } else {
                console.log('❌ 地图实例未创建');
            }
        } else {
            console.log('❌ 地图容器元素未找到');
        }
    }, 3000); // 等待3秒让地图初始化
}

// 检查要素点击事件
function verifyFeatureClick() {
    console.log('3. 检查要素点击事件...');
    
    // 模拟要素点击
    setTimeout(() => {
        const mapElement = document.querySelector('.map');
        if (mapElement && mapElement._ol_map) {
            const map = mapElement._ol_map;
            
            // 检查是否有要素点击事件监听器
            const listeners = map.getListeners('singleclick');
            if (listeners && listeners.length > 0) {
                console.log('✅ 要素点击事件监听器已注册');
                
                // 检查弹窗元素
                const popup = document.querySelector('.feature-info-popup');
                if (popup) {
                    console.log('✅ 属性弹窗元素已创建');
                } else {
                    console.log('❌ 属性弹窗元素未找到');
                }
            } else {
                console.log('❌ 要素点击事件监听器未注册');
            }
        }
    }, 5000); // 等待5秒
}

// 运行验证
console.log('开始验证要素属性显示功能...');

if (verifyComponents()) {
    verifyMapInitialization();
    verifyFeatureClick();
}

console.log('验证脚本执行完成，请查看浏览器控制台输出');
