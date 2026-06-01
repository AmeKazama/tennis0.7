<template>
	<view class="container">
		<view class="navbar">
			<view class="back" @tap="goBack">
				<text class="back-icon">←</text>
			</view>
			<text class="title">发布视频</text>
			<view class="nav-placeholder"></view>
		</view>

		<view class="content">
			<view class="upload-section">
				<view class="upload-box">
					<view class="upload-icon">+</view>
					<text class="upload-text">视频</text>
				</view>
			</view>

			<view class="input-section">
				<view class="input-item">
					<text class="input-placeholder">添加标题</text>
				</view>
				<view class="input-item">
					<text class="input-placeholder">分享美好瞬间...</text>
				</view>
			</view>
		</view>

		<view class="mascot">
			<view class="mascot-inner">🎾</view>
		</view>

		<view class="bottom-section">
			<view class="info-bar">
				<text class="info-text">添加约球信息</text>
				<view class="info-right">
					<text class="info-hint">先完善资料</text>
					<text class="info-arrow">›</text>
				</view>
			</view>

			<view class="options-bar">
				<view class="option-item">
					<text class="option-icon">🌐</text>
					<text class="option-text">公开可见</text>
				</view>
				<view class="option-item">
					<text class="option-icon">📋</text>
					<text class="option-text">运动记录</text>
				</view>
				<view class="option-item">
					<text class="option-icon">⚙️</text>
					<text class="option-text">更多设置</text>
				</view>
			</view>

			<view class="publish-btn disabled-btn">
				<text class="publish-text">发布</text>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {}
	},
	methods: {
		goBack() {
			uni.navigateBack()
		}
	}
}
</script>

<style>
.container {
	min-height: 100vh;
	background: #121212;
	padding-bottom: 300rpx;
}

.navbar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 32rpx;
}

.back {
	width: 80rpx;
	height: 80rpx;
	background: rgba(255, 255, 255, 0.05);
	border-radius: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.back-icon {
	font-size: 40rpx;
	color: #ffffff;
}

.title {
	font-size: 36rpx;
	font-weight: bold;
	color: #ffffff;
}

.nav-placeholder {
	width: 80rpx;
}

.content {
	padding: 32rpx;
}

.upload-section {
	margin-bottom: 48rpx;
}

.upload-box {
	width: 200rpx;
	height: 200rpx;
	background: rgba(255, 255, 255, 0.05);
	border-radius: 24rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
}

.upload-icon {
	font-size: 64rpx;
	color: rgba(255, 255, 255, 0.3);
	font-weight: 300;
}

.upload-text {
	font-size: 28rpx;
	color: rgba(255, 255, 255, 0.5);
	margin-top: 8rpx;
}

.input-section {
	display: flex;
	flex-direction: column;
	gap: 32rpx;
}

.input-item {
	border-bottom: 1rpx solid rgba(255, 255, 255, 0.1);
	padding-bottom: 24rpx;
}

.input-placeholder {
	font-size: 36rpx;
	color: rgba(255, 255, 255, 0.3);
	font-weight: 600;
}

.mascot {
	position: fixed;
	bottom: 320rpx;
	right: 32rpx;
}

.mascot-inner {
	width: 100rpx;
	height: 100rpx;
	background: linear-gradient(135deg, #ff6b9d, #ff8fab);
	border-radius: 50rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 48rpx;
	box-shadow: 0 8rpx 32rpx rgba(255, 107, 157, 0.4);
}

.bottom-section {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	background: linear-gradient(180deg, rgba(18, 18, 18, 0) 0%, #121212 20%);
	padding: 24rpx 32rpx;
	padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
}

.info-bar {
	background: rgba(255, 255, 255, 0.05);
	border-radius: 24rpx;
	padding: 24rpx 32rpx;
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24rpx;
}

.info-text {
	font-size: 28rpx;
	color: #ffffff;
	font-weight: 500;
}

.info-right {
	display: flex;
	align-items: center;
	gap: 8rpx;
}

.info-hint {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.5);
}

.info-arrow {
	font-size: 32rpx;
	color: rgba(255, 255, 255, 0.5);
}

.options-bar {
	display: flex;
	justify-content: space-around;
	margin-bottom: 24rpx;
}

.option-item {
	display: flex;
	align-items: center;
	gap: 8rpx;
}

.option-icon {
	font-size: 28rpx;
}

.option-text {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.7);
}

.publish-btn {
	background: rgba(255, 255, 255, 0.1);
	border-radius: 80rpx;
	padding: 28rpx 0;
	display: flex;
	align-items: center;
	justify-content: center;
}

.publish-text {
	font-size: 32rpx;
	color: rgba(255, 255, 255, 0.3);
	font-weight: 600;
}
</style>
