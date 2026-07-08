<template>
  <view class="container">
    <view class="navbar">
      <view class="back" @tap="goBack">←</view>
      <view class="title-group">
        <text class="title">设置</text>
      </view>
    </view>

    <view class="card list">
      <view class="item">
        <text>摄像头权限</text>
        <switch value color="#22c55e"/>
      </view>
      <view class="item">
        <text>麦克风权限</text>
        <switch value color="#22c55e"/>
      </view>
      <view class="item">
        <text>消息通知</text>
        <switch value color="#22c55e"/>
      </view>
      <view class="item">
        <text>关于项目</text>
        <text>&gt;</text>
      </view>
      <view class="item">
        <text>版本</text>
        <text>v1.0.0</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  methods: { goBack() { uni.navigateBack() } }
}
</script>

<style>
.container {
  background:#000;
  min-height:100vh;
  padding:0 30rpx 30rpx;
  color:#fff;
}
.navbar {
  display:flex;
  align-items:center;
  padding-top: var(--status-bar-height);
  margin-bottom:30rpx;
}
.back {font-size:34rpx; margin-right:20rpx;}
.title-group {flex:1}
.title {font-size:36rpx; font-weight:bold;}
.card {background:#111; border-radius:24rpx; overflow:hidden;}
.item {
  padding:30rpx;
  display:flex;
  justify-content:space-between;
  align-items:center;
  font-size:28rpx;
  border-bottom:1px solid #222;
}
.item:last-child {border-bottom:0}
</style>