<template>
	<Layout>
		<view class="container">
			<view class="header">
				<view class="back-btn" @tap="goBack">
					<text class="back-icon">←</text>
				</view>
				<text class="page-title">打球日记</text>
				<view class="header-spacer"></view>
			</view>

			<view class="hero-section">
				<text class="hero-title">记录今天这场球</text>
				<text class="hero-subtitle">说出训练感受、比分、技术问题，AI 会帮你转成文字日记。</text>
			</view>

			<view class="mood-section">
				<text class="section-title">今天状态</text>
				<view class="mood-list">
					<view
						v-for="mood in moods"
						:key="mood"
						class="mood-chip"
						:class="{ active: selectedMood === mood }"
						@tap="selectedMood = mood"
					>
						{{ mood }}
					</view>
				</view>
			</view>

			<view class="record-panel">
				<view class="record-btn-wrapper" :class="{ recording: isRecording }">
					<view class="ripple-outer"></view>
					<view class="ripple-middle"></view>
					<view class="record-btn" @tap="toggleRecord">
						<text class="mic-icon">{{ isRecording ? '■' : '🎤' }}</text>
						<text class="btn-text">{{ isRecording ? '停止录音' : '开始说话' }}</text>
					</view>
				</view>
				<text class="record-status">{{ recordStatus }}</text>
			</view>

			<view class="suggestions-section">
				<text class="section-title">你可以说</text>
				<view class="suggestion-list">
					<view class="suggestion-card">
						<view class="tag">训练</view>
						<text class="suggestion-text">今天正手稳定了很多，但是反手接发还有点慢。</text>
					</view>
					<view class="suggestion-card">
						<view class="tag">比赛</view>
						<text class="suggestion-text">今天打了两盘，第一盘六比四赢了，第二盘抢七输了。</text>
					</view>
					<view class="suggestion-card">
						<view class="tag">感受</view>
						<text class="suggestion-text">今天强度比较大，打完有点累，但整体状态不错。</text>
					</view>
				</view>
			</view>

			<view class="history-section">
				<view class="history-header">
					<text class="section-title">最近记录</text>
					<view class="refresh-btn" @tap="loadDiaries">刷新</view>
				</view>

				<view v-if="loadingList" class="empty-card">正在加载...</view>
				<view v-else-if="diaries.length === 0" class="empty-card">还没有语音日记，先记录今天这一场。</view>
				<view v-else class="diary-list">
					<view v-for="item in diaries" :key="item.id" class="diary-card">
						<view class="diary-top">
							<text class="diary-date">{{ item.play_date || item.playDate }}</text>
							<text class="diary-mood">{{ item.mood || '未选择心情' }}</text>
						</view>
						<text class="diary-content">{{ item.content || '未识别到内容' }}</text>
						<text class="diary-time">{{ item.createTime }}</text>
					</view>
				</view>
			</view>
		</view>
	</Layout>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import Layout from '@/components/Layout/Layout.vue'

const LAN_API_BASE_URL = 'http://192.168.1.53:9000'
const getApiBaseUrl = () => {
	// #ifdef H5
	const host = window.location.hostname
	if (host === 'localhost' || host === '127.0.0.1') return 'http://127.0.0.1:9000'
	// #endif
	return LAN_API_BASE_URL
}

const API_BASE_URL = getApiBaseUrl()
const VOICE_DIARY_API_URL = `${API_BASE_URL}/api/diary/voice`
const DIARY_LIST_API_URL = `${API_BASE_URL}/api/diary/list`

const moods = ['开心', '一般', '疲惫', '状态很好', '有点累', '发挥不错']
const selectedMood = ref('状态很好')
const isRecording = ref(false)
const uploading = ref(false)
const recordStartTime = ref(0)
const recordStatus = ref('点击开始，录制 3 到 5 秒清晰普通话效果更好')
const recorder = ref(null)
const diaries = ref([])
const loadingList = ref(false)

const today = computed(() => {
	const d = new Date()
	const yyyy = d.getFullYear()
	const mm = String(d.getMonth() + 1).padStart(2, '0')
	const dd = String(d.getDate()).padStart(2, '0')
	return `${yyyy}-${mm}-${dd}`
})

