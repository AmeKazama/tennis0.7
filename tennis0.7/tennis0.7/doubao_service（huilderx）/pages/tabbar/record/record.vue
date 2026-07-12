<template>
	<view class="container">
		<view class="header">
			<view class="avatar-wrap">
				<image class="avatar" src="/static/coach.png" mode="aspectFill"></image>
			</view>
			<text class="brand-title">COURTVISION AI</text>
			<view class="notify-btn">
				<text class="notify-icon">♙</text>
				<text class="notify-dot"></text>
			</view>
		</view>

		<view class="content">
			<text class="section-title">消息</text>

			<view class="quick-row">
				<view class="quick-item" @tap="goMessagePage('/pages/messages/likes-favorites/likes-favorites')">
					<view class="quick-circle like">
						<view class="quick-icon heart-icon"></view>
					</view>
					<text class="quick-label">赞和收藏</text>
				</view>

				<view class="quick-item" @tap="goMessagePage('/pages/messages/new-followers/new-followers')">
					<view class="quick-circle follow">
						<view class="quick-icon follow-icon">
							<text class="follow-head"></text>
							<text class="follow-body"></text>
							<text class="follow-plus">＋</text>
						</view>
						<text class="quick-dot"></text>
					</view>
					<text class="quick-label">新增关注</text>
				</view>

				<view class="quick-item" @tap="goMessagePage('/pages/messages/comments/comments')">
					<view class="quick-circle comment">
						<view class="quick-icon comment-icon"></view>
					</view>
					<text class="quick-label">评论和@</text>
				</view>
			</view>

			<view class="message-list">
				<view class="message-card" @tap="goMessagePage('/pages/messages/system/system')">
					<view class="card-icon">⌁</view>
					<view class="card-main">
						<view class="card-head">
							<text class="card-title">系统消息</text>
							<text class="card-time">10:23 AM</text>
						</view>
						<text class="card-desc">您的最后一场网球比赛高光集锦已生成，立...</text>
					</view>
				</view>

				<view class="message-card" @tap="goMessagePage('/pages/messages/guidance/guidance')">
					<view class="card-icon muted">⌕</view>
					<view class="card-main">
						<view class="card-head">
							<text class="card-title">指导消息</text>
							<text class="card-time">昨天</text>
						</view>
						<text class="card-desc">CourtVision AI分析了您的正手击球，发现主...</text>
					</view>
				</view>

				<view class="message-card" @tap="goMessagePage('/pages/messages/chat/chat')">
					<view class="card-icon group">
						<text>♚</text>
						<text class="unread-dot">3</text>
					</view>
					<view class="card-main">
						<view class="card-head">
							<text class="card-title">聊天</text>
							<text class="card-time">周二</text>
						</view>
						<text class="card-desc">与球友们的练习安排和约球信息都在这，不...</text>
					</view>
				</view>
			</view>

			<view class="course-card" @tap="goMessagePage('/pages/messages/guidance/guidance')">
				<image class="course-image" src="/static/media/hansmarkutt-tennis-5782694_1920.jpg" mode="aspectFill"></image>
				<view class="course-mask"></view>
				<view class="course-copy">
					<text class="course-tag">会员专享</text>
					<text class="course-title">大师级AI分析功能上线</text>
				</view>
			</view>
		</view>

		<AppBottomNav active="record" />
	</view>
</template>

<script setup>
import AppBottomNav from '@/components/AppBottomNav/AppBottomNav.vue'

const goMessagePage = (url) => {
	uni.navigateTo({ url })
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	box-sizing: border-box;
	padding-bottom: calc(150rpx + env(safe-area-inset-bottom));
	background:
		radial-gradient(circle at 50% 100%, rgba(53, 255, 31, 0.12), transparent 210rpx),
		#090d0b;
	color: #fff;
}

.header {
	height: 98rpx;
	padding: var(--status-bar-height) 30rpx 0;
	display: flex;
	align-items: center;
	justify-content: space-between;
	background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(9,13,11,0.72) 62%, rgba(9,13,11,0));
}

