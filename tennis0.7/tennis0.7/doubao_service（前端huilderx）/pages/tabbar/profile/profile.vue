<template>
  <view class="container">
    <view class="header">
      <view class="header-left" @tap="goBack">
        <text class="header-icon">←</text>
      </view>
      <text class="brand-title">COURTVISION AI</text>
      <view class="header-right">
        <text class="header-icon">🔔</text>
      </view>
    </view>

    <view class="user-section">
      <view class="avatar-container">
        <view class="avatar-glow"></view>
        <view class="avatar-wrapper" @tap="goEditProfile">
          <image class="avatar" :src="profile.avatar" mode="aspectFill" />
          <view class="avatar-badge">
            <text class="badge-icon">🔄</text>
          </view>
        </view>
      </view>
      <text class="username">{{ profile.nickname }}</text>
      <text class="user-desc">{{ profile.bio }} | {{ profile.region }}</text>
      <view class="action-buttons">
        <view class="action-btn" @tap="goEditProfile">
          <text class="btn-icon">✏️</text>
          <text class="btn-text">编辑</text>
        </view>
        <view class="action-btn">
          <text class="btn-icon">↗️</text>
          <text class="btn-text">分享</text>
        </view>
      </view>
    </view>

    <view class="stats-grid">
      <view class="stat-card" @tap="goProfilePage('/pages/profile/followers/followers')">
        <text class="stat-value">1.2k</text>
        <text class="stat-label">关注者</text>
      </view>
      <view class="stat-card" @tap="goProfilePage('/pages/profile/following/following')">
        <text class="stat-value">482</text>
        <text class="stat-label">关注中</text>
      </view>
      <view class="stat-card active" @tap="goProfilePage('/pages/stats/achievement/achievement')">
        <text class="stat-value">🎖️</text>
        <text class="stat-label">荣誉勋章</text>
      </view>
      <view class="stat-card" @tap="activeTab = 'favorites'">
        <text class="stat-value">{{ favoriteItems.length }}</text>
        <text class="stat-label">收藏</text>
      </view>
      <view class="stat-card" @tap="goProfilePage('/pages/profile/devices/devices')">
        <text class="stat-value">🎯</text>
        <text class="stat-label">智能设备</text>
      </view>
    </view>

    <view class="tabs-container">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{ active: activeTab === tab.key }"
        @tap="activeTab = tab.key"
      >
        <text class="tab-text">{{ tab.label }}</text>
      </view>
    </view>

    <view v-if="activeTab === 'publish'" class="publish-section">
      <view v-if="communityPosts.length" class="post-grid">
        <view class="post-card" v-for="post in communityPosts" :key="post.id">
          <view class="post-media-wrap">
            <image
              v-if="post.type === 'image'"
              class="post-media"
              :src="post.src"
              mode="aspectFill"
            ></image>
            <video
              v-else
              class="post-media"
              :src="post.src"
              :controls="false"
              :show-center-play-btn="false"
              object-fit="cover"
            ></video>
            <view class="post-type">{{ post.type === 'image' ? '图文' : '视频' }}</view>
          </view>
          <view class="post-info">
            <text class="post-text">{{ post.text }}</text>
            <text class="post-date">{{ post.dateText }}</text>
          </view>
        </view>
      </view>

      <view v-else class="empty-state">
      <view class="empty-icon-wrapper">
        <text class="empty-icon">⏱️</text>
      </view>
      <text class="empty-title">暂无帖子</text>
      <text class="empty-desc">开始记录您的第一次网球训练，与社区分享您的进步。</text>
      <view class="empty-btn" @tap="goPostVideo">
        <text class="empty-btn-text">立即拍摄</text>
      </view>
      </view>
    </view>

    <view v-else-if="activeTab === 'records'" class="records-section">
      <view v-if="videoRecords.length === 0" class="empty-state compact">
        <view class="empty-icon-wrapper">
          <text class="empty-icon">🎬</text>
        </view>
        <text class="empty-title">暂无训练记录</text>
        <text class="empty-desc">点击立即拍摄，上传后的视频会保存在这里。</text>
        <view class="empty-btn" @tap="shootAndUploadVideo">
          <text class="empty-btn-text">立即拍摄</text>
        </view>
      </view>

      <view v-else class="record-grid">
        <view class="record-card" v-for="record in videoRecords" :key="record.id" @tap="previewVideo(record)">
          <view class="record-thumb">
            <video
              class="record-video"
              :src="record.src"
              :controls="false"
              :show-center-play-btn="false"
              object-fit="cover"
            ></video>
            <view class="record-mask">
              <text class="record-play">▶</text>
            </view>
          </view>
          <view class="record-info">
            <text class="record-title">{{ record.title }}</text>
            <text class="record-date">{{ record.dateText }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-else-if="activeTab === 'favorites'" class="favorites-section">
      <view class="folder-row">
        <view class="folder-card" v-for="folder in favoriteFolders" :key="folder.id">
          <text class="folder-name">{{ folder.name }}</text>
          <text class="folder-count">{{ countFolder(folder.id) }} 条内容</text>
        </view>
      </view>

      <view v-if="favoriteItems.length" class="post-grid favorite-grid">
        <view class="post-card" v-for="item in favoriteItems" :key="item.id">
          <view class="post-media-wrap">
            <image class="post-media" :src="item.poster" mode="aspectFill"></image>
            <view class="post-type">{{ item.folderName }}</view>
          </view>
          <view class="post-info">
            <text class="post-text">{{ item.title }}</text>
            <text class="post-date">{{ item.author }}</text>
          </view>
        </view>
      </view>

      <view v-else class="empty-state compact">
        <view class="empty-icon-wrapper">
          <text class="empty-icon">☆</text>
        </view>
        <text class="empty-title">暂无收藏</text>
        <text class="empty-desc">首页收藏的视频内容，会按收藏夹记录在这里。</text>
      </view>
    </view>

    <view v-else class="empty-state compact">
      <view class="empty-icon-wrapper">
        <text class="empty-icon">🎾</text>
      </view>
      <text class="empty-title">暂无动作分析</text>
      <text class="empty-desc">上传训练视频后，可继续生成动作分析记录。</text>
    </view>

    <AppBottomNav active="profile" />
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import AppBottomNav from '@/components/AppBottomNav/AppBottomNav.vue'
import { addVideoRecord, getVideoRecords, saveLocalVideo } from '@/utils/video-records/index.js'
import { getCommunityPosts } from '@/utils/community-posts/index.js'
import { getFavoriteFolders, getFavorites, getProfile } from '@/utils/social-store/index.js'

const activeTab = ref('publish')
const videoRecords = ref([])
const communityPosts = ref([])
const favoriteFolders = ref([])
const favoriteItems = ref([])
const profile = ref(getProfile())
const tabs = [
  { key: 'publish', label: '发布' },
  { key: 'records', label: '记录' },
  { key: 'favorites', label: '收藏' },
  { key: 'actions', label: '动作' }
]

const goBack = () => {
  uni.navigateBack()
}

const goEditProfile = () => {
  uni.navigateTo({
    url: '/pages/profile/edit-profile/edit-profile'
  })
}

const goProfilePage = (url) => {
  uni.navigateTo({ url })
}

const formatDate = (time) => {
  const date = new Date(time)
  const pad = (value) => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const loadRecords = () => {
  videoRecords.value = getVideoRecords().map((record) => ({
    ...record,
    dateText: formatDate(record.createdAt)
  }))
}

const loadCommunityPosts = () => {
  communityPosts.value = getCommunityPosts().map((post) => ({
    ...post,
    dateText: formatDate(post.createdAt)
  }))
}

const loadSocialData = () => {
  profile.value = getProfile()
  favoriteFolders.value = getFavoriteFolders()
  favoriteItems.value = getFavorites()
}

const countFolder = (folderId) => favoriteItems.value.filter((item) => item.folderId === folderId).length

const goPostVideo = () => {
  uni.navigateTo({
    url: '/pages/content/post-video/post-video'
  })
}

const shootAndUploadVideo = () => {
  uni.chooseVideo({
    sourceType: ['camera', 'album'],
    compressed: true,
    maxDuration: 60,
    success: async (res) => {
      uni.showLoading({
        title: '上传中...'
      })

      // 模拟上传完成，并尽量把临时视频保存为本地持久文件，方便记录页回看。
      const savedPath = await saveLocalVideo(res.tempFilePath)
      setTimeout(() => {
        const record = addVideoRecord({
          src: savedPath,
          title: '网球训练视频',
          duration: res.duration || 0,
          size: res.size || 0
        })

        uni.hideLoading()
        uni.showToast({
          title: '上传完成',
          icon: 'success'
        })
        videoRecords.value = [{ ...record, dateText: formatDate(record.createdAt) }, ...videoRecords.value]
        activeTab.value = 'records'
      }, 700)
    }
  })
}

const previewVideo = (record) => {
  uni.navigateTo({
    url: `/pages/profile/video-preview/video-preview?src=${encodeURIComponent(record.src)}&title=${encodeURIComponent(record.title)}`
  })
}

onShow(() => {
  loadRecords()
  loadCommunityPosts()
  loadSocialData()
})
</script>

<style>
.container {
  background: #0a0a0f;
  min-height: 100vh;
  color: #fff;
  padding-bottom: calc(150rpx + env(safe-area-inset-bottom));
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32rpx;
  padding-top: var(--status-bar-height);
  padding-bottom: 30rpx;
}

.header-left,
.header-right {
  width: 64rpx;
  height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon {
  font-size: 36rpx;
}

.brand-title {
  font-size: 28rpx;
  font-weight: bold;
  color: var(--primary-green);
  letter-spacing: 2rpx;
}

.user-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 32rpx;
  margin-bottom: 48rpx;
}

.avatar-container {
  position: relative;
  margin-bottom: 24rpx;
}

.avatar-glow {
  position: absolute;
  top: -12rpx;
  left: -12rpx;
  right: -12rpx;
  bottom: -12rpx;
  border-radius: 50%;
  border: 4rpx solid var(--primary-green);
  box-shadow: 0 0 60rpx rgba(222, 255, 154, 0.5);
}

.avatar-wrapper {
  width: 180rpx;
  height: 180rpx;
  position: relative;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}

.avatar-badge {
  position: absolute;
  bottom: 4rpx;
  right: 4rpx;
  width: 48rpx;
  height: 48rpx;
  background: rgba(222, 255, 154, 0.2);
  border: 2rpx solid var(--primary-green);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge-icon {
  font-size: 24rpx;
}

.username {
  font-size: 40rpx;
  font-weight: bold;
  margin-bottom: 12rpx;
  letter-spacing: 1rpx;
}

.user-desc {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 28rpx;
}

.action-buttons {
  display: flex;
  gap: 20rpx;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  background: rgba(255, 255, 255, 0.08);
  padding: 16rpx 36rpx;
  border-radius: 12rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.1);
}

.btn-icon {
  font-size: 24rpx;
}

.btn-text {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.9);
}

.stats-grid {
  display: flex;
  gap: 12rpx;
  padding: 0 24rpx;
  margin-bottom: 32rpx;
}

.stat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  background: rgba(255, 255, 255, 0.04);
  padding: 24rpx 12rpx;
  border-radius: 16rpx;
  border: 1rpx solid transparent;
}

