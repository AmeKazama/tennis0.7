<template>
	<Layout>
		<view class="container">
			<!-- 顶部导航栏 -->
			<view class="header">
				<view class="back-btn" @tap="goBack">
					<text class="back-icon">←</text>
				</view>
				<text class="page-title">回合剪辑</text>
				<view class="header-icons">
					<view class="icon-btn">
						<text class="icon-text">💬</text>
					</view>
					<view class="icon-btn">
						<text class="icon-text">⚙️</text>
					</view>
				</view>
			</view>

			<!-- Tab 切换 -->
			<view class="tab-container">
				<view 
					class="tab-item" 
					:class="{ active: currentTab === 'full' }"
					@tap="switchTab('full')"
				>
					<text class="tab-text">完整视频</text>
					<view v-if="currentTab === 'full'" class="tab-indicator"></view>
				</view>
				<view 
					class="tab-item"
					:class="{ active: currentTab === 'favorite' }"
					@tap="switchTab('favorite')"
				>
					<text class="tab-text">收藏回合</text>
					<view v-if="currentTab === 'favorite'" class="tab-indicator"></view>
				</view>
			</view>

			<!-- 视频上传区域 -->
			<view class="video-placeholder">
				<view class="video-frame">
					<view class="camera-icon">
						<text class="camera-symbol">📹</text>
					</view>
					<view class="no-video-text">暂无视频</view>
					<view class="no-video-desc">请选择一个视频文件进行回合剪辑</view>
				</view>
			</view>

			<!-- 操作按钮 -->
			<view class="action-buttons">
				<view class="btn primary-btn" @tap="selectVideo">
					<text class="btn-icon">⊕</text>
					<text class="btn-text">从相册选择视频</text>
				</view>
				<view class="btn disabled-btn">
					<text class="btn-icon">✕</text>
					<text class="btn-text">开始剪辑</text>
				</view>
			</view>

			<!-- 提示信息 -->
			<view class="tip-card">
				<view class="tip-header">
					<text class="tip-title">把时间留给球场，算给 AI 。</text>
					<view class="tip-close">
						<text class="close-icon">••</text>
					</view>
				</view>
				<view class="tip-content">
					<text class="tip-desc">已累计为节省 <text class="highlight">0.0</text> 小时剪辑时间，足以多打 <text class="highlight">0.0</text> 场精彩对决。</text>
				</view>
				<view class="tip-footer">
					<text class="tip-sub">已累计帮助球友节省 <text class="highlight">10,000+</text> 小时。</text>
				</view>
			</view>
		</view>
	</Layout>
</template>

<script setup>
import { ref } from 'vue'
import Layout from '@/components/Layout/Layout.vue'

const currentTab = ref('full')

const goBack = () => {
	uni.navigateBack()
}

const switchTab = (tab) => {
	currentTab.value = tab
}

const selectVideo = () => {
	uni.chooseVideo({
		sourceType: ['album'],
		compressed: true,
		success: (res) => {
			uni.showToast({
				title: '视频已选择',
				icon: 'success'
			})
			console.log('选择视频成功', res.tempFilePath)
		}
	})
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	background: #000000;
	padding: 0 32rpx;
	padding-top: calc(var(--status-bar-height) + 20rpx);
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
	color: #ffffff;
	flex: 1;
	text-align: center;
}

.header-icons {
	display: flex;
	gap: 16rpx;
}

.icon-btn {
	width: 56rpx;
	height: 56rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(255, 255, 255, 0.05);
	border-radius: 14rpx;
}

.icon-text {
	font-size: 28rpx;
}

.tab-container {
	display: flex;
	gap: 48rpx;
	margin-bottom: 32rpx;
	padding: 0 8rpx;
	border-bottom: 2rpx solid rgba(255, 255, 255, 0.1);
}

.tab-item {
	position: relative;
	padding: 20rpx 0;
}

.tab-text {
	font-size: 28rpx;
	color: rgba(255, 255, 255, 0.5);
	transition: all 0.3s;
}

.tab-item.active .tab-text {
	color: var(--primary-green);
	font-weight: 600;
}

.tab-indicator {
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	height: 4rpx;
	background: var(--primary-green);
	border-radius: 2rpx;
	animation: slideIn 0.3s ease;
}

@keyframes slideIn {
	from {
		transform: scaleX(0);
	}
	to {
		transform: scaleX(1);
	}
}

.video-placeholder {
	margin-bottom: 36rpx;
}

.video-frame {
	width: 100%;
	height: 400rpx;
	background: #0a0a0a;
	border-radius: 24rpx;
	border: 2rpx solid rgba(222, 255, 154, 0.15);
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 60rpx 40rpx;
}

.camera-icon {
	width: 120rpx;
	height: 120rpx;
	background: rgba(255, 255, 255, 0.08);
	border-radius: 24rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 24rpx;
	border: 2rpx solid rgba(255, 255, 255, 0.1);
}

.camera-symbol {
	font-size: 56rpx;
	opacity: 0.4;
}

.no-video-text {
	font-size: 30rpx;
	font-weight: 600;
	color: #666666;
	margin-bottom: 12rpx;
}

.no-video-desc {
	font-size: 24rpx;
	color: #555555;
	text-align: center;
	line-height: 1.5;
}

.action-buttons {
	display: flex;
	gap: 24rpx;
	margin-bottom: 40rpx;
}

.btn {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
	padding: 32rpx 0;
	border-radius: 24rpx;
	transition: all 0.2s;
}

.btn:active {
	transform: scale(0.98);
}

.primary-btn {
	background: var(--primary-green);
	box-shadow: 0 4rpx 20rpx rgba(222, 255, 154, 0.3);
}

.btn-icon {
	font-size: 28rpx;
}

.btn-text {
	font-size: 30rpx;
	color: #000000;
	font-weight: 600;
}

.disabled-btn {
	background: #1a1a1a;
	border: 1rpx solid #2a2a2a;
}

.disabled-btn .btn-text {
	color: #444444;
}

.tip-card {
	background: rgba(222, 255, 154, 0.08);
	border: 1rpx solid rgba(222, 255, 154, 0.2);
	border-radius: 20rpx;
	padding: 28rpx 24rpx;
}

.tip-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 16rpx;
}

.tip-title {
	font-size: 26rpx;
	font-weight: 600;
	color: var(--primary-green);
}

.tip-close {
	width: 40rpx;
	height: 40rpx;
	background: rgba(255, 107, 107, 0.2);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
}

.close-icon {
	font-size: 20rpx;
	color: #ff6b6b;
	font-weight: bold;
}

.tip-content {
	margin-bottom: 12rpx;
}

.tip-desc {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.7);
	line-height: 1.6;
}

.tip-footer {
	padding-top: 12rpx;
	border-top: 1rpx solid rgba(222, 255, 154, 0.1);
}

.tip-sub {
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.5);
	line-height: 1.5;
}

.highlight {
	color: var(--primary-green);
	font-weight: 600;
}
</style>