const goBack = () => {
	uni.navigateBack()
}

const setupRecorder = () => {
	if (recorder.value) return
	if (!uni.getRecorderManager) {
		recordStatus.value = '当前运行环境不支持录音，请使用 App 真机调试'
		return
	}

	recorder.value = uni.getRecorderManager()
	recorder.value.onStart(() => {
		isRecording.value = true
		recordStartTime.value = Date.now()
		recordStatus.value = '录音中，再次点击停止'
	})
	recorder.value.onStop((res) => {
		isRecording.value = false
		handleRecordStop(res)
	})
	recorder.value.onError((err) => {
		isRecording.value = false
		recordStatus.value = '录音失败，请检查麦克风权限'
		console.error('录音失败', err)
	})
}

const toggleRecord = () => {
	if (uploading.value) return
	setupRecorder()
	if (!recorder.value) return

	if (isRecording.value) {
		recorder.value.stop()
		return
	}

	recorder.value.start({
		duration: 60000,
		sampleRate: 16000,
		numberOfChannels: 1,
		encodeBitRate: 96000,
		format: 'amr'
	})
}

const handleRecordStop = (res) => {
	const duration = Date.now() - recordStartTime.value
	if (!res.tempFilePath) {
		recordStatus.value = '录音文件为空，请重新录制'
		return
	}
	if (duration < 1500) {
		recordStatus.value = '录音时间太短，请至少录制 2 秒'
		return
	}

	uni.getFileInfo({
		filePath: res.tempFilePath,
		success: (info) => {
			if (!info.size || info.size <= 0) {
				recordStatus.value = '录音文件大小异常，请重新录制'
				return
			}
			uploadVoiceDiary(res.tempFilePath)
		},
		fail: () => {
			uploadVoiceDiary(res.tempFilePath)
		}
	})
}

const uploadVoiceDiary = (filePath) => {
	uploading.value = true
	recordStatus.value = '正在识别并保存日记...'
	uni.uploadFile({
		url: VOICE_DIARY_API_URL,
		filePath,
		name: 'audio',
		formData: {
			user_id: 1,
			play_date: today.value,
			mood: selectedMood.value || '',
			opponent: '',
			score: ''
		},
		success: (res) => {
			let body = {}
			try {
				body = JSON.parse(res.data)
			} catch (e) {
				body = {}
			}
			if (body.code === 200) {
				recordStatus.value = '保存成功'
				uni.showToast({ title: '日记已保存', icon: 'success' })
				loadDiaries()
			} else {
				recordStatus.value = body.message || '保存失败'
				uni.showToast({ title: recordStatus.value, icon: 'none' })
			}
		},
		fail: (err) => {
			console.error('上传语音日记失败', err)
			recordStatus.value = '上传失败，请检查后端服务'
			uni.showToast({ title: '上传失败', icon: 'none' })
		},
		complete: () => {
			uploading.value = false
		}
	})
}

const loadDiaries = () => {
	loadingList.value = true
	uni.request({
		url: DIARY_LIST_API_URL,
		method: 'GET',
		data: { user_id: 1, limit: 20 },
		success: (res) => {
			const body = res.data || {}
			if (body.code === 200 && Array.isArray(body.data)) {
				diaries.value = body.data
			} else {
				diaries.value = []
			}
		},
		fail: (err) => {
			console.error('加载日记失败', err)
			diaries.value = []
		},
		complete: () => {
			loadingList.value = false
		}
	})
}

onMounted(() => {
	setupRecorder()
	loadDiaries()
})

onUnmounted(() => {
	if (isRecording.value && recorder.value) recorder.value.stop()
})
</script>

<style scoped>
.container {
	min-height: 100vh;
	background: #000000;
	padding: 0 32rpx 60rpx;
	padding-top: calc(var(--status-bar-height) + 20rpx);
}

.header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 42rpx;
	padding: 8rpx 0;
}

.back-btn,
.header-spacer {
	width: 64rpx;
	height: 64rpx;
}

.back-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(255, 255, 255, 0.05);
	border-radius: 16rpx;
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

