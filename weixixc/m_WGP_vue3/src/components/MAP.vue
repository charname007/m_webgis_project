<template>
    <div id="map" class="map"></div>
</template>
<script setup>
import { onMounted, onUnmounted } from 'vue'; // 引入 onMounted
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';  
import XYZ from 'ol/source/XYZ';
import OSM from 'ol/source/OSM';    
import mapboxgl from 'mapbox-gl';
mapboxgl.accessToken = 'pk.MapBox密钥.';
onMounted(() => {
    const map = new mapboxgl.Map({
        container: 'map', 
        style: 'mapbox://styles/mapbox/standard',
        center: [114.353, 30.531],
        zoom: 16,
    });
    map.on('load', function () {
        map.getCanvasContainer().style.position = 'relative';
        const attributionControl = document.querySelector('.mapboxgl-ctrl-attrib');
        if (attributionControl) {
            attributionControl.style.display = 'none';
        }
    });
    window.currentMap = map; 
});
onUnmounted(() => {
    if (window.currentMap) {
        window.currentMap.remove();
        window.currentMap = null;
    }
});
</script>
<style>
.map {
    background-color: red;
    width: 75%;
    height: 100%;
}
</style>