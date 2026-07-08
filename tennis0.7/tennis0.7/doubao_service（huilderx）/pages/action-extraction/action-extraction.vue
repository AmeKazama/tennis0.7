<template>
	<view class="container">
		<view class="navbar">
			<view class="back" @tap="goBack">
				<text class="back-icon">←</text>
			</view>
			<text class="title">动作提取</text>
			<view class="nav-icon" @tap="goToSetting">
				<text class="nav-icon-text"></text>
			</view>
		</view>

		<view class="content">
			<view class="empty-card">
				<view class="empty-icon">
					<text class="empty-emoji"></text>
				</view>
				<text class="empty-title">暂无视频</text>
				<text class="empty-desc">请选择一个视频文件进行动作提取</text>
			</view>

			<view class="action-buttons">
				<view class="btn primary-btn" @tap="selectVideo">
					<text class="btn-icon"></text>
					<text class="btn-text">选择视频</text>
				</view>
				<view class="btn disabled-btn">
					<text class="btn-icon"></text>
					<text class="btn-text">开始提取</text>
				</view>
			</view>
		</view>

		<view class="mascot">
			<view class="mascot-inner"></view>
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
		},
		goToSetting() {
			uni.navigateTo({
				url: '/pages/setting/setting'
			})
		},
		selectVideo() {
			uni.navigateTo({
				url: '/pages/video-list/video-list'
			})
		}
	}
}
</script>

<style>
.container {
	min-height: 100vh;
	background: #ffffff;
	padding: 32rpx;
	padding-bottom: 180rpx;
}

.status-bar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 32rpx;
}

.time {
	color: #000000;
	font-size: 32rpx;
	font-weight: 600;
}

.status-icons {
	display: flex;
	gap: 16rpx;
}

.status-icon {
	font-size: 28rpx;
}

.navbar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 40rpx;
}

.back {
	width: 80rpx;
	height: 80rpx;
	background: rgba(0, 0, 0, 0.05);
	border-radius: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.back-icon {
	font-size: 40rpx;
	color: #000000;
}

.title {
	font-size: 36rpx;
	font-weight: bold;
	color: #000000;
}

.nav-icon {
	width: 80rpx;
	height: 80rpx;
	background: rgba(0, 0, 0, 0.05);
	border-radius: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.nav-icon-text {
	font-size: 36rpx;
}

.content {
	padding-bottom: 40rpx;
}

.empty-card {
	background: #f0f0f5;
	border-radius: 32rpx;
	padding: 120rpx 60rpx;
	margin-bottom: 60rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.empty-icon {
	width: 160rpx;
	height: 160rpx;
	background: rgba(0, 0, 0, 0.05);
	border-radius: 80rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 32rpx;
}

.empty-emoji {
	font-size: 80rpx;
}

.empty-title {
	font-size: 36rpx;
	font-weight: 600;
	color: #888888;
	margin-bottom: 16rpx;
}

.empty-desc {
	font-size: 28rpx;
	color: #999999;
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
	padding: 28rpx 0;
	border-radius: 80rpx;
	transition: all 0.2s;
}

.btn:active {
	transform: scale(0.98);
}

.primary-btn {
	background: #007aff;
}

.btn-icon {
	font-size: 32rpx;
}

.btn-text {
	font-size: 32rpx;
	color: #ffffff;
	font-weight: 600;
}

.disabled-btn {
	background: #e0e0e0;
}

.disabled-btn .btn-text {
	color: #aaaaaa;
}

.mascot {
	position: fixed;
	bottom: 120rpx;
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
</style>
