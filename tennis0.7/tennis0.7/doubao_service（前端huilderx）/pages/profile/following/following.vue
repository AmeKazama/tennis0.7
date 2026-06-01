<template>
	<view class="page">
		<view class="top-bar"><text class="back" @tap="goBack">‹</text><text class="title">关注</text><text class="search-icon">⌕</text></view>
		<view class="tabs"><text v-for="tab in tabs" :key="tab" :class="{active:active===tab}" @tap="active=tab">{{tab}}</text></view>
		<view class="user-card" v-for="user in following" :key="user.name">
			<view class="avatar-wrap"><image class="avatar" :src="user.avatar" mode="aspectFill"></image><text class="online"></text></view>
			<view class="info"><text class="name">{{user.name}}</text><text class="meta">{{user.level}} · {{user.place}}</text></view>
			<view class="followed">已关注</view>
		</view>
		<text class="recommend-title">推荐关注</text>
		<view class="recommend" v-for="user in recommends" :key="user.name">
			<image class="small-avatar" :src="user.avatar" mode="aspectFill"></image>
			<view class="info"><text class="name">{{user.name}}</text><text class="meta">{{user.desc}}</text></view>
			<view class="green-btn">关注</view>
		</view>
	</view>
</template>
<script setup>
import { ref } from 'vue'
const active = ref('全部')
const tabs = ['全部','球友','教练','俱乐部']
const following = [
	{ name:'Alex Rivera', level:'NTRP5.0', place:'北京市 · 钻石球场', avatar:'https://i.pravatar.cc/120?u=rivera' },
	{ name:'Chloe Wang', level:'NTRP4.5', place:'上海市 · 旗舰网球中心', avatar:'https://i.pravatar.cc/120?u=wang' },
	{ name:'Marco Santoro', level:'NTRP5.0', place:'广州市 · 体育中心', avatar:'https://i.pravatar.cc/120?u=marco' },
	{ name:'David Chen', level:'NTRP3.5', place:'深圳市 · 龙岗赛场', avatar:'https://i.pravatar.cc/120?u=david' },
	{ name:'Coach Sarah', level:'ELITE COACH', place:'北京市 · 国家网球中心', avatar:'https://i.pravatar.cc/120?u=coachsarah' }
]
const recommends = [{ name:'Jordan Mills', desc:'根据你的水平推荐 · NTRP 4.0', avatar:'https://i.pravatar.cc/120?u=mills' }]
const goBack = () => uni.navigateBack()
</script>
<style scoped>
.page{min-height:100vh;box-sizing:border-box;padding:var(--status-bar-height) 26rpx 50rpx;background:#0b0f0d;color:#fff}.top-bar{height:76rpx;display:flex;align-items:center;justify-content:space-between}.back,.search-icon{width:60rpx;color:#69ff4b;font-size:46rpx}.search-icon{text-align:right;font-size:34rpx}.title{color:#69ff4b;font-size:34rpx;font-weight:900}.tabs{display:flex;gap:18rpx;margin:18rpx 0 28rpx}.tabs text{padding:14rpx 26rpx;border-radius:999rpx;background:#232826;color:#d8dfda;font-size:24rpx;font-weight:800}.tabs .active{background:#69ff4b;color:#061606}.user-card,.recommend{display:flex;align-items:center;gap:20rpx;margin-bottom:18rpx;padding:22rpx;border-radius:18rpx;background:#1a201d}.avatar-wrap{position:relative;width:76rpx;height:76rpx}.avatar,.small-avatar{width:100%;height:100%;border-radius:50%;border:2rpx solid rgba(105,255,75,.65)}.small-avatar{width:66rpx;height:66rpx}.online{position:absolute;right:0;bottom:4rpx;width:19rpx;height:19rpx;border-radius:50%;background:#69ff4b}.info{flex:1;min-width:0;display:flex;flex-direction:column;gap:9rpx}.name{font-size:29rpx;font-weight:900}.meta{font-size:19rpx;color:#d8ffbf}.followed{width:116rpx;height:62rpx;border-radius:10rpx;display:flex;align-items:center;justify-content:center;background:#3a3f3d;color:#fff;font-size:24rpx;font-weight:800}.recommend-title{display:block;margin:42rpx 0 24rpx;color:#69ff4b;font-size:40rpx;font-weight:900}.green-btn{width:116rpx;height:58rpx;border-radius:999rpx;display:flex;align-items:center;justify-content:center;background:#69ff4b;color:#061606;font-size:24rpx;font-weight:900}
</style>
