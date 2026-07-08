<template>
  <view class="compete-page">
    <view class="page-header">
      <text class="title">训练数据</text>
      <text class="sub-title">本周训练表现</text>
    </view>

    <view class="summary-card">
      <view class="summary-item">
        <text class="num">12</text>
        <text class="label">训练次数</text>
      </view>
      <view class="summary-item">
        <text class="num">4.8h</text>
        <text class="label">总时长</text>
      </view>
      <view class="summary-item">
        <text class="num">89</text>
        <text class="label">平均评分</text>
      </view>
    </view>

    <view class="card-list">
      <view class="data-card" @tap="goReport('发球训练')">
        <view class="card-icon">🎾</view>
        <view class="card-info">
          <text class="card-title">发球训练</text>
          <text class="card-desc">共8次 · 平均87分</text>
        </view>
        <view class="card-arrow">></view>
      </view>

      <view class="data-card" @tap="goReport('正手击球')">
        <view class="card-icon">🏸</view>
        <view class="card-info">
          <text class="card-title">正手击球</text>
          <text class="card-desc">共6次 · 平均91分</text>
        </view>
        <view class="card-arrow">></view>
      </view>

      <view class="data-card" @tap="goReport('反手击球')">
        <view class="card-icon">🥎</view>
        <view class="card-info">
          <text class="card-title">反手击球</text>
          <text class="card-desc">共5次 · 平均85分</text>
        </view>
        <view class="card-arrow">></view>
      </view>

      <view class="data-card" @tap="goReport('脚步训练')">
        <view class="card-icon">👟</view>
        <view class="card-info">
          <text class="card-title">脚步训练</text>
          <text class="card-desc">共4次 · 平均83分</text>
        </view>
        <view class="card-arrow">></view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  methods: {
    goReport(type) {
      uni.navigateTo({
        url: `/pages/report/report?type=${type}`
      })
    }
  }
}
</script>

<style scoped>
.compete-page {
  background: #000;
  min-height: 100vh;
  padding: 0 30rpx 30rpx;
  box-sizing: border-box;
  color: #fff;
}
.page-header {
  padding-top: var(--status-bar-height);
  padding-bottom: 30rpx;
}
.title {
  font-size: 36rpx;
  font-weight: bold;
}
.sub-title {
  font-size: 24rpx;
  color: #888;
  margin-top: 10rpx;
  display: block;
}
.summary-card {
  background: #111;
  border-radius: 24rpx;
  padding: 40rpx 30rpx;
  display: flex;
  justify-content: space-around;
  margin-bottom: 30rpx;
}
.summary-item {
  text-align: center;
}
.num {
  font-size: 40rpx;
  font-weight: bold;
  color: #38bdf8;
}
.label {
  font-size: 24rpx;
  color: #999;
  margin-top: 10rpx;
  display: block;
}
.card-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}
.data-card {
  background: #1a1a1a;
  border-radius: 24rpx;
  padding: 30rpx;
  display: flex;
  align-items: center;
}
.card-icon {
  font-size: 40rpx;
  margin-right: 20rpx;
}
.card-info {
  flex: 1;
}
.card-title {
  font-size: 30rpx;
  font-weight: 500;
}
.card-desc {
  font-size: 24rpx;
  color: #888;
  margin-top: 8rpx;
  display: block;
}
.card-arrow {
  font-size: 30rpx;
  color: #666;
}
</style>