<template>
	<Layout>
		<view class="container">
			<view class="header">
				<view class="back-btn" @tap="goBack">
					<text class="back-icon">←</text>
				</view>
				<view class="header-copy">
					<text class="page-title">球星动作对比</text>
					<text class="page-subtitle">上传你的视频，选择球星与动作类型，查看动作差异和训练建议</text>
				</view>
				<view class="status-pill" :class="{ ready: canCompare }">
					<text>{{ canCompare ? '可开始分析' : '等待上传' }}</text>
				</view>
			</view>

			<view class="stage-card">
				<view class="stage-head">
					<view>
						<text class="stage-title">双视频动作对比</text>
						<text class="stage-subtitle">左侧播放你的原始动作视频，右侧在分析完成后播放骨骼识别回放，并生成动作差异讲解。</text>
					</view>
					<view class="stage-actions" v-if="myVideo">
						<view class="mini-btn" @tap="toggleUserPlay">{{ playing ? '暂停' : '播放' }}</view>
						<view class="mini-btn ghost" @tap="resetVideos">重置</view>
					</view>
				</view>

				<view class="video-grid">
					<view class="video-card user-card">
						<view class="video-title-row">
							<view>
								<text class="video-title">我的动作</text>
								<text class="video-desc">{{ myVideo ? myVideo.name : '还没有选择视频' }}</text>
							</view>
							<text class="video-tag">{{ poseVideoUrl ? "骨骼回放" : "用户上传" }}</text>
						</view>
						<view class="video-shell" :class="{ empty: !myVideo }">
							<video
								v-if="myVideo"
								id="userVideo"
								:key="poseVideoUrl || myVideo.path"
								class="compare-video"
								:src="poseVideoUrl || myVideo.path"
								:controls="true"
								:autoplay="Boolean(poseVideoUrl)"
								:muted="Boolean(poseVideoUrl)"
								:show-center-play-btn="true"
							/>
							<view v-else class="video-placeholder" @tap="uploadMyVideo">
								<text class="placeholder-icon">↑</text>
								<text class="placeholder-title">上传你的动作视频</text>
								<text class="placeholder-text">建议使用完整单次击球片段，人物身体关键点清晰可见</text>
							</view>
						</view>
					</view>

					<view class="video-card standard-card">
						<view class="video-title-row">
							<view>
								<text class="video-title">{{ selectedPlayer.name }} · {{ selectedStroke.name }}</text>
								<text class="video-desc">{{ bestMatchText }}</text>
							</view>
							<text class="video-tag standard">对比目标</text>
						</view>
						<view class="video-shell" :class="{ empty: !standardPoseVideoUrl }">
							<video
								v-if="standardPoseVideoUrl"
								id="poseVideo"
								:key="standardPoseVideoUrl"
								class="compare-video"
								:src="standardPoseVideoUrl"
								:controls="true"
								:autoplay="Boolean(standardPoseVideoUrl)"
								:muted="Boolean(standardPoseVideoUrl)"
								:show-center-play-btn="true"
							/>
							<view v-else class="standard-info-shell">
								<view class="match-score">
									<text class="match-label">当前目标</text>
									<text class="match-main">{{ selectedPlayer.name }} · {{ selectedStroke.name }}</text>
									<text class="match-sub">{{ distanceText }}</text>
								</view>
								<view class="match-note">
									<text>{{ analyzing ? '正在生成骨骼识别回放...' : '分析完成后会在这里播放带 MediaPipe 骨骼的人体回放。' }}</text>
								</view>
							</view>
							<view v-if="standardPoseVideoUrl" class="skeleton-badge">标准骨骼回放</view>
						</view>
					</view>
				</view>
			</view>

			<view class="workspace-grid">
				<view class="panel target-panel">
					<view class="panel-head">
						<view class="panel-icon">库</view>
						<view>
							<text class="panel-title">选择对比目标</text>
							<text class="panel-subtitle">选择你想参考的球星与击球动作</text>
						</view>
					</view>

					<text class="selector-label">球星</text>
					<view class="selector-group players">
						<view
							v-for="player in players"
							:key="player.id"
							class="selector-chip player"
							:class="{ active: selectedPlayer.id === player.id }"
							@tap="selectPlayer(player)"
						>
							<text>{{ player.name }}</text>
						</view>
					</view>

					<text class="selector-label">动作类型</text>
					<view class="selector-group strokes">
						<view
							v-for="stroke in strokeTypes"
							:key="stroke.id"
							class="selector-chip stroke"
							:class="{ active: selectedStroke.id === stroke.id }"
							@tap="selectStroke(stroke)"
						>
							<text>{{ stroke.name }}</text>
						</view>
					</view>

					<view class="path-box">
						<text class="path-title">说明</text>
						<text class="path-text">选择球星和动作类型后，系统会根据你的上传视频生成动作对比结果。</text>
					</view>
				</view>

				<view class="panel action-panel">
					<view class="panel-head">
						<view class="panel-icon user">U</view>
						<view>
							<text class="panel-title">上传与分析</text>
							<text class="panel-subtitle">上传视频后开始智能动作分析</text>
						</view>
					</view>

					<view class="upload-strip" @tap="uploadMyVideo">
						<view class="upload-mark">↑</view>
						<view class="upload-copy">
							<text class="upload-title">{{ myVideo ? '重新选择视频' : '上传我的视频' }}</text>
							<text class="upload-subtitle">{{ myVideo ? myVideo.name : '支持相册中的 mp4 视频' }}</text>
						</view>
					</view>

					<view class="compare-btn" :class="{ disabled: !canCompare || analyzing }" @tap="startCompare">
						<text>{{ analyzing ? `正在分析... ${progressText}` : '开始分析' }}</text>
					</view>

					<view class="resource-card">
						<text class="resource-title">分析流程</text>
						<text class="resource-text">上传视频并识别动作片段</text>
						<text class="resource-text">生成动作差异与训练建议</text>
					</view>
				</view>
			</view>

			<view class="report-card">
				<view class="report-head">
					<view>
						<text class="report-title">动作差异讲解</text>
						<text class="report-subtitle">展示动作差异、主要问题和训练建议</text>
					</view>
					<text class="report-status">{{ reportStatus }}</text>
				</view>
				<view v-if="analysisError" class="error-box">{{ analysisError }}</view>
				<view v-else-if="analysisReport" class="report-content">
					<text class="report-line" v-for="(line, index) in reportLines" :key="index">{{ line }}</text>
				</view>
				<view v-else class="empty-report">
					<text>上传视频并点击开始分析后，系统会自动识别动作片段，并生成动作差异讲解。</text>
				</view>
			</view>
		</view>
	</Layout>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import Layout from '@/components/Layout/Layout.vue'