.stat-card.active {
  background: rgba(222, 255, 154, 0.1);
  border: 1rpx solid rgba(222, 255, 154, 0.3);
}

.stat-value {
  font-size: 32rpx;
  font-weight: 600;
  color: #fff;
}

.stat-card.active .stat-value {
  color: var(--primary-green);
}

.stat-label {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.5);
}

.tabs-container {
  display: flex;
  padding: 0 32rpx;
  margin-bottom: 48rpx;
  position: relative;
}

.tabs-container::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 32rpx;
  right: 32rpx;
  height: 2rpx;
  background: rgba(255, 255, 255, 0.08);
}

.tab-item {
  flex: 1;
  display: flex;
  justify-content: center;
  padding: 20rpx 0;
  position: relative;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80rpx;
  height: 4rpx;
  background: var(--primary-green);
  border-radius: 2rpx;
}

.tab-text {
  font-size: 26rpx;
  color: rgba(255, 255, 255, 0.4);
}

.tab-item.active .tab-text {
  color: var(--primary-green);
  font-weight: 600;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 32rpx;
}

.empty-state.compact {
  padding-top: 16rpx;
}

.empty-icon-wrapper {
  width: 120rpx;
  height: 120rpx;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.08);
}

.empty-icon {
  font-size: 56rpx;
}

