<template>
	<Layout>
		<view class="container">
			<!-- 顶部导航栏 -->
			<view class="header">
				<view class="back-btn" @tap="goBack">
					<text class="back-icon">←</text>
				</view>
				<text class="page-title">回合剪辑</text>
				<view class="header-icons">
					<view class="icon-btn">
						<text class="icon-text">💬</text>
					</view>
					<view class="icon-btn">
						<text class="icon-text">⚙️</text>
					</view>
				</view>
			</view>

			<!-- Tab 切换 -->
			<view class="tab-container">
				<view 
					class="tab-item" 
					:class="{ active: currentTab === 'full' }"
					@tap="switchTab('full')"
				>
					<text class="tab-text">完整视频</text>
					<view v-if="currentTab === 'full'" class="tab-indicator"></view>
				</view>
				<view 
					class="tab-item"
					:class="{ active: currentTab === 'favorite' }"
					@tap="switchTab('favorite')"
				>
					<text class="tab-text">收藏回合</text>
					<view v-if="currentTab === 'favorite'" class="tab-indicator"></view>
				</view>
			</view>

			<!-- 原始视频 -->
			<view class="video-section">
				<view v-if="!selectedVideo" class="video-placeholder">
					<view class="video-frame">
						<view class="camera-icon">
							<text class="camera-symbol">📹</text>
						</view>
						<view class="no-video-text">暂无视频</view>
						<view class="no-video-desc">请选择一个视频文件进行回合剪辑</view>
					</view>
				</view>
				<view v-else class="video-player-wrapper">
					<video
						id="sourceVideo"
						class="source-video"
						:src="selectedVideo.previewUrl"
						controls
						:autoplay="false"
						:initial-time="0.1"
						object-fit="contain"
					></video>
					<view class="calibration-layer" :class="{ complete: courtPoints.length >= 4 }" @tap.stop="handleCourtTap">
						<view
							v-for="(point, index) in courtPoints"
							:key="index"
							class="court-point"
							:style="{ left: point.uiX + 'px', top: point.uiY + 'px' }"
						>
							<text class="court-point-text">{{ index + 1 }}</text>
						</view>
					</view>
				</view>
			</view>

			<view v-if="selectedVideo" class="calibration-card">
				<view class="calibration-title">球场标定</view>
				<view class="calibration-desc">{{ calibrationTip }}</view>
				<view class="calibration-actions">
					<view class="calibration-btn" @tap="resetCourtPoints">重新标点</view>
				</view>
			</view>

			<!-- 操作按钮 -->
			<view class="action-buttons">
				<view class="btn primary-btn" @tap="selectVideo">
					<text class="btn-icon">⊕</text>
					<text class="btn-text">从相册选择视频</text>
				</view>
				<view 
					class="btn" 
					:class="canSubmitSplit ? 'split-btn' : 'disabled-btn'"
					@tap="startSplit"
				>
					<text class="btn-icon">✂</text>
					<text class="btn-text">{{ cutting ? '分割中...' : '分割' }}</text>
				</view>
			</view>

			<!-- 进度条 -->
			<view v-if="cutting" class="progress-bar-wrap">
				<view class="progress-bar">
					<view class="progress-fill" :style="{ width: progress + '%' }"></view>
				</view>
				<text class="progress-text">{{ progress }}%</text>
				<text class="progress-message">{{ progressMessage }}</text>
			</view>

			<!-- 分割结果 -->
			<view v-if="rallyList.length > 0" class="result-section">
				<view class="result-header">
					<view>
						<text class="result-title">分割结果</text>
						<text class="result-subtitle">{{ rallyList.length }} 个回合片段已生成</text>
					</view>
				</view>
				<view class="rally-grid">
					<view v-for="(item, index) in rallyList" :key="item.url" class="rally-card">
						<view class="rally-card-head">
							<text class="rally-title">回合 {{ index + 1 }}</text>
							<text class="rally-index">{{ String(index + 1).padStart(2, '0') }}</text>
						</view>
						<video
							class="rally-video"
							:src="item.url"
							:poster="item.poster || ''"
							controls
							:autoplay="false"
							:initial-time="0.1"
							object-fit="contain"
							@error="handleRallyVideoError(item)"
						></video>
					</view>
				</view>
			</view>

			<!-- 提示信息 -->
			<view v-if="rallyList.length === 0 && !cutting" class="tip-card">
				<view class="tip-header">
					<text class="tip-title">{{ emptyMessage ? '暂未生成回合片段' : '把时间留给球场，算给 AI 。' }}</text>
				</view>
				<view class="tip-content">
					<text class="tip-desc">{{ emptyMessage || '选择视频后点击「分割」，自动识别回合边界并拆分。' }}</text>
				</view>
			</view>
		</view>
	</Layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import Layout from '@/components/Layout/Layout.vue'

