<template>
	<view class="edit-page">
		<view class="top-bar">
			<view class="nav-btn" @tap="goBack">‹</view>
			<text class="page-title">编辑个人资料</text>
			<view class="save-btn" @tap="saveProfile">保存</view>
		</view>

		<view class="avatar-section">
			<view class="avatar-ring" @tap="chooseAvatar">
				<image class="avatar" :src="profile.avatar" mode="aspectFill"></image>
				<view class="camera-badge">
					<text class="camera-icon">▣</text>
				</view>
			</view>
		</view>

		<view class="form-card intro-card">
			<view class="field-block">
				<text class="field-label">昵称</text>
				<view class="field-line">
					<input class="field-input" v-model="profile.nickname" />
					<text class="edit-icon">✎</text>
				</view>
			</view>

			<view class="field-block">
				<text class="field-label">简介</text>
				<textarea class="bio-input" v-model="profile.bio" maxlength="80" />
			</view>
		</view>

		<view class="form-card">
			<view class="row-item" @tap="showGenderPicker">
				<text class="row-label">性别</text>
				<view class="row-right">
					<text class="row-value">{{ profile.gender }}</text>
					<text class="row-arrow">›</text>
				</view>
			</view>
			<view class="row-divider"></view>
			<view class="row-item" @tap="showRegionPicker">
				<text class="row-label">地区</text>
				<view class="row-right">
					<text class="row-value">{{ profile.region }}</text>
					<text class="row-arrow">›</text>
				</view>
			</view>
		</view>

		<text class="section-title">网球偏好</text>

		<view class="form-card preference-card">
			<view class="preference-row">
				<view class="preference-info">
					<text class="field-label">网球等级</text>
					<text class="preference-value">Amateur Level 3</text>
				</view>
				<view class="rating-pill">NTRP 3.0</view>
			</view>

			<view class="preference-row last">
				<view class="preference-info">
					<text class="field-label">惯用手</text>
					<text class="preference-value">右手球员 (Right-handed)</text>
				</view>
				<text class="check-icon">✓</text>
			</view>
		</view>

		<AppBottomNav active="profile" />
	</view>
</template>

<script setup>
import { reactive } from 'vue'
import AppBottomNav from '@/components/AppBottomNav/AppBottomNav.vue'
import { getProfile, regionTree, updateProfile } from '@/utils/social-store/index.js'

const profile = reactive(getProfile())

const goBack = () => {
	uni.navigateBack()
}

const saveProfile = () => {
	updateProfile(profile)
	uni.showToast({
		title: '已保存',
		icon: 'success'
	})
	setTimeout(() => {
		uni.navigateBack()
	}, 500)
}

const chooseAvatar = () => {
	uni.showActionSheet({
		itemList: ['从相册选择', '本机摄像头'],
		success: (res) => {
			uni.chooseImage({
				count: 1,
				sourceType: [res.tapIndex === 0 ? 'album' : 'camera'],
				success: (imageRes) => {
					const path = imageRes.tempFilePaths && imageRes.tempFilePaths[0]
					if (path) profile.avatar = path
				}
			})
		}
	})
}

const showGenderPicker = () => {
	uni.showActionSheet({
		itemList: ['男', '女', '保密'],
		success: (res) => {
			profile.gender = ['男', '女', '保密'][res.tapIndex]
		}
	})
}

const showRegionPicker = () => {
	const countries = Object.keys(regionTree)
	uni.showActionSheet({
		itemList: countries,
		success: (countryRes) => {
			const country = countries[countryRes.tapIndex]
			const cities = regionTree[country]
			uni.showActionSheet({
				itemList: cities,
				success: (cityRes) => {
					profile.region = `${country}, ${cities[cityRes.tapIndex]}`
				}
			})
		}
	})
}
</script>

