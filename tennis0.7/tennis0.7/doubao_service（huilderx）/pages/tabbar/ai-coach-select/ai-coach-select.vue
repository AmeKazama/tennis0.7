<template>
  <Layout>
    <view class="container">
      <!-- 页头 -->
      <view class="header">
        <text class="brand-title">COURTVISION AI</text>
      </view>

      <!-- AI 教练大卡片 -->
      <view class="hero-card" @tap="goAICoachSelection">
        <view class="hero-content">
          <view class="hero-title-row">
            <text class="hero-icon">🤖</text>
            <text class="hero-title">AI 教练助手</text>
          </view>
          <text class="hero-subtitle">智慧球场 AI 实时指导</text>
          <text class="hero-desc">分析您的每一个击球动作，提供职业级优化方案。</text>
          <view class="hero-btn">
            <text class="hero-btn-text">立即体验</text>
            <text class="hero-btn-arrow">→</text>
          </view>
        </view>
        <view class="robot-icon">
          <view class="robot-svg"></view>
        </view>
      </view>

      <!-- 技术工坊 -->
      <view class="section">
        <view class="section-header">
          <text class="section-title">技术工坊</text>
          <text class="section-more">查看全部</text>
        </view>
        <view class="feature-grid">
          <view class="feature-card" @tap="goHighlightEdit">
            <view class="feature-icon-wrapper">
              <text class="feature-icon">✂️</text>
            </view>
            <text class="feature-title">回合剪辑</text>
            <text class="feature-desc">ROUND CLIPS</text>
          </view>
          
          <view class="feature-card" @tap="goDiary">
            <view class="feature-icon-wrapper">
              <text class="feature-icon">📝</text>
            </view>
            <text class="feature-title">打球日记</text>
            <text class="feature-desc">TENNIS JOURNAL</text>
          </view>
          
          <view class="feature-card" @tap="goCoach">
            <view class="feature-icon-wrapper">
              <text class="feature-icon">🏃</text>
            </view>
            <text class="feature-title">动作提取</text>
            <text class="feature-desc">MOTION CAPTURE</text>
          </view>
          
          <view class="feature-card" @tap="goReport">
            <view class="feature-icon-wrapper">
              <text class="feature-icon">📊</text>
            </view>
            <text class="feature-title">动作对比</text>
            <text class="feature-desc">POSE COMPARE</text>
          </view>
        </view>
      </view>

      <!-- 社交社区 -->
      <view class="section">
        <view class="section-header">
          <text class="section-title">社交社区</text>
          <text class="section-more">查看动态</text>
        </view>
        <view class="feature-grid single-card">
          <view class="feature-card" @tap="goServe">
            <view class="feature-icon-wrapper">
              <text class="feature-icon">🎬</text>
            </view>
            <text class="feature-title">发视频</text>
            <text class="feature-desc">POST VIDEO</text>
          </view>
        </view>
      </view>
    </view>
  </Layout>
</template>

<script setup>
import Layout from '@/components/Layout/Layout.vue'

const goAICoachSelection = () => {
  uni.navigateTo({ url: '/pages/ai-coach/ai-coach-selection/ai-coach-selection' })
}

const goHighlightEdit = () => {
  uni.navigateTo({ url: '/pages/training/highlight-edit/highlight-edit' })
}

const goDiary = () => {
  uni.navigateTo({ url: '/pages/content/diary/diary' })
}

const goServe = () => {
  uni.navigateTo({ url: '/pages/content/post-video/post-video' })
}

const goCoach = () => {
  uni.navigateTo({ url: '/pages/training/action-extraction/action-extraction' })
}

const goReport = () => {
  uni.navigateTo({ url: '/pages/training/action-comparison/action-comparison' })
}

const goSetting = () => {
  uni.navigateTo({ url: '/pages/settings/setting/setting' })
}
</script>

<style scoped>
.container {
  background: #000000;
  min-height: 100vh;
  color: var(--primary-green);
  padding-bottom: 40rpx;
  position: relative;
}

.header {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: calc(var(--status-bar-height) + 20rpx) 32rpx 20rpx;
}

.brand-title {
  font-size: 32rpx;
  font-weight: bold;
  letter-spacing: 2rpx;
  color: var(--primary-green);
}

.hero-card {
  position: relative;
  z-index: 1;
  margin: 0 32rpx 32rpx;
  background: #000000;
  border: 1rpx solid rgba(222, 255, 154, 0.3);
  border-radius: 32rpx;
  padding: 40rpx 32rpx;
  overflow: hidden;
  transition: transform 0.2s;
}

