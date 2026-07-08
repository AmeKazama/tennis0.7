<template>
	<view class="page">
		<view class="top-bar">
			<text class="back" @tap="goBack">‹</text>
			<text class="title">智能设备</text>
			<view class="icons"><text>⟳</text><text>♧</text></view>
		</view>

		<view class="radar">
			<view class="ring r1"></view><view class="ring r2"></view><view class="ring r3"></view>
			<text class="signal">⌁</text>
		</view>
		<text class="scan-title">正在扫描设备...</text>
		<text class="scan-sub">请确保您的蓝牙已开启</text>

		<view class="section-head">
			<text>已连接设备</text><text>2台在线</text>
		</view>
		<view class="device-card" v-for="item in devices" :key="item.name" :class="{ off: !item.online }">
			<view class="device-icon">{{ item.icon }}</view>
			<view class="main">
				<text class="name">{{ item.name }}</text>
				<text class="status"><text class="dot"></text>{{ item.online ? '已连接' : '离线' }}</text>
			</view>
			<view class="right">
				<text class="battery">{{ item.battery }}</text>
				<text class="action">{{ item.online ? item.action : '重新连接' }}</text>
			</view>
		</view>
	</view>
</template>

<script setup>
const devices = [
	{ name: 'Apex Pro Watch', icon: '◉', battery: '12%', action: '设置', online: true },
	{ name: 'Smart Sensor V3', icon: '⌕', battery: '98%', action: '数据', online: true },
	{ name: 'CourtCam X1', icon: '⌁', battery: '', action: '重新连接', online: false }
]
const goBack = () => uni.navigateBack()
</script>

<style scoped>
.page { min-height:100vh; box-sizing:border-box; padding:var(--status-bar-height) 26rpx 50rpx; background:linear-gradient(180deg, rgba(255,255,255,.16), #0b0f0d 150rpx); color:#fff; }
.top-bar { height:78rpx; display:flex; align-items:center; justify-content:space-between; }
.back { width:60rpx; color:#69ff4b; font-size:48rpx; }
.title { flex:1; color:#69ff4b; font-size:34rpx; font-weight:900; }
.icons { display:flex; gap:28rpx; color:rgba(255,255,255,.75); font-size:34rpx; }
.radar { position:relative; width:390rpx; height:390rpx; margin:70rpx auto 38rpx; display:flex; align-items:center; justify-content:center; }
.ring { position:absolute; border-radius:50%; border:2rpx solid rgba(105,255,75,.24); box-shadow:0 0 18rpx rgba(105,255,75,.16); }
.r1 { width:390rpx; height:390rpx; }.r2 { width:260rpx; height:260rpx; }.r3 { width:132rpx; height:132rpx; background:rgba(105,255,75,.11); }
.signal { z-index:2; font-size:62rpx; color:#69ff4b; font-weight:900; }
.scan-title { display:block; text-align:center; font-size:42rpx; font-weight:900; }
.scan-sub { display:block; margin-top:12rpx; text-align:center; color:#d8ffbf; font-size:26rpx; }
.section-head { display:flex; justify-content:space-between; margin:78rpx 0 22rpx; color:#69ff4b; font-size:23rpx; font-weight:800; }
.device-card { display:flex; align-items:center; gap:20rpx; margin-bottom:18rpx; padding:20rpx 24rpx; border-radius:16rpx; background:#1a201d; border:1rpx solid rgba(255,255,255,.06); }
.device-card.off { opacity:.5; }
.device-icon { width:80rpx; height:80rpx; border-radius:12rpx; display:flex; align-items:center; justify-content:center; background:rgba(255,255,255,.08); color:#69ff4b; font-size:36rpx; }
.main { flex:1; display:flex; flex-direction:column; gap:8rpx; }
.name { font-size:30rpx; font-weight:900; }
.status { font-size:22rpx; color:rgba(255,255,255,.65); }
.dot { display:inline-block; width:12rpx; height:12rpx; margin-right:8rpx; border-radius:50%; background:#69ff4b; }
.right { display:flex; flex-direction:column; align-items:flex-end; gap:8rpx; }
.battery { color:#69ff4b; font-size:24rpx; font-weight:900; }
.action { color:#d8ffbf; font-size:20rpx; }
</style>
