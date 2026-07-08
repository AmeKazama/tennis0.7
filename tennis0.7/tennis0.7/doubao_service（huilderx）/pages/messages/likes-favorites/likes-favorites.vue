<template>
	<view class="message-page">
		<view class="top-bar">
			<view class="back" @tap="goBack">‹</view>
			<text class="title">赞和收藏</text>
			<text class="save">保存</text>
		</view>

		<view class="filter-tabs">
			<view
				v-for="tab in filters"
				:key="tab"
				class="filter-pill"
				:class="{ active: activeFilter === tab }"
				@tap="activeFilter = tab"
			>{{ tab }}</view>
		</view>

		<view class="notice-list">
			<view class="notice-card" v-for="item in filteredList" :key="item.id">
				<view class="avatar-wrap">
					<image class="avatar" :src="item.avatar" mode="aspectFill"></image>
					<view class="badge">♥</view>
				</view>
				<view class="notice-main">
					<text class="name">{{ item.name }}</text>
					<text class="desc">{{ item.action }} · {{ item.time }}</text>
				</view>
				<image class="thumb" :src="item.thumb" mode="aspectFill"></image>
			</view>
		</view>

		<AppBottomNav active="record" />
	</view>
</template>

<script setup>
import { computed, ref } from 'vue'
import AppBottomNav from '@/components/AppBottomNav/AppBottomNav.vue'

const activeFilter = ref('全部')
const filters = ['全部', '赞了视频', '收藏文章']
const notices = [
	{ id: 1, type: '赞了视频', name: 'AceKing_Tennis', action: '赞了你的高阶正手', time: '2h', avatar: 'https://i.pravatar.cc/120?u=ace', thumb: 'https://picsum.photos/160/120?random=41' },
	{ id: 2, type: '赞了视频', name: 'Serena_Vibe', action: '赞了你的发球', time: '5h', avatar: 'https://i.pravatar.cc/120?u=serena', thumb: 'https://picsum.photos/160/120?random=42' },
	{ id: 3, type: '收藏文章', name: '网球社区达人', action: '收藏了你的动态', time: '8h', avatar: 'https://i.pravatar.cc/120?u=club', thumb: '' },
	{ id: 4, type: '赞了视频', name: 'Coach_Liu', action: '赞了你的反手训练', time: '1d', avatar: 'https://i.pravatar.cc/120?u=liu', thumb: 'https://picsum.photos/160/120?random=43' },
	{ id: 5, type: '赞了视频', name: 'RacketQueen', action: '赞了你的赛点', time: '2d', avatar: 'https://i.pravatar.cc/120?u=queen', thumb: 'https://picsum.photos/160/120?random=44' }
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
	font-size: 24rpx;
	font-weight: 800;
}

.filter-tabs {
	display: flex;
	gap: 16rpx;
	margin: 12rpx 0 28rpx;
}

.filter-pill {
	padding: 8rpx 24rpx;
	border-radius: 999rpx;
	background: #242b28;
	color: rgba(255, 255, 255, 0.54);
	font-size: 21rpx;
	font-weight: 700;
}

.filter-pill.active {
	background: #23ff31;
	color: #001400;
}

.notice-list {
	display: flex;
	flex-direction: column;
	gap: 18rpx;
}

.notice-card {
	min-height: 112rpx;
	display: flex;
	align-items: center;
	gap: 20rpx;
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
	font-size: 16rpx;
	font-weight: 900;
}

.notice-main {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 6rpx;
}

.name {
	font-size: 27rpx;
	font-weight: 800;
	color: rgba(255, 255, 255, 0.92);
}

.desc {
	font-size: 21rpx;
	color: rgba(255, 255, 255, 0.55);
}

.thumb {
	width: 86rpx;
	height: 70rpx;
	border-radius: 8rpx;
	background: rgba(255, 255, 255, 0.08);
}


</style>