const API_BASE_URL = 'http://127.0.0.1:9000'
const POLL_INTERVAL_MS = 1200
const MAX_POLL_COUNT = 180

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
const analysisError = ref('')
const analysisReport = ref('')
const poseVideoUrl = ref('')
const standardPoseVideoUrl = ref('')
const userVideoContext = ref(null)
const poseVideoContext = ref(null)
const playbackPlan = ref(null)
const bestMatchText = ref('等待分析')
const distanceText = ref('相似度将在分析后显示')
const progressText = ref('0%')
const taskOffset = ref(0)


const canCompare = computed(() => Boolean(myVideo.value))
const reportStatus = computed(() => analysisError.value ? '失败' : analyzing.value ? '分析中' : analysisReport.value ? '已生成' : '待分析')
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

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const uploadMyVideo = async () => {
	const res = await pickVideo()
	if (!res) return
	myVideo.value = {
		path: res.tempFilePath,
		name: getVideoName(res.tempFilePath)
	}
	analysisError.value = ''
	analysisReport.value = ''
	poseVideoUrl.value = ''
	standardPoseVideoUrl.value = ''
	bestMatchText.value = '等待分析'
	distanceText.value = '相似度将在分析后显示'
	progressText.value = '0%'
}

const selectPlayer = (player) => {
	selectedPlayer.value = player
}

