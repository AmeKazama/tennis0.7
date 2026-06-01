<template>
	<view class="app-bottom-nav">
		<view
			v-for="(item, index) in tabList"
			:key="item.key"
			class="nav-item"
			:class="{ active: active === item.key, center: index === 2 }"
			@tap="switchTab(item)"
		>
			<view v-if="index === 2" class="center-button">
				<view class="play-icon"></view>
			</view>
			<template v-else>
				<image class="nav-icon" :src="item.icon" mode="aspectFit"></image>
			</template>
			<text class="nav-label">{{ item.label }}</text>
		</view>
	</view>
</template>

<script setup>
defineProps({
	active: {
		type: String,
		default: 'home'
	}
})

const tabList = [
	{ key: 'home', label: '首页', path: '/pages/tabbar/index/index', icon: '/static/coach/首页.png' },
	{ key: 'record', label: '社交圈', path: '/pages/tabbar/record/record', icon: '/static/coach/社交圈白.png' },
	{ key: 'review', label: '复盘', path: '/pages/tabbar/ai-coach-select/ai-coach-select', icon: '' },
	{ key: 'data', label: '数据', path: '/pages/tabbar/data/data', icon: '/static/coach/数据白.png' },
	{ key: 'profile', label: '我的', path: '/pages/tabbar/profile/profile', icon: '/static/coach/我的.png' }
]

const switchTab = (item) => {
	uni.reLaunch({
		url: item.path
	})
}
</script>

<style scoped>
.app-bottom-nav {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 1000;
	--tab-center-size: 104rpx;
	--tab-center-icon-width: 22rpx;
	--tab-center-icon-height: 15rpx;
	box-sizing: border-box;
	height: calc(126rpx + env(safe-area-inset-bottom));
	padding: 10rpx 24rpx calc(10rpx + env(safe-area-inset-bottom));
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	background: #000;
	border-top: 1rpx solid rgba(255, 255, 255, 0.14);
}

.nav-item {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 4rpx;
	padding-top: 10rpx;
	color: rgba(222, 255, 154, 0.48);
	position: relative;
}

.nav-item.active:not(.center)::before {
	content: '';
	position: absolute;
	top: 0;
	width: 38rpx;
	height: 4rpx;
	border-radius: 999rpx;
	background: #deff9a;
	box-shadow: 0 0 12rpx rgba(222, 255, 154, 0.62);
}

.nav-icon {
	width: 40rpx;
	height: 40rpx;
	opacity: 0.42;
}

.nav-item.active .nav-icon {
	opacity: 1;
}

.nav-label {
	font-size: 18rpx;
	line-height: 1.2;
	color: currentColor;
}

.nav-item.active {
	color: #deff9a;
}

.nav-item.center {
	margin-top: -28rpx;
	gap: 6rpx;
	color: #deff9a;
}

.center-button {
	width: var(--tab-center-size);
	height: var(--tab-center-size);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	background: linear-gradient(135deg, #deff9a 0%, #c8ff6d 100%);
	border: 4rpx solid #000;
	box-shadow: 0 0 28rpx rgba(222, 255, 154, 0.82);
}

.play-icon {
	width: 0;
	height: 0;
	margin-left: 6rpx;
	border-left: var(--tab-center-icon-width) solid #000;
	border-top: var(--tab-center-icon-height) solid transparent;
	border-bottom: var(--tab-center-icon-height) solid transparent;
}
</style>
