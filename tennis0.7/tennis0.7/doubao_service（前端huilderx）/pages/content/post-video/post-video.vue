<template>
	<Layout>
		<view class="container">
			<!-- 顶部导航栏 -->
			<view class="header">
				<view class="back-btn" @tap="goBack">
					<text class="back-icon">←</text>
				</view>
				<text class="page-title">发布内容</text>
				<view class="publish-btn" :class="{ disabled: !selectedMedia.path }" @tap="publishPost">
					<text class="publish-text">发布</text>
				</view>
			</view>

			<!-- 媒体上传区域 -->
			<view class="video-upload-area">
				<view v-if="!selectedMedia.path" class="upload-content" @tap="selectMedia">
					<view class="upload-icon-wrapper">
						<text class="upload-icon">＋</text>
					</view>
					<text class="upload-title">选择图片或视频</text>
					<text class="upload-desc">支持从相册选择，也可以直接拍摄</text>
					<view class="select-file-btn">
						<text class="btn-icon">⌁</text>
						<text class="btn-text">选择文件</text>
					</view>
				</view>

				<view v-else class="preview-card">
					<image
						v-if="selectedMedia.type === 'image'"
						class="media-preview"
						:src="selectedMedia.path"
						mode="aspectFill"
					></image>
					<video
					  v-else
					  class="media-preview"
					  :src="selectedMedia.path"
					  controls
					  muted
					  preload="auto"
					  @error="videoErr"
					></video>
					<view class="preview-actions">
						<text class="media-type">{{ selectedMedia.type === 'image' ? '图片' : '视频' }}</text>
						<view class="change-btn" @tap="selectMedia">重新选择</view>
					</view>
				</view>
			</view>

			<!-- 文本输入区域 -->
			<view class="input-section">
				<textarea 
					class="content-input" 
					placeholder="写点什么..." 
					placeholder-class="input-placeholder"
					v-model="textContent"
					maxlength="200"
				></textarea>
				<view class="char-count">{{ textContent.length }}/200</view>
			</view>

			<!-- 标签区域 -->
			<view class="tags-section">
				<text class="section-label">#建议标签：</text>
				<scroll-view scroll-x class="tags-scroll">
					<view class="tags-wrapper">
						<view class="tag-item" v-for="(tag, index) in suggestedTags" :key="index" @tap="addTag(tag)">
							<text class="tag-text">{{ tag }}</text>
						</view>
					</view>
				</scroll-view>
			</view>

			<!-- 添加地点 -->
			<view class="option-item" @tap="addLocation">
				<view class="option-left">
					<text class="option-icon">📍</text>
					<text class="option-label">添加地点</text>
				</view>
				<text class="arrow-icon">></text>
			</view>

			<!-- 谁可以看 -->
			<view class="option-item" @tap="setPrivacy">
				<view class="option-left">
					<text class="option-icon">👁️</text>
					<view class="label-group">
						<text class="option-label">谁可以看</text>
						<text class="option-sub">公开</text>
					</view>
				</view>
				<text class="arrow-icon">></text>
			</view>

			<!-- AI美颜优化 -->
			<view class="option-item ai-option">
				<view class="option-left">
					<text class="option-icon">✨</text>
					<text class="option-label">应用AI美颜优化</text>
				</view>
				<switch :checked="aiEnabled" @change="toggleAI" color="#DEFF9A" />
			</view>
		</view>
	</Layout>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import Layout from '@/components/Layout/Layout.vue'
import { addCommunityPost, saveLocalFile } from '@/utils/community-posts/index.js'

const textContent = ref('')
const aiEnabled = ref(true)
const selectedMedia = ref({
	type: '',
	path: ''
})
const suggestedTags = ['#网球', '#训练日记', '#AI教练']

const goBack = () => {
	uni.navigateBack()
}

// 替换为视频专用API，彻底解决模拟器不回调、无响应问题
const chooseVideo = () => {
  console.log("📹 开始选择视频");
  uni.chooseVideo({
    sourceType: ['album'], // 从相册选
    compressed: false, // 不压缩
    success: (res) => {
      console.log("✅ 视频选择成功", res.tempFilePath);
      // 赋值，直接显示预览
      selectedMedia.value = {
        type: 'video',
        path: res.tempFilePath
      };
    },
    fail: (err) => {
      console.error("❌ 选择视频失败", err);
    }
  });
}