const selectStroke = (stroke) => {
	selectedStroke.value = stroke
	analysisError.value = ''
	analysisReport.value = ''
	bestMatchText.value = '等待分析'
	distanceText.value = '相似度将在分析后显示'
}

const ensureVideoContexts = () => {
	if (!userVideoContext.value) userVideoContext.value = uni.createVideoContext('userVideo')
	if (!poseVideoContext.value) poseVideoContext.value = uni.createVideoContext('poseVideo')
}

const startCompare = async () => {
	if (!canCompare.value || analyzing.value) {
		uni.showToast({ title: '请先上传视频', icon: 'none' })
		return
	}

	analyzing.value = true
	analysisError.value = ''
	analysisReport.value = '正在上传视频并进行动作分析，请稍候...'
	poseVideoUrl.value = ''
	standardPoseVideoUrl.value = ''
	bestMatchText.value = `${selectedPlayer.value.name} · ${selectedStroke.value.name}`
	distanceText.value = '请稍等'
	progressText.value = '0%'
	taskOffset.value = 0

	try {
		const taskId = await submitAnalyzeTask()
		const result = await pollAnalyzeTask(taskId)
		applyAnalysisResult(result)
	} catch (error) {
		analysisReport.value = ''
		analysisError.value = error.message || '视频分析失败'
	} finally {
		analyzing.value = false
	}
}

const submitAnalyzeTask = async () => {
	const formData = new FormData()
	const userBlob = await fetch(myVideo.value.path).then((res) => res.blob())
	formData.append('file', userBlob, myVideo.value.name || 'user_video.mp4')
	formData.append('selected_player', selectedPlayer.value.name)
	formData.append('selected_stroke', selectedStroke.value.id)
	formData.append('source_page', 'training_action_comparison')

	const response = await fetch(`${API_BASE_URL}/api/analyze_video_submit`, {
		method: 'POST',
		body: formData
	})

	if (!response.ok) {
		throw new Error(`视频分析提交失败：${response.status}`)
	}

	const data = await response.json()
	if (!data.task_id) {
		throw new Error('分析任务创建失败')
	}
	return data.task_id
}

const pollAnalyzeTask = async (taskId) => {
	const collected = []

	for (let i = 0; i < MAX_POLL_COUNT; i += 1) {
		progressText.value = `${Math.min(95, Math.round((i / MAX_POLL_COUNT) * 100))}%`
		const response = await fetch(`${API_BASE_URL}/api/analyze_video_poll/${taskId}?offset=${taskOffset.value}`)
		if (!response.ok) {
			throw new Error(`轮询分析结果失败：${response.status}`)
		}

		const data = await response.json()
		const items = Array.isArray(data.items) ? data.items : []
		collected.push(...items)
		taskOffset.value = data.total || taskOffset.value + items.length

		const errorItem = items.find((item) => item.type === 'error')
		if (errorItem) {
			throw new Error(errorItem.message || '动作分析失败')
		}

		if (data.done) {
			progressText.value = '100%'
			return collected
		}

		await sleep(POLL_INTERVAL_MS)
	}

	throw new Error('分析超时，请稍后重试')
}

