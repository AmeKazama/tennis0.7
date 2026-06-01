<template>
  <view class="container">
    <view class="navbar">
      <view class="back" @tap="goBack">←</view>
      <view class="title-group">
        <text class="title">训练报告</text>
        <text class="subtitle">AI 评分趋势</text>
      </view>
    </view>

    <view class="card">
      <view class="charts-box">
        <qiun-data-charts type="line" :chartData="chartData" :opts="opts" canvasId="lineChart" />
      </view>
    </view>

    <view class="card stat-row">
      <view class="stat">
        <text class="num">12</text>
        <text class="label">训练次数</text>
      </view>
      <view class="stat">
        <text class="num">4.7h</text>
        <text class="label">总时长</text>
      </view>
      <view class="stat">
        <text class="num">8.6</text>
        <text class="label">综合评分</text>
      </view>
    </view>

    <view class="card">
      <text class="card-title">AI 建议</text>
      <text class="desc">发球稳定性良好，建议加强击球点控制与转体幅度，提升深度球比例。</text>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      chartData: {
        categories: ['周一','二','三','四','五','六','日'],
        series: [{ name: '技术评分', data: [7.2,7.5,7.9,8.2,8.5,8.3,8.6] }]
      },
      opts: {
        color: ['#38bdf8'],
        xAxis: { fontColor: '#888' },
        yAxis: { min:5, max:10, fontColor:'#888' },
        legend: { show:false }
      }
    }
  },
  methods: { goBack() { uni.navigateBack() } }
}
</script>

<style>
.container {
  background:#000;
  min-height:100vh;
  padding: 0 30rpx 30rpx;
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
  color:#fff;
}
.title-group {
  flex:1;
}
.title {
  font-size:36rpx;
  font-weight:bold;
}
.subtitle {
  font-size:24rpx;
  color:#888;
}
.card {
  background:#111;
  border-radius:24rpx;
  padding:30rpx;
  margin-bottom:24rpx;
}
.charts-box {
  width:100%;
  height:400rpx;
}
.stat-row {
  display:flex;
  justify-content:space-around;
}
.stat {
  text-align:center;
}
.num {
  font-size:36rpx;
  font-weight:bold;
}
.label {
  font-size:22rpx;
  color:#888;
}
.card-title {
  font-size:28rpx;
  margin-bottom:20rpx;
}
.desc {
  color:#aaa;
  line-height:1.6;
  font-size:26rpx;
}
</style>