.empty-title {
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 12rpx;
  color: #fff;
}

.empty-desc {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
  line-height: 1.6;
  margin-bottom: 32rpx;
  padding: 0 40rpx;
}

.empty-btn {
  background: var(--primary-green);
  padding: 18rpx 48rpx;
  border-radius: 12rpx;
}

.empty-btn-text {
  font-size: 26rpx;
  font-weight: 600;
  color: #000;
}

.records-section,
.favorites-section {
  padding: 0 24rpx;
}

.publish-section {
  padding: 0 24rpx;
}

.folder-row {
  display: flex;
  gap: 16rpx;
  margin-bottom: 24rpx;
  overflow-x: auto;
}

.folder-card {
  min-width: 190rpx;
  padding: 22rpx 18rpx;
  border-radius: 16rpx;
  background: rgba(222, 255, 154, 0.1);
  border: 1rpx solid rgba(222, 255, 154, 0.26);
}

.folder-name {
  display: block;
  margin-bottom: 10rpx;
  color: #fff;
  font-size: 25rpx;
  font-weight: 700;
}

.folder-count {
  color: rgba(255, 255, 255, 0.52);
  font-size: 21rpx;
}

.favorite-grid {
  padding-bottom: 24rpx;
}

.post-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.post-card {
  min-width: 0;
  overflow: hidden;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.05);
  border: 1rpx solid rgba(255, 255, 255, 0.08);
}

