<template>
	<view class="page">
		<view class="top-bar">
			<text class="back" @tap="goBack">‹</text>
			<text class="title">个人主页</text>
			<view class="placeholder"></view>
		</view>

		<view class="hero">
			<image class="avatar" :src="user.avatar" mode="aspectFill"></image>
			<text class="name">{{ user.name }}</text>
			<text class="region">{{ user.region }}</text>
			<text class="bio">{{ user.bio }}</text>

			<view class="actions">
				<view class="follow-btn" :class="{ followed }" @tap="handleFollow">
					{{ followed ? '已关注' : '+ 关注' }}
				</view>
				<view class="chat-btn" @tap="openChat">私信</view>
			</view>
		</view>

		<view class="stats">
			<view class="stat-item">
				<text class="stat-num">128</text>
				<text class="stat-label">作品</text>
			</view>
			<view class="stat-item">
				<text class="stat-num">2.4k</text>
				<text class="stat-label">粉丝</text>
			</view>
			<view class="stat-item">
				<text class="stat-num">91%</text>
				<text class="stat-label">训练完成率</text>
			</view>
		</view>

		<view class="section-title">训练动态</view>
		<view class="post-grid">
			<view class="post-card" v-for="post in posts" :key="post.id">
				<image class="post-cover" :src="post.cover" mode="aspectFill"></image>
				<text class="post-title">{{ post.title }}</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getUserProfile, isFollowing, toggleFollow } from '@/utils/social-store/index.js'

const user = ref({
	id: '',
	name: '',
	avatar: '',
	region: '',
	bio: ''
})
const followed = ref(false)
const posts = ref([])

const refresh = () => {
	followed.value = isFollowing(user.value.id)
	posts.value = [1, 2, 3, 4].map((item) => ({
		id: `${user.value.id}_${item}`,
		cover: `https://picsum.photos/360/460?random=${user.value.id}${item}`,
		title: item % 2 ? '正手动作拆解' : '发球节奏训练'
	}))
}

const handleFollow = () => {
	followed.value = toggleFollow(user.value.id)
	uni.showToast({
		title: followed.value ? '已关注' : '已取消关注',
		icon: 'none'
	})
}

const openChat = () => {
	uni.navigateTo({
		url: `/pages/messages/chat-detail/chat-detail?id=${encodeURIComponent(user.value.id)}&name=${encodeURIComponent(user.value.name)}&avatar=${encodeURIComponent(user.value.avatar)}&online=1`
	})
}

const goBack = () => {
	uni.navigateBack()
}

onLoad((query) => {
	user.value = getUserProfile(decodeURIComponent(query.userId || 'u1'))
	refresh()
})
</script>

<style scoped>
.page {
	min-height: 100vh;
	box-sizing: border-box;
	padding: var(--status-bar-height) 28rpx 42rpx;
	background: #0b0f0d;
	color: #fff;
}

.top-bar {
	height: 86rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.back,
.placeholder {
	width: 70rpx;
}

.back {
	font-size: 58rpx;
	line-height: 1;
	color: rgba(255, 255, 255, 0.9);
}

.title {
	font-size: 31rpx;
	font-weight: 900;
}

.hero {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 30rpx 0 34rpx;
}

.avatar {
	width: 164rpx;
	height: 164rpx;
	border-radius: 50%;
	border: 4rpx solid #deff9a;
	box-shadow: 0 0 34rpx rgba(222, 255, 154, 0.38);
}

.name {
	margin-top: 22rpx;
	font-size: 38rpx;
	font-weight: 900;
}

.region {
	margin-top: 8rpx;
	color: rgba(255, 255, 255, 0.48);
	font-size: 23rpx;
}

.bio {
	margin-top: 16rpx;
	max-width: 560rpx;
	color: rgba(255, 255, 255, 0.72);
	font-size: 25rpx;
	line-height: 1.45;
	text-align: center;
}

.actions {
	display: flex;
	gap: 18rpx;
	margin-top: 28rpx;
}

.follow-btn,
.chat-btn {
	min-width: 150rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 999rpx;
	font-size: 25rpx;
	font-weight: 800;
}

.follow-btn {
	background: #deff9a;
	color: #0b0f0d;
}

.follow-btn.followed,
.chat-btn {
	background: rgba(255, 255, 255, 0.08);
	color: #fff;
	border: 1rpx solid rgba(255, 255, 255, 0.12);
}

.stats {
	display: flex;
	gap: 14rpx;
	margin-bottom: 34rpx;
}

.stat-item {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8rpx;
	padding: 22rpx 8rpx;
	border-radius: 16rpx;
	background: rgba(255, 255, 255, 0.05);
	border: 1rpx solid rgba(255, 255, 255, 0.08);
}

.stat-num {
	color: #fff;
	font-size: 30rpx;
	font-weight: 900;
}

.stat-label {
	color: rgba(255, 255, 255, 0.45);
	font-size: 21rpx;
}

.section-title {
	margin-bottom: 20rpx;
	font-size: 29rpx;
	font-weight: 900;
}

.post-grid {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 18rpx;
}

.post-card {
	min-width: 0;
	overflow: hidden;
	border-radius: 16rpx;
	background: rgba(255, 255, 255, 0.05);
	border: 1rpx solid rgba(255, 255, 255, 0.08);
}

.post-cover {
	width: 100%;
	height: 300rpx;
	background: #111;
}

.post-title {
	display: block;
	padding: 16rpx;
	color: #fff;
	font-size: 25rpx;
	font-weight: 700;
}
</style>
