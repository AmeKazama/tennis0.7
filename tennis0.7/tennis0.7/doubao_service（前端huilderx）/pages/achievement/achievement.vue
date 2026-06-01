<template>
  <view class="container">
    <view class="navbar">
      <view class="back" @tap="goBack">←</view>
      <view class="title-group">
        <text class="title">成就墙</text>
        <text class="subtitle">完成训练即可解锁</text>
      </view>
    </view>

    <view class="grid">
      <view class="item" v-for="(item,i) in list" :key="i">
        <view class="icon">{{item.icon}}</view>
        <text class="name">{{item.name}}</text>
        <text class="desc">{{item.desc}}</text>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      list: [
        {icon:'🏆',name:'首次发球',desc:'完成第一次发球训练'},
        {icon:'🔥',name:'连续训练',desc:'一周训练≥5次'},
        {icon:'🎯',name:'精准发球',desc:'命中率>80%'},
        {icon:'💪',name:'力量达人',desc:'发球速度≥140km/h'},
        {icon:'📈',name:'进步之星',desc:'评分连续上涨'},
        {icon:'🛡️',name:'稳定发挥',desc:'连续50球无失误'},
        {icon:'🏸',name:'正手大师',desc:'正手评分≥90'},
        {icon:'🥎',name:'反手稳健',desc:'稳定率≥85%'},
      ]
    }
  },
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
.back {
  font-size:34rpx;
  margin-right:20rpx;
}
.title-group {flex:1}
.title {font-size:36rpx; font-weight:bold;}
.subtitle {font-size:24rpx; color:#888;}
.grid {
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:24rpx;
}
.item {
  background:#111;
  border-radius:24rpx;
  padding:30rpx;
  text-align:center;
}
.icon {font-size:40rpx; margin-bottom:12rpx;}
.name {font-size:28rpx; font-weight:500;}
.desc {font-size:22rpx; color:#888; margin-top:6rpx;}
</style>