.post-media-wrap {
  position: relative;
  width: 100%;
  height: 360rpx;
  overflow: hidden;
  background: #000;
}

.post-media {
  width: 100%;
  height: 100%;
  display: block;
}

.post-type {
  position: absolute;
  top: 12rpx;
  right: 12rpx;
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: rgba(0, 0, 0, 0.62);
  color: var(--primary-green);
  font-size: 20rpx;
  font-weight: 700;
}

.post-info {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  padding: 16rpx;
}

.post-text {
  font-size: 25rpx;
  line-height: 1.35;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-date {
  font-size: 21rpx;
  color: rgba(255, 255, 255, 0.45);
}

.record-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.record-card {
  min-width: 0;
  overflow: hidden;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.05);
  border: 1rpx solid rgba(255, 255, 255, 0.08);
}

.record-card:active {
  transform: scale(0.98);
}

.record-thumb {
  position: relative;
  width: 100%;
  height: 360rpx;
  overflow: hidden;
  background: #000;
}

.record-video {
  width: 100%;
  height: 100%;
  display: block;
}

.record-mask {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.18);
}

.record-play {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-left: 6rpx;
  font-size: 34rpx;
  color: #000;
  background: var(--primary-green);
  box-shadow: 0 0 24rpx rgba(222, 255, 154, 0.45);
}

.record-info {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  padding: 16rpx;
}

.record-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-date {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.45);
}
</style>