const LAN_API_BASE_URL = 'http://192.168.1.53:9000'
const getApiBaseUrl = () => {
	// #ifdef H5
	const host = window.location.hostname
	if (host === 'localhost' || host === '127.0.0.1') {
		return 'http://localhost:9000'
	}
	// #endif
	return LAN_API_BASE_URL
}
const API_BASE_URL = getApiBaseUrl()

const toWebUrl = (path) => {
	if (!path) return path
	// #ifdef APP-PLUS
	if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('blob:')) return path
	if (path.startsWith('file://')) return path
	if (path.startsWith('/')) return 'file://' + path
	try { return plus.io.convertLocalFileSystemURL(path) } catch(e) { return path }
	// #endif
	return path
}

const currentTab = ref('full')
const selectedVideo = ref(null)
const cutting = ref(false)
const progress = ref(0)
const progressMessage = ref('')
const taskId = ref('')
const rallyList = ref([])
const courtPoints = ref([])
const pollAttempts = ref(0)
const emptyMessage = ref('')

const canSplit = computed(() => selectedVideo.value && !cutting.value)
const canSubmitSplit = computed(() => selectedVideo.value && courtPoints.value.length === 4 && !cutting.value)
const courtPointLabels = ['左上角', '右上角', '左下角', '右下角']
const calibrationTip = computed(() => {
	if (courtPoints.value.length >= 4) return '标定完成，可以开始剪辑。'
	return `请点击球场${courtPointLabels[courtPoints.value.length]}（${courtPoints.value.length + 1}/4）`
})

const goBack = () => {
	uni.navigateBack()
}

const switchTab = (tab) => {
	currentTab.value = tab
}

const selectVideo = () => {
	uni.chooseVideo({
		sourceType: ['album'],
		compressed: true,
		success: (res) => {
			selectedVideo.value = {
				rawPath: res.tempFilePath,
				previewUrl: toWebUrl(res.tempFilePath),
				file: res.tempFile || res.tempFiles?.[0]?.file || res.tempFiles?.[0],
				name: res.name || res.tempFiles?.[0]?.name || 'rally_video.mp4',
				width: Number(res.width || 0),
				height: Number(res.height || 0)
			}
			courtPoints.value = []
			rallyList.value = []
			emptyMessage.value = ''
			uni.showToast({ title: '视频已选择', icon: 'success' })
		}
	})
}

const getManualPointsPayload = () => {
	return JSON.stringify(courtPoints.value.map(({ x, y }) => ({ x, y })))
}

const normalizeVideoFile = (fileLike) => {
	if (!fileLike) return null
	if (typeof Blob !== 'undefined' && fileLike instanceof Blob) return fileLike
	if (fileLike.file && typeof Blob !== 'undefined' && fileLike.file instanceof Blob) return fileLike.file
	if (fileLike.raw && typeof Blob !== 'undefined' && fileLike.raw instanceof Blob) return fileLike.raw
	return null
}

const handleSubmitSuccess = (data) => {
	if (!data.task_id) {
		cutting.value = false
		progress.value = 0
		progressMessage.value = ''
		uni.showToast({ title: data.detail || data.message || '任务创建失败', icon: 'none' })
		return
	}
	taskId.value = data.task_id
	progress.value = Math.max(progress.value, 10)
	progressMessage.value = '任务已创建，等待后端处理'
	pollStatus(data.task_id)
}

