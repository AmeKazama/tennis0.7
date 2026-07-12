<template>
	<view class="container">
		<view class="navbar">
			<view class="back" @tap="goBack">←</view>
			<view class="nav-right">
				<view class="nav-icon">💬</view>
				<view class="nav-icon">🔒</view>
				<view class="nav-icon">⚙️</view>
			</view>
		</view>

		<view class="tabs">
			<view class="tab-item active">
				<text class="tab-text">完整视频</text>
			</view>
			<view class="tab-item">
				<text class="tab-text">收藏回合</text>
			</view>
		</view>

		<view class="video-section">
			<view class="video-empty">
				<text class="video-icon">🎬</text>
				<text class="empty-title">暂无视频</text>
				<text class="empty-desc">请选择一个视频文件进行回合检测</text>
			</view>
			<view class="mascot">🎾</view>
		</view>

		<view class="btn-group">
			<view class="btn primary" @tap="selectVideo">
				<text class="btn-icon">📂</text>
				<text class="btn-text">选择视频</text>
			</view>
			<view class="btn disabled">
				<text class="btn-icon">✂️</text>
				<text class="btn-text">开始剪辑</text>
			</view>
		</view>

		<view class="footer-card">
			<text class="footer-title">把时间留给球场，繁琐留给 AI。</text>
			<text class="footer-desc">已累计为你节省 0.0 小时剪辑时间，足以多打 0.0 场精彩对决。</text>
			<text class="footer-desc">已累计帮助球友节省 10,000+ 小时。</text>
		</view>
	</view>
</template>

<script>
export default {
	methods: {
		goBack() {
			uni.navigateBack()
		},
		selectVideo() {
			uni.showToast({
				title: '选择视频功能',
				icon: 'none'
			})
		}
	}
}
</script>

<style>
.container {
	background: #000;
	min-height: 100vh;
	padding: 0 32rpx 32rpx;
}

.navbar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding-top: var(--status-bar-height);
	padding-bottom: 24rpx;
}

.back {
	font-size: 40rpx;
	color: #fff;
}

.nav-right {
	display: flex;
	gap: 24rpx;
}

.nav-icon {
	width: 64rpx;
	height: 64rpx;
	background: rgba(255, 255, 255, 0.1);
	border-radius: 32rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 28rpx;
}

.tabs {
	display: flex;
	background: #1a1a1a;
	border-radius: 24rpx;
	padding: 8rpx;
	margin-bottom: 32rpx;
}

.tab-item {
	flex: 1;
	text-align: center;
	padding: 20rpx 0;
	border-radius: 16rpx;
	transition: all 0.3s;
}

.tab-item.active {
	background: #333;
}

.tab-text {
	font-size: 28rpx;
	color: #fff;
	font-weight: 500;
}

.video-section {
	position: relative;
	background: #1a1a1a;
	border-radius: 24rpx;
	padding: 80rpx 32rpx;
	margin-bottom: 32rpx;
}

.video-empty {
	display: flex;
	flex-direction: column;
	align-items: center;
}

.video-icon {
	font-size: 100rpx;
	margin-bottom: 24rpx;
	opacity: 0.5;
}

.empty-title {
	font-size: 32rpx;
	color: #fff;
	font-weight: 500;
	margin-bottom: 12rpx;
}

.empty-desc {
	font-size: 26rpx;
	color: #888;
}

.mascot {
	position: absolute;
	top: 16rpx;
	right: 16rpx;
	width: 64rpx;
	height: 64rpx;
	background: rgba(255, 182, 193, 0.7);
	border-radius: 32rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 32rpx;
}

.btn-group {
	display: flex;
	gap: 20rpx;
	margin-bottom: 60rpx;
}

.btn {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
	padding: 28rpx 0;
	border-radius: 28rpx;
	transition: all 0.3s;
}

.btn.primary {
	background: #3b82f6;
}

.btn.disabled {
	background: #333;
}

.btn-icon {
	font-size: 32rpx;
}

.btn-text {
	font-size: 30rpx;
	color: #fff;
	font-weight: 500;
}

.btn.disabled .btn-text {
	color: #666;
}

.footer-card {
	background: #1a1a1a;
	border-radius: 28rpx;
	padding: 32rpx;
}

.footer-title {
	display: block;
	font-size: 30rpx;
	color: #fff;
	font-weight: 600;
	margin-bottom: 16rpx;
}

.footer-desc {
	display: block;
	font-size: 26rpx;
	color: #888;
	margin-bottom: 8rpx;
	line-height: 1.5;
}
</style>
