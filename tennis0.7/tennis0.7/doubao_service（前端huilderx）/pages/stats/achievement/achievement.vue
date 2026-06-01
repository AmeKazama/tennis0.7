<template>
	<view class="page">
		<view class="top-bar">
			<text class="back" @tap="goBack">‹</text>
			<text class="title">荣誉勋章</text>
			<text class="share">⌯</text>
		</view>

		<view class="progress-card">
			<view>
				<text class="label">荣誉成就进度</text>
				<view class="score"><text class="done">12</text><text class="total"> / 32</text></view>
			</view>
			<view class="star">★</view>
			<view class="progress"><view class="fill"></view></view>
		</view>

		<view class="badge-grid">
			<view class="badge-card" v-for="item in badges" :key="item.name" :class="{ locked: item.locked }">
				<view class="icon-wrap">
					<text class="icon">{{ item.icon }}</text>
					<text class="check">{{ item.locked ? '▧' : '✓' }}</text>
				</view>
				<text class="badge-name">{{ item.name }}</text>
				<text class="badge-desc">{{ item.desc }}</text>
			</view>
		</view>
	</view>
</template>

<script setup>
const badges = [
	{ icon: '⌕', name: 'First Match', desc: '完成首次AI对局' },
	{ icon: '⚡', name: 'AI Master', desc: '精准击中50+次' },
	{ icon: '◎', name: 'Elite Tier', desc: '进入全球前10%' },
	{ icon: '↺', name: '100 Sessions', desc: '累计完成100场训练', locked: true },
	{ icon: '🏆', name: 'Grand Slam', desc: '解锁全部基础荣誉', locked: true },
	{ icon: '♜', name: 'Nocturnal Pro', desc: '在午夜完成高级训练', locked: true }
]

const goBack = () => uni.navigateBack()
</script>

<style scoped>
.page {
	min-height: 100vh;
	box-sizing: border-box;
	padding: var(--status-bar-height) 28rpx 48rpx;
	background: linear-gradient(180deg, rgba(255,255,255,.2), #0b0f0d 150rpx);
	color: #fff;
}
.top-bar {
	height: 78rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
}
.back,.share { width: 64rpx; color: #69ff4b; font-size: 46rpx; }
.share { text-align: right; font-size: 34rpx; color: rgba(255,255,255,.75); }
.title { font-size: 34rpx; font-weight: 900; color: #69ff4b; }
.progress-card {
	position: relative;
	margin: 34rpx 0 34rpx;
	padding: 32rpx;
	border-radius: 18rpx;
	overflow: hidden;
	background: #202522;
}
.label { font-size: 22rpx; color: rgba(204,255,194,.82); }
.score { margin-top: 12rpx; }
.done { font-size: 56rpx; line-height: 1; font-weight: 900; color: #5dff49; }
.total { font-size: 32rpx; font-weight: 800; }
.star {
	position: absolute;
	right: 26rpx;
	top: 42rpx;
	width: 118rpx;
	height: 118rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(255,255,255,.08);
	color: rgba(255,255,255,.13);
	font-size: 70rpx;
}
.progress { height: 6rpx; margin-top: 30rpx; background: rgba(255,255,255,.14); border-radius: 999rpx; overflow: hidden; }
.fill { width: 38%; height: 100%; background: #69ff4b; }
.badge-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 24rpx; }
.badge-card {
	min-height: 210rpx;
	padding: 26rpx 18rpx;
	border-radius: 14rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	background: #171c19;
	border: 1rpx solid rgba(105,255,75,.22);
}
.badge-card.locked { opacity: .46; border-color: rgba(255,255,255,.06); }
.icon-wrap { position: relative; width: 96rpx; height: 96rpx; border-radius: 50%; display:flex; align-items:center; justify-content:center; background: rgba(105,255,75,.16); box-shadow: 0 0 34rpx rgba(105,255,75,.28); }
.icon { color: #69ff4b; font-size: 48rpx; font-weight: 900; }
.check { position:absolute; right:-2rpx; top:-8rpx; width:34rpx; height:46rpx; border-radius:999rpx; display:flex; align-items:center; justify-content:center; background:#69ff4b; color:#082008; font-size:22rpx; font-weight:900; }
.locked .check { background: rgba(255,255,255,.12); color: rgba(255,255,255,.5); }
.badge-name { margin-top: 22rpx; font-size: 24rpx; font-weight: 900; }
.badge-desc { margin-top: 6rpx; font-size: 20rpx; color: rgba(255,255,255,.55); text-align:center; }
</style>
