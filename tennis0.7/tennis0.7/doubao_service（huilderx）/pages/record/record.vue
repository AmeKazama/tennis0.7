<template>
  <view class="container">
    <!-- 顶部标题（适配状态栏，彻底解决空白） -->
    <view class="page-header">
      <text class="title">训练记录</text>
    </view>

    <!-- 训练模式 -->
    <view class="card">
      <text class="card-title">训练模式</text>
      <view class="type-grid">
        <view 
          class="type-item" 
          :class="{ active: currentType === idx }" 
          @tap="selectType(idx)"
          v-for="(item, idx) in modeList" 
          :key="idx"
        >
          <text class="type-icon">{{ item.icon }}</text>
          <text class="type-text">{{ item.label }}</text>
        </view>
      </view>
    </view>

    <!-- 球员管理 -->
    <view class="card">
      <text class="card-title">球员管理</text>
      <view class="player-item" v-for="(player, idx) in players" :key="idx">
        <view class="player-avatar">{{ player.avatar }}</view>
        <text class="player-name">{{ player.name }}</text>
        <text class="player-close" @tap="removePlayer(idx)">✕</text>
      </view>
      <view class="add-player" @tap="addPlayer">+ 添加球员</view>
    </view>

    <!-- 功能入口 -->
    <view class="card">
      <view class="list-item" @tap="goServe">
        <text>发球数据详情</text>
        <text class="arrow">></text>
      </view>
      <view class="list-item">
        <text>击球追踪设置</text>
        <text class="arrow">></text>
      </view>
    </view>

    <!-- 开始训练按钮 -->
    <view class="start-btn" @tap="startTraining">开始训练</view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      currentType: 0,
      modeList: [
        { label: "练习模式", icon: "🏃" },
        { label: "比赛模式", icon: "🤝" },
        { label: "发球专项", icon: "🎾" },
        { label: "发球机模拟", icon: "🤖" }
      ],
      players: [
        { avatar: "JL", name: "Jean Lee" }
      ]
    }
  },
  methods: {
    selectType(idx) {
      this.currentType = idx
    },
    removePlayer(idx) {
      uni.showModal({
        title: "删除球员",
        content: "确定要删除该球员吗？",
        success: (res) => {
          if (res.confirm) {
            this.players.splice(idx, 1)
          }
        }
      })
    },
    addPlayer() {
      uni.showToast({
        title: "添加球员功能",
        icon: "none"
      })
    },
    startTraining() {
      uni.switchTab({
        url: "/pages/index/index"
      })
    },
    goServe() {
      uni.navigateTo({
        url: "/pages/serve/serve"
      })
    }
  }
}
</script>

<style scoped>
/* 核心：彻底解决顶部空白，适配所有机型 */
.container {
  background: #000;
  min-height: 100vh;
  /* 关键：给状态栏留空间，内容紧贴顶部 */
  padding: 0 30rpx 30rpx;
  padding-top: calc(var(--status-bar-height) + 20rpx);
  box-sizing: border-box;
  color: #fff;
}

.page-header {
  margin-bottom: 30rpx;
}
.title {
  font-size: 36rpx;
  font-weight: bold;
  color: #fff;
}

/* 卡片样式 */
.card {
  background: #111;
  border-radius: 24rpx;
  padding: 30rpx;
  margin-bottom: 24rpx;
}
.card-title {
  font-size: 28rpx;
  color: #38bdf8;
  margin-bottom: 24rpx;
  display: block;
}

/* 训练模式网格 */
.type-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20rpx;
}
.type-item {
  background: #1a1a1a;
  border-radius: 16rpx;
  padding: 25rpx;
  display: flex;
  align-items: center;
  gap: 15rpx;
  transition: all 0.2s ease;
}
.type-item.active {
  background: linear-gradient(135deg, #22c55e, #a3e635);
  color: #000;
}
.type-icon {
  font-size: 30rpx;
  flex-shrink: 0;
}
.type-text {
  font-size: 26rpx;
  font-weight: 500;
}

/* 球员管理 */
.player-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  background: #1a1a1a;
  padding: 25rpx;
  border-radius: 16rpx;
  margin-bottom: 15rpx;
}
.player-avatar {
  width: 60rpx;
  height: 60rpx;
  background: #38bdf8;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  color: #fff;
  font-weight: bold;
  flex-shrink: 0;
}
.player-name {
  flex: 1;
  font-size: 26rpx;
}
.player-close {
  color: #ef4444;
  font-size: 24rpx;
  flex-shrink: 0;
}
.add-player {
  text-align: center;
  padding: 25rpx;
  border: 1rpx dashed #333;
  border-radius: 16rpx;
  color: #888;
  font-size: 24rpx;
}

/* 列表项 */
.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28rpx 0;
  font-size: 26rpx;
  border-bottom: 1rpx solid #222;
}
.list-item:last-child {
  border-bottom: none;
}
.arrow {
  color: #888;
  font-size: 24rpx;
}

/* 开始按钮 */
.start-btn {
  margin-top: 30rpx;
  background: linear-gradient(135deg, #22c55e, #a3e635);
  text-align: center;
  padding: 30rpx;
  border-radius: 100rpx;
  font-size: 30rpx;
  font-weight: bold;
  color: #000;
}
</style>