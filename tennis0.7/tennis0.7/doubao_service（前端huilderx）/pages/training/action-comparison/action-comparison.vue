<template>
	<Layout>
		<view class="container">
			<view class="header">
				<view class="back-btn" @tap="goBack">
					<text class="back-icon">←</text>
				</view>
				<text class="page-title">动作对比</text>
			</view>

			<view class="section-card">
				<view class="section-header">
					<view class="section-icon user-icon">♟</view>
					<text class="section-title">我的视频</text>
				</view>
				<view class="button-group">
					<view class="action-btn" @tap="uploadMyVideo">
						<view class="btn-icon-wrapper">
							<text class="btn-icon">↑</text>
						</view>
						<text class="btn-text">{{ myVideo ? '重新上传' : '上传视频' }}</text>
					</view>
				</view>
				<text v-if="myVideo" class="selected-text">已选择：{{ myVideo.name }}</text>
			</view>

			<view class="section-card">
				<view class="section-header">
					<view class="section-icon target-icon">◎</view>
					<text class="section-title">对比目标</text>
				</view>
				<view class="button-group">
					<view class="action-btn" @tap="selectFromActionLib">
						<view class="btn-icon-wrapper check">
							<text class="btn-icon">✓</text>
						</view>
						<text class="btn-text">{{ targetAction ? targetAction.name : '从动作库选择' }}</text>
					</view>
					<view class="action-btn" @tap="uploadTargetVideo">
						<view class="btn-icon-wrapper">
							<text class="btn-icon">▸</text>
						</view>
						<text class="btn-text">{{ targetVideo ? '重新上传' : '上传视频' }}</text>
					</view>
				</view>
				<text v-if="targetVideo" class="selected-text">已上传目标：{{ targetVideo.name }}</text>
			</view>

			<view class="action-library">
				<view class="library-head">
					<text class="library-title">动作库</text>
					<text class="library-count">{{ actionLibrary.length }} 个标准动作</text>
				</view>
				<view
					v-for="item in actionLibrary"
					:key="item.id"
					class="library-item"
					:class="{ active: targetAction?.id === item.id }"
					@tap="chooseAction(item)"
				>
					<view class="library-icon">{{ item.icon }}</view>
					<view class="library-main">
						<text class="library-name">{{ item.name }}</text>
						<text class="library-desc">{{ item.desc }}</text>
					</view>
					<text class="library-tag">{{ item.level }}</text>
				</view>
			</view>

			<view class="ai-tip-card">
				<view class="ai-header">
					<view class="ai-icon-wrapper">
						<text class="ai-icon">▮</text>
					</view>
					<text class="ai-title">AI 智能识别</text>
				</view>
				<text class="ai-desc">AI 将自动识别并标记关键骨骼点差异，助你快速找到需要改进的区域。</text>
			</view>

			<view class="compare-btn" :class="{ disabled: !canCompare }" @tap="startCompare">
				<text class="compare-btn-icon">▮</text>
				<text class="compare-btn-text">开始对比</text>
			</view>

			<view class="footer-tip">
				<text class="tip-text">请先确保我的视频与对比目标都已选择后再开始对比</text>
			</view>
		</view>
	</Layout>
</template>

<script setup>
import { computed, ref } from 'vue'
import Layout from '@/components/Layout/Layout.vue'

const myVideo = ref(null)
const targetVideo = ref(null)
const targetAction = ref(null)

const actionLibrary = [
	{ id: 'forehand-drive', name: '职业正手抽击', desc: '稳定击球点，完整随挥路径', level: 'NTRP 4.5', icon: 'F' },
	{ id: 'backhand-slice', name: '反手削球控制', desc: '低重心切削，落点压制', level: 'NTRP 4.0', icon: 'B' },
	{ id: 'kick-serve', name: '上旋发球', desc: '抛球、蹬地、刷球一体化', level: 'NTRP 5.0', icon: 'S' },
	{ id: 'split-step', name: '分腿垫步启动', desc: '接发前预判与重心转换', level: '基础', icon: 'M' }
]

const canCompare = computed(() => {
	return Boolean(myVideo.value && (targetVideo.value || targetAction.value))
})

const goBack = () => {
	uni.navigateBack()
}

const pickVideo = () => {
	return new Promise((resolve) => {
		uni.chooseVideo({
			sourceType: ['album'],
			compressed: true,
			success: (res) => resolve(res),
			fail: () => resolve(null)
		})
	})
}

const getVideoName = (path) => {
	if (!path) return '本地视频'
	const parts = path.split(/[\\/]/)
	return parts[parts.length - 1] || '本地视频'
}

const uploadMyVideo = async () => {
	const res = await pickVideo()
	if (!res) return
	myVideo.value = {
		path: res.tempFilePath,
		name: getVideoName(res.tempFilePath)
	}
}

const uploadTargetVideo = async () => {
	const res = await pickVideo()
	if (!res) return
	targetVideo.value = {
		path: res.tempFilePath,
		name: getVideoName(res.tempFilePath)
	}
	targetAction.value = null
}

const selectFromActionLib = () => {
	const names = actionLibrary.map((item) => item.name)
	uni.showActionSheet({
		itemList: names,
		success: (res) => chooseAction(actionLibrary[res.tapIndex])
	})
}

const chooseAction = (item) => {
	targetAction.value = item
	targetVideo.value = null
}

const startCompare = () => {
	if (!canCompare.value) {
		uni.showToast({
			title: '请先选择两个对比素材',
			icon: 'none'
		})
		return
	}

	uni.showToast({
		title: '开始对比',
		icon: 'success'
	})
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	box-sizing: border-box;
	background: #000000;
	padding: 0 32rpx;
	padding-top: calc(var(--status-bar-height) + 20rpx);
}

