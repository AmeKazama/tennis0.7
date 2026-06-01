<template>
  <view class="container">
    <!-- 页头 -->
    <view class="header">
      <view class="back-btn" @tap="goBack">
        <text class="back-icon">←</text>
      </view>
      <text class="page-title">AI 教练</text>
      <view class="placeholder"></view>
    </view>

    <!-- AI 教练大卡片 -->
    <view class="hero-card">
      <view class="hero-content">
        <text class="hero-title">AI 教练</text>
        <text class="hero-subtitle">智能动作分析与指导</text>
      </view>
      <view class="robot-icon">
        <text class="robot-emoji">🤖</text>
      </view>
    </view>

    <!-- 选择指导类型 -->
    <view class="guide-selection">
      <view class="guide-card" @tap="goSingleGuide">
        <view class="guide-icon-wrapper">
          <text class="guide-icon">🎯</text>
        </view>
        <text class="guide-title">单次动作指导</text>
        <text class="guide-desc">针对单个动作进行详细分析</text>
        <view class="guide-btn">
          <text class="guide-btn-text">立即开始</text>
          <text class="guide-btn-arrow">→</text>
        </view>
      </view>
      
      <view class="guide-card" @tap="goComprehensiveGuide">
        <view class="guide-icon-wrapper">
          <text class="guide-icon">📊</text>
        </view>
        <text class="guide-title">综合指导</text>
        <text class="guide-desc">全方位的技术分析与建议</text>
        <view class="guide-btn">
          <text class="guide-btn-text">立即开始</text>
          <text class="guide-btn-arrow">→</text>
        </view>
      </view>
    </view>

    <!-- 底部导航栏 -->
    <view class="tab-bar">
      <view class="tab-item" @tap="switchTab('home')">
        <text class="tab-icon">🏠</text>
        <text class="tab-label">首页</text>
      </view>
      <view class="tab-item" @tap="switchTab('social')">
        <text class="tab-icon">🤝</text>
        <text class="tab-label">社交圈</text>
      </view>
      <view class="tab-center-item" @tap="switchTab('publish')">
        <view class="tab-center-btn">
          <text class="tab-center-icon">▶</text>
        </view>
        <text class="tab-center-label">复盘</text>
      </view>
      <view class="tab-item" @tap="switchTab('data')">
        <text class="tab-icon">📈</text>
        <text class="tab-label">数据</text>
      </view>
      <view class="tab-item" @tap="switchTab('profile')">
        <text class="tab-icon">👤</text>
        <text class="tab-label">我的</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'

const goBack = () => {
  uni.navigateBack()
}

const switchTab = (tab) => {
  if (tab === 'home') {
    uni.reLaunch({ url: '/pages/tabbar/index/index' })
  } else if (tab === 'social') {
    uni.navigateTo({ url: '/pages/tabbar/record/record' })
  } else if (tab === 'publish') {
    uni.navigateTo({ url: '/pages/tabbar/ai-coach-select/ai-coach-select' })
  } else if (tab === 'data') {
    uni.navigateTo({ url: '/pages/tabbar/data/data' })
  } else if (tab === 'profile') {
    uni.navigateTo({ url: '/pages/tabbar/profile/profile' })
  }
}

const goSingleGuide = () => {
  uni.navigateTo({ url: '/pages/ai-coach/action-guide/action-guide' })
}

const goComprehensiveGuide = () => {
  uni.navigateTo({ url: '/pages/ai-coach/comprehensive-guide/comprehensive-guide' })
}
</script>

<style scoped>
.container {
  background: #0a0a0a;
  min-height: 100vh;
  color: #fff;
  padding-bottom: 180rpx;
  position: relative;
}

.container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 400rpx;
  background: linear-gradient(180deg, #1a1a1a 0%, #0a0a0a 100%);
  z-index: 0;
}

.header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(var(--status-bar-height) + 20rpx) 32rpx 30rpx;
}

.back-btn {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 50%;
}

.back-icon {
  font-size: 36rpx;
  color: #fff;
}

.page-title {
  font-size: 32rpx;
  font-weight: bold;
  letter-spacing: 1rpx;
}

.placeholder {
  width: 64rpx;
}

.hero-card {
  position: relative;
  z-index: 1;
  margin: 0 32rpx 40rpx;
  background: linear-gradient(135deg, #6a5acd 0%, #006400 100%);
  border-radius: 28rpx;
  padding: 40rpx 32rpx;
  overflow: hidden;
  transition: transform 0.2s;
}

.hero-card:active {
  transform: scale(0.98);
}

.hero-content {
  position: relative;
  z-index: 2;
}

.hero-title {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  margin-bottom: 12rpx;
  letter-spacing: 2rpx;
}

.hero-subtitle {
  display: block;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 28rpx;
}

.robot-icon {
  position: absolute;
  top: 20rpx;
  right: 20rpx;
  width: 100rpx;
  height: 100rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.robot-emoji {
  font-size: 64rpx;
  filter: drop-shadow(0 0 20rpx rgba(0, 255, 0, 0.6));
}

.guide-selection {
  position: relative;
  z-index: 1;
  padding: 0 32rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.guide-card {
  background: #1a1a1a;
  border-radius: 24rpx;
  padding: 32rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  transition: transform 0.2s;
  position: relative;
  overflow: hidden;
}

.guide-card:active {
  transform: scale(0.98);
}

.guide-icon-wrapper {
  width: 80rpx;
  height: 80rpx;
  background: linear-gradient(135deg, rgba(222, 255, 154, 0.2), rgba(106, 90, 205, 0.2));
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.guide-icon {
  font-size: 40rpx;
}

.guide-title {
  font-size: 32rpx;
  font-weight: 600;
}

.guide-desc {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.6);
}

.guide-btn {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  background: #deff9a;
  padding: 12rpx 24rpx;
  border-radius: 16rpx;
  align-self: flex-start;
  margin-top: 8rpx;
}

.guide-btn-text {
  font-size: 22rpx;
  font-weight: bold;
  color: #000;
}

.guide-btn-arrow {
  font-size: 24rpx;
  color: #000;
  font-weight: bold;
}

/* 底部导航栏 */
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding: 12rpx 24rpx;
  padding-bottom: calc(12rpx + env(safe-area-inset-bottom));
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  z-index: 1000;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  flex: 1;
  padding: 8rpx 0;
}

.tab-icon {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.5);
  transition: all 0.3s;
}

.tab-label {
  font-size: 18rpx;
  color: rgba(255, 255, 255, 0.5);
  transition: all 0.3s;
}

.tab-center-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
  padding: 8rpx 0;
  margin-top: -24rpx;
  position: relative;
}

.tab-center-btn {
  width: 96rpx;
  height: 96rpx;
  background: var(--primary-green);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 30rpx rgba(222, 255, 154, 0.5);
  border: 4rpx solid #000;
}

.tab-center-icon {
  font-size: 40rpx;
  color: #000;
  font-weight: bold;
}

.tab-center-label {
  font-size: 18rpx;
  color: var(--primary-green);
  font-weight: 600;
}
</style>
