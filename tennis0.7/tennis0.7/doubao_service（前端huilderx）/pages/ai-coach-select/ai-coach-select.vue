<template>
	<view class="container">
		<view class="navbar">
			<view class="back" @tap="goBack">←</view>
			<text class="title">AI 教练</text>
		</view>

		<view class="content">
			<view class="section">
				<text class="section-title">选择分析模式</text>
				<view class="mascot">🎾</view>
			</view>

			<view class="mode-list">
				<view class="mode-card" @tap="selectMode('action')">
					<view class="mode-icon purple-bg">
						<text class="mode-emoji">💃</text>
					</view>
					<view class="mode-info">
						<text class="mode-title">动作指导</text>
						<text class="mode-desc">针对单次挥拍进行建议</text>
					</view>
					<text class="arrow">></text>
				</view>

				<view class="mode-card" @tap="selectMode('comprehensive')">
					<view class="mode-icon orange-bg">
						<text class="mode-emoji">🎥</text>
					</view>
					<view class="mode-info">
						<text class="mode-title">综合指导</text>
						<text class="mode-desc">针对视频片段进行综合指导</text>
					</view>
					<text class="arrow">></text>
				</view>
			</view>

			<view class="section">
				<text class="section-title">历史记录</text>
			</view>

			<view class="history-card" @tap="goHistory">
				<view class="history-icon purple-bg">
					<text class="history-emoji">⏪</text>
				</view>
				<view class="history-info">
					<text class="history-title">历史记录</text>
					<text class="history-desc">查看历史分析记录</text>
				</view>
				<text class="arrow">></text>
			</view>

			<view class="footer">
				<text class="footer-title">24小时随身职业私教。</text>
				<text class="footer-desc">已累计为你进行 0 次专业技术诊断。</text>
				<text class="footer-desc">全网球友已累计获得 100,000+ 次动作纠正。</text>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	methods: {
		goBack() {
			uni.navigateBack()
		},
		selectMode(mode) {
			if (mode === 'comprehensive') {
				uni.navigateTo({
					url: '/pages/comprehensive-guide/comprehensive-guide'
				})
			} else {
				uni.navigateTo({
					url: '/pages/action-guide/action-guide'
				})
			}
		},
		goHistory() {
			uni.navigateTo({
				url: '/pages/history/history'
			})
		}
	}
}
</script>

<style>
.container {
	background: #121212;
	min-height: 100vh;
	padding: 0 30rpx 30rpx;
}

.navbar {
	display: flex;
	align-items: center;
	padding-top: var(--status-bar-height);
	padding-bottom: 40rpx;
}

.back {
	font-size: 40rpx;
	margin-right: 20rpx;
	color: #fff;
}

.title {
	font-size: 36rpx;
	font-weight: bold;
	color: #fff;
}

.content {
	padding-bottom: 60rpx;
}

.section {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 30rpx;
}

.section-title {
	font-size: 44rpx;
	font-weight: bold;
	color: #fff;
}

.mascot {
	width: 64rpx;
	height: 64rpx;
	border-radius: 32rpx;
	background: rgba(255, 255, 255, 0.1);
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 32rpx;
}

.mode-list {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
	margin-bottom: 48rpx;
}

.mode-card {
	background: rgba(255, 255, 255, 0.05);
	border-radius: 28rpx;
	padding: 32rpx;
	display: flex;
	align-items: center;
	border: 1rpx solid rgba(255, 255, 255, 0.1);
	transition: transform 0.3s;
}

.mode-card:active {
	transform: scale(0.98);
}

.mode-icon {
	width: 100rpx;
	height: 100rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 24rpx;
}

.purple-bg {
	background: linear-gradient(135deg, #8b5cf6, #6366f1);
}

.orange-bg {
	background: linear-gradient(135deg, #f97316, #ea580c);
}

.mode-emoji {
	font-size: 48rpx;
}

.mode-info {
	flex: 1;
}

.mode-title {
	display: block;
	font-size: 32rpx;
	font-weight: 600;
	color: #fff;
	margin-bottom: 8rpx;
}

.mode-desc {
	display: block;
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.6);
}

.arrow {
	font-size: 32rpx;
	color: rgba(255, 255, 255, 0.4);
}

.history-card {
	background: rgba(255, 255, 255, 0.05);
	border-radius: 28rpx;
	padding: 32rpx;
	display: flex;
	align-items: center;
	border: 1rpx solid rgba(255, 255, 255, 0.1);
	margin-bottom: 60rpx;
	transition: transform 0.3s;
}

.history-card:active {
	transform: scale(0.98);
}

.history-icon {
	width: 100rpx;
	height: 100rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 24rpx;
}

.history-emoji {
	font-size: 48rpx;
}

.history-info {
	flex: 1;
}

.history-title {
	display: block;
	font-size: 32rpx;
	font-weight: 600;
	color: #fff;
	margin-bottom: 8rpx;
}

.history-desc {
	display: block;
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.6);
}

.footer {
	padding-top: 60rpx;
}

.footer-title {
	display: block;
	font-size: 32rpx;
	font-weight: 600;
	color: #fff;
	margin-bottom: 16rpx;
}

.footer-desc {
	display: block;
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.6);
	margin-bottom: 8rpx;
	line-height: 1.5;
}
</style>
