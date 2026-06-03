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
				<view v-else
					class="video-player-wrapper"
					id="source-video-container"
					:source-data="sourceVideoData"
					:change:source-data="domVideo.renderSource"
				></view>
			</view>

			<!-- 操作按钮 -->
			<view class="action-buttons">
				<view class="btn primary-btn" @tap="selectVideo">
					<text class="btn-icon">⊕</text>
					<text class="btn-text">从相册选择视频</text>
				</view>
				<view 
					class="btn" 
					:class="canSplit ? 'split-btn' : 'disabled-btn'"
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
			</view>

			<!-- 分割结果：左右滑动 -->
			<view v-if="rallyList.length > 0" class="result-section">
				<view class="result-header">
					<text class="result-title">分割结果（{{ rallyList.length }} 个回合）</text>
				</view>
				<scroll-view class="rally-scroll" scroll-x="true" show-scrollbar="false">
					<view 
						id="rally-video-container" 
						style="display:flex;flex-direction:row;padding-bottom:12rpx;"
						:video-data="rallyVideoData"
						:change:video-data="domVideo.renderVideos"
					></view>
				</scroll-view>
			</view>

			<!-- 提示信息 -->
			<view v-if="rallyList.length === 0 && !cutting" class="tip-card">
				<view class="tip-header">
					<text class="tip-title">把时间留给球场，算给 AI 。</text>
				</view>
				<view class="tip-content">
					<text class="tip-desc">选择视频后点击「分割」，自动识别回合边界并拆分。</text>
				</view>
			</view>
		</view>
	</Layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import Layout from '@/components/Layout/Layout.vue'

const API_BASE_URL = 'http://10.24.51.159:9000'

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
const selectedVideo = ref('')
const cutting = ref(false)
const progress = ref(0)
const taskId = ref('')
const rallyList = ref([])

const canSplit = computed(() => selectedVideo.value && !cutting.value)
const sourceVideoData = computed(() => selectedVideo.value ? JSON.stringify([{ url: selectedVideo.value }]) : '')
const rallyVideoData = computed(() => JSON.stringify(rallyList.value.map(r => ({ url: r.url, poster: r.poster || '' }))))

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
			selectedVideo.value = toWebUrl(res.tempFilePath)
			rallyList.value = []
			uni.showToast({ title: '视频已选择', icon: 'success' })
		}
	})
}

const downloadRallyVideos = (files) => {
	const tasks = files.map(f => {
		const filename = f.replace(/\\/g, '/').split('/').pop()
		const videoUrl = `${API_BASE_URL}/output_rallies/${filename}`
		const posterUrl = videoUrl.replace('.mp4', '.jpg')
		return new Promise((resolve, reject) => {
			uni.downloadFile({
				url: videoUrl,
				success: (res) => resolve({ url: toWebUrl(res.tempFilePath), poster: posterUrl }),
				fail: reject
			})
		})
	})
	Promise.all(tasks).then(items => {
		rallyList.value = items
		uni.hideLoading()
		uni.showToast({ title: `分割完成，共 ${files.length} 个回合`, icon: 'success' })
	}).catch(() => {
		rallyList.value = files.map(f => {
			const filename = f.replace(/\\/g, '/').split('/').pop()
			const videoUrl = `${API_BASE_URL}/output_rallies/${filename}`
			return { url: videoUrl, poster: videoUrl.replace('.mp4', '.jpg') }
		})
		uni.hideLoading()
		uni.showToast({ title: `分割完成（网络播放）`, icon: 'success' })
	}).finally(() => {
		cutting.value = false
	})
}

const startSplit = () => {
	if (!canSplit.value) return
	cutting.value = true
	progress.value = 5
	rallyList.value = []

	uni.showLoading({ title: '上传中...' })
	const task = uni.uploadFile({
		url: `${API_BASE_URL}/api/rally/cut/submit?no_net=true&slow_speed=5&net_reversal_dist=4`,
		filePath: selectedVideo.value,
		name: 'file',
		timeout: 600000,
		success: (res) => {
			uni.hideLoading()
			const data = JSON.parse(res.data)
			taskId.value = data.task_id
			progress.value = 10
			pollStatus(data.task_id)
		},
		fail: (err) => {
			uni.hideLoading()
			cutting.value = false
			progress.value = 0
			uni.showToast({ title: '上传失败', icon: 'none' })
		}
	})
	if (task && task.onProgressUpdate) {
		task.onProgressUpdate((res) => {
			progress.value = Math.min(90, 5 + Math.floor(res.progress * 0.85))
		})
	}
}

const pollStatus = (tid) => {
	setTimeout(() => {
		uni.request({
			url: `${API_BASE_URL}/api/rally/cut/status/${tid}`,
			method: 'GET',
			success: (res) => {
				const data = res.data
				if (data.status === 'running') {
					progress.value = Math.max(progress.value, data.progress || 30)
					pollStatus(tid)
				} else if (data.status === 'done') {
					progress.value = 100
					const files = data.result?.files || []
					downloadRallyVideos(files)
				} else if (data.status === 'error') {
					cutting.value = false
					progress.value = 0
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

.result-section {
	margin-bottom: 28rpx;
}

.result-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 20rpx;
}

.result-title {
	font-size: 28rpx;
	font-weight: 600;
	color: #ffffff;
}

.rally-scroll {
	display: flex;
	flex-direction: row;
	white-space: nowrap;
	padding-bottom: 12rpx;
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
