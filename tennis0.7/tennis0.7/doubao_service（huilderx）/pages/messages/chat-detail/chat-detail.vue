<template>
	<view class="page">
		<view class="top-bar">
			<text class="top-icon back" @tap="goBack">‹</text>
			<view class="title-wrap">
				<text class="title">{{ peer.name }}</text>
				<text class="status">{{ peer.online ? '在线' : '离线' }}</text>
			</view>
			<image class="top-avatar" :src="peer.avatar" mode="aspectFill" @tap="openUserProfile(peer.id)"></image>
		</view>

		<scroll-view class="message-list" scroll-y :scroll-into-view="lastMessageId" scroll-with-animation>
			<view
				v-for="message in messages"
				:id="`msg-${message.id}`"
				:key="message.id"
				class="message-row"
				:class="{ mine: message.from === 'me' }"
			>
				<image v-if="message.from !== 'me'" class="bubble-avatar" :src="peer.avatar" mode="aspectFill" @tap="openUserProfile(peer.id)"></image>
				<view class="bubble-wrap">
					<text class="msg-time" v-if="message.showTime">{{ message.time }}</text>
					<view class="bubble" :class="{ mine: message.from === 'me' }">
						<text class="bubble-text">{{ message.content }}</text>
					</view>
				</view>
				<image v-if="message.from === 'me'" class="bubble-avatar" :src="myAvatar" mode="aspectFill"></image>
			</view>
		</scroll-view>

		<view class="input-bar">
			<input
				class="message-input"
				v-model="draft"
				confirm-type="send"
				placeholder="发消息..."
				placeholder-class="placeholder"
				@confirm="sendMessage"
			/>
			<button class="send-btn" :class="{ active: draft.trim() }" @tap="sendMessage">发送</button>
		</view>
	</view>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const myAvatar = 'https://i.pravatar.cc/120?u=me-tennis'
const peer = ref({
	id: 'friend',
	name: '球友',
	avatar: 'https://i.pravatar.cc/120?u=friend',
	online: false
})
const messages = ref([])
const draft = ref('')

const storageKey = computed(() => `courtvision_chat_${peer.value.id}`)
const lastMessageId = computed(() => {
	const last = messages.value[messages.value.length - 1]
	return last ? `msg-${last.id}` : ''
})

const defaultMessages = (name) => [
	{
		id: 1,
		from: 'friend',
		content: `刚看了你的训练视频，正手击球点比上次稳定多了。`,
		time: '14:18',
		showTime: true
	},
	{
		id: 2,
		from: 'me',
		content: '哈哈我也觉得顺了点，你下次帮我看看发球动作。',
		time: '14:19',
		showTime: false
	},
	{
		id: 3,
		from: 'friend',
		content: `可以，${name}下次带个三脚架，侧面角度更容易分析。`,
		time: '14:20',
		showTime: false
	}
]

const loadMessages = () => {
	const cached = uni.getStorageSync(storageKey.value)
	messages.value = Array.isArray(cached) && cached.length ? cached : defaultMessages(peer.value.name)
}

const saveMessages = () => {
	uni.setStorageSync(storageKey.value, messages.value)
}

const formatTime = () => {
	const now = new Date()
	const hours = String(now.getHours()).padStart(2, '0')
	const minutes = String(now.getMinutes()).padStart(2, '0')
	return `${hours}:${minutes}`
}

const sendMessage = () => {
	const content = draft.value.trim()
	if (!content) return

	messages.value.push({
		id: Date.now(),
		from: 'me',
		content,
		time: formatTime(),
		showTime: false
	})
	draft.value = ''
	saveMessages()

	nextTick(() => {
		setTimeout(() => {
			autoReply()
		}, 650)
	})
}

const autoReply = () => {
	const replies = [
		'收到，我晚点看一下你的动作报告。',
		'这个建议不错，下次训练可以试试。',
		'你这个节奏挺好，主要注意击球前的准备姿势。',
		'可以约一场，我帮你录几个侧面角度。'
	]
	const content = replies[Math.floor(Math.random() * replies.length)]
	messages.value.push({
		id: Date.now() + 1,
		from: 'friend',
		content,
		time: formatTime(),
		showTime: false
	})
	saveMessages()
}

const goBack = () => {
	uni.navigateBack()
}

const openUserProfile = (userId) => {
	uni.navigateTo({
		url: `/pages/profile/user-profile/user-profile?userId=${encodeURIComponent(userId)}`
	})
}

onLoad((query) => {
	peer.value = {
		id: decodeURIComponent(query.id || 'friend'),
		name: decodeURIComponent(query.name || '球友'),
		avatar: decodeURIComponent(query.avatar || 'https://i.pravatar.cc/120?u=friend'),
		online: query.online === '1'
	}
	loadMessages()
})
</script>

<style scoped>
.page {
	min-height: 100vh;
	box-sizing: border-box;
	display: flex;
	flex-direction: column;
	padding: var(--status-bar-height) 0 0;
	background: #ededed;
	color: #111;
}

.top-bar {
	height: 92rpx;
	padding: 0 26rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
	background: #f7f7f7;
	border-bottom: 1rpx solid rgba(0, 0, 0, 0.06);
}

.top-icon {
	width: 64rpx;
	color: #111;
	font-size: 34rpx;
}

.back {
	font-size: 60rpx;
	line-height: 1;
}

.title-wrap {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 4rpx;
}

.title {
	font-size: 31rpx;
	font-weight: 700;
}

.status {
	font-size: 20rpx;
	color: #777;
}

.top-avatar {
	width: 58rpx;
	height: 58rpx;
	border-radius: 50%;
}

.message-list {
	flex: 1;
	box-sizing: border-box;
	padding: 28rpx 24rpx 20rpx;
}

.message-row {
	display: flex;
	align-items: flex-start;
	gap: 16rpx;
	margin-bottom: 26rpx;
}

.message-row.mine {
	justify-content: flex-end;
}

.bubble-avatar {
	width: 72rpx;
	height: 72rpx;
	border-radius: 8rpx;
	flex: 0 0 auto;
}

.bubble-wrap {
	max-width: 560rpx;
	display: flex;
	flex-direction: column;
}

.msg-time {
	align-self: center;
	margin-bottom: 16rpx;
	color: #999;
	font-size: 20rpx;
}

.bubble {
	padding: 20rpx 22rpx;
	border-radius: 10rpx;
	background: #fff;
}

.bubble.mine {
	background: #95ec69;
}

.bubble-text {
	font-size: 29rpx;
	line-height: 1.55;
	color: #111;
	word-break: break-word;
}

.input-bar {
	padding: 14rpx 18rpx calc(14rpx + env(safe-area-inset-bottom));
	display: flex;
	align-items: center;
	gap: 14rpx;
	background: #f7f7f7;
	border-top: 1rpx solid rgba(0, 0, 0, 0.06);
}

.message-input {
	flex: 1;
	height: 76rpx;
	box-sizing: border-box;
	padding: 0 22rpx;
	border-radius: 10rpx;
	background: #fff;
	font-size: 29rpx;
}

.placeholder {
	color: #aaa;
}

.send-btn {
	width: 116rpx;
	height: 76rpx;
	line-height: 76rpx;
	padding: 0;
	border-radius: 10rpx;
	background: #d8d8d8;
	color: #777;
	font-size: 28rpx;
}

.send-btn.active {
	background: #07c160;
	color: #fff;
}
</style>
