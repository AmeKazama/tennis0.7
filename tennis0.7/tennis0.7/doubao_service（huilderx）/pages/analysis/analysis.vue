<template>
  <view class="container">
    <view class="navbar">
      <view class="back" @tap="goBack">←</view>
      <text class="title">网球正手技术分析</text>
    </view>

    <!-- 美观分段式分析内容 -->
    <view class="analysis-card">
      <view class="item" v-for="(item, index) in analysisList" :key="index">
        <view class="num">{{ index + 1 }}</view>
        <view class="text">
          <text class="title">{{ item.title }}</text>
          <text class="desc">{{ item.desc }}</text>
        </view>
      </view>
    </view>

    <!-- 倍速切换 -->
    <view class="speed-group">
      <button 
        v-for="(s, idx) in speedList" 
        :key="idx"
        @click="setSpeed(s.value)"
        class="speed-btn"
        :class="currentSpeed === s.value ? 'active' : ''"
      >
        {{ s.label }}
      </button>
    </view>

    <!-- 播放控制 -->
    <view class="btn-group">
      <button @click="startSpeak" class="btn start-btn">▶ 开始朗读</button>
      <button @click="stopSpeak" class="btn stop-btn">⏹ 停止朗读</button>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      // 分段结构化内容，朗读时会自动拼接
      analysisList: [
        {
          title: "击球点偏晚，力量释放不足",
          desc: "你的击球点明显偏晚，导致力量无法完全释放。建议提前引拍，在身体前方完成击球，更好控制球的方向和力度。"
        },
        {
          title: "重心后坐，转体幅度不足",
          desc: "重心过度后坐，转体幅度不够，击球稳定性一般。建议击球时重心前移，利用转髋带动转肩发力，提升爆发力。"
        },
        {
          title: "随拍动作不完整，控球质量一般",
          desc: "随拍动作不完整，影响延续性与控球质量。建议随拍自然放松，完整收拍至肩部，避免动作僵硬。"
        },
        {
          title: "整体评价与改进方向",
          desc: "整体动作框架基本合理，提升击球时机与重心转移后，稳定性和力量会有明显改善。"
        }
      ],
      ttsInstance: null,
      speedList: [
        { label: "0.5x", value: 0.5 },
        { label: "1.0x", value: 1.0 },
        { label: "1.5x", value: 1.5 },
        { label: "2.0x", value: 2.0 }
      ],
      currentSpeed: 1.0
    }
  },
  computed: {
    // 拼接成一段用于朗读
    content() {
      return this.analysisList.map((item, index) => {
        return `${index + 1}、${item.title}。${item.desc}`
      }).join('')
    }
  },
  methods: {
    goBack() {
      uni.navigateBack()
    },
    setSpeed(val) {
      this.currentSpeed = val
      uni.showToast({ title: `已切换至${val}倍速`, icon: "none" })
    },
    startSpeak() {
      // #ifdef APP-PLUS
      try {
        var main = plus.android.runtimeMainActivity()
        var TextToSpeech = plus.android.importClass("android.speech.tts.TextToSpeech")
        var Locale = plus.android.importClass("java.util.Locale")

        this.ttsInstance = new TextToSpeech(main, function() {})

        setTimeout(() => {
          this.ttsInstance.setLanguage(Locale.CHINA)
          this.ttsInstance.setSpeechRate(this.currentSpeed)
          this.ttsInstance.speak(this.content, 0, null, null)
          uni.showToast({ title: `播放中 ${this.currentSpeed}x`, icon: "none" })
        }, 300)
      } catch (e) {
        uni.showToast({ title: "播放中" })
      }
      // #endif
    },
    stopSpeak() {
      // #ifdef APP-PLUS
      if (this.ttsInstance) {
        this.ttsInstance.stop()
        this.ttsInstance.shutdown()
        this.ttsInstance = null
        uni.showToast({ title: "已停止", icon: "none" })
      }
      // #endif
    }
  },
  onUnload() {
    this.stopSpeak()
  }
}
</script>

<style>
.container {
  padding: 30rpx;
  background: #121212;
  min-height: 100vh;
  box-sizing: border-box;
}
.navbar {
  display: flex;
  align-items: center;
  margin-bottom: 30rpx;
}
.back {
  color: #a855f7;
  font-size: 40rpx;
  margin-right: 20rpx;
}
.title {
  color: #fff;
  font-size: 34rpx;
  font-weight: bold;
}

/* 美观卡片布局 */
.analysis-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}
.item {
  display: flex;
  margin-bottom: 30rpx;
}
.item:last-child {
  margin-bottom: 0;
}
.num {
  width: 50rpx;
  height: 50rpx;
  background: #a855f7;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: bold;
  margin-right: 20rpx;
  flex-shrink: 0;
  margin-top: 4rpx;
}
.text {
  flex: 1;
}
.text .title {
  display: block;
  color: #fff;
  font-size: 28rpx;
  font-weight: 500;
  margin-bottom: 8rpx;
}
.text .desc {
  display: block;
  color: #ccc;
  font-size: 26rpx;
  line-height: 1.6;
}

/* 倍速 */
.speed-group {
  display: flex;
  gap: 15rpx;
  margin-bottom: 40rpx;
  flex-wrap: wrap;
}
.speed-btn {
  padding: 15rpx 25rpx;
  background: #333;
  color: #fff;
  border-radius: 10rpx;
  font-size: 26rpx;
  border: none;
}
.speed-btn.active {
  background: #a855f7;
}

/* 按钮 */
.btn-group {
  display: flex;
  gap: 20rpx;
}
.btn {
  flex: 1;
  padding: 25rpx 0;
  border-radius: 16rpx;
  color: #fff;
  font-size: 28rpx;
  border: none;
}
.start-btn {
  background: #a855f7;
}
.stop-btn {
  background: #555;
}
</style>