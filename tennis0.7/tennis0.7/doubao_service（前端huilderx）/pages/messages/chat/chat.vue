<template>
	<view class="page">
		<view class="top-bar">
			<text class="top-icon back" @tap="goBack">‹</text>
			<text class="title">聊天</text>
			<text class="top-icon green">＋</text>
		</view>

		<scroll-view class="story-scroll" scroll-x show-scrollbar="false">
			<view class="story-row">
				<view class="story" v-for="story in stories" :key="story.id" @tap="openChat(story)">
					<view class="story-avatar-wrap" :class="{ muted: !story.online }">
						<image class="story-avatar" :src="story.avatar" mode="aspectFill" @tap.stop="openUserProfile(story.id)"></image>
						<view v-if="story.online" class="online-dot"></view>
					</view>
					<text class="story-name">{{ story.name }}</text>
				</view>
			</view>
		</scroll-view>

		<view class="chat-list">
			<view class="chat-item" v-for="chat in chats" :key="chat.id" @tap="openChat(chat)">
				<view class="avatar-wrap">
					<image class="avatar" :src="chat.avatar" mode="aspectFill" @tap.stop="openUserProfile(chat.id)"></image>
					<view v-if="chat.online" class="online-dot"></view>
				</view>
				<view class="chat-main">
					<view class="name-row">
						<text class="name">{{ chat.name }}</text>
						<text class="time">{{ chat.time }}</text>
					</view>
					<text class="preview">{{ chat.preview }}</text>
				</view>
				<view v-if="chat.unread" class="unread">{{ chat.unread }}</view>
			</view>
		</view>

		<AppBottomNav active="record" />
	</view>
</template>

<script setup>
import AppBottomNav from '@/components/AppBottomNav/AppBottomNav.vue'

const stories = [
	{ id: 'zhang', name: '张凡', online: true, avatar: 'https://i.pravatar.cc/120?u=chat1' },
	{ id: 'li', name: '李娅', online: false, avatar: 'https://i.pravatar.cc/120?u=chat2' },
	{ id: 'wang', name: '王强', online: true, avatar: 'https://i.pravatar.cc/120?u=chat3' },
	{ id: 'chen', name: '陈芳', online: true, avatar: 'https://i.pravatar.cc/120?u=chat4' }
]

const chats = [
	{ id: 'lin', name: '林子涵', preview: '今天下午三点在中心场练吗？', time: '14:20', unread: 1, online: true, avatar: 'https://i.pravatar.cc/120?u=lin' },
	{ id: 'fan', name: '樊晓', preview: '你的正手进步太快了，下次再约。', time: '昨天', online: true, avatar: 'https://i.pravatar.cc/120?u=fan' },
	{ id: 'zhao', name: '赵霖', preview: '谢谢你的网球拍推荐，手感确实不错。', time: '周三', online: false, avatar: 'https://i.pravatar.cc/120?u=zhao' },
	{ id: 'club', name: '俱乐部通知', preview: '本周六业余公开赛开始报名了，点开看看。', time: '09:20', online: true, avatar: 'https://i.pravatar.cc/120?u=clubchat' },
	{ id: 'sun', name: '孙浩', preview: '好的，那就放到下周一晚上。', time: '03-18', online: false, avatar: 'https://i.pravatar.cc/120?u=sun' }
]

const openChat = (chat) => {
	uni.navigateTo({
		url: `/pages/messages/chat-detail/chat-detail?id=${encodeURIComponent(chat.id)}&name=${encodeURIComponent(chat.name)}&avatar=${encodeURIComponent(chat.avatar)}&online=${chat.online ? '1' : '0'}`
	})
}

const openUserProfile = (userId) => {
	uni.navigateTo({
		url: `/pages/profile/user-profile/user-profile?userId=${encodeURIComponent(userId)}`
	})
}

const goBack = () => {
	uni.navigateBack()
}
</script>

<style scoped>
.page {
	min-height: 100vh;
	box-sizing: border-box;
	padding: var(--status-bar-height) 28rpx 150rpx;
	color: #fff;
	background: #0b0f0d;
}

.top-bar {
	height: 72rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.title {
	font-size: 30rpx;
	font-weight: 900;
}

.top-icon {
	width: 54rpx;
	color: #1fff2a;
	font-size: 30rpx;
}

.back {
	font-size: 56rpx;
	line-height: 1;
}

.green {
	text-align: right;
}

.story-scroll {
	width: 100%;
	padding: 20rpx 0 28rpx;
}

.story-row {
	display: flex;
	flex-direction: row;
	align-items: center;
	width: max-content;
	min-width: 100%;
}

.story {
	width: 96rpx;
	flex: 0 0 96rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 10rpx;
	margin-right: 24rpx;
}

.story-avatar-wrap,
.avatar-wrap {
	position: relative;
	border-radius: 50%;
	box-shadow: 0 0 0 2rpx rgba(31, 255, 42, 0.7);
}

.story-avatar-wrap {
	width: 72rpx;
	height: 72rpx;
}

.story-avatar-wrap.muted {
	box-shadow: 0 0 0 2rpx rgba(255, 255, 255, 0.18);
	opacity: 0.55;
}

.story-avatar,
.avatar {
	width: 100%;
	height: 100%;
	border-radius: 50%;
}

.online-dot {
	position: absolute;
	right: -2rpx;
	bottom: 2rpx;
	width: 18rpx;
	height: 18rpx;
	border-radius: 50%;
	background: #20ff2b;
	box-shadow: 0 0 12rpx rgba(32, 255, 43, 0.8);
}

.story-name {
	font-size: 20rpx;
	color: rgba(255, 255, 255, 0.78);
}

.chat-list {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}

.chat-item {
	display: flex;
	align-items: center;
	gap: 18rpx;
	padding: 10rpx 0;
}

.avatar-wrap {
	width: 66rpx;
	height: 66rpx;
	flex: 0 0 auto;
}

.chat-main {
	flex: 1;
	min-width: 0;
}

.name-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 8rpx;
}

.name {
	color: #20ff2b;
	font-size: 27rpx;
	font-weight: 900;
}

.time {
	color: rgba(255, 255, 255, 0.42);
	font-size: 18rpx;
}

.preview {
	display: block;
	color: rgba(255, 255, 255, 0.72);
	font-size: 24rpx;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.unread {
	width: 28rpx;
	height: 28rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #20ff2b;
	color: #001500;
	font-size: 18rpx;
	font-weight: 900;
}
</style>
