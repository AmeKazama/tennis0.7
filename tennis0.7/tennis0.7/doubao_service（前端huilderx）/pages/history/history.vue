<template>
	<view class="container">
		<view class="navbar">
			<view class="back" @tap="goBack">
				<text class="back-icon">←</text>
			</view>
			<text class="title">历史记录</text>
			<view class="nav-placeholder"></view>
		</view>

		<view class="stats-section">
			<view class="stat-item">
				<text class="stat-label">累计分析次数</text>
				<view class="stat-value-wrapper">
					<text class="stat-value">12</text>
					<text class="stat-unit">次</text>
				</view>
			</view>
			<view class="stat-item">
				<text class="stat-label">平均得分</text>
				<view class="stat-value-wrapper">
					<text class="stat-value">85</text>
					<text class="stat-unit">分</text>
				</view>
			</view>
		</view>

		<view class="filter-tabs">
			<view class="tab-item active">
				<text class="tab-text">全部</text>
			</view>
			<view class="tab-item">
				<text class="tab-text">动作指导</text>
			</view>
			<view class="tab-item">
				<text class="tab-text">综合指导</text>
			</view>
		</view>

		<view class="history-list">
			<view class="history-item" @tap="goToDetail">
			  <view class="item-icon purple-bg">
			    <text class="icon-emoji">🔍</text>
			  </view>
			  <view class="item-content">
			    <text class="item-title">正手击球分析</text>
			    <text class="item-date">2023-10-26 15:30</text>
			  </view>
			  <view class="item-score">
			    <text class="score-value">88</text>
			    <text class="score-label">得分</text>
			  </view>
			  <text class="item-arrow">›</text>
			</view>

			<view class="history-item">
				<view class="item-icon orange-bg">
					<text class="icon-emoji">🎬</text>
				</view>
				<view class="item-content">
					<text class="item-title">全场比赛复盘</text>
					<text class="item-date">2023-10-22 10:15</text>
				</view>
				<view class="item-improve">
					<text class="improve-text">改善建议</text>
				</view>
				<text class="item-arrow">›</text>
			</view>

			<view class="history-item">
				<view class="item-icon purple-bg">
					<text class="icon-emoji">🔍</text>
				</view>
				<view class="item-content">
					<text class="item-title">反手削球练习</text>
					<text class="item-date">2023-10-21 16:45</text>
				</view>
				<view class="item-score">
					<text class="score-value">82</text>
					<text class="score-label">得分</text>
				</view>
				<text class="item-arrow">›</text>
			</view>

			<view class="highlight-card">
				<view class="highlight-content">
					<text class="highlight-title">发球技术专项分析</text>
					<text class="highlight-date">2023-10-19 09:00</text>
				</view>
				<view class="highlight-score">
					<text class="highlight-score-value">91</text>
				</view>
			</view>

			<view class="history-item">
				<view class="item-icon purple-bg">
					<text class="icon-emoji">🔍</text>
				</view>
				<view class="item-content">
					<text class="item-title">网前截击训练</text>
					<text class="item-date">2023-10-18 14:20</text>
				</view>
				<view class="item-score">
					<text class="score-value">79</text>
					<text class="score-label">得分</text>
				</view>
				<text class="item-arrow">›</text>
			</view>
		</view>

		<view class="bottom-nav">
			<view class="nav-item" @tap="goToHome">
				<text class="nav-icon">🏠</text>
				<text class="nav-label">首页</text>
			</view>
			<view class="nav-item active" @tap="goToHistory">
				<text class="nav-icon">⏪</text>
				<text class="nav-label">历史</text>
			</view>
			<view class="nav-item" @tap="goToAnalysis">
				<text class="nav-icon">📊</text>
				<text class="nav-label">分析</text>
			</view>
			<view class="nav-item" @tap="goToSettings">
				<text class="nav-icon">⚙️</text>
				<text class="nav-label">设置</text>
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
		},
		// 新增：跳转到详情分析页
		goToDetail() {
			uni.navigateTo({
				url:"/pages/analysis/analysis"
			})
		},
		goToHome() {
			uni.switchTab({
				url: '/pages/index/index'
			})
		},
		goToHistory() {
			// 已经在历史记录页面
		},
		goToAnalysis() {
			uni.navigateTo({
				url: '/pages/ai-coach-select/ai-coach-select'
			})
		},
		goToSettings() {
			uni.navigateTo({
				url: '/pages/setting/setting'
			})
		}
	}
}
</script>

