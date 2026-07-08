<template>
	<view class="page">
		<view class="top-bar">
			<text class="back" @tap="goBack">‹</text>
			<text class="title">评论</text>
			<view class="placeholder"></view>
		</view>

		<view class="post-card">
			<image class="post-cover" :src="post.poster" mode="aspectFill"></image>
			<view class="post-main">
				<view class="author-row" @tap="openUserByAuthor">
					<image class="author-avatar" :src="post.avatar" mode="aspectFill"></image>
					<text class="author-name">{{ post.author }}</text>
				</view>
				<text class="post-title">{{ post.title }}</text>
			</view>
		</view>

		<scroll-view class="comment-list" scroll-y>
			<view class="comment-item" v-for="comment in comments" :key="comment.id">
				<image class="comment-avatar" :src="comment.avatar" mode="aspectFill" @tap="openUser(comment.userId)"></image>
				<view class="comment-main">
					<text class="comment-name">{{ comment.name }}</text>
					<text class="comment-content">{{ comment.content }}</text>
					<text class="comment-time">{{ formatTime(comment.createdAt) }}</text>
				</view>
			</view>
		</scroll-view>

		<view class="input-bar">
			<input
				class="comment-input"
				v-model="draft"
				placeholder="写下你的看法..."
				placeholder-class="placeholder-text"
				confirm-type="send"
				@confirm="sendComment"
			/>
			<button class="send-btn" :class="{ active: draft.trim() }" @tap="sendComment">发送</button>
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { addComment, getComments } from '@/utils/social-store/index.js'

const post = ref({
	id: '',
	author: '',
	avatar: '',
	title: '',
	poster: ''
})
const comments = ref([])
const draft = ref('')

const loadComments = () => {
	comments.value = getComments(post.value.id)
}

const sendComment = () => {
	const content = draft.value.trim()
	if (!content) return
	comments.value = addComment(post.value.id, content)
	draft.value = ''
}

const formatTime = (time) => {
	const date = new Date(time)
	const now = Date.now()
	const diff = Math.max(0, now - date.getTime())
	if (diff < 60000) return '刚刚'
	if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
	if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
	return `${date.getMonth() + 1}-${date.getDate()}`
}

const openUser = (userId) => {
	uni.navigateTo({
		url: `/pages/profile/user-profile/user-profile?userId=${encodeURIComponent(userId)}`
	})
}

const openUserByAuthor = () => {
	const idMap = {
		'@TennisPro_Jack': 'u1',
		'@TennisQueen_Lily': 'u2',
		'@Coach_Mike': 'u3',
		'@Match_Highlight': 'u4',
		'@Training_Warrior': 'u5'
	}
	openUser(idMap[post.value.author] || 'u1')
}

const goBack = () => {
	uni.navigateBack()
}

onLoad((query) => {
	post.value = {
		id: decodeURIComponent(query.postId || ''),
		author: decodeURIComponent(query.author || ''),
		avatar: decodeURIComponent(query.avatar || ''),
		title: decodeURIComponent(query.title || ''),
		poster: decodeURIComponent(query.poster || '')
	}
	loadComments()
})
</script>

<style scoped>
.page {
	min-height: 100vh;
	box-sizing: border-box;
	display: flex;
	flex-direction: column;
	padding: var(--status-bar-height) 24rpx 0;
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

.post-card {
	display: flex;
	gap: 18rpx;
	padding: 18rpx;
	border-radius: 16rpx;
	background: rgba(255, 255, 255, 0.06);
	border: 1rpx solid rgba(255, 255, 255, 0.08);
}

.post-cover {
	width: 128rpx;
	height: 168rpx;
	border-radius: 12rpx;
	background: #111;
}

.post-main {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.author-row {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

.author-avatar {
	width: 42rpx;
	height: 42rpx;
	border-radius: 50%;
}

.author-name {
	color: #deff9a;
	font-size: 24rpx;
	font-weight: 700;
}

.post-title {
	color: rgba(255, 255, 255, 0.88);
	font-size: 26rpx;
	line-height: 1.45;
}

.comment-list {
	flex: 1;
	min-height: 0;
	padding: 24rpx 0 130rpx;
}

.comment-item {
	display: flex;
	gap: 18rpx;
	padding: 20rpx 0;
}

.comment-avatar {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	flex: 0 0 auto;
}

.comment-main {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}

.comment-name {
	color: rgba(255, 255, 255, 0.52);
	font-size: 23rpx;
}

.comment-content {
	color: #fff;
	font-size: 27rpx;
	line-height: 1.45;
}

.comment-time {
	color: rgba(255, 255, 255, 0.35);
	font-size: 21rpx;
}

.input-bar {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	box-sizing: border-box;
	display: flex;
	align-items: center;
	gap: 16rpx;
	padding: 18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));
	background: #111715;
	border-top: 1rpx solid rgba(255, 255, 255, 0.08);
}

.comment-input {
	flex: 1;
	height: 72rpx;
	box-sizing: border-box;
	padding: 0 24rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.08);
	color: #fff;
	font-size: 26rpx;
}

.placeholder-text {
	color: rgba(255, 255, 255, 0.36);
}

.send-btn {
	width: 118rpx;
	height: 72rpx;
	line-height: 72rpx;
	padding: 0;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.1);
	color: rgba(255, 255, 255, 0.45);
	font-size: 25rpx;
}

.send-btn.active {
	background: #deff9a;
	color: #0b0f0d;
	font-weight: 800;
}
</style>