const chooseImage = () => {
	uni.chooseImage({
		count: 1,
		sizeType: ['compressed'],
		sourceType: ['album', 'camera'],
		success: (res) => {
			selectedMedia.value = {
				type: 'image',
				path: res.tempFilePaths[0]
			}
			console.log("图片路径：", res.tempFilePaths[0])
		}
	})
}
const selectMedia = () => {
	uni.showActionSheet({
		itemList: ['选择图片', '选择视频'],
		success: (res) => {
			if (res.tapIndex === 0) {
				chooseImage()
			} else {
				chooseVideo()
			}
		}
	})
}

// 替换你现在的 publishPost 函数
const publishPost = async () => {
  if (!selectedMedia.value.path) {
    uni.showToast({ title: '请先选择图片或视频', icon: 'none' })
    return
  }

  uni.showLoading({ title: '发布中...' })

  try {
    const isVideo = selectedMedia.value.type === 'video'
    const uploadUrl = isVideo
      ? 'http://10.24.57.203:8003/api/feed/upload'
      : 'http://10.24.57.203:8003/api/feed/upload-cover'

    // 上传逻辑和你之前成功的版本完全一致
    const uploadResult = await new Promise((resolve, reject) => {
      uni.uploadFile({
        url: uploadUrl,
        filePath: selectedMedia.value.path,
        name: isVideo ? 'video' : 'file',
        timeout: 60000,
        success: (res) => {
          try {
            const data = JSON.parse(res.data)
            resolve(data)
          } catch (e) {
            reject(e)
          }
        },
        fail: reject
      })
    })

    if (uploadResult.code !== 200) {
      throw new Error(uploadResult.msg)
    }

    // 保存逻辑也和你之前的版本一致
    const backendBase = 'http://10.24.57.203:8003'
    const realUrl = backendBase + uploadResult.url

    addCommunityPost({
      type: selectedMedia.value.type,
      src: realUrl,
      text: textContent.value || '分享一次新的网球训练',
      createdAt: Date.now()
    })

    uni.showToast({ title: '发布成功！', icon: 'success' })
    selectedMedia.value = { type: '', path: '' }
    textContent.value = ''

    setTimeout(() => {
      uni.switchTab({ url: '/pages/tabbar/profile/profile' })
    }, 800)

  } catch (err) {
    console.error('发布失败', err)
    uni.showToast({ title: '发布失败', icon: 'error' })
  } finally {
    uni.hideLoading()
  }
}

const addTag = (tag) => {
	if (!textContent.value.includes(tag)) {
		textContent.value += (textContent.value ? ' ' : '') + tag
	}
}

const addLocation = () => {
	uni.showToast({
		title: '添加地点',
		icon: 'none'
	})
}

const setPrivacy = () => {
	uni.showActionSheet({
		itemList: ['公开', '仅好友可见', '私密'],
		success: (res) => {
			console.log('选择了第' + (res.tapIndex + 1) + '个按钮')
		}
	})
}
const videoErr = (e) => {
  console.error("❌ 视频播放错误：", e.detail);
}
const toggleAI = (e) => {
	aiEnabled.value = e.detail.value
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	background: #000000;
	padding: 0 32rpx;
	padding-top: calc(var(--status-bar-height) + 20rpx);
	padding-bottom: calc(120rpx + env(safe-area-inset-bottom));
}

.header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 32rpx;
	padding: 8rpx 0;
}

.back-btn {
	width: 64rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(255, 255, 255, 0.05);
	border-radius: 16rpx;
	transition: all 0.2s;
}

.back-btn:active {
	background: rgba(255, 255, 255, 0.1);
	transform: scale(0.95);
}

.back-icon {
	font-size: 36rpx;
	color: #ffffff;
	font-weight: bold;
}

.page-title {
	font-size: 36rpx;
	font-weight: bold;
	color: var(--primary-green);
	flex: 1;
	text-align: center;
}

.publish-btn {
	background: var(--primary-green);
	padding: 12rpx 28rpx;
	border-radius: 20rpx;
	box-shadow: 0 4rpx 16rpx rgba(222, 255, 154, 0.3);
}

.publish-btn.disabled {
	opacity: 0.45;
}

.publish-btn:active {
	transform: scale(0.95);
}

.publish-text {
	font-size: 26rpx;
	font-weight: bold;
	color: #000000;
}

.video-upload-area {
	margin-bottom: 24rpx;
}

.upload-content {
	background: #0a0a0a;
	border: 2rpx dashed rgba(222, 255, 154, 0.3);
	border-radius: 24rpx;
	padding: 80rpx 40rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	min-height: 500rpx;
	transition: all 0.3s;
}