.header {
	display: flex;
	align-items: center;
	gap: 24rpx;
	margin-bottom: 32rpx;
	padding: 8rpx 0;
}

.back-btn {
	width: 64rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(255, 255, 255, 0.05);
	border-radius: 16rpx;
}

.back-btn:active,
.action-btn:active,
.library-item:active,
.compare-btn:active {
	transform: scale(0.98);
}

.back-icon {
	font-size: 36rpx;
	color: #ffffff;
	font-weight: bold;
}

.page-title {
	font-size: 36rpx;
	font-weight: bold;
	color: #ffffff;
}

.section-card {
	background: #0a0a0a;
	border: 1rpx solid rgba(222, 255, 154, 0.15);
	border-radius: 24rpx;
	padding: 28rpx 24rpx;
	margin-bottom: 24rpx;
}

.section-header {
	display: flex;
	align-items: center;
	gap: 16rpx;
	margin-bottom: 24rpx;
}

.section-icon {
	width: 48rpx;
	height: 48rpx;
	border-radius: 12rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #33ff3d;
	font-size: 24rpx;
	font-weight: 900;
	background: rgba(34, 197, 94, 0.18);
}

.section-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #ffffff;
}

.button-group {
	display: flex;
	gap: 16rpx;
}

.action-btn {
	flex: 1;
	min-height: 126rpx;
	background: #151515;
	border: 1rpx solid rgba(255, 255, 255, 0.08);
	border-radius: 16rpx;
	padding: 24rpx 16rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 14rpx;
}

.btn-icon-wrapper {
	width: 56rpx;
	height: 56rpx;
	background: rgba(255, 255, 255, 0.05);
	border-radius: 14rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.btn-icon-wrapper.check {
	background: rgba(34, 197, 94, 0.22);
	border: 1rpx solid rgba(34, 197, 94, 0.48);
}

.btn-icon {
	font-size: 28rpx;
	color: rgba(255, 255, 255, 0.72);
	font-weight: 900;
}

.check .btn-icon {
	color: #33ff3d;
}

.btn-text {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.82);
	text-align: center;
}

.selected-text {
	display: block;
	margin-top: 18rpx;
	font-size: 22rpx;
	color: rgba(222, 255, 154, 0.72);
}

.action-library {
	margin-bottom: 24rpx;
}

.library-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 16rpx;
}

.library-title {
	font-size: 28rpx;
	font-weight: 800;
	color: #fff;
}

.library-count {
	font-size: 22rpx;
	color: rgba(222, 255, 154, 0.58);
}

.library-item {
	display: flex;
	align-items: center;
	gap: 18rpx;
	margin-bottom: 14rpx;
	padding: 20rpx;
	border-radius: 18rpx;
	background: #111513;
	border: 1rpx solid rgba(255, 255, 255, 0.06);
}

.library-item.active {
	border-color: rgba(51, 255, 61, 0.58);
	background: rgba(51, 255, 61, 0.08);
}

.library-icon {
	width: 58rpx;
	height: 58rpx;
	border-radius: 14rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(51, 255, 61, 0.16);
	color: #33ff3d;
	font-size: 26rpx;
	font-weight: 900;
}

.library-main {
	flex: 1;
	min-width: 0;
	display: flex;
	flex-direction: column;
	gap: 6rpx;
}

.library-name {
	font-size: 25rpx;
	font-weight: 800;
	color: #fff;
}

.library-desc {
	font-size: 21rpx;
	color: rgba(255, 255, 255, 0.5);
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.library-tag {
	padding: 6rpx 10rpx;
	border-radius: 999rpx;
	background: rgba(51, 255, 61, 0.12);
	color: #a8ff9e;
	font-size: 18rpx;
	font-weight: 800;
}

.ai-tip-card {
	background: linear-gradient(135deg, rgba(34, 197, 94, 0.14) 0%, rgba(34, 197, 94, 0.06) 100%);
	border: 1rpx solid rgba(34, 197, 94, 0.28);
	border-radius: 20rpx;
	padding: 24rpx 20rpx;
	margin-bottom: 32rpx;
}

.ai-header {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-bottom: 12rpx;
}

.ai-icon-wrapper {
	width: 40rpx;
	height: 40rpx;
	background: rgba(34, 197, 94, 0.25);
	border-radius: 10rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.ai-icon {
	font-size: 22rpx;
	color: #ff9c27;
}

.ai-title {
	font-size: 26rpx;
	font-weight: 700;
	color: var(--primary-green);
}

.ai-desc {
	display: block;
	padding-left: 52rpx;
	font-size: 23rpx;
	color: rgba(255, 255, 255, 0.62);
	line-height: 1.6;
}

.compare-btn {
	width: 100%;
	border-radius: 24rpx;
	padding: 32rpx 0;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
	margin-bottom: 24rpx;
	background: var(--primary-green);
	box-shadow: 0 4rpx 24rpx rgba(222, 255, 154, 0.3);
}

.compare-btn.disabled {
	background: #1a1a1a;
	border: 1rpx solid #2a2a2a;
	box-shadow: none;
}

.compare-btn-icon {
	font-size: 30rpx;
	color: #ff9c27;
}

.compare-btn-text {
	font-size: 32rpx;
	font-weight: 700;
	color: #000000;
}

.compare-btn.disabled .compare-btn-text {
	color: #555555;
}

.footer-tip {
	text-align: center;
	padding-bottom: 40rpx;
}

.tip-text {
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.35);
	line-height: 1.5;
}
</style>