<style scoped>
.edit-page {
	min-height: 100vh;
	box-sizing: border-box;
	padding: 0 28rpx;
	padding-top: var(--status-bar-height);
	padding-bottom: calc(126rpx + env(safe-area-inset-bottom));
	color: #fff;
	background:
		linear-gradient(180deg, rgba(255, 255, 255, 0.32) 0, rgba(13, 15, 15, 0.88) 92rpx, #0b0f0d 220rpx),
		#0b0f0d;
}

.top-bar {
	height: 88rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.nav-btn,
.save-btn {
	width: 90rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
}

.nav-btn {
	font-size: 52rpx;
	color: rgba(255, 255, 255, 0.92);
}

.page-title {
	flex: 1;
	text-align: center;
	font-size: 31rpx;
	font-weight: 800;
	color: rgba(255, 255, 255, 0.92);
}

.save-btn {
	justify-content: flex-end;
	font-size: 29rpx;
	font-weight: 800;
	color: #78ff5b;
}

.avatar-section {
	display: flex;
	justify-content: center;
	padding: 34rpx 0 62rpx;
}

.avatar-ring {
	position: relative;
	width: 148rpx;
	height: 148rpx;
	border-radius: 50%;
	border: 4rpx solid #22ff24;
	box-shadow: 0 0 24rpx rgba(34, 255, 36, 0.95), 0 0 52rpx rgba(34, 255, 36, 0.45);
}

.avatar {
	width: 100%;
	height: 100%;
	border-radius: 50%;
	background: #121718;
}

.camera-badge {
	position: absolute;
	right: -6rpx;
	bottom: 4rpx;
	width: 38rpx;
	height: 38rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #001900;
	font-size: 20rpx;
	font-weight: 900;
	background: #25ff2e;
	box-shadow: 0 0 16rpx rgba(37, 255, 46, 0.8);
}

.form-card {
	border-radius: 16rpx;
	background: #1c2220;
	overflow: hidden;
	margin-bottom: 28rpx;
}

.intro-card {
	padding: 30rpx 24rpx;
}

.field-block + .field-block {
	margin-top: 38rpx;
}

.field-label {
	display: block;
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.45);
	margin-bottom: 14rpx;
}

.field-line {
	display: flex;
	align-items: center;
	gap: 20rpx;
}

.field-input {
	flex: 1;
	height: 42rpx;
	color: rgba(255, 255, 255, 0.9);
	font-size: 28rpx;
}

.edit-icon {
	color: rgba(255, 255, 255, 0.48);
	font-size: 28rpx;
}

.bio-input {
	width: 100%;
	height: 74rpx;
	color: rgba(255, 255, 255, 0.9);
	font-size: 27rpx;
	line-height: 1.45;
}

.row-item {
	height: 104rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 24rpx;
}

.row-label {
	font-size: 23rpx;
	color: rgba(255, 255, 255, 0.45);
}

.row-right {
	display: flex;
	align-items: center;
	gap: 14rpx;
}

.row-value {
	font-size: 27rpx;
	color: rgba(255, 255, 255, 0.88);
}

.row-arrow {
	font-size: 34rpx;
	color: rgba(255, 255, 255, 0.44);
}

.row-divider {
	height: 1rpx;
	margin-left: 24rpx;
	background: rgba(255, 255, 255, 0.04);
}

.section-title {
	display: block;
	margin: 36rpx 0 22rpx;
	font-size: 27rpx;
	font-weight: 800;
	color: rgba(255, 255, 255, 0.9);
}

.preference-card {
	padding: 0 24rpx;
}

.preference-row {
	min-height: 104rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.preference-row.last {
	border-top: 1rpx solid rgba(255, 255, 255, 0.04);
}

.preference-info {
	display: flex;
	flex-direction: column;
}

.preference-value {
	font-size: 27rpx;
	color: rgba(255, 255, 255, 0.9);
}

.rating-pill {
	padding: 8rpx 16rpx;
	border-radius: 999rpx;
	border: 2rpx solid #23ff24;
	color: #23ff24;
	font-size: 22rpx;
	font-weight: 800;
	box-shadow: 0 0 16rpx rgba(35, 255, 36, 0.28);
}

.check-icon {
	width: 30rpx;
	height: 30rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	border: 2rpx solid rgba(255, 255, 255, 0.56);
	color: rgba(255, 255, 255, 0.78);
	font-size: 20rpx;
}

.bottom-nav {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	height: calc(106rpx + env(safe-area-inset-bottom));
	box-sizing: border-box;
	padding: 12rpx 42rpx calc(12rpx + env(safe-area-inset-bottom));
	display: flex;
	align-items: center;
	justify-content: space-between;
	background: #070909;
	border-top: 1rpx solid rgba(255, 255, 255, 0.06);
}

.bottom-item {
	width: 72rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 4rpx;
	color: rgba(218, 236, 214, 0.78);
}

.bottom-item.active {
	color: #23ff24;
}

.bottom-icon {
	font-size: 30rpx;
	line-height: 1;
}

.bottom-label {
	font-size: 19rpx;
}

.bottom-add {
	width: 74rpx;
	height: 74rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #020802;
	font-size: 48rpx;
	font-weight: 900;
	background: #2cff30;
	box-shadow: 0 0 24rpx rgba(44, 255, 48, 0.9);
}
</style>
