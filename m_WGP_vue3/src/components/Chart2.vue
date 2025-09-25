<template>
    <div id="chart2" class="chart2"></div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import * as echarts from 'echarts';
onMounted(() => {
    var chartDom = document.getElementById('chart2');
    var myChart = echarts.init(chartDom);
    var option;
    option = {
        backgroundColor: "#0A2E5D",
        title: {
            text: "九月第一周气温",
            textStyle: {
                color: "#ccc",
            },
        },
        tooltip: {
            trigger: "axis",
        },
        legend: {
            data: ["最高温度", "最低温度"],
            textStyle: {
                color: "#fff",
            },
        },
        grid: {
            top: "middle",
            left: "3%",
            top: "18%",
            right: "8%",
            bottom: "0%",
            height: "80%",
            containLabel: true,
        },
        toolbox: {
            show: true,
            feature: {
                mark: { show: true },
                dataView: { show: true, readOnly: false },
                magicType: { show: true, type: ["line", "bar"] },
                restore: { show: true },
                saveAsImage: { show: true },
            },
        },
        calculable: true,
        xAxis: [
            {
                type: "category",
                boundaryGap: false,
                data: [
                    "2025-9-1",
                    "2025-9-2",
                    "2025-9-3",
                    "2025-9-4",
                    "2025-9-5",
                    "2025-9-6",
                    "2025-9-7",
                ],
                axisTick: {
                    show: true, //隐藏X轴刻度
                },
                axisLabel: {
                    show: true,
                    textStyle: {
                        color: "#ebf8ac", //X轴文字颜色
                    },
                },
            },
        ],
        yAxis: [
            {
                type: "value",
                name: "℃'",
                nameTextStyle: {
                    color: "#ebf8ac",
                },
                axisLabel: {
                    formatter: "{value}℃",
                },
                axisLabel: {
                    show: true,
                    textStyle: {
                        color: "#ebf8ac",
                    },
                },
                splitLine: {
                    lineStyle: {
                        type: "dashed",
                        color: "#DDD",
                    },
                },
            },
        ],
        series: [
            {
                name: "最高温度",
                type: "line",
                min: 10,
                max: 40,
                data: [33, 34, 35, 35, 36, 28, 32],
                markPoint: {
                    data: [{ name: "周最高", value: 36, xAxis: 4, yAxis: 36 }],
                },
                lineStyle: {
                    normal: {
                        width: 5,
                        color: {
                            type: "linear",

                            colorStops: [
                                {
                                    offset: 0,
                                    color: "#AAF487", // 0% 处的颜色
                                },
                                {
                                    offset: 0.4,
                                    color: "#47D8BE", // 100% 处的颜色
                                },
                                {
                                    offset: 1,
                                    color: "#47D8BE", // 100% 处的颜色
                                },
                            ],
                            globalCoord: false, 
                        },
                        shadowColor: "rgba(71,216,190, 0.5)",
                        shadowBlur: 10,
                        shadowOffsetY: 7,
                    },
                },
                itemStyle: {
                    normal: {
                        color: "#AAF487",
                        borderWidth: 10,
                        borderColor: "#AAF487",
                    },
                },
                smooth: true,
                markLine: {
                    data: [{ type: "average", name: "平均值" }],
                },
            },
            {
                name: "最低温度",
                type: "line",
                min: 10,
                max: 40,
                data: [24, 25, 26, 27, 25, 25, 26],
                markPoint: {
                    data: [{ name: "周最低", value: 24, xAxis: 0, yAxis: 24 }],
                },
                lineStyle: {
                    normal: {
                        width: 5,
                        color: {
                            type: "linear",

                            colorStops: [
                                {
                                    offset: 0,
                                    color: "#F6D06F", // 0% 处的颜色
                                },
                                {
                                    offset: 0.4,
                                    color: "#F9A589", // 100% 处的颜色
                                },
                                {
                                    offset: 1,
                                    color: "#F9A589", // 100% 处的颜色
                                },
                            ],
                            globalCoord: false, 
                        },
                        shadowColor: "rgba(249,165,137, 0.5)",
                        shadowBlur: 10,
                        shadowOffsetY: 7,
                    },
                },
                itemStyle: {
                    normal: {
                        color: "#F6D06F",
                        borderWidth: 10,
                        borderColor: "#F6D06F",
                    },
                },
                smooth: true,
                markLine: {
                    data: [{ type: "average", name: "平均值" }],
                },
            },
        ],
    };
    option && myChart.setOption(option);
        window.addEventListener('resize', () => {
        myChart?.resize();
    });
});


onUnmounted(() => {
    if (myChart) {
        myChart.dispose();
        myChart = null;
    }
});
</script>

<style scoped>
.chart2 {
    width: 100%;
    height: 40%;
}
</style>