<template>
	<view class="container">
		<view class="navbar">
			<view class="back" @tap="goBack">←</view>
			<text class="title">单次动作指导</text>
			<view class="nav-icon">⏱️</view>
		</view>

		<view class="content">
			<view class="card">
				<view class="card-header">
					<text class="card-title">当前运动类型</text>
					<view class="sport-type">
						<text class="sport-icon">🎾</text>
						<text class="sport-name">网球</text>
					</view>
				</view>
			</view>

			<view class="card">
				<view class="card-header">
					<text class="card-title">分析内容</text>
				</view>
				<view class="analysis-items">
					<view class="analysis-item">
						<view class="analysis-icon">
							<text class="analysis-emoji">📊</text>
						</view>
						<text class="analysis-label">维度评分</text>
					</view>
					<view class="analysis-item">
						<view class="analysis-icon">
							<text class="analysis-emoji">🏃</text>
						</view>
						<text class="analysis-label">动作分析</text>
					</view>
					<view class="analysis-item">
						<view class="analysis-icon">
							<text class="analysis-emoji">⚡</text>
						</view>
						<text class="analysis-label">节奏战术</text>
					</view>
				</view>
			</view>

			<view class="card">
				<view class="card-header">
					<text class="card-title">注意事项</text>
				</view>
				<view class="notes">
					<view class="note-item">
						<text class="note-dot">●</text>
						<text class="note-text">分析视频不能超过 60 秒。</text>
					</view>
					<view class="note-item">
						<text class="note-dot">●</text>
						<text class="note-text">超过 60 秒将先裁剪后分析。</text>
					</view>
				</view>
			</view>
		</view>

		<view class="bottom-btn" :class="{ active: btnActive }" @touchstart="btnActive = true" @touchend="btnActive = false" @tap="showUploadOptions">
			<text class="btn-icon">📹</text>
			<text class="btn-text">选择视频</text>
		</view>

		<view class="popup-mask" v-if="showPopup" @tap="closePopup"></view>
		<view class="popup-content" :class="{ show: showPopup }">
			<view class="popup-header">
				<view class="popup-handle"></view>
				<text class="popup-title">选择视频来源</text>
			</view>
			<view class="popup-options">
				<view class="option-item" @tap="recordVideo">
					<view class="option-icon-wrapper">
						<text class="option-icon">🎥</text>
					</view>
					<view class="option-info">
						<text class="option-label">直接录制</text>
						<text class="option-desc">现场录制视频</text>
					</view>
					<text class="option-arrow">›</text>
				</view>
				<view class="option-divider"></view>
				<view class="option-item" @tap="importVideo">
					<view class="option-icon-wrapper">
						<text class="option-icon">📂</text>
					</view>
					<view class="option-info">
						<text class="option-label">导入视频</text>
						<text class="option-desc">从相册选择视频</text>
					</view>
					<text class="option-arrow">›</text>
				</view>
			</view>
			<view class="cancel-btn" @tap="closePopup">取消</view>
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue';

const btnActive = ref(false);
const showPopup = ref(false);

const goBack = () => {
	uni.navigateBack();
};

const showUploadOptions = () => {
	showPopup.value = true;
};

const closePopup = () => {
	showPopup.value = false;
};

const goToCoachTest = (source) => {
	uni.setStorageSync('coachVideoSource', source);
	uni.navigateTo({
		url: `/pages/ai-coach/coach-test/coach-test?mode=video&source=${source}`
	});
};

const recordVideo = () => {
	closePopup();
	goToCoachTest('camera');
};

const importVideo = () => {
	closePopup();
	goToCoachTest('album');
};
</script>

<style>
.container {
	background: linear-gradient(180deg, #0c1528 0%, #000 100%);
	min-height: 100vh;
	padding: 0 32rpx;
	padding-bottom: 220rpx;
	position: relative;
}

.navbar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 40rpx;
	padding-top: var(--status-bar-height);
}

.back {
	font-size: 40rpx;
	color: #fff;
}

.title {
	font-size: 36rpx;
	font-weight: bold;
	color: #fff;
}

.nav-icon {
	width: 64rpx;
	height: 64rpx;
	background: rgba(255, 255, 255, 0.1);
	border-radius: 32rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 28rpx;
}

.content {
	padding-bottom: 40rpx;
}

