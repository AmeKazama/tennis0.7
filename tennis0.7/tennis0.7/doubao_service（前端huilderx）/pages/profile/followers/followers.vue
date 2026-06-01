<template>
	<view class="page">
		<view class="top-bar"><text class="back" @tap="goBack">‹</text><text class="title">关注者</text><text class="more">⋮</text></view>
		<view class="search">⌕　搜索关注者...</view>
		<view class="user-card" v-for="user in users" :key="user.name">
			<view class="avatar-wrap"><image class="avatar" :src="user.avatar" mode="aspectFill"></image><text class="online"></text></view>
			<view class="info"><text class="name">{{ user.name }}</text><text class="meta">{{ user.level }} · {{ user.distance }}</text></view>
			<view class="btn" :class="{ active: !user.mutual }">{{ user.mutual ? '彳 相互关注' : '+ 回关' }}</view>
		</view>
	</view>
</template>
<script setup>
const users = [
	{ name:'Alex Zhang', level:'NTRP4.5', distance:'3.2km', mutual:true, avatar:'https://i.pravatar.cc/120?u=alexz' },
	{ name:'Sarah Tennis', level:'NTRP5.0', distance:'1.5km', avatar:'https://i.pravatar.cc/120?u=sarah' },
	{ name:'Li Wei', level:'NTRP3.5', distance:'8.0km', mutual:true, avatar:'https://i.pravatar.cc/120?u=liwei' },
	{ name:'Chloe Ace', level:'NTRP4.0', distance:'5.4km', avatar:'https://i.pravatar.cc/120?u=chloe' },
	{ name:'Jordan Smash', level:'NTRP4.5', distance:'12km', avatar:'https://i.pravatar.cc/120?u=jordans' }
]
const goBack = () => uni.navigateBack()
</script>
<style scoped>
.page{min-height:100vh;box-sizing:border-box;padding:var(--status-bar-height) 26rpx 50rpx;background:#0b0f0d;color:#fff}.top-bar{height:76rpx;display:flex;align-items:center;justify-content:space-between}.back,.more{width:60rpx;color:#69ff4b;font-size:46rpx}.more{text-align:right;color:rgba(255,255,255,.7);font-size:34rpx}.title{color:#69ff4b;font-size:34rpx;font-weight:900}.search{height:100rpx;border-radius:16rpx;margin:22rpx 0 34rpx;padding:0 30rpx;display:flex;align-items:center;background:#242826;color:rgba(255,255,255,.32);font-size:25rpx}.user-card{display:flex;align-items:center;gap:20rpx;margin-bottom:16rpx;padding:24rpx;border-radius:18rpx;background:#1a201d}.avatar-wrap{position:relative;width:78rpx;height:78rpx}.avatar{width:100%;height:100%;border-radius:50%;border:2rpx solid rgba(105,255,75,.65)}.online{position:absolute;right:0;bottom:4rpx;width:20rpx;height:20rpx;border-radius:50%;background:#69ff4b}.info{flex:1;display:flex;flex-direction:column;gap:10rpx}.name{font-size:28rpx;font-weight:900}.meta{font-size:19rpx;color:#d8ffbf}.btn{min-width:126rpx;height:72rpx;border-radius:10rpx;display:flex;align-items:center;justify-content:center;background:#3a3f3d;color:#dfffd8;font-size:25rpx;font-weight:800}.btn.active{background:#69ff4b;color:#061606;box-shadow:0 0 22rpx rgba(105,255,75,.45)}
</style>