.hero-section {
	margin-bottom: 34rpx;
}

.hero-title {
	display: block;
	font-size: 44rpx;
	font-weight: 800;
	color: #ffffff;
	margin-bottom: 14rpx;
}

.hero-subtitle {
	display: block;
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.58);
	line-height: 1.5;
}

.section-title {
	font-size: 30rpx;
	font-weight: 700;
	color: var(--primary-green);
}

.mood-section,
.suggestions-section,
.history-section {
	margin-bottom: 34rpx;
}

.mood-list {
	display: flex;
	flex-wrap: wrap;
	gap: 14rpx;
	margin-top: 18rpx;
}

.mood-chip {
	padding: 14rpx 22rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.06);
	color: rgba(255, 255, 255, 0.72);
	font-size: 24rpx;
}

.mood-chip.active {
	background: var(--primary-green);
	color: #061606;
	font-weight: 800;
}

.record-panel {
	margin-bottom: 40rpx;
	padding: 38rpx 0 28rpx;
	border-radius: 24rpx;
	background: rgba(222, 255, 154, 0.06);
	border: 1rpx solid rgba(222, 255, 154, 0.16);
	display: flex;
	flex-direction: column;
	align-items: center;
}

.record-btn-wrapper {
	position: relative;
	width: 240rpx;
	height: 240rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 24rpx;
}

.ripple-outer,
.ripple-middle {
	position: absolute;
	border-radius: 50%;
	background: radial-gradient(circle, rgba(222, 255, 154, 0.24) 0%, transparent 70%);
}

.ripple-outer {
	width: 240rpx;
	height: 240rpx;
}

.ripple-middle {
	width: 190rpx;
	height: 190rpx;
	background: radial-gradient(circle, rgba(222, 255, 154, 0.32) 0%, transparent 70%);
}

.record-btn-wrapper.recording .ripple-outer {
	animation: pulse 1.4s ease-in-out infinite;
}

.record-btn {
	width: 160rpx;
	height: 160rpx;
	border-radius: 50%;
	background: var(--primary-green);
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	position: relative;
	z-index: 1;
	box-shadow: 0 10rpx 38rpx rgba(222, 255, 154, 0.3);
}

.mic-icon {
	font-size: 42rpx;
	margin-bottom: 8rpx;
	color: #061606;
}

.btn-text {
	font-size: 23rpx;
	color: #061606;
	font-weight: 800;
}

.record-status {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.68);
	text-align: center;
	padding: 0 32rpx;
}

.suggestion-list,
.diary-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	margin-top: 18rpx;
}

.suggestion-card,
.diary-card,
.empty-card {
	background: #0a0f0c;
	border: 1rpx solid rgba(255, 255, 255, 0.08);
	border-radius: 18rpx;
	padding: 22rpx;
}

.tag {
	display: inline-block;
	font-size: 22rpx;
	font-weight: 700;
	padding: 6rpx 16rpx;
	border-radius: 8rpx;
	margin-bottom: 12rpx;
	background: rgba(222, 255, 154, 0.16);
	color: var(--primary-green);
}

.suggestion-text,
.diary-content,
.empty-card {
	display: block;
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.75);
	line-height: 1.6;
}

.history-header,
.diary-top {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.refresh-btn {
	padding: 10rpx 18rpx;
	border-radius: 999rpx;
	background: rgba(255, 255, 255, 0.08);
	color: rgba(255, 255, 255, 0.78);
	font-size: 22rpx;
}

.diary-top {
	margin-bottom: 12rpx;
}

.diary-date {
	font-size: 24rpx;
	color: #ffffff;
	font-weight: 700;
}

.diary-mood {
	font-size: 22rpx;
	color: var(--primary-green);
}

.diary-time {
	display: block;
	margin-top: 14rpx;
	font-size: 21rpx;
	color: rgba(255, 255, 255, 0.42);
}

@keyframes pulse {
	0%, 100% {
		transform: scale(1);
		opacity: 0.7;
	}
	50% {
		transform: scale(1.18);
		opacity: 0.35;
	}
}
</style>