const submitByFetch = async () => {
	let blob = normalizeVideoFile(selectedVideo.value.file)
	if (!blob) {
		const response = await fetch(selectedVideo.value.rawPath)
		if (!response.ok) throw new Error('无法读取浏览器临时视频文件')
		blob = await response.blob()
	}

	const formData = new FormData()
	formData.append('file', blob, selectedVideo.value.name || 'rally_video.mp4')
	formData.append('manual_points', getManualPointsPayload())

	const response = await fetch(`${API_BASE_URL}/api/rally/cut/submit?no_net=true&slow_speed=5&net_reversal_dist=4&min_rally_sec=1`, {
		method: 'POST',
		body: formData
	})

	let data = {}
	try {
		data = await response.json()
	} catch (e) {
		data = {}
	}

	if (!response.ok) {
		throw new Error(data.detail || data.message || `上传失败：${response.status}`)
	}

	handleSubmitSuccess(data)
}

const submitByUniUpload = () => {
	const task = uni.uploadFile({
		url: `${API_BASE_URL}/api/rally/cut/submit?no_net=true&slow_speed=5&net_reversal_dist=4&min_rally_sec=1`,
		filePath: selectedVideo.value.rawPath,
		name: 'file',
		formData: {
			manual_points: getManualPointsPayload()
		},
		timeout: 600000,
		success: (res) => {
			uni.hideLoading()
			const data = JSON.parse(res.data)
			handleSubmitSuccess(data)
		},
		fail: (err) => {
			uni.hideLoading()
			cutting.value = false
			progress.value = 0
			progressMessage.value = ''
			uni.showToast({ title: '上传失败', icon: 'none' })
		}
	})
	if (task && task.onProgressUpdate) {
		task.onProgressUpdate((res) => {
			progress.value = Math.min(90, 5 + Math.floor(res.progress * 0.85))
			progressMessage.value = '正在上传视频'
		})
	}
}

const resetCourtPoints = () => {
	courtPoints.value = []
}

const getTapPoint = (event) => {
	const touch = event.changedTouches?.[0] || event.touches?.[0]
	return {
		clientX: touch?.clientX ?? event.detail?.x ?? 0,
		clientY: touch?.clientY ?? event.detail?.y ?? 0
	}
}

const mapTapToVideoPoint = (rect, tap) => {
	const videoWidth = selectedVideo.value?.width || rect.width
	const videoHeight = selectedVideo.value?.height || rect.height
	const boxRatio = rect.width / rect.height
	const videoRatio = videoWidth / videoHeight

	let displayWidth = rect.width
	let displayHeight = rect.height
	let offsetX = 0
	let offsetY = 0

	if (videoRatio > boxRatio) {
		displayHeight = rect.width / videoRatio
		offsetY = (rect.height - displayHeight) / 2
	} else {
		displayWidth = rect.height * videoRatio
		offsetX = (rect.width - displayWidth) / 2
	}

	const localX = tap.clientX - rect.left - offsetX
	const localY = tap.clientY - rect.top - offsetY
	if (localX < 0 || localY < 0 || localX > displayWidth || localY > displayHeight) {
		return null
	}

	return {
		x: Math.round((localX / displayWidth) * videoWidth),
		y: Math.round((localY / displayHeight) * videoHeight),
		uiX: Math.round(localX + offsetX),
		uiY: Math.round(localY + offsetY)
	}
}

const handleCourtTap = (event) => {
	if (!selectedVideo.value || cutting.value || courtPoints.value.length >= 4) return
	const tap = getTapPoint(event)
	uni.createSelectorQuery()
		.select('.video-player-wrapper')
		.boundingClientRect((rect) => {
			if (!rect) return
			const point = mapTapToVideoPoint(rect, tap)
			if (!point) {
				uni.showToast({ title: '请点击视频画面内', icon: 'none' })
				return
			}
			courtPoints.value.push(point)
		})
		.exec()
}

const downloadRallyVideos = (files) => {
	rallyList.value = files.map((f, index) => {
		const relativePath = f.replace(/\\/g, '/').replace(/^\/+/, '')
		const videoUrl = `${API_BASE_URL}/output_rallies/${relativePath}`
		return {
			id: `${relativePath}-${index}`,
			url: videoUrl,
			poster: ''
		}
	})
	uni.hideLoading()
	cutting.value = false
	uni.showToast({ title: `分割完成，共 ${files.length} 个回合`, icon: 'success' })
}

const handleRallyVideoError = (item) => {
	console.warn('回合视频播放失败', item.url)
	uni.showToast({ title: '片段加载失败，请检查后端视频地址', icon: 'none' })
}

