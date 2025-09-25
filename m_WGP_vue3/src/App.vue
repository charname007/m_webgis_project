<template>
  <div class="container">
    <!-- <suoluetu></suoluetu> -->
    <MapView>
      <SpatialTableFetcher
        :tableNamesUrl="'http://localhost:8081/postgis/WGP_db/tables/SpatialTables'"
        :geojsonUrl="'http://localhost:8081/postgis/WGP_db/tables/SpatialTables/{tableName}/geojson'"
        :timeout="15000"
      >
      </SpatialTableFetcher>
    </MapView>
    <!-- <geojsonfetcher url="https://geojson.xyz/point/30.531,114.353"></geojsonfetcher> -->
  </div>
</template>
<script setup>
import Chart from "./components/Chart.vue";
import MAP from "./components/MAP.vue";
import MapView from "./components/OlMap.vue";
import suoluetu from "./components/suoluetu.vue";
import Title from "./components/Title.vue";
import SpatialTableFetcher from "./components/SpatialTableFetcher.vue";
</script>
<style scoped>
.container {
  display: flex;
  flex-direction: row;
  width: 100%;
  height: 100%;
  /* overflow: hidden; */
}
</style>