const applyAnalysisResult = (items) => {
	const segments = items.filter((item) => item.type === 'segment').map((item) => item.data || {})
	const summaryItem = items.find((item) => item.type === 'summary')
	const summary = summaryItem?.data || {}

	if (!segments.length) {
		bestMatchText.value = '没有识别到有效动作'
		distanceText.value = '请换更清晰的视频再试'
		analysisReport.value = '没有识别到有效击球片段。建议上传完整单次击球视频，并确保人物身体关键点清晰可见。'
		return
	}

	const first = segments[0]
	const annotatedVideo = findFirstValue(first, ['pose_video_url', 'annotated_video_url', 'skeleton_video_url', 'result_video_url', 'output_video_url']) || findFirstValue(summary, ['pose_video_url', 'annotated_video_url', 'skeleton_video_url', 'result_video_url', 'output_video_url'])
	if (annotatedVideo) poseVideoUrl.value = normalizeMediaUrl(annotatedVideo)
	const standardAnnotatedVideo = findFirstValue(first, ['standard_pose_video_url', 'standard_annotated_video_url', 'standard_skeleton_video_url']) || findFirstValue(first.analysis || {}, ['standard_pose_video_url', 'standard_annotated_video_url'])
	if (standardAnnotatedVideo) standardPoseVideoUrl.value = normalizeMediaUrl(standardAnnotatedVideo)
	playbackPlan.value = buildPlaybackPlan(first, summary)
	const analysis = first.analysis || first.dtw_analysis || first.result || {}
	const best = findFirstValue(analysis, ['best_match', 'standard', 'matched_standard', 'standard_name', 'match_name']) || findFirstValue(first, ['best_match', 'standard', 'matched_standard']) || '职业标准动作'
	const distance = findFirstValue(analysis, ['distance', 'dtw_distance', 'phase_dtw_distance', 'score_distance']) || findFirstValue(first, ['distance', 'dtw_distance'])
	const grade = findFirstValue(analysis, ['grade', 'rating']) || findFirstValue(first, ['grade', 'rating']) || ''

	bestMatchText.value = best
	distanceText.value = distance !== undefined && distance !== null ? `相似度距离：${formatNumber(distance)}${grade ? `，评级：${grade}` : ''}` : '已完成动作匹配'
	analysisReport.value = buildReportFromSegments(segments, summary)
	playAnalyzedVideos()
}
const normalizeMediaUrl = (url) => {
	if (!url || typeof url !== 'string') return ''
	if (/^https?:\/\//.test(url) || url.startsWith('blob:') || url.startsWith('file:')) return url
	return `${API_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`
}

const findFirstValue = (source, keys) => {
	if (!source || typeof source !== 'object') return undefined
	for (const key of keys) {
		if (source[key] !== undefined && source[key] !== null && source[key] !== '') return source[key]
	}
	return undefined
}

const formatNumber = (value) => {
	const num = Number(value)
	return Number.isFinite(num) ? num.toFixed(2) : value
}

const buildReportFromSegments = (segments, summary) => {
	const lines = []
	lines.push(`总结：共识别到 ${segments.length} 个动作片段。${summary?.fps ? `FPS ${summary.fps}` : ''}`)

	segments.forEach((segment, index) => {
		const analysis = segment.analysis || segment.dtw_analysis || segment.result || {}
		const shot = segment.shot_type_cn || segment.shot_type || `片段 ${index + 1}`
		const grade = findFirstValue(analysis, ['grade', 'rating']) || segment.grade || '未评级'
		const distance = findFirstValue(analysis, ['distance', 'dtw_distance', 'phase_dtw_distance']) || segment.distance
		const best = findFirstValue(analysis, ['best_match', 'standard', 'matched_standard', 'standard_name']) || segment.best_match || '职业标准动作'
		const advice = segment.coach_advice || segment.advice || analysis.coach_advice || ''
		const problems = extractProblems(analysis, segment)

		lines.push(`片段 ${index + 1}：${shot}`)
		lines.push(`参考动作：${best}`)
		lines.push(`评分：${grade}${distance !== undefined && distance !== null ? `，相似度距离：${formatNumber(distance)}` : ''}`)
		if (problems.length) lines.push(`主要问题：${problems.join('；')}`)
		if (advice) lines.push(`教练建议：${advice}`)
	})

	return lines.join('\n')
}

const extractProblems = (analysis, segment) => {
	const candidates = analysis.major_problems || analysis.problems || segment.major_problems || segment.problems || []
	if (!Array.isArray(candidates)) return []
	return candidates.slice(0, 4).map((item) => {
		if (typeof item === 'string') return item
		const joint = item.joint || item.name || item.part || item.phase || '问题点'
		const diff = item.diff ?? item.difference ?? item.angle_diff ?? item.distance
		return diff !== undefined && diff !== null ? `${joint} ${formatNumber(diff)}` : joint
	})
}

const buildPlaybackPlan = (segment, summary) => {
	const analysis = segment.analysis || {}
	const userAnn = analysis.user_annotation || segment.user_annotation || {}
	const standardAnn = segment.standard_annotation || analysis.standard_annotation || {}
	return {
		user: annotationToPlaybackRange(userAnn, summary?.fps),
		standard: annotationToPlaybackRange(standardAnn, standardAnn?.fps || summary?.fps)
	}
}

const annotationToPlaybackRange = (annotation, fallbackFps = 30) => {
	const range = annotation?.segment_range
	const fps = Number(annotation?.fps || fallbackFps || 30)
	if (!Array.isArray(range) || range.length < 2 || !Number.isFinite(fps) || fps <= 0) {
		return { start: 0, duration: 0 }
	}
	const startFrame = Number(range[0]) || 0
	const endFrame = Number(range[1]) || startFrame
	const start = Math.max(0, startFrame / fps)
	const duration = Math.max(0, (endFrame - startFrame) / fps)
	return { start, duration }
}
const playAnalyzedVideos = async () => {
	await nextTick()
	ensureVideoContexts()
	const plan = playbackPlan.value || {}
	const userRange = plan.user || { start: 0, duration: 0 }
	const standardRange = plan.standard || { start: 0, duration: 0 }

	if (poseVideoUrl.value) {
		userVideoContext.value?.seek(userRange.start || 0)
		userVideoContext.value?.play()
	}
	if (standardPoseVideoUrl.value) {
		poseVideoContext.value?.seek(standardRange.start || 0)
		poseVideoContext.value?.play()
	}
	playing.value = Boolean(poseVideoUrl.value || standardPoseVideoUrl.value)
}

const toggleUserPlay = () => {
	if (!myVideo.value) return
	ensureVideoContexts()
	if (playing.value) {
		userVideoContext.value.pause()
		playing.value = false
	} else {
		userVideoContext.value.play()
		playing.value = true
	}
}

const resetVideos = () => {
	ensureVideoContexts()
	userVideoContext.value?.seek(0)
	userVideoContext.value?.pause()
	playing.value = false
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	box-sizing: border-box;
	background: #050609;
	padding: 0 28rpx 56rpx;
	padding-top: calc(var(--status-bar-height) + 18rpx);
}

.header {
	display: flex;
	align-items: center;
	gap: 22rpx;
	margin-bottom: 24rpx;
}

.back-btn {
	width: 64rpx;
	height: 64rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #151821;
	border: 1rpx solid rgba(255,255,255,.08);
	border-radius: 16rpx;
}

.back-icon {
	font-size: 36rpx;
	color: #fff;
	font-weight: 800;
}

.header-copy {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 8rpx;
	min-width: 0;
}

.page-title {
	font-size: 38rpx;
	font-weight: 900;
	color: #fff;
}

.page-subtitle {
	font-size: 22rpx;
	color: rgba(255,255,255,.56);
	line-height: 1.4;
}

.status-pill {
	padding: 12rpx 18rpx;
	border-radius: 999rpx;
	background: #1b1f2a;
	border: 1rpx solid rgba(255,255,255,.08);
}

.status-pill text {
	font-size: 21rpx;
	font-weight: 800;
	color: rgba(255,255,255,.48);
}

.status-pill.ready {
	background: rgba(38,201,133,.14);
	border-color: rgba(38,201,133,.42);
}

.status-pill.ready text {
	color: #a8ff9e;
}

.stage-card,
.panel,
.report-card {
	background: #10131b;
	border: 1rpx solid rgba(222,255,154,.14);
	border-radius: 22rpx;
	box-shadow: 0 18rpx 50rpx rgba(0,0,0,.28);
}

.stage-card {
	padding: 24rpx;
	margin-bottom: 20rpx;
}

.stage-head,
.video-title-row,
.panel-head,
.report-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 18rpx;
}

