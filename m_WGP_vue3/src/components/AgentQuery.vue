<template>
    
</template>

<script>
import {ref, inject,onMounted,onUnmounted } from "vue";

export default{
    name: "AgentQuery",
    setup() {
            // 注入 mapUtils 响应式引用
    const mapUtilsRef = inject('mapUtils', null);
    const isMapUtilsReady = ref(false);
    const mapUtils = ref(null);

    // 调试信息
    console.log("mapUtilsRef 注入状态:", mapUtilsRef ? "已注入" : "未注入");
    if (mapUtilsRef) {
      console.log("mapUtilsRef 内容:", mapUtilsRef);
      console.log("mapUtilsRef.value:", mapUtilsRef.value);
    }

    // 检查 mapUtils 是否可用
    const checkMapUtilsReady = () => {
      console.log("检查 mapUtils 可用性...");

      if (mapUtilsRef && mapUtilsRef.value) {
        console.log("mapUtilsRef.value 存在:", mapUtilsRef.value);

        // 检查是否有 map 属性
        if (mapUtilsRef.value.map) {
          mapUtils.value = mapUtilsRef.value;
          isMapUtilsReady.value = true;
          console.log("✅ mapUtils 实例准备就绪", mapUtils.value);
        } else {
          console.warn("⚠️ mapUtilsRef.value 存在，但没有 map 属性");
          isMapUtilsReady.value = false;
          mapUtils.value = null;
        }
      } else {
        console.warn("❌ mapUtils 实例未准备好", mapUtilsRef);
        isMapUtilsReady.value = false;
        mapUtils.value = null;
      }

      console.log("isMapUtilsReady 状态:", isMapUtilsReady.value);
    };

    // 监听 mapUtilsRef 的变化
    watch(
      () => mapUtilsRef?.value,
      (newValue) => {
        console.log("mapUtilsRef.value 发生变化:", newValue);
        if (newValue && newValue.map) {
          mapUtils.value = newValue;
          isMapUtilsReady.value = true;
          console.log("✅ mapUtils 实例已更新", mapUtils.value);
        } else {
          isMapUtilsReady.value = false;
          mapUtils.value = null;
          console.warn("❌ mapUtils 实例更新失败");
        }
      },
      { immediate: true }
    );

    onMounted(() => {
      console.log("组件已挂载，开始检查 mapUtils...");

      // 组件挂载后立即检查
      checkMapUtilsReady();

      // 设置定时器定期检查，直到 mapUtils 可用
      const checkInterval = setInterval(() => {
        console.log("定时检查 mapUtils 状态...");
        if (mapUtilsRef && mapUtilsRef.value && mapUtilsRef.value.map) {
          mapUtils.value = mapUtilsRef.value;
          isMapUtilsReady.value = true;
          console.log("✅ mapUtils 实例准备就绪");
          clearInterval(checkInterval);
        } else {
          console.log("⏳ 等待 mapUtils 实例初始化...", {
            hasRef: !!mapUtilsRef,
            hasValue: mapUtilsRef ? !!mapUtilsRef.value : false,
            hasMap: mapUtilsRef && mapUtilsRef.value ? !!mapUtilsRef.value.map : false
          });
        }
      }, 1000);

      // 30秒后停止检查
      setTimeout(() => {
        clearInterval(checkInterval);
        if (!isMapUtilsReady.value) {
          console.error("❌ mapUtils 实例初始化超时");
          // 添加一个备选方案：允许用户手动启用按钮
          console.warn("⚠️ 地图工具初始化失败，按钮将保持禁用状态");
        }
      }, 30000);
    });


    }

}
</script>

<style scoped>  

</style>