<style>
.container {
	min-height: 100vh;
	background: #121212;
	padding-bottom: 160rpx;
}

.navbar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 32rpx;
}

.back {
	width: 64rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.back-icon {
	font-size: 40rpx;
	color: #a855f7;
}

.title {
	font-size: 36rpx;
	font-weight: 600;
	color: #ffffff;
}

.nav-placeholder {
	width: 64rpx;
}

.stats-section {
	padding: 0 32rpx 32rpx;
}

.stat-item {
	margin-bottom: 32rpx;
}

.stat-label {
	display: block;
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.6);
	margin-bottom: 8rpx;
}

.stat-value-wrapper {
	display: flex;
	align-items: baseline;
	gap: 8rpx;
}

.stat-value {
	font-size: 56rpx;
	font-weight: bold;
	color: #a855f7;
}

.stat-unit {
	font-size: 28rpx;
	color: rgba(255, 255, 255, 0.6);
}

.filter-tabs {
	display: flex;
	gap: 16rpx;
	padding: 0 32rpx 32rpx;
}

.tab-item {
	padding: 16rpx 32rpx;
	background: rgba(255, 255, 255, 0.05);
	border-radius: 32rpx;
}

.tab-item.active {
	background: rgba(168, 85, 247, 0.2);
}

.tab-text {
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.6);
}

.tab-item.active .tab-text {
	color: #a855f7;
}

.history-list {
	padding: 0 32rpx;
}

.history-item {
	display: flex;
	align-items: center;
	background: rgba(255, 255, 255, 0.05);
	border-radius: 24rpx;
	padding: 24rpx;
	margin-bottom: 24rpx;
}

.item-icon {
	width: 80rpx;
	height: 80rpx;
	border-radius: 20rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 24rpx;
}

.purple-bg {
	background: rgba(168, 85, 247, 0.2);
}

.orange-bg {
	background: rgba(249, 115, 22, 0.2);
}

.icon-emoji {
	font-size: 36rpx;
}

.item-content {
	flex: 1;
}

.item-title {
	display: block;
	font-size: 30rpx;
	font-weight: 500;
	color: #ffffff;
	margin-bottom: 8rpx;
}

.item-date {
	display: block;
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.4);
}

.item-score {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-right: 16rpx;
}

.score-value {
	font-size: 36rpx;
	font-weight: bold;
	color: #a855f7;
}

.score-label {
	font-size: 20rpx;
	color: rgba(255, 255, 255, 0.4);
}

.item-improve {
	margin-right: 16rpx;
}

.improve-text {
	font-size: 22rpx;
	color: #f97316;
	background: rgba(249, 115, 22, 0.1);
	padding: 8rpx 16rpx;
	border-radius: 8rpx;
}

.item-arrow {
	font-size: 32rpx;
	color: rgba(255, 255, 255, 0.3);
}

.highlight-card {
	display: flex;
	justify-content: space-between;
	align-items: center;
	background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
	border-radius: 24rpx;
	padding: 32rpx;
	margin-bottom: 24rpx;
	position: relative;
	overflow: hidden;
}

.highlight-card::before {
	content: '';
	position: absolute;
	left: 0;
	top: 0;
	bottom: 0;
	width: 8rpx;
	background: linear-gradient(180deg, #a855f7, #6366f1);
}

.highlight-content {
	flex: 1;
}

.highlight-title {
	display: block;
	font-size: 30rpx;
	font-weight: 500;
	color: #ffffff;
	margin-bottom: 8rpx;
}

.highlight-date {
	display: block;
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.4);
}

.highlight-score {
	width: 80rpx;
	height: 80rpx;
	background: linear-gradient(135deg, #6366f1, #a855f7);
	border-radius: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.highlight-score-value {
	font-size: 32rpx;
	font-weight: bold;
	color: #ffffff;
}

.bottom-nav {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	background: rgba(18, 18, 18, 0.95);
	backdrop-filter: blur(20rpx);
	display: flex;
	justify-content: space-around;
	padding: 24rpx 0;
	padding-bottom: calc(24rpx + env(safe-area-inset-bottom));
	border-top: 1rpx solid rgba(255, 255, 255, 0.05);
}

.nav-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8rpx;
}

.nav-icon {
	font-size: 40rpx;
	opacity: 0.5;
}

.nav-label {
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.5);
}

.nav-item.active .nav-icon {
	opacity: 1;
}

.nav-item.active .nav-label {
	color: #a855f7;
}
</style>
