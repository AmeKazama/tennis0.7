<template>
	<view class="message-page">
		<view class="top-bar">
			<view class="back" @tap="goBack">‹</view>
			<text class="title">新增关注</text>
			<text class="save">全部已读</text>
		</view>

		<view class="section" v-for="group in groups" :key="group.title">
			<text class="section-title">{{ group.title }}</text>
			<view class="follow-card" v-for="item in group.items" :key="item.id">
				<view class="avatar-wrap">
					<image class="avatar" :src="item.avatar" mode="aspectFill"></image>
					<view class="badge">+</view>
				</view>
				<view class="follow-main">
					<text class="name">{{ item.name }}</text>
					<text class="meta">NTRP {{ item.level }} · {{ item.time }}</text>
				</view>
				<view class="follow-btn" :class="{ muted: item.followed }" @tap="toggleFollow(item)">
					{{ item.followed ? '相互关注' : '回关' }}
				</view>
			</view>
		</view>

		<AppBottomNav active="record" />
	</view>
</template>

<script setup>
import { reactive } from 'vue'
import AppBottomNav from '@/components/AppBottomNav/AppBottomNav.vue'

const groups = reactive([
	{
		title: '今天',
		items: [
			{ id: 1, name: 'Ace_Master', level: '4.5', time: '刚刚关注了你', followed: false, avatar: 'https://i.pravatar.cc/120?u=master' },
			{ id: 2, name: 'TennisQueen_99', level: '3.5', time: '23分钟前', followed: false, avatar: 'https://i.pravatar.cc/120?u=tq99' }
		]
	},
	{
		title: '更早',
		items: [
			{ id: 3, name: 'RocketServer', level: '4.0', time: '昨天', followed: true, avatar: 'https://i.pravatar.cc/120?u=rocket' },
			{ id: 4, name: 'Court_Vibes', level: '3.0', time: '3天前', followed: false, avatar: 'https://i.pravatar.cc/120?u=court' }
		]
	}
])

const toggleFollow = (item) => {
	item.followed = !item.followed
}

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
	background: #0b0f0d;
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

.section {
	margin-top: 22rpx;
}

.section-title {
	display: block;
	margin-bottom: 14rpx;
	font-size: 22rpx;
	font-weight: 800;
	color: rgba(255, 255, 255, 0.8);
}

.follow-card {
	min-height: 110rpx;
	display: flex;
	align-items: center;
	gap: 18rpx;
	margin-bottom: 18rpx;
	padding: 16rpx 18rpx;
	border-radius: 18rpx;
	background: #1b211f;
}

.avatar-wrap {
	position: relative;
	width: 64rpx;
	height: 64rpx;
}

.avatar {
	width: 64rpx;
	height: 64rpx;
	border-radius: 50%;
}

.badge {
	position: absolute;
	right: -4rpx;
	bottom: -4rpx;
	width: 28rpx;
	height: 28rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 50%;
	background: #20ff2b;
	color: #062306;
	font-size: 18rpx;
	font-weight: 900;
}

.follow-main {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 6rpx;
}

.name {
	font-size: 27rpx;
	font-weight: 800;
}

.meta {
	font-size: 21rpx;
	color: rgba(255, 255, 255, 0.52);
}

.follow-btn {
	min-width: 102rpx;
	height: 44rpx;
	padding: 0 18rpx;
	border-radius: 999rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #22ff2f;
	color: #041604;
	font-size: 22rpx;
	font-weight: 900;
	box-shadow: 0 0 18rpx rgba(34, 255, 47, 0.55);
}

.follow-btn.muted {
	background: transparent;
	border: 1rpx solid rgba(255, 255, 255, 0.24);
	color: rgba(255, 255, 255, 0.72);
	box-shadow: none;
}


</style>
