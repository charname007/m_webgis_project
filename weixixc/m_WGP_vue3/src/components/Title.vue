<template>
    <div id="title" class="title">
        <slot>默认内容文本</slot>
    </div>
</template>

<script setup>

</script>

<style scoped>
.title {
    background-color: rgba(4, 67, 97, 0.911);
    width: 100%;
    height: 10vh; 
    font-size: 40px;
    font-style: oblique;
    color: #ffffff;

    display: flex;
    justify-content: center; /* 水平居中 */
    align-items: center;     /* 垂直居中 */

    /* 防止文字换行 */
    white-space: nowrap;
}</style>