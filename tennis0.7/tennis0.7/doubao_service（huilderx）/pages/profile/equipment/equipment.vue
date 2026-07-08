<template>
	<view class="page">
		<view class="top-bar"><text class="back" @tap="goBack">‹</text><text class="title">我的装备</text><text class="bell">♧</text></view>
		<view class="head-row"><view><text class="main-title">Equipment Bag</text><text class="sub">Active setups for competitive play</text></view><view class="add">＋ ADD</view></view>
		<view class="racket-card">
			<image class="racket-img" src="/static/media/felix1999-tennis-ball-4716315_1920.jpg" mode="aspectFill"></image>
			<text class="primary">PRIMARY</text>
			<text class="brand">WILSON PRO STAFF</text>
			<text class="model">v14 Night Session</text>
			<view class="specs"><view><text>TENSION</text><text class="spec-value">52 lbs</text></view><view><text>WEIGHT</text><text class="spec-value">315g</text></view><view><text>PATTERN</text><text class="spec-value">16x19</text></view></view>
			<text class="note">⚡ Strung with Luxilon ALU Power 1.25</text>
		</view>
		<view class="string-card">
			<view class="brand-mark">APERTURE</view><text class="kicker">Strings Inventory</text><text class="string-name">Solinco Hyper-G</text><text class="sub">1.20mm / 18 Gauge</text>
			<view class="stock"><text>Remaining: 4 full sets</text><view><view></view></view></view>
		</view>
	</view>
</template>
<script setup>
const goBack = () => uni.navigateBack()
</script>
<style scoped>
.page{min-height:100vh;box-sizing:border-box;padding:var(--status-bar-height) 26rpx 60rpx;background:#0b0f0d;color:#fff}.top-bar{height:76rpx;display:flex;align-items:center;justify-content:space-between}.back,.bell{width:60rpx;color:#69ff4b;font-size:46rpx}.bell{text-align:right;color:rgba(255,255,255,.75);font-size:34rpx}.title{flex:1;color:#69ff4b;font-size:32rpx;font-weight:900}.head-row{display:flex;justify-content:space-between;align-items:center;margin:34rpx 0 24rpx}.main-title{display:block;font-size:38rpx;font-weight:900}.sub{display:block;color:#d9ffd0;font-size:22rpx;margin-top:6rpx}.add{height:72rpx;padding:0 24rpx;border-radius:14rpx;display:flex;align-items:center;background:#69ff4b;color:#061606;font-size:24rpx;font-weight:900}.racket-card,.string-card{position:relative;margin-bottom:22rpx;padding:24rpx;border-radius:18rpx;background:#1a201d;border:1rpx solid rgba(105,255,75,.35);box-shadow:0 0 24rpx rgba(105,255,75,.1)}.racket-img{width:100%;height:280rpx;border-radius:10rpx;background:#111}.primary{position:absolute;right:36rpx;top:40rpx;padding:6rpx 14rpx;border-radius:999rpx;background:rgba(105,255,75,.28);color:#bfffaa;font-size:17rpx;font-weight:900}.brand{display:block;margin-top:24rpx;color:#69ff4b;font-size:22rpx;font-weight:900}.model{display:block;margin-top:10rpx;font-size:31rpx;font-weight:900;color:rgba(255,255,255,.82)}.specs{display:flex;gap:38rpx;margin:24rpx 0}.specs view{display:flex;flex-direction:column;gap:4rpx}.specs text{font-size:16rpx;color:rgba(255,255,255,.45)}.specs .spec-value{font-size:24rpx;color:#fff;font-weight:900}.note{font-size:21rpx;color:#d9ffd0;font-weight:800}.brand-mark{display:inline-flex;padding:10rpx 22rpx;margin-bottom:28rpx;border-radius:4rpx;background:rgba(105,255,75,.12);color:#69ff4b;font-size:36rpx;letter-spacing:2rpx}.kicker{display:block;color:rgba(255,255,255,.55);font-size:22rpx}.string-name{display:block;margin-top:6rpx;font-size:31rpx;font-weight:900}.stock{margin-top:42rpx;padding-top:20rpx;border-top:1rpx solid rgba(255,255,255,.06);display:flex;align-items:center;justify-content:space-between;font-size:19rpx;color:#fff}.stock>view{width:112rpx;height:8rpx;border-radius:999rpx;background:rgba(255,255,255,.12);overflow:hidden}.stock>view>view{width:72%;height:100%;background:#69ff4b}
</style>