.stage-head {
	margin-bottom: 20rpx;
}

.stage-title,
.panel-title,
.report-title,
.video-title {
	display: block;
	font-size: 28rpx;
	font-weight: 900;
	color: #fff;
}

.stage-subtitle,
.panel-subtitle,
.report-subtitle,
.video-desc {
	display: block;
	font-size: 21rpx;
	color: rgba(255,255,255,.5);
	line-height: 1.45;
	margin-top: 6rpx;
}

.video-desc {
	max-width: 520rpx;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.stage-actions {
	display: flex;
	gap: 12rpx;
	flex-shrink: 0;
}

.mini-btn {
	min-width: 112rpx;
	height: 54rpx;
	padding: 0 16rpx;
	border-radius: 14rpx;
	background: #26c985;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 22rpx;
	font-weight: 900;
	color: #06120d;
}

.mini-btn.ghost {
	background: #1d2230;
	color: #fff;
}

.video-grid,
.workspace-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 20rpx;
}

.video-card {
	min-width: 0;
}

.video-title-row {
	align-items: flex-start;
	margin-bottom: 14rpx;
}

.video-tag {
	flex-shrink: 0;
	font-size: 19rpx;
	font-weight: 900;
	color: #a8ff9e;
	background: rgba(51,255,61,.12);
	padding: 7rpx 12rpx;
	border-radius: 999rpx;
}

