<template>
	<view class="page">
		<view class="top-bar">
			<view class="back" @tap="goBack">‹</view>
			<text class="title">系统消息</text>
			<text class="more">⋮</text>
		</view>

		<view class="filters">
			<view
				v-for="tab in filters"
				:key="tab"
				class="filter"
				:class="{ active: activeFilter === tab }"
				@tap="activeFilter = tab"
			>{{ tab }}</view>
		</view>

		<view class="notice-list">
			<view class="notice-card" v-for="item in filteredList" :key="item.id" :class="{ muted: item.muted }">
				<view class="notice-head">
					<view class="notice-icon">{{ item.icon }}</view>
					<view class="notice-main">
						<view class="title-row">
							<text class="notice-title">{{ item.title }}</text>
							<text class="notice-time">{{ item.time }}</text>
						</view>
						<text class="notice-desc">{{ item.desc }}</text>
					</view>
				</view>
				<image v-if="item.image" class="notice-image" :src="item.image" mode="aspectFill"></image>
				<view v-if="item.action" class="action-btn">{{ item.action }}</view>
			</view>
		</view>

		<view class="float-btn">♙</view>

		<AppBottomNav active="record" />
	</view>
</template>

<script setup>
import { computed, ref } from 'vue'
import AppBottomNav from '@/components/AppBottomNav/AppBottomNav.vue'

const activeFilter = ref('全部')
const filters = ['全部', '安全', '奖励', '互动']
const notices = [
	{ id: 1, type: '互动', icon: '✦', title: '您的视频已被推荐', time: '10:15', desc: '恭喜！您的网球发球视频正在本地热门页被系统推荐，今日曝光量持续增长。', image: 'https://picsum.photos/700/260?random=91' },
	{ id: 2, type: '奖励', icon: '▣', title: '等级提升奖励', time: '昨天', desc: '您的活跃度已达到新高度：等级提升至 LV.12，已为您发放专属成就奖励。', action: '查看奖励' },
	{ id: 3, type: '安全', icon: '▢', title: '账号安全提醒', time: '昨天', desc: '检测到您在新的设备上登录了账号。如果不是本人操作，请立即修改密码并联系支持。', action: '查看详情' },
	{ id: 4, type: '奖励', icon: '☻', title: 'AI 动作分析报告已就绪', time: '前天', desc: '您的最新一场练习赛 AI 分析报告已生成，点击查看您的关键动作得分与建议。', action: '查看报告' },
	{ id: 5, type: '互动', icon: '⌁', title: '社区中国更新', time: '3天前', desc: '为了提高网球同城交流质量，我们更新了评论区互动规范，请留意新的内容公约。', muted: true }
]

const filteredList = computed(() => {
	if (activeFilter.value === '全部') return notices
	return notices.filter((item) => item.type === activeFilter.value)
})

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
	height: 76rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.back,
.more {
	width: 56rpx;
	color: #20ff2b;
	font-size: 50rpx;
	line-height: 1;
}

.more {
	text-align: right;
	font-size: 34rpx;
}

.title {
	flex: 1;
	font-size: 31rpx;
	font-weight: 900;
}

.filters {
	display: flex;
	gap: 14rpx;
	margin: 12rpx 0 24rpx;
}

.filter {
	padding: 8rpx 20rpx;
	border-radius: 999rpx;
	background: #232a27;
	color: rgba(255, 255, 255, 0.62);
	font-size: 20rpx;
	font-weight: 800;
}

.filter.active {
	background: #20ff2b;
	color: #001500;
}

.notice-list {
	display: flex;
	flex-direction: column;
	gap: 18rpx;
}

.notice-card {
	padding: 20rpx;
	border-radius: 16rpx;
	background: #1b211f;
	border: 1rpx solid rgba(255, 255, 255, 0.06);
}

.notice-card.muted {
	opacity: 0.52;
}

.notice-head {
	display: flex;
	gap: 18rpx;
}

.notice-icon {
	width: 50rpx;
	height: 50rpx;
	border-radius: 12rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	flex: 0 0 auto;
	background: rgba(32, 255, 43, 0.16);
	color: #20ff2b;
	font-size: 24rpx;
	font-weight: 900;
}

.notice-main {
	flex: 1;
	min-width: 0;
}

.title-row {
	display: flex;
	justify-content: space-between;
	gap: 16rpx;
	margin-bottom: 8rpx;
}

.notice-title {
	font-size: 25rpx;
	font-weight: 900;
}

.notice-time {
	font-size: 18rpx;
	color: rgba(255, 255, 255, 0.42);
}

.notice-desc {
	font-size: 22rpx;
	line-height: 1.5;
	color: rgba(255, 255, 255, 0.7);
}

.notice-image {
	width: 100%;
	height: 160rpx;
	margin-top: 18rpx;
	border-radius: 8rpx;
	background: rgba(255, 255, 255, 0.08);
}

.action-btn {
	display: inline-flex;
	margin-top: 16rpx;
	padding: 8rpx 18rpx;
	border-radius: 8rpx;
	background: rgba(32, 255, 43, 0.14);
	color: #20ff2b;
	font-size: 20rpx;
	font-weight: 900;
}

.float-btn {
	position: fixed;
	right: 28rpx;
	bottom: calc(132rpx + env(safe-area-inset-bottom));
	width: 54rpx;
	height: 54rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(32, 255, 43, 0.18);
	color: #20ff2b;
	box-shadow: 0 0 20rpx rgba(32, 255, 43, 0.35);
}


</style>
