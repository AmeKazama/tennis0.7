<template>
	<view class="page">
		<view class="top-bar">
			<text class="top-space back" @tap="goBack">‹</text>
			<text class="title">指导消息</text>
			<text class="top-icon">⌕</text>
		</view>

		<view class="daily">
			<view class="daily-head">
				<text class="daily-title">每日反馈</text>
				<text class="ai-pill">AI 未读</text>
			</view>
			<view class="hero-card">
				<image class="hero-img" src="https://picsum.photos/720/320?random=81" mode="aspectFill"></image>
				<view class="hero-copy">
					<text class="hero-title">进阶课程</text>
					<text class="hero-desc">本周已有 3 条新分析</text>
				</view>
			</view>
		</view>

		<view class="coach-list">
			<view class="coach-card" v-for="item in cards" :key="item.id">
				<view class="card-icon">{{ item.icon }}</view>
				<view class="card-main">
					<view class="card-head">
						<text class="card-title">{{ item.title }}</text>
						<text class="card-time">{{ item.time }}</text>
					</view>
					<text class="card-desc">{{ item.desc }}</text>
					<view class="tag-row">
						<text class="green-tag">{{ item.tag }}</text>
					</view>
					<view v-if="item.progress" class="progress">
						<view class="progress-fill" :style="{ width: item.progress + '%' }"></view>
					</view>
				</view>
			</view>
		</view>

		<AppBottomNav active="record" />
	</view>
</template>

<script setup>
import AppBottomNav from '@/components/AppBottomNav/AppBottomNav.vue'

const cards = [
	{ id: 1, icon: '⌕', title: 'Forehand Analysis Ready', time: '16:45 AM', desc: '系统在你的正手击球中发现了一个关键改进点。你的挥拍路径更稳定了，但收拍阶段仍可继续优化。', tag: '查看建议' },
	{ id: 2, icon: '●', title: '发球弱点标记', time: '昨天', desc: '根据训练区间数据，在蹬地发力时，你的肩髋转动有待结合角度调整，这能让你的球速更具穿透性。', tag: '查看动作图谱' },
	{ id: 3, icon: '↗', title: '步伐效率洞察', time: '周二', desc: '你的横移步伐效率本周提升了 12%，继续保持分腿垫步，你的防守范围正在扩大。', tag: '训练完成度', progress: 74 },
	{ id: 4, icon: '◆', title: '失误分布热区', time: '11月30日', desc: '在短球处理时，深网误判断让重心落点提前偏移较多。稳定时节奏是短期方向。', tag: '查看热区' }
]

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

.top-space,
.top-icon {
	width: 54rpx;
	color: #1fff2a;
	font-size: 28rpx;
}

.top-icon {
	text-align: right;
}

.back {
	font-size: 52rpx;
	line-height: 1;
}

.title {
	font-size: 30rpx;
	font-weight: 900;
}

.daily-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin: 12rpx 0 18rpx;
}

.daily-title {
	font-size: 24rpx;
	font-weight: 900;
}

.ai-pill {
	padding: 6rpx 14rpx;
	border-radius: 999rpx;
	background: rgba(32, 255, 43, 0.14);
	color: #20ff2b;
	font-size: 19rpx;
	font-weight: 900;
}

.hero-card {
	position: relative;
	height: 180rpx;
	border-radius: 12rpx;
	overflow: hidden;
	background: #111;
}

.hero-img {
	width: 100%;
	height: 100%;
	opacity: 0.76;
}

.hero-copy {
	position: absolute;
	left: 20rpx;
	bottom: 18rpx;
	display: flex;
	flex-direction: column;
	gap: 6rpx;
}

.hero-title {
	font-size: 25rpx;
	font-weight: 900;
}

.hero-desc {
	font-size: 21rpx;
	color: rgba(255, 255, 255, 0.78);
}

.coach-list {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	margin-top: 28rpx;
}

.coach-card {
	display: flex;
	gap: 18rpx;
	padding: 22rpx;
	border-radius: 14rpx;
	background: #1b211f;
}

.card-icon {
	width: 52rpx;
	height: 52rpx;
	border-radius: 14rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	flex: 0 0 auto;
	background: rgba(32, 255, 43, 0.18);
	color: #20ff2b;
	font-size: 24rpx;
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
	margin-bottom: 8rpx;
}

.card-title {
	font-size: 24rpx;
	font-weight: 900;
}

.card-time {
	font-size: 18rpx;
	color: rgba(255, 255, 255, 0.34);
}

.card-desc {
	font-size: 22rpx;
	line-height: 1.5;
	color: rgba(255, 255, 255, 0.66);
}

.tag-row {
	margin-top: 12rpx;
}

.green-tag {
	color: #20ff2b;
	font-size: 20rpx;
	font-weight: 900;
}

.progress {
	height: 6rpx;
	border-radius: 999rpx;
	margin-top: 14rpx;
	background: rgba(255, 255, 255, 0.1);
	overflow: hidden;
}

.progress-fill {
	height: 100%;
	border-radius: inherit;
	background: #20ff2b;
	box-shadow: 0 0 14rpx rgba(32, 255, 43, 0.7);
}


</style>