const startSplit = () => {
	if (!selectedVideo.value || cutting.value) return
	if (courtPoints.value.length !== 4) {
		uni.showToast({ title: '请先完成球场四点标定', icon: 'none' })
		return
	}
	cutting.value = true
	progress.value = 5
	progressMessage.value = '正在上传视频'
	rallyList.value = []
	emptyMessage.value = ''
	pollAttempts.value = 0

	uni.showLoading({ title: '上传中...' })
	// #ifdef H5
	submitByFetch()
		.then(() => {
			uni.hideLoading()
		})
		.catch((error) => {
			uni.hideLoading()
			cutting.value = false
			progress.value = 0
			uni.showToast({ title: error.message || '上传失败', icon: 'none' })
		})
	// #endif

	// #ifndef H5
	submitByUniUpload()
	// #endif
}

const pollStatus = (tid) => {
	setTimeout(() => {
		pollAttempts.value += 1
		if (pollAttempts.value > 180) {
			cutting.value = false
			progress.value = 0
			progressMessage.value = ''
			uni.showToast({ title: '分割超时，请重试', icon: 'none' })
			return
		}
		uni.request({
			url: `${API_BASE_URL}/api/rally/cut/status/${tid}`,
			method: 'GET',
			success: (res) => {
				const data = res.data
				if (data.status === 'running') {
					progress.value = Math.max(progress.value, data.progress || 30)
					progressMessage.value = data.message || '正在处理视频'
					pollStatus(tid)
				} else if (data.status === 'done') {
					progress.value = 100
					progressMessage.value = data.message || '分割完成'
					const files = data.result?.files || []
					if (files.length === 0) {
						cutting.value = false
						progress.value = 0
						progressMessage.value = ''
						emptyMessage.value = data.result?.message || '没有识别到满足条件的回合片段，请重新标定球场角点或换一段更完整的视频。'
						uni.hideLoading()
						uni.showToast({ title: '未生成回合片段', icon: 'none' })
						return
					}
					downloadRallyVideos(files)
				} else if (data.status === 'error') {
					cutting.value = false
					progress.value = 0
					progressMessage.value = ''
					uni.showToast({ title: '分割失败: ' + (data.error || '未知错误'), icon: 'none' })
				} else {
					pollStatus(tid)
				}
			},
			fail: () => {
				pollStatus(tid)
			}
		})
	}, 2000)
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	background: #000000;
	padding: 0 32rpx;
	padding-top: calc(var(--status-bar-height) + 20rpx);
}

.header {
	display: flex;
	align-items: center;
	justify-content: space-between;
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

.back-btn:active {
	background: rgba(255, 255, 255, 0.1);
	transform: scale(0.95);
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
	flex: 1;
	text-align: center;
}

.header-icons {
	display: flex;
	gap: 16rpx;
}

.icon-btn {
	width: 56rpx;
	height: 56rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(255, 255, 255, 0.05);
	border-radius: 14rpx;
}

.icon-text {
	font-size: 28rpx;
}

.tab-container {
	display: flex;
	gap: 48rpx;
	margin-bottom: 32rpx;
	padding: 0 8rpx;
	border-bottom: 2rpx solid rgba(255, 255, 255, 0.1);
}

.tab-item {
	position: relative;
	padding: 20rpx 0;
}

.tab-text {
	font-size: 28rpx;
	color: rgba(255, 255, 255, 0.5);
}

.tab-item.active .tab-text {
	color: var(--primary-green);
	font-weight: 600;
}

.tab-indicator {
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	height: 4rpx;
	background: var(--primary-green);
	border-radius: 2rpx;
}

.video-section {
	margin-bottom: 28rpx;
}

.video-placeholder {
	margin-bottom: 0;
}

.video-frame {
	width: 100%;
	height: 380rpx;
	background: #0a0a0a;
	border-radius: 24rpx;
	border: 2rpx solid rgba(222, 255, 154, 0.15);
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
}

.camera-icon {
	width: 120rpx;
	height: 120rpx;
	background: rgba(255, 255, 255, 0.08);
	border-radius: 24rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 24rpx;
	border: 2rpx solid rgba(255, 255, 255, 0.1);
}

.camera-symbol {
	font-size: 56rpx;
	opacity: 0.4;
}

.no-video-text {
	font-size: 30rpx;
	font-weight: 600;
	color: #666666;
	margin-bottom: 12rpx;
}

.no-video-desc {
	font-size: 24rpx;
	color: #555555;
	text-align: center;
}

.video-player-wrapper {
	width: 100%;
	height: 380rpx;
	border-radius: 24rpx;
	overflow: hidden;
	background: #0a0a0a;
	position: relative;
}

.source-video {
	width: 100%;
	height: 100%;
	background: #000000;
	display: block;
}

.calibration-layer {
	position: absolute;
	left: 0;
	top: 0;
	right: 0;
	bottom: 0;
	z-index: 2;
}

.calibration-layer.complete {
	pointer-events: none;
}

.court-point {
	position: absolute;
	width: 44rpx;
	height: 44rpx;
	margin-left: -22rpx;
	margin-top: -22rpx;
	border-radius: 50%;
	background: var(--primary-green);
	border: 4rpx solid #000000;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 0 20rpx rgba(222, 255, 154, 0.65);
}

.court-point-text {
	font-size: 22rpx;
	color: #000000;
	font-weight: 800;
}

.calibration-card {
	margin-bottom: 28rpx;
	padding: 22rpx;
	border-radius: 20rpx;
	background: rgba(222, 255, 154, 0.08);
	border: 1rpx solid rgba(222, 255, 154, 0.2);
}

.calibration-title {
	font-size: 28rpx;
	color: var(--primary-green);
	font-weight: 700;
	margin-bottom: 8rpx;
}

.calibration-desc {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.76);
	line-height: 1.5;
}

