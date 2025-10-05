<template>
  <div class="container">
    <!-- <suoluetu></suoluetu> -->
    <MapView>
      <!-- <template  #SpatialTableFetcher>
        <SpatialTableFetcher :tableNamesUrl="tableNamesUrl"
          :geojsonUrl="geojsonUrl"
          :timeout="15000">
        </SpatialTableFetcher>
      </template> -->
      <!-- Place TouristSpotSearch into the named slot so it renders correctly -->
      <template #TouristSpotSearch>
        <tourist-spot-search />
      </template>
      <!-- AI智能查询组件 -->
      <template #AgentQueryBar>
        <agent-query-bar />
      </template>
    </MapView>
    <!-- <geojsonfetcher url="https://geojson.xyz/point/30.531,114.353"></geojsonfetcher> -->
  </div>
</template>
<script setup>
// import Chart from "./components/Chart.vue";
// import MAP from "./components/MAP.vue";
import MapView from "./components/OlMap.vue";
import Title from "./components/Title.vue";
import SpatialTableFetcher from "./components/SpatialTableFetcher.vue";
import API_CONFIG from '@/config/api.js';
import TouristSpotSearch from "./components/TouristSpotSearch.vue";
import AgentQueryBar from "./components/agent_query_bar.vue";  // 引入 AI 智能查询组件
// Use dynamic config to build URLs
const tableNamesUrl = API_CONFIG.buildURL(API_CONFIG.endpoints.spatialTables.list);
const geojsonUrl = API_CONFIG.buildURL(API_CONFIG.endpoints.spatialTables.geojsonByTable);

</script>
<style scoped>
.container {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100vh;
  /* Critical to ensure the container has full height */
  /* overflow: hidden; */
}
</style>