.card {
	background: rgba(255, 255, 255, 0.05);
	border-radius: 24rpx;
	padding: 32rpx;
	margin-bottom: 24rpx;
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24rpx;
}

.card-title {
	font-size: 32rpx;
	font-weight: 600;
	color: #fff;
}

.sport-type {
	display: flex;
	align-items: center;
	gap: 8rpx;
	color: #60a5fa;
}

.sport-icon {
	font-size: 28rpx;
}

.sport-name {
	font-size: 28rpx;
	font-weight: 500;
}

.analysis-items {
	display: flex;
	justify-content: space-around;
}

.analysis-item {
	display: flex;
	flex-direction: column;
	align-items: center;
}

.analysis-icon {
	width: 120rpx;
	height: 120rpx;
	background: rgba(96, 165, 250, 0.1);
	border-radius: 60rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 16rpx;
}

.analysis-emoji {
	font-size: 56rpx;
}

.analysis-label {
	font-size: 26rpx;
	color: #fff;
}

.notes {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.note-item {
	display: flex;
	align-items: flex-start;
	gap: 12rpx;
}

.note-dot {
	font-size: 24rpx;
	color: #888;
	line-height: 1.6;
}

.note-text {
	flex: 1;
	font-size: 26rpx;
	color: #ccc;
	line-height: 1.6;
}

.bottom-btn {
	position: fixed;
	bottom: 40rpx;
	left: 32rpx;
	right: 32rpx;
	background: var(--primary-green);
	border-radius: 28rpx;
	padding: 32rpx 0;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
	z-index: 100;
	box-shadow: 0 0 40rpx rgba(222, 255, 154, 0.5);
	transition: transform 0.15s ease;
	padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
}

.btn-icon {
	font-size: 32rpx;
}

.bottom-btn.active {
	transform: scale(0.95);
}

.btn-text {
	font-size: 32rpx;
	color: #000;
	font-weight: bold;
}

.popup-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.6);
	z-index: 999;
	backdrop-filter: blur(10rpx);
}

.popup-content {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
	border-radius: 48rpx 48rpx 0 0;
	padding: 32rpx 32rpx calc(32rpx + env(safe-area-inset-bottom));
	z-index: 1000;
	transform: translateY(100%);
	transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
	box-shadow: 0 -20rpx 60rpx rgba(0, 0, 0, 0.5);
}

.popup-content.show {
	transform: translateY(0);
}

.popup-header {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-bottom: 32rpx;
}

.popup-handle {
	width: 80rpx;
	height: 8rpx;
	background: rgba(255, 255, 255, 0.2);
	border-radius: 4rpx;
	margin-bottom: 24rpx;
}

.popup-title {
	font-size: 32rpx;
	font-weight: 600;
	color: #fff;
}

.popup-options {
	background: rgba(255, 255, 255, 0.03);
	border-radius: 24rpx;
	padding: 8rpx 0;
	margin-bottom: 24rpx;
	border: 1rpx solid rgba(255, 255, 255, 0.05);
}

.option-item {
	display: flex;
	align-items: center;
	padding: 28rpx 32rpx;
	transition: background 0.2s;
}

.option-item:active {
	background: rgba(255, 255, 255, 0.05);
}

.option-icon-wrapper {
	width: 96rpx;
	height: 96rpx;
	background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(37, 99, 235, 0.1));
	border-radius: 24rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 24rpx;
	border: 1rpx solid rgba(59, 130, 246, 0.2);
}

.option-icon {
	font-size: 44rpx;
}

.option-info {
	flex: 1;
	display: flex;
	flex-direction: column;
}

.option-label {
	font-size: 30rpx;
	font-weight: 500;
	color: #fff;
	margin-bottom: 6rpx;
}

.option-desc {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.5);
}

.option-arrow {
	font-size: 40rpx;
	color: rgba(255, 255, 255, 0.3);
	font-weight: 300;
}

.option-divider {
	height: 1rpx;
	background: rgba(255, 255, 255, 0.08);
	margin: 0 32rpx;
}

.cancel-btn {
	background: rgba(255, 255, 255, 0.08);
	border-radius: 24rpx;
	padding: 28rpx 0;
	text-align: center;
	font-size: 30rpx;
	color: #fff;
	font-weight: 500;
	transition: background 0.2s;
	border: 1rpx solid rgba(255, 255, 255, 0.1);
}

.cancel-btn:active {
	background: rgba(255, 255, 255, 0.12);
}
</style>
