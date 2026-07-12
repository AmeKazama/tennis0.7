<template>
  <view class="container">
    <view class="navbar">
      <text class="title">我的</text>
    </view>

    <view class="user-card">
      <view class="avatar">U</view>
      <view class="info">
        <text class="name">网球训练者</text>
        <text class="level">业余3级 · 正在提升</text>
      </view>
    </view>

    <view class="stat-row">
      <view class="stat">
        <text class="num">24</text>
        <text class="label">总训练</text>
      </view>
      <view class="stat">
        <text class="num">9.3h</text>
        <text class="label">总时长</text>
      </view>
      <view class="stat">
        <text class="num">86</text>
        <text class="label">平均分</text>
      </view>
    </view>

    <view class="menu">
      <view class="item" @tap="goGrowth">
        <text>成长数据</text>
        <text>&gt;</text>
      </view>
      <view class="item" @tap="goAchieve">
        <text>成就墙</text>
        <text>&gt;</text>
      </view>
      <view class="item" @tap="goSetting">
        <text>设置</text>
        <text>&gt;</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  methods: {
    goGrowth() {
      uni.switchTab({ url: '/pages/growth/growth' })
    },
    goAchieve() {
      uni.navigateTo({ url: '/pages/achievement/achievement' })
    },
    goSetting() {
      uni.navigateTo({ url: '/pages/setting/setting' })
    }
  }
}
</script>

<style>
.container {
  background: #000;
  min-height: 100vh;
  padding: 0 30rpx 30rpx;
  color: #fff;
}
.navbar {
  padding-top: var(--status-bar-height);
  margin-bottom: 30rpx;
}
.title {
  font-size: 36rpx;
  font-weight: bold;
}
.user-card {
  display: flex;
  align-items: center;
  gap: 24rpx;
  margin-bottom: 30rpx;
}
.avatar {
  width: 100rpx;
  height: 100rpx;
  background: #22c55e;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
}
.name {
  font-size: 36rpx;
  font-weight: bold;
}
.level {
  color: #888;
  font-size: 24rpx;
}
.stat-row {
  background: #111;
  border-radius: 24rpx;
  padding: 40rpx 30rpx;
  display: flex;
  justify-content: space-around;
  margin-bottom: 30rpx;
}
.stat {
  text-align: center;
}
.num {
  font-size: 36rpx;
  font-weight: bold;
}
.label {
  font-size: 22rpx;
  color: #888;
}
.menu {
  background: #111;
  border-radius: 24rpx;
  overflow: hidden;
}
.item {
  display: flex;
  justify-content: space-between;
  padding: 30rpx;
  font-size: 28rpx;
  border-bottom: 1px solid #222;
}
.item:last-child {
  border-bottom: 0;
}
</style>