.calibration-actions {
	display: flex;
	margin-top: 16rpx;
}

.calibration-btn {
	padding: 12rpx 22rpx;
	border-radius: 14rpx;
	background: rgba(255, 255, 255, 0.08);
	color: #ffffff;
	font-size: 24rpx;
}

.btn {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 12rpx;
	padding: 28rpx 0;
	border-radius: 24rpx;
}

.btn:active {
	transform: scale(0.98);
}

.primary-btn {
	background: var(--primary-green);
	box-shadow: 0 4rpx 20rpx rgba(222, 255, 154, 0.3);
}

.split-btn {
	background: #4a90d9;
	box-shadow: 0 4rpx 20rpx rgba(74, 144, 217, 0.3);
}

.btn-icon {
	font-size: 28rpx;
}

.btn-text {
	font-size: 30rpx;
	color: #000000;
	font-weight: 600;
}

.split-btn .btn-text {
	color: #ffffff;
}

.disabled-btn {
	background: #1a1a1a;
	border: 1rpx solid #2a2a2a;
}

.disabled-btn .btn-text {
	color: #444444;
}

.progress-bar-wrap {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 16rpx;
	margin-bottom: 24rpx;
}

.progress-bar {
	flex: 1;
	height: 8rpx;
	background: #1a1a1a;
	border-radius: 4rpx;
	overflow: hidden;
}

.progress-fill {
	height: 100%;
	background: linear-gradient(90deg, var(--primary-green), #4a90d9);
	border-radius: 4rpx;
	transition: width 0.5s;
}

.progress-text {
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.6);
	min-width: 48rpx;
	text-align: right;
}

.progress-message {
	width: 100%;
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.55);
	line-height: 1.5;
}

.result-section {
	margin: 10rpx 0 32rpx;
}

.result-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 18rpx;
}

.result-title {
	display: block;
	font-size: 30rpx;
	font-weight: 800;
	color: #ffffff;
}

.result-subtitle {
	display: block;
	margin-top: 6rpx;
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.55);
}

.rally-grid {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 18rpx;
}

.rally-card {
	overflow: hidden;
	border-radius: 14rpx;
	background: #121610;
	border: 1rpx solid rgba(222, 255, 154, 0.16);
}

.rally-card-head {
	height: 64rpx;
	padding: 0 18rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
	background: rgba(222, 255, 154, 0.07);
}

.rally-title {
	font-size: 24rpx;
	font-weight: 700;
	color: #deff9a;
}

.rally-index {
	font-size: 20rpx;
	color: rgba(255, 255, 255, 0.45);
}

.rally-video {
	display: block;
	width: 100%;
	height: 260rpx;
	background: #000000;
}

