<template>
  <view class="report-page">
    <view class="header">
      <view class="back" @tap="goBack">←</view>
      <view class="title-group">
        <text class="title">{{ reportType }}</text>
        <text class="subtitle">训练报告</text>
      </view>
    </view>

    <view class="score-card">
      <text class="score">89</text>
      <text class="score-label">综合评分</text>
      <view class="score-line">
        <view class="score-fill"></view>
      </view>
    </view>

    <view class="section">
      <text class="section-title">关键指标</text>
      <view class="metric-grid">
        <view class="metric" v-for="item in metrics" :key="item.label">
          <text class="metric-value">{{ item.value }}</text>
          <text class="metric-label">{{ item.label }}</text>
        </view>
      </view>
    </view>

    <view class="section">
      <text class="section-title">AI 建议</text>
      <view class="advice-card" v-for="item in advices" :key="item">
        <text>{{ item }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const reportType = ref('训练报告')

const metrics = [
  { label: '稳定性', value: '92%' },
  { label: '力量', value: '86' },
  { label: '节奏', value: '88' },
  { label: '完成度', value: '95%' }
]

const advices = [
  '保持击球前的重心稳定，减少上半身提前打开。',
  '下一组训练建议加入 10 分钟移动步伐热身。',
  '连续击球质量良好，可以提高多拍回合强度。'
]

const goBack = () => {
  uni.navigateBack()
}

onLoad((options) => {
  reportType.value = decodeURIComponent(options.type || '训练报告')
})
</script>

<style scoped>
.report-page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: var(--status-bar-height) 28rpx 48rpx;
  background: #0b0f0d;
  color: #fff;
}

.header {
  height: 88rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.back {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.06);
  color: var(--primary-green);
  font-size: 34rpx;
}

.title-group {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.title {
  font-size: 34rpx;
  font-weight: 800;
}

.subtitle {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.48);
}

.score-card {
  margin: 28rpx 0;
  padding: 34rpx;
  border-radius: 22rpx;
  background: #1b211f;
  border: 1rpx solid rgba(222, 255, 154, 0.22);
}

.score {
  display: block;
  font-size: 72rpx;
  line-height: 1;
  font-weight: 900;
  color: var(--primary-green);
}

.score-label {
  display: block;
  margin-top: 10rpx;
  color: rgba(255, 255, 255, 0.64);
  font-size: 24rpx;
}

.score-line {
  height: 8rpx;
  margin-top: 28rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
}

.score-fill {
  width: 89%;
  height: 100%;
  background: var(--primary-green);
}

.section {
  margin-top: 32rpx;
}

.section-title {
  display: block;
  margin-bottom: 18rpx;
  font-size: 28rpx;
  font-weight: 800;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.metric,
.advice-card {
  padding: 24rpx;
  border-radius: 18rpx;
  background: #1b211f;
}

.metric-value {
  display: block;
  color: var(--primary-green);
  font-size: 32rpx;
  font-weight: 900;
}

.metric-label {
  display: block;
  margin-top: 8rpx;
  color: rgba(255, 255, 255, 0.54);
  font-size: 22rpx;
}

.advice-card {
  margin-bottom: 14rpx;
  color: rgba(255, 255, 255, 0.78);
  font-size: 25rpx;
  line-height: 1.5;
}
</style>
