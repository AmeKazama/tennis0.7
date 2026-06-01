<template>
  <view class="container">
    <view class="page-header-wrapper">
      <view class="user-avatar">
        <image src="https://i.pravatar.cc/150?u=1" mode="aspectFill" class="avatar-img"></image>
      </view>
      <text class="brand-title">COURTVISION AI</text>
      <view class="notification-icon">
        <text class="bell">🔔</text>
        <view class="notification-dot"></view>
      </view>
    </view>

    <view class="page-content">
      <view class="week-header">
        <text class="page-title">Weekly Performance</text>
        <text class="page-date">Oct 24 - Oct 30</text>
      </view>

      <view class="stats-grid">
        <view class="stat-card">
          <text class="stat-label">训练次数</text>
          <text class="stat-value">12</text>
        </view>
        <view class="stat-card">
          <text class="stat-label">总时长</text>
          <text class="stat-value">4.8h</text>
        </view>
      </view>

      <view class="score-card">
        <view class="score-info">
          <text class="score-label">平均评分</text>
          <text class="score-value">89</text>
        </view>
        <view class="score-ring">
          <view class="score-circle">
            <text class="score-emoji">⭐</text>
          </view>
        </view>
      </view>

      <view class="skill-section">
        <text class="section-title">Skill Breakdown</text>

        <view class="skill-list">
          <view class="skill-card">
            <view class="skill-icon">
              <text class="skill-emoji">🎾</text>
            </view>
            <view class="skill-info">
              <text class="skill-name">发球训练</text>
              <text class="skill-reps">45 reps</text>
            </view>
            <view class="skill-score">
              <text class="score-num">92</text>
              <text class="score-label">Avg Score</text>
            </view>
            <view class="progress-bar">
              <view class="progress-fill" style="width: 92%"></view>
            </view>
          </view>

          <view class="skill-card">
            <view class="skill-icon">
              <text class="skill-emoji">🎾</text>
            </view>
            <view class="skill-info">
              <text class="skill-name">正手击球</text>
              <text class="skill-reps">120 reps</text>
            </view>
            <view class="skill-score">
              <text class="score-num">88</text>
              <text class="score-label">Avg Score</text>
            </view>
            <view class="progress-bar">
              <view class="progress-fill" style="width: 88%"></view>
            </view>
          </view>

          <view class="skill-card">
            <view class="skill-icon">
              <text class="skill-emoji">🎾</text>
            </view>
            <view class="skill-info">
              <text class="skill-name">反手击球</text>
              <text class="skill-reps">85 reps</text>
            </view>
            <view class="skill-score">
              <text class="score-num">85</text>
              <text class="score-label">Avg Score</text>
            </view>
            <view class="progress-bar">
              <view class="progress-fill" style="width: 85%"></view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <AppBottomNav active="data" />
  </view>
</template>

<script setup>
import AppBottomNav from '@/components/AppBottomNav/AppBottomNav.vue'
</script>

<style scoped>
.container {
  background: var(--dark-bg, #000000);
  min-height: 100vh;
  color: #fff;
  position: relative;
  display: flex;
  flex-direction: column;
}

.page-header-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(var(--status-bar-height) + 20rpx) 30rpx 20rpx;
  background: transparent;
}

.user-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
}

.brand-title {
  font-size: 28rpx;
  font-weight: bold;
  color: var(--primary-green, #DEFF9A);
  letter-spacing: 2rpx;
}

.notification-icon {
  position: relative;
}

.bell {
  font-size: 36rpx;
}

.notification-dot {
  position: absolute;
  top: 4rpx;
  right: 4rpx;
  width: 16rpx;
  height: 16rpx;
  background: #FF3B30;
  border-radius: 50%;
}

.page-content {
  flex: 1;
  padding: 0 30rpx;
  overflow-y: auto;
}

.week-header {
  margin-bottom: 32rpx;
}

.page-title {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  margin-bottom: 8rpx;
}

.page-date {
  display: block;
  font-size: 24rpx;
  color: var(--text-gray, rgba(255, 255, 255, 0.5));
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.stat-card {
  background: var(--card-bg, #1A1A1A);
  border-radius: 24rpx;
  padding: 32rpx 24rpx;
}

.stat-label {
  display: block;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 8rpx;
}

.stat-value {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  color: var(--primary-green, #DEFF9A);
}

.score-card {
  background: var(--card-bg, #1A1A1A);
  border-radius: 24rpx;
  padding: 32rpx 24rpx;
  margin-bottom: 40rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-info {
  flex: 1;
}

.score-label {
  display: block;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 8rpx;
}

.score-value {
  display: block;
  font-size: 64rpx;
  font-weight: bold;
  color: var(--primary-green, #DEFF9A);
}

.score-ring {
  width: 120rpx;
  height: 120rpx;
  position: relative;
}

.score-circle {
  width: 100%;
  height: 100%;
  border: 4rpx solid rgba(222, 255, 154, 0.3);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.score-circle::before {
  content: '';
  position: absolute;
  top: -4rpx;
  left: -4rpx;
  right: -4rpx;
  bottom: -4rpx;
  border: 4rpx solid var(--primary-green, #DEFF9A);
  border-radius: 50%;
  border-top-color: transparent;
  border-right-color: transparent;
  transform: rotate(45deg);
}

.score-emoji {
  font-size: 40rpx;
}

.skill-section {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  padding-bottom: calc(150rpx + env(safe-area-inset-bottom));
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: var(--text-light, rgba(255, 255, 255, 0.9));
}

.skill-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.skill-card {
  background: var(--card-bg, #1A1A1A);
  border-radius: 20rpx;
  padding: 24rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
  position: relative;
  overflow: hidden;
}

.skill-icon {
  width: 64rpx;
  height: 64rpx;
  background: rgba(222, 255, 154, 0.15);
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.skill-emoji {
  font-size: 32rpx;
}

.skill-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.skill-name {
  font-size: 28rpx;
  font-weight: 600;
}

.skill-reps {
  font-size: 22rpx;
  color: var(--text-gray, rgba(255, 255, 255, 0.5));
}

.skill-score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4rpx;
}

.score-num {
  font-size: 32rpx;
  font-weight: bold;
  color: var(--primary-green, #DEFF9A);
}

.score-label {
  font-size: 18rpx;
  color: rgba(255, 255, 255, 0.4);
}

.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4rpx;
  background: rgba(255, 255, 255, 0.1);
}

.progress-fill {
  height: 100%;
  background: var(--primary-green, #DEFF9A);
  box-shadow: 0 0 10rpx var(--primary-green, #DEFF9A), 0 0 20rpx rgba(222, 255, 154, 0.5);
  border-radius: 0 0 20rpx 20rpx;
}
</style>
