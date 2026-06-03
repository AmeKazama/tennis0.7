<template>
	<view class="container">
		<view class="navbar">
			<view class="back" @tap="goBack">
				<text class="back-icon">←</text>
			</view>
			<view class="title-block">
				<text class="page-title">球星动作对比</text>
				<text class="page-subtitle">选择球星与击球类型，上传你的视频进行骨骼对齐分析</text>
			</view>
		</view>

		<view class="content">
			<view class="section-card">
				<view class="section-header">
					<view class="section-title-wrapper">
						<text class="section-icon">U</text>
						<text class="section-title">我的视频</text>
					</view>
					<text class="status-pill">{{ myVideo ? '已选择' : '待上传' }}</text>
				</view>

				<view class="upload-area" @tap="uploadMyVideo">
					<view class="upload-icon-box">
						<text class="upload-icon">↑</text>
					</view>
					<view class="upload-copy">
						<text class="upload-title">{{ myVideo ? '重新上传用户视频' : '上传用户视频' }}</text>
						<text class="upload-desc">{{ myVideo ? myVideo.name : '建议选择完整正手、反手或发球视频' }}</text>
					</view>
				</view>
			</view>

			<view class="section-card">
				<view class="section-header">
					<view class="section-title-wrapper">
						<text class="section-icon green">S</text>
						<text class="section-title">球星标准动作</text>
					</view>
					<text class="status-pill green">{{ selectedPlayer.name }} · {{ selectedStroke.name }}</text>
				</view>

				<view class="option-label">选择球星</view>
				<view class="chip-grid players">
					<view
						v-for="player in players"
						:key="player.id"
						class="chip"
						:class="{ active: selectedPlayer.id === player.id }"
						@tap="selectPlayer(player)"
					>
						<text>{{ player.name }}</text>
					</view>
				</view>

				<view class="option-label">选择击球类型</view>
				<view class="chip-grid strokes">
					<view
						v-for="stroke in strokeTypes"
						:key="stroke.id"
						class="chip stroke"
						:class="{ active: selectedStroke.id === stroke.id }"
						@tap="selectStroke(stroke)"
					>
						<text>{{ stroke.name }}</text>
					</view>
				</view>

				<text class="resource-path">资源路径：{{ standardVideoPath }}</text>
			</view>

			<view class="compare-btn" :class="{ disabled: !canCompare || analyzing }" @tap="startCompare">
				<text>{{ analyzing ? '分析中...' : '开始分析' }}</text>
			</view>

			<view class="video-stage" v-if="showStage">
				<view class="video-panel">
					<view class="video-head">
						<text class="video-title">用户视频</text>
						<text class="video-note">MediaPipe 骨骼</text>
					</view>
					<view class="video-frame">
						<video
							id="userVideo"
							class="video"
							:src="displayUserVideo"
							:controls="false"
							:show-center-play-btn="false"
							:show-play-btn="false"
							:show-fullscreen-btn="false"
							@timeupdate="onUserTimeUpdate"
						/>
						<view class="overlay-hint">骨骼叠加视频由后端返回</view>
					</view>
				</view>

				<view class="video-panel">
					<view class="video-head">
						<text class="video-title">{{ selectedPlayer.name }} · {{ selectedStroke.name }}</text>
						<text class="video-note standard">标准动作</text>
					</view>
					<view class="video-frame">
						<video
							id="starVideo"
							class="video"
							:src="displayStandardVideo"
							:controls="false"
							:show-center-play-btn="false"
							:show-play-btn="false"
							:show-fullscreen-btn="false"
						/>
						<view class="overlay-hint">骨骼叠加视频由后端返回</view>
					</view>
				</view>
			</view>

			<view class="sync-bar" v-if="showStage">
				<view class="sync-btn" @tap="toggleSyncPlay">
					<text>{{ playing ? '暂停同步播放' : '同步播放' }}</text>
				</view>
				<view class="sync-btn ghost" @tap="resetVideos">
					<text>回到开头</text>
				</view>
			</view>

			<view class="report-card">
				<view class="report-header">
					<text class="report-title">动作比对区别讲解</text>
					<text class="report-state">{{ reportStatus }}</text>
				</view>

				<view v-if="analysisError" class="error-box">
					<text>{{ analysisError }}</text>
				</view>
				<view v-else-if="analysisReport" class="report-content">
					<text class="report-line" v-for="(line, index) in reportLines" :key="index">{{ line }}</text>
				</view>
				<view v-else class="empty-report">
					<text>分析后这里会展示准备阶段、引拍阶段、击球关键帧、随挥阶段的差异说明。</text>
				</view>
			</view>

			<view class="resource-note">
				<text>请把球星视频放到 static/pro-stars/{球星id}/{动作id}.mp4，例如 static/pro-stars/federer/forehand.mp4。</text>
			</view>
		</view>
	</view>
