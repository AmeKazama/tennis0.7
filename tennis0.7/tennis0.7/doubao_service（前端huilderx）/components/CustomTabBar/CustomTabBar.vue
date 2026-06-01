<template>
  <view class="tab-bar-container">
    <view class="tab-bar">
      <view 
        v-for="(item, index) in tabList" 
        :key="index"
        class="tab-item"
        :class="{ active: currentIndex === index && index !== 2 }"
        @tap="switchTab(item, index)"
      >
        <view v-if="index === 2" class="tab-center-wrapper">
          <view class="tab-center-btn">
            <view class="tab-center-icon"></view>
          </view>
          <view class="tab-center-label">复盘</view>
        </view>
        <template v-else>
          <view :class="['tab-icon', item.iconClass, { 'icon-active': currentIndex === index }]"></view>
          <view class="tab-label">{{ item.text }}</view>
        </template>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, watchEffect } from 'vue'

const tabList = [
  {
    pagePath: '/pages/tabbar/index/index',
    text: '首页',
    iconClass: 'icon-home'
  },
  {
    pagePath: '/pages/tabbar/record/record',
    text: '社交圈',
    iconClass: 'icon-social'
  },
  {
    pagePath: '/pages/tabbar/ai-coach-select/ai-coach-select',
    text: '复盘',
    iconClass: ''
  },
  {
    pagePath: '/pages/tabbar/data/data',
    text: '数据',
    iconClass: 'icon-data'
  },
  {
    pagePath: '/pages/tabbar/profile/profile',
    text: '我的',
    iconClass: 'icon-profile'
  }
]

const currentIndex = ref(0)

const getCurrentPageIndex = () => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  if (!currentPage) return 0
  
  const route = '/' + currentPage.route
  const index = tabList.findIndex(item => item.pagePath === route)
  return index >= 0 ? index : 0
}

watchEffect(() => {
  const index = getCurrentPageIndex()
  currentIndex.value = index
})

const switchTab = (item, index) => {
  if (item.pagePath === getCurrentPagePath()) return
  
  uni.reLaunch({ url: item.pagePath })
}

const getCurrentPagePath = () => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  return currentPage ? '/' + currentPage.route : ''
}
</script>

<style scoped>
.tab-bar-container {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  --tab-center-size: 104rpx;
  --tab-center-icon-width: 22rpx;
  --tab-center-icon-height: 15rpx;
}

.tab-bar {
  box-sizing: border-box;
  height: calc(126rpx + env(safe-area-inset-bottom));
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  background: #000000;
  border-top: 1rpx solid rgba(255, 255, 255, 0.14);
  padding: 10rpx 24rpx calc(10rpx + env(safe-area-inset-bottom));
}

.tab-item {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  padding-top: 10rpx;
  transition: all 0.3s ease;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40rpx;
  height: 4rpx;
  background: #DEFF9A;
  border-radius: 2rpx;
  transition: all 0.3s ease;
}

.tab-icon {
  width: 40rpx;
  height: 40rpx;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.6;
  transition: all 0.3s ease;
  margin-bottom: 4rpx;
}

.tab-icon.icon-active {
  opacity: 1;
}

.icon-home {
  background-image: url("data:image/svg+xml,%3Csvg t='1778142722145' class='icon' viewBox='0 0 1024 1024' version='1.1' xmlns='http://www.w3.org/2000/svg' p-id='1336' width='200' height='200'%3E%3Cpath d='M576 821.077333v-149.333333a42.666667 42.666667 0 0 0-42.666667-42.666667h-42.666666a42.666667 42.666667 0 0 0-42.666667 42.666667v149.333333h-192a42.666667 42.666667 0 0 1-42.666667-42.666666V429.312a42.666667 42.666667 0 0 1 16.853334-33.962667l256-194.645333a42.666667 42.666667 0 0 1 51.626666 0l256 194.645333a42.666667 42.666667 0 0 1 16.853334 33.962667v349.098667a42.666667 42.666667 0 0 1-42.666667 42.666666h-192z' fill='%23DEFF9A' p-id='1337'%3E%3C/path%3E%3C/svg%3E");
}

.icon-social {
  background-image: url("data:image/svg+xml,%3Csvg t='1778143722775' class='icon' viewBox='0 0 1024 1024' version='1.1' xmlns='http://www.w3.org/2000/svg' p-id='2586' width='200' height='200'%3E%3Cpath d='M961.842 691.566h-46.749c-8.666-87.381-82.357-155.539-171.996-155.539-12.087 0-23.957 1.383-35.39 3.787 12.67-13.035 23.593-27.598 32.695-43.399 2.331 0.146 4.66 0.729 7.063 0.729 59.711 0 107.988-48.351 107.988-107.988 0-59.637-48.351-107.988-107.988-107.988-2.403 0-4.733 0.51-7.063 0.729-8.156-14.272-18.059-27.379-29.127-39.394 11.651-2.839 23.739-4.515 36.191-4.515 83.45 0 151.243 67.648 151.243 151.243 0 52.138-26.433 98.158-66.556 125.319 70.851 30.074 121.751 97.284 129.689 177.020M619.453 575.058c124.155 37.719 214.522 152.845 214.522 289.378h-47.987c0-1.383 0.219-2.913 0.219-4.297 0-143.233-115.999-259.305-259.158-259.305-143.087 0-259.158 115.999-259.158 259.305 0 1.383 0.219 2.913 0.291 4.297h-39.249c0-126.775 78.061-235.129 188.671-280.058-73.182-34.661-123.79-108.935-123.79-195.225 0-119.276 96.702-216.050 216.050-216.050 119.348 0 215.978 96.774 215.978 216.050 0 79.226-42.745 148.33-106.387 185.904M509.863 216.284c-95.537 0-172.869 77.405-172.869 172.869s77.332 172.869 172.869 172.869c95.391 0 172.869-77.405 172.869-172.869 0-95.465-77.478-172.869-172.869-172.869z' p-id='2587' fill='%23DEFF9A'%3E%3C/path%3E%3Cpath d='M63.054 690.838c8.010-79.735 58.836-146.946 129.689-177.166-40.195-27.088-66.556-73.109-66.556-125.247 0-83.522 67.793-151.243 151.243-151.243 12.452 0 24.54 1.675 36.191 4.515-11.069 12.015-20.972 25.122-29.127 39.394-2.331-0.219-4.66-0.729-7.063-0.729-59.711 0-107.988 48.351-107.988 107.988 0 59.711 48.351 107.988 107.988 107.988 2.403 0 4.733-0.582 7.063-0.729 9.102 15.874 20.098 30.437 32.695 43.472-11.433-2.403-23.301-3.787-35.39-3.787-89.638 0-163.33 68.158-171.996 155.539h-46.749z' p-id='2588' fill='%23DEFF9A'%3E%3C/path%3E%3C/svg%3E");
}