.tip-card {
	background: rgba(222, 255, 154, 0.08);
	border: 1rpx solid rgba(222, 255, 154, 0.2);
	border-radius: 20rpx;
	padding: 24rpx;
}

.tip-header {
	margin-bottom: 12rpx;
}

.tip-title {
	font-size: 26rpx;
	font-weight: 600;
	color: var(--primary-green);
}

.tip-content {
	margin-bottom: 0;
}

.tip-desc {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.7);
	line-height: 1.6;
}

@media (min-width: 900px) {
	.container {
		max-width: 1040px;
		margin: 0 auto;
		padding: 24px 28px 110px;
		box-sizing: border-box;
	}

	.header {
		margin-bottom: 18px;
	}

	.page-title {
		font-size: 24px;
	}

	.tab-container {
		margin-bottom: 20px;
		gap: 28px;
	}

	.tab-text {
		font-size: 16px;
	}

	.video-player-wrapper,
	.video-frame {
		height: 420px;
		border-radius: 12px;
	}

	.calibration-card {
		margin-bottom: 18px;
		padding: 14px 16px;
		border-radius: 10px;
	}

	.calibration-title {
		font-size: 16px;
	}

	.calibration-desc,
	.calibration-btn {
		font-size: 14px;
	}

	.action-buttons {
		gap: 14px;
		margin-bottom: 18px;
	}

	.btn {
		height: 54px;
		padding: 0;
		border-radius: 10px;
	}

	.btn-text {
		font-size: 16px;
	}

	.btn-icon {
		font-size: 18px;
	}

	.result-header {
		margin-bottom: 12px;
	}

	.result-title {
		font-size: 20px;
	}

	.result-subtitle {
		font-size: 13px;
	}

	.rally-grid {
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 14px;
	}

	.rally-card {
		border-radius: 10px;
	}

	.rally-card-head {
		height: 42px;
		padding: 0 12px;
	}

	.rally-title {
		font-size: 14px;
	}

	.rally-index {
		font-size: 12px;
	}

	.rally-video {
		height: 180px;
	}
}
</style>

<script module="domVideo" lang="renderjs">
function rpx(v) {
	return Math.round((window.innerWidth / 750) * v)
}
function parseData(val) {
	return typeof val === 'string' ? JSON.parse(val) : val
}
function createVideo(src, poster, w, h) {
	var video = document.createElement('video')
	video.src = src
	if (poster) video.poster = poster
	video.controls = true
	video.preload = 'metadata'
	video.style.cssText = 'width:100%;height:' + h + 'px;display:block;background:#000;object-fit:contain;'
	video.setAttribute('playsinline', '')
	video.setAttribute('webkit-playsinline', '')
	video.addEventListener('loadeddata', function() {
		if (video.readyState >= 2) {
			try { video.currentTime = 0.05 } catch(e) {}
		}
	})
	return video
}
export default {
	methods: {
		renderSource(newVal, oldVal) {
			if (!newVal) return
			var container = document.getElementById('source-video-container')
			if (!container) return
			container.innerHTML = ''
			var data = parseData(newVal)
			if (data && data.length > 0) {
				container.appendChild(createVideo(data[0].url, data[0].poster || '', 0, rpx(380)))
			}
		},
		renderVideos(newVal, oldVal) {
			if (!newVal) return
			var container = document.getElementById('rally-video-container')
			if (!container) return
			container.innerHTML = ''
			var videos = parseData(newVal)
			for (var i = 0; i < videos.length; i++) {
				var card = document.createElement('div')
				card.style.cssText = 'flex-shrink:0;width:' + rpx(400) + 'px;margin-right:' + rpx(24) + 'px;border-radius:' + rpx(20) + 'px;overflow:hidden;background:#0a0a0a;border:2px solid rgba(222,255,154,0.15);'
				var label = document.createElement('div')
				label.style.cssText = 'font-size:' + rpx(24) + 'px;color:#00ff88;font-weight:600;padding:' + rpx(12) + 'px ' + rpx(16) + 'px;background:rgba(222,255,154,0.05);'
				label.textContent = '\u56de\u5408 ' + (i + 1)
				card.appendChild(label)
				card.appendChild(createVideo(videos[i].url, videos[i].poster || '', 0, rpx(280)))
				container.appendChild(card)
			}
		}
	}
}
</script>