.preview-card {
	position: relative;
	height: 620rpx;
	overflow: hidden;
	border-radius: 24rpx;
	background: #0a0a0a;
	border: 1rpx solid rgba(222, 255, 154, 0.18);
}

.media-preview {
	width: 100%;
	height: 100%;
	display: block;
	background: #111;
}

.preview-actions {
	position: absolute;
	left: 20rpx;
	right: 20rpx;
	bottom: 20rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.media-type,
.change-btn {
	padding: 10rpx 18rpx;
	border-radius: 999rpx;
	background: rgba(0, 0, 0, 0.62);
	color: var(--primary-green);
	font-size: 22rpx;
	font-weight: 700;
}

.change-btn {
	background: var(--primary-green);
	color: #000;
}

.upload-content:active {
	background: #101010;
	border-color: rgba(222, 255, 154, 0.5);
}

.upload-icon-wrapper {
	width: 120rpx;
	height: 120rpx;
	background: linear-gradient(135deg, rgba(222, 255, 154, 0.15), rgba(184, 255, 106, 0.1));
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 24rpx;
	border: 2rpx solid rgba(222, 255, 154, 0.3);
}

.upload-icon {
	font-size: 56rpx;
}

.upload-title {
	font-size: 32rpx;
	font-weight: 600;
	color: var(--primary-green);
	margin-bottom: 12rpx;
}

.upload-desc {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.5);
	margin-bottom: 32rpx;
}

.select-file-btn {
	display: flex;
	align-items: center;
	gap: 8rpx;
	background: rgba(222, 255, 154, 0.1);
	border: 1rpx solid rgba(222, 255, 154, 0.3);
	padding: 16rpx 32rpx;
	border-radius: 16rpx;
	transition: all 0.2s;
}

.btn-icon {
	font-size: 24rpx;
	color: var(--primary-green);
}

.btn-text {
	font-size: 26rpx;
	color: var(--primary-green);
	font-weight: 500;
}

.input-section {
	position: relative;
	margin-bottom: 32rpx;
}

.content-input {
	width: 100%;
	min-height: 100rpx;
	background: #0a0a0a;
	border: 1rpx solid rgba(255, 255, 255, 0.08);
	border-radius: 20rpx;
	padding: 20rpx 24rpx;
	font-size: 28rpx;
	color: #ffffff;
	line-height: 1.6;
}

.input-placeholder {
	color: rgba(255, 255, 255, 0.35);
}

.char-count {
	position: absolute;
	right: 24rpx;
	bottom: 16rpx;
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.4);
}

.tags-section {
	margin-bottom: 24rpx;
}

.section-label {
	font-size: 26rpx;
	color: var(--primary-green);
	font-weight: 600;
	margin-bottom: 16rpx;
	display: block;
}

.tags-scroll {
	white-space: nowrap;
}

.tags-wrapper {
	display: inline-flex;
	gap: 12rpx;
}

.tag-item {
	display: inline-flex;
	align-items: center;
	background: rgba(222, 255, 154, 0.1);
	border: 1rpx solid rgba(222, 255, 154, 0.25);
	padding: 10rpx 20rpx;
	border-radius: 20rpx;
	transition: all 0.2s;
}

.tag-item:active {
	background: rgba(222, 255, 154, 0.2);
	transform: scale(0.95);
}

.tag-text {
	font-size: 24rpx;
	color: var(--primary-green);
}

.option-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	background: #0a0a0a;
	border: 1rpx solid rgba(255, 255, 255, 0.06);
	border-radius: 20rpx;
	padding: 28rpx 24rpx;
	margin-bottom: 16rpx;
	transition: all 0.2s;
}

.option-item:active {
	background: #101010;
	border-color: rgba(222, 255, 154, 0.2);
}

.option-left {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.option-icon {
	font-size: 32rpx;
}

.label-group {
	display: flex;
	flex-direction: column;
	gap: 4rpx;
}

.option-label {
	font-size: 28rpx;
	color: #ffffff;
	font-weight: 500;
}

.option-sub {
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.45);
}

.arrow-icon {
	font-size: 32rpx;
	color: rgba(255, 255, 255, 0.4);
}

.ai-option {
	border-color: rgba(139, 92, 246, 0.2);
}

.ai-option .option-label {
	color: rgba(167, 139, 250, 0.9);
}
</style>
