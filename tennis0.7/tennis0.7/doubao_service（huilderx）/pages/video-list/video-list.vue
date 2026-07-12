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
	</view>
</template>

<script>
export default {
	data() {
		return {
			videoList: [
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
			]
		}
	},
	methods: {
		goBack() {
			uni.navigateBack()
		},
		selectVideo(item) {
			uni.showToast({
				title: '已选择: ' + item.title,
				icon: 'success'
			})
			setTimeout(() => {
				uni.navigateTo({
					url: '/pages/coach-test/coach-test'
				})
			}, 1000)
		}
	}
}
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
</style>
