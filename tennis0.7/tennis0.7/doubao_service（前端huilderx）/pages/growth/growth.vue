<template>
  <view class="container">
    <view class="navbar">
      <text class="title">成长轨迹</text>
    </view>

    <view class="card">
      <text class="card-title">本周训练频率</text>
      <view class="charts-box">
        <qiun-data-charts type="column" :chartData="chartData" :opts="opts" canvasId="col" />
      </view>
    </view>

    <view class="cards">
      <view class="item green" @tap="goReport"><text>击球次数</text><text>70</text></view>
      <view class="item yellow" @tap="goReport"><text>有效击球</text><text>37</text></view>
      <view class="item orange" @tap="goReport"><text>深度球</text><text>21</text></view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      chartData: {
        categories:['一','二','三','四','五','六','日'],
        series:[{name:'时长',data:[30,55,25,60,40,80,45]}]
      },
      opts: {color:['#22c55e'],xAxis:{fontColor:'#888'},yAxis:{fontColor:'#888'},legend:{show:false}}
    }
  },
  methods: {
    goReport() { uni.navigateTo({url:'/pages/report/report'}) }
  }
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
  padding-top: var(--status-bar-height);
  margin-bottom:30rpx;
}
.title {font-size:36rpx; font-weight:bold;}
.card {
  background:#111;
  border-radius:24rpx;
  padding:30rpx;
  margin-bottom:24rpx;
}
.card-title {font-size:28rpx; margin-bottom:20rpx;}
.charts-box {width:100%; height:400rpx;}
.cards {display:flex; flex-direction:column; gap:20rpx;}
.item {
  border-radius:20rpx;
  padding:30rpx;
  display:flex;
  justify-content:space-between;
  font-size:30rpx;
  font-weight:bold;
}
.green {background:linear-gradient(135deg,#22c55e,#a3e635); color:#000;}
.yellow {background:linear-gradient(135deg,#fbbf24,#f97316); color:#000;}
.orange {background:linear-gradient(135deg,#fb923c,#ef4444); color:#000;}
</style>