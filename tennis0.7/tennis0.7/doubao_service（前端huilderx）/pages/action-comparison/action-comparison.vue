<template>
	<view class="container">
		<view class="navbar">
			<view class="back" @tap="goBack">
				<text class="back-icon">←</text>
			</view>
		</view>

		<view class="content">
			<view class="page-title">选择两段动作进行对比</view>

			<view class="section-card">
				<view class="section-header">
					<view class="section-title-wrapper">
						<text class="section-icon">L</text>
						<text class="section-title">左侧动作</text>
					</view>
					<view class="switch-wrapper">
						<text class="switch-label">镜像</text>
						<view class="switch">
							<view class="switch-circle"></view>
						</view>
					</view>
				</view>
				<view class="source-buttons">
					<view class="source-btn" @tap="selectFromLibrary('left')">
						<text class="source-icon"></text>
						<text class="source-text">从动作库</text>
					</view>
					<view class="source-btn" @tap="selectFromVideo('left')">
						<text class="source-icon"></text>
						<text class="source-text">从视频</text>
					</view>
				</view>
			</view>

			<view class="section-card">
				<view class="section-header">
					<view class="section-title-wrapper">
						<text class="section-icon green">R</text>
						<text class="section-title">右侧动作</text>
					</view>
					<view class="switch-wrapper">
						<text class="switch-label">镜像</text>
						<view class="switch">
							<view class="switch-circle"></view>
						</view>
					</view>
				</view>
				<view class="source-buttons">
					<view class="source-btn" @tap="selectFromLibrary('right')">
						<text class="source-icon"></text>
						<text class="source-text">从动作库</text>
					</view>
					<view class="source-btn" @tap="selectFromVideo('right')">
						<text class="source-icon"></text>
						<text class="source-text">从视频</text>
					</view>
				</view>
			</view>

			<view class="preview-section">
				<view class="preview-title">
					<text class="preview-icon"></text>
					<text class="preview-label">预览</text>
				</view>
				<view class="preview-grid">
					<view class="preview-item">
						<text class="preview-side">左侧</text>
						<view class="preview-box">
							<view class="preview-empty">
								<text class="preview-empty-icon"></text>
								<text class="preview-empty-text">未选择</text>
							</view>
						</view>
					</view>
					<view class="preview-item">
						<text class="preview-side">右侧</text>
						<view class="preview-box">
							<view class="preview-empty">
								<text class="preview-empty-icon"></text>
								<text class="preview-empty-text">未选择</text>
							</view>
						</view>
					</view>
				</view>
			</view>

			<view class="compare-btn disabled-btn">
				<text class="compare-icon"></text>
				<text class="compare-text">进行对比</text>
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
		selectFromLibrary(side) {
			uni.showToast({
				title: '从动作库选择',
				icon: 'none'
			})
		},
		selectFromVideo(side) {
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

.content {
	padding-bottom: 40rpx;
}

.page-title {
	font-size: 40rpx;
	font-weight: bold;
	color: #000000;
	margin-bottom: 40rpx;
}

.section-card {
	background: #f0f0f5;
	border-radius: 32rpx;
	padding: 32rpx;
	margin-bottom: 32rpx;
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 32rpx;
}

.section-title-wrapper {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.section-icon {
	width: 48rpx;
	height: 48rpx;
	background: rgba(0, 122, 255, 0.1);
	border-radius: 24rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 28rpx;
	font-weight: bold;
	color: #007aff;
}

.section-icon.green {
	background: rgba(52, 199, 89, 0.1);
	color: #34c759;
}

.section-title {
	font-size: 32rpx;
	font-weight: 600;
	color: #000000;
}

.switch-wrapper {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.switch-label {
	font-size: 28rpx;
	color: #666666;
}

.switch {
	width: 100rpx;
	height: 56rpx;
	background: #e0e0e0;
	border-radius: 28rpx;
	padding: 4rpx;
}

.switch-circle {
	width: 48rpx;
	height: 48rpx;
	background: #ffffff;
	border-radius: 24rpx;
}

.source-buttons {
	display: flex;
	gap: 24rpx;
}

.source-btn {
	flex: 1;
	background: #e0e0e0;
	border-radius: 80rpx;
	padding: 24rpx 0;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
}

.source-icon {
	font-size: 36rpx;
}

.source-text {
	font-size: 28rpx;
	color: #007aff;
	font-weight: 500;
}

.preview-section {
	background: #f0f0f5;
	border-radius: 32rpx;
	padding: 32rpx;
	margin-bottom: 32rpx;
}

.preview-title {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-bottom: 24rpx;
}

.preview-icon {
	font-size: 32rpx;
}

.preview-label {
	font-size: 32rpx;
	font-weight: 600;
	color: #000000;
}

.preview-grid {
	display: flex;
	gap: 24rpx;
}

.preview-item {
	flex: 1;
}

.preview-side {
	display: block;
	font-size: 24rpx;
	color: #666666;
	margin-bottom: 12rpx;
}

.preview-box {
	background: #ffffff;
	border-radius: 24rpx;
	padding: 80rpx 32rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.preview-empty {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 12rpx;
}

.preview-empty-icon {
	font-size: 48rpx;
}

.preview-empty-text {
	font-size: 24rpx;
	color: #999999;
}

.compare-btn {
	background: #e0e0e0;
	border-radius: 80rpx;
	padding: 28rpx 0;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
}

.compare-icon {
	font-size: 32rpx;
}

.compare-text {
	font-size: 32rpx;
	color: #aaaaaa;
	font-weight: 600;
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