.avatar-wrap {
	width: 58rpx;
	height: 58rpx;
	border-radius: 50%;
	padding: 3rpx;
	background: linear-gradient(180deg, #64ff40, #13dc26);
	box-shadow: 0 0 18rpx rgba(47, 255, 37, 0.52);
}

.avatar {
	width: 100%;
	height: 100%;
	border-radius: 50%;
	background: #111;
}

.brand-title {
	font-size: 22rpx;
	font-weight: 900;
	font-style: italic;
	letter-spacing: 1rpx;
	color: #37ff2d;
	text-shadow: 0 0 14rpx rgba(55, 255, 45, 0.4);
}

.notify-btn {
	position: relative;
	width: 58rpx;
	height: 58rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #37ff2d;
}

.notify-icon {
	font-size: 36rpx;
	line-height: 1;
}

.notify-dot {
	position: absolute;
	top: 4rpx;
	right: 8rpx;
	width: 14rpx;
	height: 14rpx;
	border-radius: 50%;
	background: #37ff2d;
	box-shadow: 0 0 12rpx rgba(55, 255, 45, 0.9);
}

.content {
	padding: 34rpx 30rpx 0;
}

.section-title {
	display: block;
	font-size: 28rpx;
	font-weight: 800;
	margin-bottom: 34rpx;
}

.quick-row {
	display: flex;
	justify-content: space-between;
	margin-bottom: 36rpx;
}

.quick-item {
	width: 31%;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 16rpx;
}

.quick-circle {
	position: relative;
	width: 94rpx;
	height: 94rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background:
		radial-gradient(circle at 50% 35%, rgba(82, 255, 64, 0.22), rgba(29, 97, 34, 0.36) 58%, rgba(16, 41, 24, 0.92));
	border: 1rpx solid rgba(84, 255, 70, 0.2);
	box-shadow: inset 0 0 24rpx rgba(84, 255, 70, 0.08), 0 0 18rpx rgba(84, 255, 70, 0.08);
}

.quick-circle.like {
	background:
		radial-gradient(circle at 50% 35%, rgba(255, 145, 75, 0.2), rgba(31, 94, 37, 0.42) 58%, rgba(16, 41, 24, 0.92));
}

.quick-icon {
	position: relative;
	width: 46rpx;
	height: 46rpx;
}

.heart-icon::before,
.heart-icon::after {
	content: '';
	position: absolute;
	top: 9rpx;
	width: 24rpx;
	height: 32rpx;
	border-radius: 24rpx 24rpx 6rpx 6rpx;
	background: #ff8948;
}

.heart-icon::before {
	left: 8rpx;
	transform: rotate(-45deg);
	transform-origin: 0 100%;
}

.heart-icon::after {
	right: 8rpx;
	transform: rotate(45deg);
	transform-origin: 100% 100%;
}

.follow-head {
	position: absolute;
	left: 10rpx;
	top: 6rpx;
	width: 18rpx;
	height: 18rpx;
	border: 5rpx solid #37ff2d;
	border-radius: 50%;
	box-sizing: border-box;
}

.follow-body {
	position: absolute;
	left: 4rpx;
	bottom: 7rpx;
	width: 30rpx;
	height: 18rpx;
	border: 5rpx solid #37ff2d;
	border-top-left-radius: 22rpx;
	border-top-right-radius: 22rpx;
	border-bottom: 0;
	box-sizing: border-box;
}

.follow-plus {
	position: absolute;
	right: 0;
	top: 13rpx;
	color: #37ff2d;
	font-size: 24rpx;
	line-height: 1;
	font-weight: 900;
}

.comment-icon {
	width: 42rpx;
	height: 34rpx;
	border: 5rpx solid #37ff2d;
	border-radius: 6rpx;
	box-sizing: border-box;
}

.comment-icon::after {
	content: '';
	position: absolute;
	left: 8rpx;
	bottom: 2rpx;
	width: 14rpx;
	height: 14rpx;
	border-left: 5rpx solid #37ff2d;
	border-bottom: 5rpx solid #37ff2d;
	transform: rotate(-35deg);
	background: transparent;
	box-sizing: border-box;
}

.quick-dot {
	position: absolute;
	top: 9rpx;
	right: 18rpx;
	width: 12rpx;
	height: 12rpx;
	border-radius: 50%;
	background: #37ff2d;
	box-shadow: 0 0 12rpx rgba(55, 255, 45, 0.9);
}

.quick-label {
	font-size: 23rpx;
	font-weight: 500;
	color: rgba(230, 246, 228, 0.82);
}

.message-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	margin-bottom: 20rpx;
}

.message-card {
	min-height: 92rpx;
	display: flex;
	align-items: center;
	gap: 22rpx;
	padding: 18rpx 22rpx;
	border-radius: 12rpx;
	background: #181d1b;
	border: 1rpx solid rgba(255, 255, 255, 0.035);
}

.message-card:active,
.quick-item:active,
.course-card:active {
	transform: scale(0.98);
}

.card-icon {
	position: relative;
	width: 70rpx;
	height: 70rpx;
	border-radius: 8rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	flex: 0 0 auto;
	background: rgba(55, 255, 45, 0.16);
	color: #37ff2d;
	font-size: 34rpx;
	font-weight: 900;
}

.card-icon.muted {
	background: rgba(255, 255, 255, 0.08);
}

.card-icon.group {
	font-size: 30rpx;
}

.unread-dot {
	position: absolute;
	top: -8rpx;
	right: -8rpx;
	width: 18rpx;
	height: 18rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #ff4242;
	color: #fff;
	font-size: 14rpx;
	font-weight: 900;
}

.card-main {
	flex: 1;
	min-width: 0;
}

.card-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 14rpx;
	margin-bottom: 6rpx;
}

.card-title {
	font-size: 26rpx;
	font-weight: 800;
	color: rgba(255, 255, 255, 0.88);
}

.card-time {
	font-size: 17rpx;
	color: rgba(255, 255, 255, 0.34);
}

.card-desc {
	display: block;
	font-size: 21rpx;
	color: rgba(255, 255, 255, 0.45);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.course-card {
	position: relative;
	height: 236rpx;
	overflow: hidden;
	border-radius: 14rpx;
	background: #111;
}

.course-image {
	width: 100%;
	height: 100%;
	display: block;
}

.course-mask {
	position: absolute;
	left: 0;
	right: 0;
	bottom: 0;
	height: 65%;
	background: linear-gradient(180deg, transparent, rgba(0, 0, 0, 0.88));
}

.course-copy {
	position: absolute;
	left: 22rpx;
	bottom: 22rpx;
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	gap: 10rpx;
}

.course-tag {
	padding: 6rpx 12rpx;
	border-radius: 6rpx;
	background: #37ff2d;
	color: #041204;
	font-size: 18rpx;
	font-weight: 900;
}

.course-title {
	font-size: 30rpx;
	font-weight: 900;
	color: #fff;
}
</style>
