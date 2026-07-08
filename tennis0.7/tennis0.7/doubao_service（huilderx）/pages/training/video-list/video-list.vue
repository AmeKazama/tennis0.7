<template>
	<view class="container">
		<view class="navbar">
			<view class="back" @tap="goBack">←</view>
			<text class="title">选择视频</text>
		</view>

		<view class="video-list">
			<view class="video-item" v-for="(item, index) in videoList" :key="index" @tap="selectVideo(item)">
				<view class="video-thumb">
					<image class="thumb-img" :src="item.thumb" mode="aspectFill"></image>
					<view class="play-overlay">
						<text class="play-icon">▶</text>
					</view>
					<view class="duration">{{ item.duration }}</view>
				</view>
				<view class="video-info">
					<text class="video-title">{{ item.title }}</text>
					<text class="video-date">{{ item.date }}</text>
				</view>
			</view>
		</view>

		<!-- 底部导航栏 -->
		<view class="tab-bar">
			<view class="tab-item active" @tap="switchTab('home')">
				<text class="tab-icon">🏠</text>
				<text class="tab-label">首页</text>
			</view>
			<view class="tab-item" @tap="switchTab('social')">
				<text class="tab-icon">🤝</text>
				<text class="tab-label">社交圈</text>
			</view>
			<view class="tab-center-item" @tap="switchTab('publish')">
				<view class="tab-center-btn">
					<text class="tab-center-icon">▶</text>
				</view>
				<text class="tab-center-label">复盘</text>
			</view>
			<view class="tab-item" @tap="switchTab('data')">
				<text class="tab-icon">📈</text>
				<text class="tab-label">数据</text>
			</view>
			<view class="tab-item" @tap="switchTab('profile')">
				<text class="tab-icon">👤</text>
				<text class="tab-label">我的</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue';

const videoList = ref([
	{
		title: '正手击球练习',
		date: '2026-04-12 15:30',
		duration: '3:25',
		thumb: '/static/logo.png'
	},
	{
		title: '发球专项训练',
		date: '2026-04-11 10:20',
		duration: '5:40',
		thumb: '/static/logo.png'
	},
	{
		title: '反手击球练习',
		date: '2026-04-10 16:45',
		duration: '4:15',
		thumb: '/static/logo.png'
	},
	{
		title: '比赛录像',
		date: '2026-04-09 14:00',
		duration: '12:30',
		thumb: '/static/logo.png'
	},
	{
		title: '脚步训练',
		date: '2026-04-08 09:15',
		duration: '2:50',
		thumb: '/static/logo.png'
	},
	{
		title: '截击练习',
		date: '2026-04-07 17:20',
		duration: '3:45',
		thumb: '/static/logo.png'
	}
]);

const goBack = () => {
	uni.navigateBack();
};

const selectVideo = (item) => {
	uni.showToast({
		title: '已选择: ' + item.title,
		icon: 'success'
	});
	setTimeout(() => {
		uni.navigateTo({
			url: '/pages/ai-coach/coach-test/coach-test'
		});
	}, 1000);
};

const switchTab = (tab) => {
	if (tab === 'home') {
		uni.reLaunch({ url: '/pages/tabbar/index/index' });
	} else if (tab === 'social') {
		uni.navigateTo({ url: '/pages/tabbar/record/record' });
	} else if (tab === 'publish') {
		uni.navigateTo({ url: '/pages/tabbar/ai-coach-select/ai-coach-select' });
	} else if (tab === 'data') {
		uni.navigateTo({ url: '/pages/tabbar/data/data' });
	} else if (tab === 'profile') {
		uni.navigateTo({ url: '/pages/tabbar/profile/profile' });
	}
};
</script>

<style>
.container {
	background: #000;
	min-height: 100vh;
	padding: 0 30rpx 30rpx;
	color: #fff;
}

.navbar {
	display: flex;
	align-items: center;
	padding-top: var(--status-bar-height);
	margin-bottom: 30rpx;
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

.video-list {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}

.video-item {
	background: #111;
	border-radius: 20rpx;
	overflow: hidden;
	transition: transform 0.3s;
}

.video-item:active {
	transform: scale(0.98);
}

.video-thumb {
	position: relative;
	width: 100%;
	height: 400rpx;
	background: #222;
}

.thumb-img {
	width: 100%;
	height: 100%;
}

.play-overlay {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(0, 0, 0, 0.3);
}

.play-icon {
	font-size: 60rpx;
	color: #fff;
	opacity: 0.9;
}

.duration {
	position: absolute;
	bottom: 16rpx;
	right: 16rpx;
	background: rgba(0, 0, 0, 0.7);
	padding: 8rpx 16rpx;
	border-radius: 8rpx;
	font-size: 24rpx;
	color: #fff;
}

.video-info {
	padding: 24rpx;
}

.video-title {
	display: block;
	font-size: 28rpx;
	font-weight: 500;
	color: #fff;
	margin-bottom: 8rpx;
}

.video-date {
	display: block;
	font-size: 24rpx;
	color: #888;
}

/* 底部导航栏 */
.tab-bar {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	background: rgba(0, 0, 0, 0.8);
	backdrop-filter: blur(20px);
	-webkit-backdrop-filter: blur(20px);
	border-top: 1px solid rgba(255, 255, 255, 0.1);
	padding: 12rpx 24rpx;
	padding-bottom: calc(12rpx + env(safe-area-inset-bottom));
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	z-index: 1000;
}

.tab-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 4rpx;
	flex: 1;
	padding: 8rpx 0;
}

.tab-icon {
	font-size: 28rpx;
	color: rgba(255, 255, 255, 0.5);
	transition: all 0.3s;
}

.tab-label {
	font-size: 18rpx;
	color: rgba(255, 255, 255, 0.5);
	transition: all 0.3s;
}

.tab-item.active .tab-icon,
.tab-item.active .tab-label {
	color: var(--primary-green);
}

.tab-center-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 4rpx;
	padding: 8rpx 0;
	margin-top: -24rpx;
	position: relative;
}

.tab-center-btn {
	width: 96rpx;
	height: 96rpx;
	background: var(--primary-green);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 0 30rpx rgba(222, 255, 154, 0.5);
	border: 4rpx solid #000;
}

.tab-center-icon {
	font-size: 40rpx;
	color: #000;
	font-weight: bold;
}

.tab-center-label {
	font-size: 18rpx;
	color: var(--primary-green);
	font-weight: 600;
}
</style>
