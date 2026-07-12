<template>
	<view class="message-page">
		<view class="top-bar">
			<view class="back" @tap="goBack">‹</view>
			<text class="title">评论和@</text>
			<text class="save">全部已读</text>
		</view>

		<view class="feed-title-row">
			<text class="feed-title">最新动态</text>
			<text class="feed-count">+3条消息</text>
		</view>

		<view class="comment-list">
			<view class="comment-card" v-for="item in comments" :key="item.id" :class="{ hot: item.hot }">
				<image class="avatar" :src="item.avatar" mode="aspectFill"></image>
				<view class="comment-main">
					<view class="name-row">
						<text class="name">{{ item.name }}</text>
						<text class="time">{{ item.time }}</text>
					</view>
					<text class="comment-text">{{ item.text }}</text>
					<view class="comment-actions">
						<text class="reply">回复</text>
						<text class="like">♡ {{ item.likes }}</text>
					</view>
				</view>
				<image v-if="item.thumb" class="thumb" :src="item.thumb" mode="aspectFill"></image>
			</view>
		</view>

		<view class="end-tip">
			<text class="end-icon">◎</text>
			<text>消息都看完了</text>
		</view>

		<AppBottomNav active="record" />
	</view>
</template>

<script setup>
import AppBottomNav from '@/components/AppBottomNav/AppBottomNav.vue'

const comments = [
	{ id: 1, name: 'AceRunner_Tennis', time: '2小时前', text: '正手很稳！这球转体质量至少有3000转，要不要组局试试？', likes: 9, avatar: 'https://i.pravatar.cc/120?u=runner', thumb: 'https://picsum.photos/160/120?random=61' },
	{ id: 2, name: 'NetKing_Vicky', time: '5分钟前', text: '@你 看这不会撞角，就是比较像打墙，周末来不来练一下？', likes: 12, hot: true, avatar: 'https://i.pravatar.cc/120?u=vicky', thumb: 'https://picsum.photos/160/120?random=62' },
	{ id: 3, name: 'TennisPro_Coach', time: '昨天', text: '这个发球动作的挥拍轨迹不错，但重心回落稍早，建议再练三天，稳定输出！', likes: 4, avatar: 'https://i.pravatar.cc/120?u=coachpro', thumb: 'https://picsum.photos/160/120?random=63' },
	{ id: 4, name: 'SpinMaster', time: '昨天', text: '直线！太丝滑了。期待你下次这个角度。', likes: 5, avatar: 'https://i.pravatar.cc/120?u=spin', thumb: 'https://picsum.photos/160/120?random=64' }
]

const goBack = () => {
	uni.navigateBack()
}
</script>

<style scoped>
.message-page {
	min-height: 100vh;
	box-sizing: border-box;
	padding: var(--status-bar-height) 28rpx 150rpx;
	color: #fff;
	background:
		linear-gradient(180deg, rgba(255, 255, 255, 0.16) 0, rgba(11, 15, 13, 0.96) 150rpx, #0b0f0d 260rpx),
		#0b0f0d;
}

.top-bar {
	height: 76rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.back {
	width: 60rpx;
	color: #20ff2b;
	font-size: 52rpx;
	line-height: 1;
}

.title {
	flex: 1;
	font-size: 31rpx;
	font-weight: 800;
}

.save {
	color: #20ff2b;
	font-size: 22rpx;
	font-weight: 800;
}

.feed-title-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin: 28rpx 0 20rpx;
}

.feed-title {
	font-size: 44rpx;
	font-weight: 900;
}

.feed-count {
	color: #20ff2b;
	font-size: 20rpx;
	font-weight: 800;
}

.comment-list {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.comment-card {
	position: relative;
	display: flex;
	gap: 18rpx;
	min-height: 168rpx;
	padding: 20rpx;
	border-radius: 18rpx;
	background: #1b211f;
}

.comment-card.hot::before {
	content: '';
	position: absolute;
	left: 0;
	top: 18rpx;
	bottom: 18rpx;
	width: 6rpx;
	border-radius: 999rpx;
	background: #20ff2b;
	box-shadow: 0 0 18rpx rgba(32, 255, 43, 0.6);
}

.avatar {
	width: 58rpx;
	height: 58rpx;
	border-radius: 50%;
	flex: 0 0 auto;
}

.comment-main {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 10rpx;
}

.name-row {
	display: flex;
	align-items: center;
	gap: 8rpx;
}

.name {
	font-size: 24rpx;
	font-weight: 800;
	color: rgba(255, 255, 255, 0.9);
}

.time {
	font-size: 19rpx;
	color: rgba(255, 255, 255, 0.45);
}

.comment-text {
	font-size: 24rpx;
	line-height: 1.45;
	color: rgba(255, 255, 255, 0.82);
}

.comment-actions {
	display: flex;
	gap: 28rpx;
}

.reply {
	color: #20ff2b;
	font-size: 22rpx;
	font-weight: 800;
}

.like {
	color: rgba(255, 255, 255, 0.62);
	font-size: 22rpx;
}

.thumb {
	width: 86rpx;
	height: 70rpx;
	border-radius: 8rpx;
	flex: 0 0 auto;
	background: rgba(255, 255, 255, 0.08);
}

.end-tip {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 10rpx;
	margin: 46rpx 0 10rpx;
	color: rgba(255, 255, 255, 0.28);
	font-size: 20rpx;
}

.end-icon {
	font-size: 28rpx;
}


</style>