</template>

<script setup>
import { computed, ref } from 'vue'

const API_BASE_URL = 'http://127.0.0.1:9000'

const players = [
	{ id: 'donald', name: '唐纳德' },
	{ id: 'nadal', name: '纳达尔' },
	{ id: 'federer', name: '费德勒' },
	{ id: 'djokovic', name: '德约科维奇' },
	{ id: 'sinner', name: '辛纳' }
]

const strokeTypes = [
	{ id: 'forehand', name: '正手' },
	{ id: 'backhand', name: '反手' },
	{ id: 'serve', name: '发球' }
]

const myVideo = ref(null)
const selectedPlayer = ref(players[2])
const selectedStroke = ref(strokeTypes[0])
const analyzing = ref(false)
const playing = ref(false)
const showStage = ref(false)
const analysisError = ref('')
const analysisReport = ref('')
const userPoseVideoUrl = ref('')
const standardPoseVideoUrl = ref('')
const userVideoContext = ref(null)
const starVideoContext = ref(null)

const standardVideoPath = computed(() => `/static/pro-stars/${selectedPlayer.value.id}/${selectedStroke.value.id}.mp4`)
const displayUserVideo = computed(() => userPoseVideoUrl.value || myVideo.value?.path || '')
const displayStandardVideo = computed(() => standardPoseVideoUrl.value || standardVideoPath.value)
const canCompare = computed(() => Boolean(myVideo.value && selectedPlayer.value && selectedStroke.value))
const reportStatus = computed(() => analyzing.value ? '分析中' : analysisReport.value ? '已生成' : '待分析')
const reportLines = computed(() => String(analysisReport.value || '').split('\n').filter(Boolean))

const goBack = () => {
	uni.navigateBack()
}