.video-tag.standard {
	color: #78d8ff;
	background: rgba(120,216,255,.12);
}

.video-shell,
.standard-info-shell {
	position: relative;
	width: 100%;
	aspect-ratio: 16 / 9;
	background: #000;
	border-radius: 18rpx;
	overflow: hidden;
	border: 1rpx solid rgba(255,255,255,.08);
}

.compare-video {
	width: 100%;
	height: 100%;
	background: #000;
}

.video-shell.empty {
	background: #0b0e15;
	border-style: dashed;
	border-color: rgba(38,201,133,.38);
}

.video-placeholder,
.standard-info-shell {
	height: 100%;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-direction: column;
	gap: 12rpx;
	padding: 32rpx;
	box-sizing: border-box;
	text-align: center;
}

.standard-info-shell {
	background: radial-gradient(circle at top, rgba(38,201,133,.16), #0b0e15 56%);
}


.video-grid {
	align-items: start;
}

.video-card {
	display: flex;
	flex-direction: column;
}

.video-title-row {
	min-height: 72rpx;
}

.video-title-row > view {
	min-width: 0;
}

.video-shell,
.standard-info-shell {
	box-sizing: border-box;
	height: auto;
	min-height: 0;
	flex: none;
}

.video-placeholder {
	position: absolute;
	inset: 0;
	height: auto;
}

.standard-info-shell {
	height: auto;
}

.placeholder-icon {
	width: 72rpx;
	height: 72rpx;
	border-radius: 18rpx;
	background: #26c985;
	color: #06120d;
	font-size: 36rpx;
	font-weight: 900;
	line-height: 72rpx;
}

.placeholder-title,
.match-main {
	font-size: 27rpx;
	font-weight: 900;
	color: #fff;
}

.placeholder-text,
.match-sub,
.match-note text {
	font-size: 21rpx;
	line-height: 1.45;
	color: rgba(255,255,255,.48);
}

.match-label {
	display: block;
	font-size: 20rpx;
	color: #a8ff9e;
	font-weight: 900;
	margin-bottom: 10rpx;
}

.match-main,
.match-sub {
	display: block;
}

.match-sub {
	margin-top: 10rpx;
}

.skeleton-badge {
	position: absolute;
	left: 14rpx;
	bottom: 14rpx;
	font-size: 19rpx;
	font-weight: 800;
	color: #a8ff9e;
	background: rgba(0,0,0,.62);
	padding: 7rpx 12rpx;
	border-radius: 999rpx;
}

.workspace-grid {
	margin-bottom: 20rpx;
}

.panel {
	padding: 24rpx;
	min-width: 0;
}

.panel-head {
	justify-content: flex-start;
	margin-bottom: 22rpx;
}

.panel-icon {
	width: 54rpx;
	height: 54rpx;
	border-radius: 14rpx;
	background: rgba(51,255,61,.14);
	color: #a8ff9e;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24rpx;
	font-weight: 900;
	flex-shrink: 0;
}

.panel-icon.user {
	background: rgba(38,201,133,.18);
	color: #7bf5c2;
}

.selector-label {
	display: block;
	font-size: 21rpx;
	font-weight: 900;
	color: rgba(255,255,255,.54);
	margin: 18rpx 0 12rpx;
}

.selector-group {
	display: flex;
	flex-wrap: wrap;
	gap: 12rpx;
}

.selector-chip {
	padding: 17rpx 21rpx;
	border-radius: 15rpx;
	background: #171b25;
	border: 1rpx solid rgba(255,255,255,.08);
}

.selector-chip text {
	font-size: 23rpx;
	color: rgba(255,255,255,.72);
	font-weight: 800;
}

.selector-chip.active {
	background: rgba(51,255,61,.12);
	border-color: rgba(51,255,61,.58);
}

.selector-chip.active text {
	color: #a8ff9e;
}

.path-box,
.resource-card {
	margin-top: 22rpx;
	padding: 18rpx;
	border-radius: 16rpx;
	background: #0b0e15;
	border: 1rpx solid rgba(255,255,255,.06);
}

.path-title,
.resource-title {
	display: block;
	font-size: 21rpx;
	font-weight: 900;
	color: #fff;
	margin-bottom: 8rpx;
}

.path-text,
.resource-text {
	display: block;
	font-size: 20rpx;
	line-height: 1.5;
	color: rgba(255,255,255,.5);
	word-break: break-all;
}

.upload-strip {
	display: flex;
	align-items: center;
	gap: 16rpx;
	padding: 20rpx;
	border-radius: 18rpx;
	background: rgba(38,201,133,.1);
	border: 1rpx solid rgba(38,201,133,.24);
}

.upload-mark {
	width: 66rpx;
	height: 66rpx;
	border-radius: 18rpx;
	background: #26c985;
	color: #06120d;
	font-size: 34rpx;
	font-weight: 900;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.upload-copy {
	flex: 1;
	min-width: 0;
}

.upload-title,
.upload-subtitle {
	display: block;
}

.upload-title {
	font-size: 25rpx;
	font-weight: 900;
	color: #fff;
}

.upload-subtitle {
	font-size: 21rpx;
	color: rgba(255,255,255,.5);
	margin-top: 6rpx;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.compare-btn {
	margin-top: 18rpx;
	height: 82rpx;
	border-radius: 18rpx;
	background: #26c985;
	display: flex;
	align-items: center;
	justify-content: center;
}

.compare-btn text {
	font-size: 28rpx;
	font-weight: 900;
	color: #06120d;
}

.compare-btn.disabled {
	background: #20232d;
}

.compare-btn.disabled text {
	color: rgba(255,255,255,.34);
}

.report-card {
	padding: 26rpx;
}

.report-head {
	align-items: flex-start;
	margin-bottom: 20rpx;
}

.report-status {
	font-size: 22rpx;
	font-weight: 900;
	color: #a8ff9e;
	background: rgba(51,255,61,.1);
	padding: 8rpx 14rpx;
	border-radius: 999rpx;
	flex-shrink: 0;
}

.report-content {
	display: flex;
	flex-direction: column;
	gap: 13rpx;
}

.report-line,
.empty-report text {
	font-size: 24rpx;
	color: rgba(255,255,255,.82);
	line-height: 1.65;
}

.empty-report {
	padding: 22rpx;
	border-radius: 16rpx;
	background: #0b0e15;
	border: 1rpx dashed rgba(255,255,255,.1);
}

.error-box {
	font-size: 24rpx;
	line-height: 1.5;
	color: #ff7474;
	background: rgba(255,80,80,.1);
	border: 1rpx solid rgba(255,80,80,.22);
	border-radius: 14rpx;
	padding: 18rpx;
	margin-bottom: 16rpx;
}

.back-btn:active,
.selector-chip:active,
.upload-strip:active,
.compare-btn:active,
.mini-btn:active,
.video-placeholder:active {
	transform: scale(.98);
}

@media (max-width: 700px) {
	.header {
		align-items: flex-start;
	}

	.status-pill {
		display: none;
	}

	.stage-head,
	.report-head {
		align-items: flex-start;
		flex-direction: column;
	}

	.stage-actions {
		width: 100%;
	}

	.mini-btn {
		flex: 1;
	}

	.video-grid,
	.workspace-grid {
		grid-template-columns: 1fr;
	}
}
</style>






























