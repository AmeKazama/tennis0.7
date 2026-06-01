<template>
	<Layout>
		<view class="container">
			<!-- 顶部导航栏 -->
			<view class="header">
				<view class="back-btn" @tap="goBack">
					<text class="back-icon">←</text>
				</view>
				<text class="page-title">打球日记</text>
				<view class="header-right">
					<view class="icon-btn">
						<text class="icon-text">⚙️</text>
					</view>
				</view>
			</view>

			<!-- 主标题区域 -->
			<view class="hero-section">
				<text class="hero-title">直接描述这次打球</text>
				<text class="hero-subtitle">比如、花、感觉、技术点等。想说什么什么</text>
			</view>

			<!-- 录音按钮区域 -->
			<view class="record-container">
				<view class="record-btn-wrapper">
					<view class="ripple-outer"></view>
					<view class="ripple-middle"></view>
					<view class="record-btn" @tap="startRecord">
						<text class="mic-icon">🎤</text>
						<text class="btn-text">开始说话</text>
					</view>
				</view>
				<view class="ai-badge">
					<text class="badge-icon">✏️</text>
				</view>
			</view>

			<!-- 你可以说区域 -->
			<view class="suggestions-section">
				<view class="section-header">
					<view class="location-icon">
						<text class="location-text">📍</text>
					</view>
					<text class="section-title">你可以说</text>
				</view>

				<view class="suggestion-list">
					<view class="suggestion-card">
						<view class="tag blue-tag">计算</view>
						<text class="suggestion-text">今天和老王打了2场，6比4赢了一场，4比6输了一场</text>
					</view>

					<view class="suggestion-card">
						<view class="tag blue-tag">开篇</view>
						<text class="suggestion-text">今天订花花了120元。满教培培花花了800元</text>
					</view>

					<view class="suggestion-card">
						<view class="tag purple-tag">感受</view>
						<text class="suggestion-text">今天强度比较大，打完有点累。但心情不错</text>
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

const startRecord = () => {
	uni.showToast({
		title: '开始录音',
		icon: 'none'
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
	margin-bottom: 48rpx;
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

.header-right {
	display: flex;
	gap: 12rpx;
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

.hero-section {
	text-align: center;
	margin-bottom: 60rpx;
}

.hero-title {
	display: block;
	font-size: 44rpx;
	font-weight: bold;
	color: #ffffff;
	margin-bottom: 16rpx;
	line-height: 1.3;
}

.hero-subtitle {
	display: block;
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.5);
	line-height: 1.5;
}

.record-container {
	position: relative;
	display: flex;
	justify-content: center;
	align-items: center;
	margin-bottom: 60rpx;
	padding: 40rpx 0;
}

.record-btn-wrapper {
	position: relative;
	display: flex;
	align-items: center;
	justify-content: center;
}

.ripple-outer {
	position: absolute;
	width: 320rpx;
	height: 320rpx;
	border-radius: 50%;
	background: radial-gradient(circle, rgba(222, 255, 154, 0.15) 0%, transparent 70%);
	animation: pulse-outer 3s ease-in-out infinite;
	z-index: 0;
}

.ripple-middle {
	position: absolute;
	width: 260rpx;
	height: 260rpx;
	border-radius: 50%;
	background: radial-gradient(circle, rgba(222, 255, 154, 0.25) 0%, transparent 70%);
	animation: pulse-middle 3s ease-in-out infinite 0.5s;
	z-index: 0;
}

.record-btn {
	width: 200rpx;
	height: 200rpx;
	background: linear-gradient(135deg, #DEFF9A 0%, #B8FF6A 100%);
	border-radius: 50%;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	position: relative;
	z-index: 1;
	box-shadow: 
		0 8rpx 32rpx rgba(222, 255, 154, 0.4),
		0 0 80rpx rgba(222, 255, 154, 0.3),
		inset 0 -4rpx 20rpx rgba(0, 0, 0, 0.1);
	transition: all 0.3s ease;
}

.record-btn:active {
	transform: scale(0.95);
	box-shadow: 
		0 4rpx 20rpx rgba(222, 255, 154, 0.3),
		0 0 40rpx rgba(222, 255, 154, 0.2),
		inset 0 -4rpx 20rpx rgba(0, 0, 0, 0.15);
}

.mic-icon {
	font-size: 56rpx;
	margin-bottom: 8rpx;
	filter: drop-shadow(0 2rpx 4rpx rgba(0, 0, 0, 0.2));
}

.btn-text {
	font-size: 26rpx;
	color: #000000;
	font-weight: 600;
	letter-spacing: 2rpx;
}

.ai-badge {
	position: absolute;
	top: 10rpx;
	right: calc(50% - 180rpx);
	width: 52rpx;
	height: 52rpx;
	background: rgba(139, 92, 246, 0.2);
	border: 2rpx solid rgba(139, 92, 246, 0.4);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	animation: float 3s ease-in-out infinite;
}

.badge-icon {
	font-size: 24rpx;
}

@keyframes pulse-outer {
	0%, 100% {
		transform: scale(1);
		opacity: 0.6;
	}
	50% {
		transform: scale(1.2);
		opacity: 0.3;
	}
}

@keyframes pulse-middle {
	0%, 100% {
		transform: scale(1);
		opacity: 0.7;
	}
	50% {
		transform: scale(1.15);
		opacity: 0.4;
	}
}

@keyframes float {
	0%, 100% {
		transform: translateY(0);
	}
	50% {
		transform: translateY(-8rpx);
	}
}

.suggestions-section {
	margin-bottom: 40rpx;
}

.section-header {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-bottom: 24rpx;
}

.location-icon {
	font-size: 28rpx;
}

.location-text {
	font-size: 28rpx;
}

.section-title {
	font-size: 30rpx;
	font-weight: 600;
	color: var(--primary-green);
}

.suggestion-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.suggestion-card {
	background: #0a0a0a;
	border: 1rpx solid rgba(255, 255, 255, 0.08);
	border-radius: 20rpx;
	padding: 24rpx 20rpx;
	transition: all 0.2s;
}

.suggestion-card:active {
	background: #101010;
	border-color: rgba(222, 255, 154, 0.2);
	transform: scale(0.98);
}

.tag {
	display: inline-block;
	font-size: 22rpx;
	font-weight: 600;
	padding: 6rpx 16rpx;
	border-radius: 8rpx;
	margin-bottom: 12rpx;
}

.blue-tag {
	background: rgba(222, 255, 154, 0.2);
	color: #DEFF9A;
	border: 1rpx solid rgba(222, 255, 154, 0.3);
}

.purple-tag {
	background: rgba(222, 255, 154, 0.2);
	color: #DEFF9A;
	border: 1rpx solid rgba(222, 255, 154, 0.3);
}

.suggestion-text {
	display: block;
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.75);
	line-height: 1.6;
}
</style>