const pickVideo = () => {
	return new Promise((resolve) => {
		uni.chooseVideo({
			sourceType: ['album'],
			compressed: false,
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
	analysisError.value = ''
	analysisReport.value = ''
	userPoseVideoUrl.value = ''
	showStage.value = false
}

const selectPlayer = (player) => {
	selectedPlayer.value = player
	resetResultOnly()
}

const selectStroke = (stroke) => {
	selectedStroke.value = stroke
	resetResultOnly()
}

const resetResultOnly = () => {
	analysisError.value = ''
	analysisReport.value = ''
	standardPoseVideoUrl.value = ''
	showStage.value = false
}

const ensureVideoContexts = () => {
	if (!userVideoContext.value) userVideoContext.value = uni.createVideoContext('userVideo')
	if (!starVideoContext.value) starVideoContext.value = uni.createVideoContext('starVideo')
}

const startCompare = async () => {
	if (!canCompare.value || analyzing.value) {
		uni.showToast({ title: '请先上传视频并选择球星动作', icon: 'none' })
		return
	}

	analyzing.value = true
	showStage.value = true
	analysisError.value = ''
	analysisReport.value = '正在上传用户视频，并请求后端进行 MediaPipe 骨骼提取与动作差异分析...'

	try {
		const result = await submitCompareTask()
		userPoseVideoUrl.value = result.user_pose_video_url || ''
		standardPoseVideoUrl.value = result.standard_pose_video_url || ''
		analysisReport.value = result.report || buildLocalReport()
	} catch (error) {
		analysisError.value = error.message || '动作对比接口暂未接通'
		analysisReport.value = buildLocalReport()
	} finally {
		analyzing.value = false
	}
}

const submitCompareTask = async () => {
	const formData = new FormData()
	const userBlob = await fetch(myVideo.value.path).then((res) => res.blob())
	formData.append('user_video', userBlob, myVideo.value.name || 'user_video.mp4')
	formData.append('player', selectedPlayer.value.id)
	formData.append('stroke_type', selectedStroke.value.id)
	formData.append('standard_video_path', standardVideoPath.value)

	const response = await fetch(`${API_BASE_URL}/api/action_compare_submit`, {
		method: 'POST',
		body: formData
	})

	if (!response.ok) {
		throw new Error(`后端动作对比接口未返回成功：${response.status}`)
	}

	return response.json()
}

const buildLocalReport = () => {
	return [
		`对比目标：${selectedPlayer.value.name}的${selectedStroke.value.name}`,
		'当前页面已完成双视频同步播放与后端接口预留。',
		'后端接入后，应返回用户骨骼视频、球星骨骼视频和动作差异报告。',
		'建议报告内容包括：准备阶段、引拍阶段、击球关键帧、随挥结束四部分的差异。'
	].join('\n')
}

const toggleSyncPlay = () => {
	if (!showStage.value) return
	ensureVideoContexts()
	if (playing.value) {
		userVideoContext.value.pause()
		starVideoContext.value.pause()
		playing.value = false
	} else {
		userVideoContext.value.play()
		starVideoContext.value.play()
		playing.value = true
	}
}

const resetVideos = () => {
	ensureVideoContexts()
	userVideoContext.value.seek(0)
	starVideoContext.value.seek(0)
	userVideoContext.value.pause()
	starVideoContext.value.pause()
	playing.value = false
}

const onUserTimeUpdate = (event) => {
	if (!playing.value || !starVideoContext.value) return
	const current = event.detail?.currentTime
	if (typeof current === 'number') {
		starVideoContext.value.seek(current)
	}
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	box-sizing: border-box;
	background: #050609;
	padding: 0 28rpx 48rpx;
	padding-top: calc(var(--status-bar-height) + 18rpx);
}

.navbar {
	display: flex;
	align-items: center;
	gap: 22rpx;
	margin-bottom: 28rpx;
}

.back {
	width: 64rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #151821;
	border-radius: 14rpx;
}

.back-icon {
	font-size: 36rpx;
	color: #fff;
	font-weight: 800;
}

.title-block {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}

.page-title {
	font-size: 36rpx;
	font-weight: 800;
	color: #fff;
}

.page-subtitle {
	font-size: 22rpx;
	color: rgba(255,255,255,.52);
}

.content {
	display: flex;
	flex-direction: column;
	gap: 22rpx;
}

.section-card,
.report-card,
.resource-note {
	background: #10131b;
	border: 1rpx solid rgba(222,255,154,.14);
	border-radius: 18rpx;
	padding: 24rpx;
}

.section-header,
.section-title-wrapper,
.video-head,
.report-header,
.upload-area {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.section-header,
.report-header {
	justify-content: space-between;
	margin-bottom: 20rpx;
}

.section-icon {
	width: 48rpx;
	height: 48rpx;
	border-radius: 12rpx;
	background: rgba(51,255,61,.14);
	color: #a8ff9e;
	display: flex;
	align-items: center;
	justify-content: center;
	font-weight: 900;
}

.section-icon.green {
	background: rgba(120,216,255,.14);
	color: #78d8ff;
}

.section-title,
.video-title,
.report-title {
	font-size: 28rpx;
	font-weight: 800;
	color: #fff;
}

.status-pill {
	font-size: 20rpx;
	color: #a8ff9e;
	background: rgba(51,255,61,.12);
	padding: 8rpx 12rpx;
	border-radius: 999rpx;
}

.status-pill.green {
	color: #78d8ff;
	background: rgba(120,216,255,.12);
}

.upload-area {
	min-height: 126rpx;
	background: #171b25;
	border: 1rpx dashed rgba(255,255,255,.12);
	border-radius: 16rpx;
	padding: 20rpx;
}

.upload-icon-box {
	width: 64rpx;
	height: 64rpx;
	border-radius: 16rpx;
	background: rgba(51,255,61,.12);
	display: flex;
	align-items: center;
	justify-content: center;
}

.upload-icon {
	font-size: 32rpx;
	color: #a8ff9e;
	font-weight: 900;
}

.upload-copy {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
	min-width: 0;
}

.upload-title {
	font-size: 26rpx;
	font-weight: 800;
	color: #fff;
}

.upload-desc,
.resource-path,
.resource-note text,
.empty-report text {
	font-size: 22rpx;
	color: rgba(255,255,255,.52);
	line-height: 1.5;
}

.upload-desc {
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.option-label {
	font-size: 22rpx;
	color: rgba(255,255,255,.6);
	margin-bottom: 12rpx;
}

.chip-grid {
	display: flex;
	flex-wrap: wrap;
	gap: 14rpx;
	margin-bottom: 18rpx;
}

.chip {
	padding: 18rpx 22rpx;
	border-radius: 14rpx;
	background: #171b25;
	border: 1rpx solid rgba(255,255,255,.08);
}

.chip text {
	font-size: 24rpx;
	color: rgba(255,255,255,.72);
	font-weight: 700;
}

.chip.active {
	background: rgba(51,255,61,.12);
	border-color: rgba(51,255,61,.56);
}

.chip.active text {
	color: #a8ff9e;
}

.compare-btn {
	height: 88rpx;
	border-radius: 16rpx;
	background: #19c785;
	display: flex;
	align-items: center;
	justify-content: center;
}

.compare-btn text {
	color: #06120d;
	font-size: 30rpx;
	font-weight: 900;
}

.compare-btn.disabled {
	background: #20232d;
}

.compare-btn.disabled text {
	color: rgba(255,255,255,.34);
}

.video-stage {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 18rpx;
}

.video-panel {
	min-width: 0;
}

.video-head {
	justify-content: space-between;
	margin-bottom: 12rpx;
}

.video-note {
	font-size: 20rpx;
	color: #a8ff9e;
	background: rgba(51,255,61,.12);
	padding: 6rpx 10rpx;
	border-radius: 999rpx;
}

.video-note.standard {
	color: #78d8ff;
	background: rgba(120,216,255,.12);
}

.video-frame {
	position: relative;
	width: 100%;
	aspect-ratio: 16 / 9;
	background: #000;
	border-radius: 16rpx;
	overflow: hidden;
	border: 1rpx solid rgba(255,255,255,.08);
}

.video {
	width: 100%;
	height: 100%;
}

.overlay-hint {
	position: absolute;
	left: 12rpx;
	bottom: 12rpx;
	font-size: 18rpx;
	color: #a8ff9e;
	background: rgba(0,0,0,.62);
	padding: 6rpx 10rpx;
	border-radius: 999rpx;
}

.sync-bar {
	display: flex;
	gap: 16rpx;
}

.sync-btn {
	flex: 1;
	height: 76rpx;
	border-radius: 16rpx;
	background: #19c785;
	display: flex;
	align-items: center;
	justify-content: center;
}

.sync-btn text {
	color: #06120d;
	font-weight: 900;
}

.sync-btn.ghost {
	background: #1d2230;
}

.sync-btn.ghost text {
	color: #fff;
}

.report-state {
	font-size: 22rpx;
	color: #a8ff9e;
}

.report-content {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
}

.report-line {
	font-size: 24rpx;
	color: rgba(255,255,255,.82);
	line-height: 1.6;
}

.error-box {
	background: rgba(255,80,80,.1);
	border: 1rpx solid rgba(255,80,80,.22);
	border-radius: 12rpx;
	padding: 18rpx;
}

.error-box text {
	font-size: 24rpx;
	line-height: 1.5;
	color: #ff7474;
}

@media (max-width: 700px) {
	.video-stage {
		grid-template-columns: 1fr;
	}
}
</style>