.icon-data {
  background-image: url("data:image/svg+xml,%3Csvg t='1778143267395' class='icon' viewBox='0 0 1024 1024' version='1.1' xmlns='http://www.w3.org/2000/svg' p-id='1525' width='200' height='200'%3E%3Cpath d='M513.67514038 643.03009033v191.82211304c0 3.37088013 1.29034424 6.75 3.86444092 9.33233642a13.10778809 13.10778809 0 0 0 9.32739258 3.87680054h97.00653076a13.21737671 13.21737671 0 0 0 13.20419312-13.20831299V579.23303223l-98.63882447 84.90234375-24.76373291-21.10610962zM99.08160401 834.84808349c0 3.37088013 1.29528808 6.76730347 3.87680053 9.33233643a13.10366821 13.10366821 0 0 0 9.33151246 3.87680054h96.98510742a13.09295654 13.09295654 0 0 0 9.32739258-3.87680054 13.14981079 13.14981079 0 0 0 3.87762451-9.33233643v-195.67749023L99.08160401 740.95535278v93.89190675zM306.3359375 569.96166992v264.88641357a13.16711426 13.16711426 0 0 0 3.87680054 9.33233643 13.17535401 13.17535401 0 0 0 9.33233642 3.87680054h97.02713013c3.3914795 0 6.7664795-1.29528808 9.33151245-3.87680054a13.16217041 13.16217041 0 0 0 3.87268067-9.33233643V571.61538696l-61.67779542-52.506958-61.76266479 50.85324096z m414.63555908 264.88641357a13.16217041 13.16217041 0 0 0 13.18771363 13.20913697H831.20776367a13.09295654 13.09295654 0 0 0 9.32821656-3.87680054 13.16711426 13.16711426 0 0 0 3.87680053-9.33233643V400.72634888l-123.43963623 106.28695678v327.83477783z m-21.28326416-658.90118408c-1.73858643 0-3.39642334 1.00854492-4.08361817 2.72570801-0.70861817 1.69985962-0.2496643 3.57687378 0.96569825 4.80871582l92.76223755 91.18432617-250.89367676 216.02966309-170.340271-145.08297729L98.37710571 568.10525513v96.11169433l269.72561646-222.47561645 170.33615112 145.04425048 303.06610108-260.88272094 76.62963867 75.36730957a4.44781494 4.44781494 0 0 0 4.80541992 0.90719604 4.38024902 4.38024902 0 0 0 2.69192505-4.03747558V180.32632446a4.39178467 4.39178467 0 0 0-4.40826416-4.37942505H699.68740844z' p-id='1526' fill='%23DEFF9A'%3E%3C/path%3E%3C/svg%3E");
}

.icon-profile {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1024 1024'%3E%3Cpath d='M512 512a192 192 0 1 0 0-384 192 192 0 0 0 0 384z m0 64a256 256 0 1 1 0-512 256 256 0 0 1 0 512z m0 128c-212.08 0-384 108.592-384 256v64h768v-64c0-147.408-171.92-256-384-256z m0 64c149.6 0 288 65.696 320 160H192c32-94.304 170.4-160 320-160z' fill='%23DEFF9A'/%3E%3C/svg%3E");
}

.tab-label {
  font-size: 18rpx;
  line-height: 1.2;
  color: rgba(222, 255, 154, 0.6);
  transition: all 0.3s ease;
}

.tab-item.active .tab-label {
  color: #DEFF9A;
}

.tab-center-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: -28rpx;
}

.tab-center-btn {
  width: var(--tab-center-size);
  height: var(--tab-center-size);
  background: linear-gradient(135deg, #DEFF9A 0%, #B8FF6A 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 20rpx rgba(222, 255, 154, 0.4);
  transition: all 0.3s ease;
}

.tab-center-btn:active {
  transform: scale(0.95);
}

.tab-center-icon {
  width: 0;
  height: 0;
  border-left: var(--tab-center-icon-width) solid #000;
  border-top: var(--tab-center-icon-height) solid transparent;
  border-bottom: var(--tab-center-icon-height) solid transparent;
  margin-left: 6rpx;
}

.tab-center-label {
  font-size: 18rpx;
  color: #DEFF9A;
  margin-top: 8rpx;
}
</style>
