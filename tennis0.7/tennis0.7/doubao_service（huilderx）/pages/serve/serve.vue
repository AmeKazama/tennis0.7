<template>
  <view class="container">
    <view class="navbar">
      <view class="back" @tap="goBack">←</view>
      <view class="title-group">
        <text class="title">发球训练</text>
      </view>
    </view>

    <view class="stat-row">
      <view class="stat"><text class="num">57</text><text class="label">总发球</text></view>
      <view class="stat"><text class="num">32</text><text class="label">ACE球</text></view>
      <view class="stat"><text class="num">64%</text><text class="label">一发进区</text></view>
    </view>

    <view class="card">
      <text class="card-title">发球速度趋势</text>
      <view class="charts-box">
        <qiun-data-charts type="line" :chartData="speedChart" :opts="opts" canvasId="speed" />
      </view>
    </view>

    <view class="card">
      <text class="card-title">最近5次发球</text>
      <view class="items">
        <view class="item" v-for="(i,idx) in last5" :key="idx">
          <text>#{{i.no}}</text>
          <text :class="i.in?'in':'out'">{{i.in?'有效':'出界'}}</text>
          <text>{{i.speed}} km/h</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      last5: [
        {no:34,in:true,speed:142},{no:33,in:true,speed:138},
        {no:32,in:false,speed:129},{no:31,in:true,speed:146},
        {no:30,in:true,speed:137}
      ],
      speedChart: {
        categories:['1','5','10','15','20','25','30'],
        series:[{name:'速度',data:[122,131,127,139,142,138,141]}]
      },
      opts: {color:['#22c55e'],xAxis:{fontColor:'#888'},yAxis:{fontColor:'#888'},legend:{show:false}}
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
.back {font-size:34rpx; margin-right:20rpx;}
.title-group {flex:1}
.title {font-size:36rpx; font-weight:bold;}
.stat-row {
  display:flex;
  justify-content:space-between;
  margin-bottom:30rpx;
}
.stat {text-align:center;}
.num {font-size:40rpx; font-weight:bold;}
.label {font-size:22rpx; color:#888;}
.card {
  background:#111;
  border-radius:24rpx;
  padding:30rpx;
  margin-bottom:24rpx;
}
.card-title {font-size:28rpx; margin-bottom:20rpx;}
.charts-box {width:100%; height:360rpx;}
.items {display:flex; flex-direction:column; gap:16rpx;}
.item {
  background:#1a1a1a;
  border-radius:12rpx;
  padding:24rpx;
  display:flex;
  justify-content:space-between;
  font-size:26rpx;
}
.in {color:#22c55e}
.out {color:#ef4444}
</style>