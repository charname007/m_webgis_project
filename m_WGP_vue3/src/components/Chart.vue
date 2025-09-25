<template>
    <div id="chart" class="chart">
        <Title>市民出行方式饼图</Title>
        <Chart1></Chart1>
        <Title>武汉市气温统计图</Title>
        <Chart2></Chart2>
    </div>
</template>
<script setup>
import Title from './Title.vue';
import Chart1 from './Chart1.vue';
import Chart2 from './Chart2.vue';
</script>
<style scoped>
.chart{
    width: 25%;
    height: 100%;
    display: flex;
    flex-direction: column;
}
</style>