.hero-card:active {
  transform: scale(0.97);
}

.hero-content {
  position: relative;
  z-index: 2;
}

.hero-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 12rpx;
}

.hero-icon {
  font-size: 36rpx;
}

.hero-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #fff;
}

.hero-subtitle {
  display: block;
  font-size: 24rpx;
  color: var(--primary-green);
  margin-bottom: 8rpx;
  font-weight: 500;
}

.hero-desc {
  display: block;
  font-size: 24rpx;
  color: rgba(222, 255, 154, 0.7);
  margin-bottom: 20rpx;
  line-height: 1.5;
}

.hero-btn {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  background: var(--primary-green);
  padding: 18rpx 32rpx;
  border-radius: 24rpx;
  align-self: flex-start;
  box-shadow: 0 0 30rpx rgba(222, 255, 154, 0.4);
}

.hero-btn-text {
  font-size: 24rpx;
  font-weight: bold;
  color: #000;
}

.hero-btn-arrow {
  font-size: 28rpx;
  color: #000;
  font-weight: bold;
}

.robot-icon {
  position: absolute;
  top: 20rpx;
  right: 20rpx;
  width: 140rpx;
  height: 140rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.robot-svg {
  width: 120rpx;
  height: 120rpx;
  background-image: url("data:image/svg+xml,%3Csvg t='1778203713588' class='icon' viewBox='0 0 1024 1024' version='1.1' xmlns='http://www.w3.org/2000/svg' p-id='3649'%3E%3Cpath d='M340.59998 127.910463m-94.858399 0a92.7 92.7 0 1 0 189.716798 0 92.7 92.7 0 1 0-189.716798 0Z' p-id='3650' fill='%23ffffff'%3E%3C/path%3E%3Cpath d='M949.351454 71.732187c-9.618867-6.549016-20.874988-9.618867-32.847407-9.618867-27.62866 0-58.634156 16.679524-80.327771 46.661737-3.888478 5.423404-7.367643 11.051464-10.335165 16.679524-0.818627 1.330269-1.637254 3.069851-2.455881 5.01409-6.139702 13.098031-9.721195 26.605376-10.846807 39.601079-1.22794 5.218747-2.558209 10.539822-3.990806 15.860897-9.41421 39.498751-27.219346 82.681323-43.694214 129.445388l-19.749375 26.912361c-3.78615 2.762866-6.856001 6.549016-9.107225 10.949136-2.046567 1.944239-12.995703 10.02818-57.917857 17.805136-35.405616 6.139702-79.509144 10.130509-126.273209 14.325972-4.093135 0.409313-8.083941 0.716299-12.177076 1.125612-33.870691-7.674628-64.05756-20.056361-92.095533-37.349855 1.739582 0 3.376836 0 5.116419 0 74.597382 0 137.120016-26.912361 165.77196-39.294094 3.479165-1.534926 6.549016-2.762866 8.697911-3.683821 15.656241-6.344359 23.330868-24.149495 16.986509-39.908064-6.344359-15.656241-24.149495-23.330868-39.908064-16.986509-2.865194 1.125612-6.139702 2.558209-10.02818 4.195463-18.623763 8.083941-49.833916 21.488958-88.411712 28.958929-20.363346 3.990806-40.215049 5.62806-59.350455 5.116419-0.818627-18.009793-2.762866-29.879884-2.762866-29.879884s-138.1433-37.759169-174.469871 31.721795c-9.209553 17.395823-23.944839 31.824123-1.944239 156.869391 6.549016 37.247527-3.581493 93.221145-4.195463 118.803238l-54.438693 133.74318c-39.601079 20.363346-81.044069 51.061857-115.426402 85.546517-51.880484 51.982812-63.341261 86.774458-63.852903 106.830818-0.511642 20.158689 8.902568 36.838213 25.991406 45.945438 4.604777 2.455881 9.516538 3.581493 14.4283 3.581493 10.949136 0 21.591286-5.935045 27.219346-16.167882 6.446687-12.177076 3.990806-26.707705-5.218747-36.019586 3.376836-10.02818 16.065554-31.824123 45.024483-60.88538 32.64275-32.745078 72.346158-61.397022 108.979714-78.588188 6.958329-3.274508 12.484061-9.107225 15.349256-16.270211l66.718097-164.032377c0.716299-1.841911 1.330269-3.78615 1.637254-5.730389L472.603577 646.408314c4.40012 47.378035 23.433197 106.72849 52.699111 162.702109 20.772659 39.703408 63.034276 108.672729 113.175177 124.124313 2.967523 0.920955 6.037374 1.330269 9.004897 1.330269 13.20036 0 25.275107-8.493255 29.470571-21.488958 4.911762-16.167882-4.195463-33.359049-20.363346-38.373139-15.963226-4.911762-46.764065-36.4289-76.848606-93.937444-28.24263-54.234036-46.150095-112.765864-46.661737-152.878585-0.102328-10.846807-5.935045-20.772659-15.246927-26.196063l-117.472969-68.45768c-1.739582-12.791046-2.148896-48.708304 25.172779-125.761567 32.335765 18.521435 67.332068 31.824123 105.50055 40.112721 2.046567 0.511642 4.297792 0.716299 6.446687 0.716299 0.920955 0 1.841911-0.102328 2.967523-0.204657 5.62806-0.511642 11.256121-1.023284 16.884181-1.534926 57.099231-5.116419 103.863296-9.721195 140.599181-16.781853l16.577196 11.256121c4.707105 3.172179 13.81433-2.865194 19.954032-12.893375l5.62806-9.107225c26.298391-9.107225 43.387229-21.591286 51.47117-39.805736 5.218747-11.870091 2.455881-25.172779-6.037374-33.870691l0.818627-1.330269c40.215049-36.531228 75.722994-73.164785 110.923953-99.156191 4.502448-3.479165 9.107225-6.958329 13.609673-10.232837 17.60048-9.209553 34.177676-24.354152 46.45708-44.103528C985.473369 145.613271 981.277905 93.323474 949.351454 71.732187zM819.189767 211.615069c4.502448 9.41421 11.153792 17.498151 19.954032 23.433197 9.107225 6.139702 19.544719 9.311882 30.493854 9.721195-17.60048 14.121315-35.303288 30.289198-54.029379 47.68502-0.102328-2.148896-0.920955-3.990806-2.455881-5.01409l-12.995703-8.80024c-0.920955-0.61397-1.944239-0.818627-3.172179-0.818627C805.477766 254.592985 813.152393 232.694714 819.189767 211.615069zM940.039572 179.688618c-8.697911 13.81433-19.954032 25.377436-32.745078 33.461377-11.767763 7.367643-23.84251 11.256121-35.098631 11.256121-8.18627 0-15.451584-2.148896-21.591286-6.242031-11.153792-7.572299-15.349256-19.544719-16.884181-28.344959-3.78615-21.488958 3.274508-47.275707 19.033077-68.969321 8.80024-12.074748 19.647047-22.102928 31.517138-28.8566 10.846807-6.139702 22.0006-9.41421 32.233437-9.41421 8.18627 0 15.349256 2.046567 21.386629 6.139702 10.232837 6.856001 16.474868 19.340062 17.60048 35.098631C956.821425 141.827121 951.295693 161.678825 940.039572 179.688618z' p-id='3651' fill='%23ffffff'%3E%3C/path%3E%3Cpath d='M628.858999 519.82812m-37.247527 0a36.4 36.4 0 1 0 74.495053 0 36.4 36.4 0 1 0-74.495053 0Z' p-id='3652' fill='%23ffffff'%3E%3C/path%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.9;
}

.section {
  position: relative;
  z-index: 1;
  margin-bottom: 32rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32rpx 20rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #fff;
}

.section-more {
  font-size: 24rpx;
  color: rgba(222, 255, 154, 0.6);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
  padding: 0 32rpx;
}

.feature-grid.single-card {
  grid-template-columns: 1fr;
  justify-items: center;
}

.feature-grid.single-card .feature-card {
  max-width: 400rpx;
  width: 100%;
}

.feature-card {
  background: #000000;
  border: 1rpx solid rgba(222, 255, 154, 0.2);
  border-radius: 28rpx;
  padding: 36rpx 28rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  transition: transform 0.2s, border-color 0.2s;
}

.feature-card:active {
  transform: scale(0.97);
  border-color: rgba(222, 255, 154, 0.5);
}

.feature-icon-wrapper {
  width: 80rpx;
  height: 80rpx;
  background: rgba(222, 255, 154, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2rpx solid var(--primary-green);
}

.feature-icon {
  font-size: 36rpx;
}

.feature-title {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--primary-green);
}

.feature-desc {
  font-size: 20rpx;
  color: rgba(222, 255, 154, 0.5);
  letter-spacing: 1rpx;
}
</style>
