<template>
  <view class="layout">
    <view class="page-content">
      <slot></slot>
    </view>
    <CustomTabBar />
  </view>
</template>

<script setup>
import CustomTabBar from '@/components/CustomTabBar/CustomTabBar.vue'
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #000000;
}

.page-content {
  flex: 1;
  padding-bottom: 150rpx;
  padding-bottom: calc(150rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}
</style>
