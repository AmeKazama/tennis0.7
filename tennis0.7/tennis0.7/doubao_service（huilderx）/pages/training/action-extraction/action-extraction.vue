<template>
	<Layout>
		<view class="container">
			<view class="header">
				<view class="back-btn" @tap="goBack">
					<text class="back-icon">←</text>
				</view>
				<view class="page-title">动作提取</view>
			</view>

			<view class="content">
				<view class="ai-section">
					<view class="ai-title">
						<text class="ai-line">|</text>
						<text class="ai-text">AI EXTRACTION ENGINE</text>
					</view>
					<view class="ai-subtitle">AI 智能动作提取</view>
					<view class="ai-desc">上传您的网球比赛或练习视频，AI将自动识别并提取关键挥拍动作，为您生成精细的复盘数据。</view>
				</view>

				<view class="video-placeholder">
					<view class="video-frame">
						<view class="play-icon">
							<text class="play-symbol">▶</text>
						</view>
						<view class="no-video-text">暂无视频</view>
						<view class="no-video-desc">请选择一个视频文件进行动作提取，建议选择视角清晰的侧面或斜侧面视角。</view>
					</view>
				</view>

				<view class="action-buttons">
					<view class="btn primary-btn" @tap="selectVideo">
						<text class="btn-icon">⊕</text>
						<text class="btn-text">从相册选择视频</text>
					</view>
					<view class="btn disabled-btn">
						<text class="btn-icon">🚀</text>
						<text class="btn-text">开始提取</text>
					</view>
				</view>
			</view>
		</view>
	</Layout>
</template>

<script setup>
import { ref } from 'vue'
import Layout from '@/components/Layout/Layout.vue'

const goBack = () => {
	uni.navigateBack()
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

<style>
.container {
	min-height: 100vh;
	background: #000000;
	padding: 0 32rpx;
	padding-top: calc(var(--status-bar-height) + 40rpx);
}

.header {
	display: flex;
	align-items: center;
	gap: 24rpx;
	margin-bottom: 40rpx;
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
	font-size: 40rpx;
	font-weight: bold;
	color: #ffffff;
}

.ai-section {
	margin-bottom: 32rpx;
}

.ai-title {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-bottom: 12rpx;
}

.ai-line {
	width: 6rpx;
	height: 32rpx;
	background: var(--primary-green);
	border-radius: 3rpx;
}

.ai-text {
	font-size: 24rpx;
	font-weight: 600;
	color: var(--primary-green);
	letter-spacing: 2rpx;
}

.ai-subtitle {
	font-size: 32rpx;
	font-weight: bold;
	color: #ffffff;
	margin-bottom: 16rpx;
}

.ai-desc {
	font-size: 26rpx;
	color: #888888;
	line-height: 1.6;
}

.video-placeholder {
	margin-bottom: 36rpx;
}

.video-frame {
	width: 100%;
	height: 340rpx;
	background: #0a0a0a;
	border-radius: 24rpx;
	border: 2rpx solid rgba(222, 255, 154, 0.2);
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 40rpx 32rpx;
}

.play-icon {
	width: 120rpx;
	height: 120rpx;
	background: rgba(255, 255, 255, 0.1);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 20rpx;
	border: 2rpx solid rgba(255, 255, 255, 0.15);
}

.play-symbol {
	font-size: 44rpx;
	color: rgba(255, 255, 255, 0.3);
	margin-left: 6rpx;
}

.no-video-text {
	font-size: 28rpx;
	font-weight: 600;
	color: #666666;
	margin-bottom: 12rpx;
}

.no-video-desc {
	font-size: 22rpx;
	color: #555555;
	text-align: center;
	line-height: 1.4;
}

.action-buttons {
	display: flex;
	gap: 24rpx;
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
</style>
