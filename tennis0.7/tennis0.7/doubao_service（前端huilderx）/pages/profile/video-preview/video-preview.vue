<template>
	<view class="preview-page">
		<view class="header">
			<view class="back-btn" @tap="goBack">←</view>
			<text class="title">{{ title }}</text>
			<view class="header-space"></view>
		</view>

		<video
			v-if="videoSrc"
			class="preview-video"
			:src="videoSrc"
			:controls="true"
			:autoplay="true"
			object-fit="contain"
		></video>
	</view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const videoSrc = ref('')
const title = ref('训练记录')

const goBack = () => {
	uni.navigateBack()
}

onLoad((options) => {
	videoSrc.value = decodeURIComponent(options.src || '')
	title.value = decodeURIComponent(options.title || '训练记录')
})
</script>

<style scoped>
.preview-page {
	min-height: 100vh;
	background: #000;
	color: #fff;
	padding-top: var(--status-bar-height);
}

.header {
	height: 96rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 28rpx;
}

.back-btn,
.header-space {
	width: 72rpx;
	height: 72rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 40rpx;
}

.title {
	flex: 1;
	text-align: center;
	font-size: 30rpx;
	font-weight: 700;
	color: var(--primary-green);
}

.preview-video {
	width: 100vw;
	height: calc(100vh - var(--status-bar-height) - 96rpx);
	background: #000;
}
</style>
