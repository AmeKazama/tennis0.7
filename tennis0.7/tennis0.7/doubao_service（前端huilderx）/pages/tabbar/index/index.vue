<template>
	<view class="container">
		<view class="video-area"
			@touchstart="onTouchStart"
			@touchmove="onTouchMove"
			@touchend="onTouchEnd"
		>
			<!-- 顶层 Tab -->
			<view class="top-tabs">
				<view class="tab-item" :class="{ active: videoTab === 'following' }" @tap="videoTab = 'following'">Following</view>
				<view class="tab-divider">·</view>
				<view class="tab-item" :class="{ active: videoTab === 'forYou' }" @tap="videoTab = 'forYou'">For You</view>
			</view>

			<!-- renderjs DOM 视频容器 -->
			<view id="social-video-container" class="video-wrapper"
				:video-data="currentVideoData"
				:change:video-data="socialVideo.renderVideo"
			></view>

			<!-- UI 浮层 -->
			<view class="overlay" @dblclick="handleDoubleClick">
				<view class="bottom-info">
					<view class="video-info">
						<view class="author-info">
							<view class="author-name">{{ currentVideo.author || '' }}</view>
							<view class="verified">✓</view>
						</view>
						<view class="video-desc">{{ currentVideo.desc || '' }}</view>
						<view class="music-info">
							<view class="music-icon">🎵</view>
							<view class="music-name">{{ currentVideo.music || '' }}</view>
						</view>
					</view>
					<view class="action-bar">
						<view class="action-item avatar-wrapper">
							<image class="avatar" :src="currentVideo.avatar || ''" mode="aspectFill" @tap="openUserProfile(currentVideo.userId)"></image>
							<view class="follow-badge" :class="{ followed: currentVideo.isFollowed }" @tap="handleFollow(currentVideo)">
								{{ currentVideo.isFollowed ? 'V' : '+' }}
							</view>
						</view>
						<view class="action-item" @tap="toggleLike(currentVideo)">
							<view class="like-icon" :class="{ liked: currentVideo.isLiked }">{{ currentVideo.isLiked ? '♥' : '♡' }}</view>
							<view class="action-count">{{ formatNumber(currentVideo.likes) }}</view>
						</view>
						<view class="action-item" @tap="openComments(currentVideo)">
							<view class="comment-icon">✉</view>
							<view class="action-count">{{ formatNumber(currentVideo.comments) }}</view>
						</view>
						<view class="action-item" @tap="chooseFavoriteFolder(currentVideo)">
							<view class="favorite-icon" :class="{ collected: currentVideo.isCollected }">{{ currentVideo.isCollected ? '★' : '☆' }}</view>
							<view class="action-count">{{ formatNumber(currentVideo.shares) }}</view>
						</view>
						<view class="action-item music-disc-wrapper">
							<view class="music-disc" :class="{ spinning: true }">
								<image class="disc-cover" :src="currentVideo.poster || ''" mode="aspectFill"></image>
							</view>
						</view>
					</view>
				</view>
				<view class="like-heart-animation" v-if="showHeart" :style="heartStyle">❤</view>
			</view>

			<!-- 进度条 -->
			<view class="progress-bar">
				<view class="progress-fill" :style="{ width: progressPercent + '%' }"></view>
			</view>
		</view>

		<CustomTabBar />
	</view>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import CustomTabBar from '@/components/CustomTabBar/CustomTabBar.vue'
import { addFavorite, getFavoriteFolders, isFavorited, isFollowing, removeFavorite, toggleFollow } from '@/utils/social-store/index.js'

const videoTab = ref('forYou')
const currentVideoIndex = ref(0)
const showHeart = ref(false)
const heartStyle = ref({})
const progressPercent = ref(0)
let progressTimer = null
let lastTapTime = 0
let touchStartY = 0
let touchMoveY = 0

const mockDataList = reactive([])
const currentVideo = computed(() => mockDataList[currentVideoIndex.value] || {})
const currentVideoData = computed(() => JSON.stringify({
	url: currentVideo.value.videoUrl || '',
	poster: currentVideo.value.poster || '',
	type: currentVideo.value.mediaType || 'video' // 传递类型
}))
const LAN_FEED_API_BASE_URL = 'http://10.24.57.203:8003'
const getFeedApiBaseUrl = () => {
	// #ifdef H5
	const host = window.location.hostname
	if (host === 'localhost' || host === '127.0.0.1') {
		return 'http://127.0.0.1:9000'
	}
	// #endif
	return LAN_FEED_API_BASE_URL
}
const FEED_API_BASE_URL = getFeedApiBaseUrl()
const fallbackVideoList = [
	{
		id: 'demo_1',
		userId: 'u1',
		videoUrl: 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4',
		poster: '/static/media/bessi-tennis-1381230.jpg',
		avatar: 'https://i.pravatar.cc/150?u=1',
		author: '@TennisCoach_1',
		desc: '演示视频：后端视频流服务不可用时的兜底播放内容。',
		music: 'Original Sound - Tennis',
		likes: 125000,
		comments: 4567,
		shares: 890,
		isLiked: false,
		isFollowed: false,
		isCollected: false
	},
	{
		id: 'demo_2',
		userId: 'u2',
		videoUrl: 'https://media.w3.org/2010/05/sintel/trailer.mp4',
		poster: '/static/media/dietmaha-tennis-251907_1920.jpg',
		avatar: 'https://i.pravatar.cc/150?u=2',
		author: '@TennisCoach_2',
		desc: '演示视频：用于验证前端播放器、滑动切换和互动按钮。',
		music: 'Training Beat',
		likes: 89500,
		comments: 3456,
		shares: 567,
		isLiked: false,
		isFollowed: false,
		isCollected: false
	},
	{
		id: 'demo_3',
		userId: 'u3',
		videoUrl: 'https://media.w3.org/2010/05/bunny/trailer.mp4',
		poster: '/static/media/felix1999-tennis-ball-4716315_1920.jpg',
		avatar: 'https://i.pravatar.cc/150?u=3',
		author: '@TennisCoach_3',
		desc: '演示视频：真实 feed/list 接口接好后会自动替换这些数据。',
		music: 'Court Vision',
		likes: 234000,
		comments: 6789,
		shares: 1234,
		isLiked: false,
		isFollowed: false,
		isCollected: false
	}
]

const setVideoList = (list) => {
	mockDataList.length = 0
	list.forEach((item) => {
		mockDataList.push(item)
	})
	currentVideoIndex.value = 0
	refreshSocialState()
}

const switchVideo = (dir) => {
	const len = mockDataList.length
	if (len === 0) return
	if (dir === 'next') {
		currentVideoIndex.value = (currentVideoIndex.value + 1) % len
	} else {
		currentVideoIndex.value = (currentVideoIndex.value - 1 + len) % len
	}
	progressPercent.value = 0
}

const onTouchStart = (e) => {
	touchStartY = e.touches[0].clientY
	touchMoveY = touchStartY
}

const onTouchMove = (e) => {
	touchMoveY = e.touches[0].clientY
}

const onTouchEnd = () => {
	const diff = touchMoveY - touchStartY
	if (Math.abs(diff) > 50) {
		if (diff < 0) switchVideo('next')
		else switchVideo('prev')
	}
}

const toggleLike = (item) => {
	item.isLiked = !item.isLiked
	item.likes += item.isLiked ? 1 : -1
}

const refreshSocialState = () => {
	mockDataList.forEach((item) => {
		item.isFollowed = isFollowing(item.userId)
		item.isCollected = isFavorited(item.id)
	})
}

const handleFollow = (item) => {
	const followed = toggleFollow(item.userId)
	item.isFollowed = followed
	uni.showToast({
		title: followed ? '已关注' : '已取消关注',
		icon: 'none'
	})
}

const chooseFavoriteFolder = (item) => {
	if (isFavorited(item.id)) {
		removeFavorite(item.id)
		item.isCollected = false
		uni.showToast({
			title: '已取消收藏',
			icon: 'none'
		})
		return
	}

	const folders = getFavoriteFolders()
	uni.showActionSheet({
		itemList: folders.map((folder) => folder.name),
		success: (res) => {
			const folder = folders[res.tapIndex]
			addFavorite(folder.id, item)
			item.isCollected = true
			uni.showToast({
				title: `已收藏到${folder.name}`,
				icon: 'none'
			})
		}
	})
}

const openComments = (item) => {
	uni.navigateTo({
		url: `/pages/social/comments-detail/comments-detail?postId=${encodeURIComponent(item.id)}&author=${encodeURIComponent(item.author)}&avatar=${encodeURIComponent(item.avatar)}&title=${encodeURIComponent(item.desc)}&poster=${encodeURIComponent(item.poster)}&comments=${item.comments}`
	})
}

const openUserProfile = (userId) => {
	uni.navigateTo({
		url: `/pages/profile/user-profile/user-profile?userId=${encodeURIComponent(userId)}`
	})
}

const handleDoubleClick = () => {
	const now = Date.now()
	if (now - lastTapTime < 300) {
		const item = currentVideo.value
		if (item && !item.isLiked) {
			item.isLiked = true
			item.likes += 1
		}
		showHeart.value = true
		heartStyle.value = {
			left: '50%',
			top: '50%',
			transform: 'translate(-50%, -50%)'
		}
		setTimeout(() => {
			showHeart.value = false
		}, 800)
	}
	lastTapTime = now
}

const formatNumber = (num) => {
	if (num == null) return '0'
	if (num >= 1000000) {
		return (num / 1000000).toFixed(1) + 'M'
	} else if (num >= 1000) {
		return (num / 1000).toFixed(1) + 'K'
	}
	return num.toString()
}

const startProgress = () => {
	progressPercent.value = 0
	stopProgress()
	progressTimer = setInterval(() => {
		progressPercent.value += 0.5
		if (progressPercent.value >= 100) {
			progressPercent.value = 0
		}
	}, 100)
}

const stopProgress = () => {
	if (progressTimer) {
		clearInterval(progressTimer)
		progressTimer = null
	}
}

// 修复后的请求函数（100%解决报错+对接后端）
const fetchVideoList = async () => {
	try {
		// 核心：你的后端地址是 10.24.57.203:8003 必须写死正确！
		const baseUrl = "http://10.24.57.203:8003"
		
		uni.request({
			url: baseUrl + "/api/feed/list",
			method: "GET",
			data: { page: 1, page_size: 10 },
			success: (response) => {
				console.log("✅ 后端返回数据：", response)
				// 正确解析后端数据
				if (response.data && response.data.code === 200) {
					const backendList = response.data.data
					if (backendList.length > 0) {
						setVideoList(backendList.map(item => ({
							id: item.id,
							userId: item.id,
							videoUrl: baseUrl + item.src,
							poster: baseUrl + item.cover,
							avatar: "https://i.pravatar.cc/150?u=" + item.id,
							author: '@TennisUser',
							desc: item.desc || item.title,
							music: 'Original Sound',
							likes: Math.floor(Math.random()*10000),
							comments: Math.floor(Math.random()*1000),
							shares: Math.floor(Math.random()*500),
							isLiked: false,
							isFollowed: false,
							isCollected: false,
							mediaType: item.type
						})))
						return
					}
				}
				// 无数据用兜底
				setVideoList(fallbackVideoList)
			},
			fail: (err) => {
				console.error("❌ 请求后端失败：", err)
				setVideoList(fallbackVideoList)
			}
		})
	} catch (e) {
		console.warn("视频流服务不可用，使用演示视频", e)
		setVideoList(fallbackVideoList)
	}
}

onMounted(() => {
	fetchVideoList()
	refreshSocialState()
	startProgress()
})

onShow(() => {
	refreshSocialState()
})

onUnmounted(() => {
	stopProgress()
})
</script>

<style>
.container {
	width: 100%;
	height: 100vh;
	background: #000;
	color: #fff;
	display: flex;
	flex-direction: column;
}

.video-area {
	flex: 1;
	position: relative;
	overflow: hidden;
	background: #000;
}

/* ===== 视频层 ===== */
.fullscreen-video {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
}

/* ===== 顶层 Tab ===== */
/* ===== 顶部 Tab ===== */
.top-tabs {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	z-index: 20;
	display: flex;
	justify-content: center;
	align-items: center;
	gap: 30rpx;
	padding-top: calc(var(--status-bar-height) + 20rpx);
	padding-bottom: 20rpx;
	background: linear-gradient(180deg, rgba(0,0,0,0.6) 0%, transparent 100%);
}

.top-tabs .tab-item {
	font-size: 32rpx;
	color: rgba(255,255,255,0.6);
	position: relative;
}

.top-tabs .tab-item.active {
	color: #fff;
	font-weight: bold;
}

.top-tabs .tab-item.active::after {
	content: '';
	position: absolute;
	bottom: -8rpx;
	left: 50%;
	transform: translateX(-50%);
	width: 80rpx;
	height: 4rpx;
	background: var(--primary-green);
	border-radius: 2rpx;
}

.tab-divider {
	color: rgba(255,255,255,0.4);
	font-size: 24rpx;
}

/* ===== 视频容器 ===== */
.video-wrapper {
	position: absolute;
	top: 0;
	left: 0;
	width: 100%;
	height: 100%;
	z-index: 1;
}

.video-wrapper video {
	width: 100%;
	height: 100%;
	object-fit: cover;
	display: block;
	background: #000;
}

/* ===== UI 浮层 ===== */
.overlay {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 10;
	display: flex;
	flex-direction: column;
	justify-content: flex-end;
	padding: 0 24rpx;
	padding-bottom: calc(140rpx + env(safe-area-inset-bottom));
	pointer-events: none;
}

.overlay > * {
	pointer-events: auto;
}

.bottom-info {
	display: flex;
	justify-content: space-between;
	align-items: flex-end;
}

.video-info {
	flex: 1;
	margin-right: 24rpx;
}

.author-info {
	display: flex;
	align-items: center;
	gap: 16rpx;
	margin-bottom: 16rpx;
}

.author-name {
	font-size: 32rpx;
	font-weight: bold;
	color: #fff;
}

.verified {
	font-size: 28rpx;
	color: #4ade80;
}

.video-desc {
	font-size: 28rpx;
	color: #fff;
	line-height: 1.5;
	margin-bottom: 16rpx;
}

.music-info {
	display: flex;
	align-items: center;
	gap: 12rpx;
	font-size: 24rpx;
	color: #fff;
}

.music-icon {
	font-size: 28rpx;
}

/* ===== 右侧操作栏 ===== */
.action-bar {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 32rpx;
	padding: 24rpx 16rpx;
	background: rgba(0, 0, 0, 0.3);
	backdrop-filter: blur(8px);
	border-radius: 48rpx;
}

.action-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8rpx;
}

.avatar-wrapper {
	position: relative;
}

.avatar {
	width: 88rpx;
	height: 88rpx;
	border-radius: 50%;
	border: 2rpx solid #fff;
}

.follow-badge {
	position: absolute;
	bottom: -8rpx;
	left: 50%;
	transform: translateX(-50%);
	width: 36rpx;
	height: 36rpx;
	background: var(--primary-green);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #000;
	font-size: 24rpx;
	font-weight: bold;
}

.follow-badge.followed {
	background: #ffffff;
	color: #111;
}

.like-icon {
	font-size: 52rpx;
	text-align: center;
	color: #fff;
}

.like-icon.liked {
	color: #fe2c55;
}

.comment-icon {
	font-size: 44rpx;
	text-align: center;
	color: #fff;
}

.favorite-icon {
	font-size: 48rpx;
	text-align: center;
	color: #fff;
}

.favorite-icon.collected {
	color: #ffd700;
}

.action-count {
	font-size: 22rpx;
	color: #fff;
	text-align: center;
}

.music-disc-wrapper {
	margin-top: 8rpx;
}

.music-disc {
	width: 80rpx;
	height: 80rpx;
	border-radius: 50%;
	background: linear-gradient(135deg, #1a1a1a, #2a2a2a);
	display: flex;
	align-items: center;
	justify-content: center;
	border: 4rpx solid #333;
}

.disc-cover {
	width: 100%;
	height: 100%;
	border-radius: 50%;
}

.music-disc.spinning {
	animation: spin 3s linear infinite;
}

@keyframes spin {
	from { transform: rotate(0deg); }
	to { transform: rotate(360deg); }
}

/* ===== 双击爱心 ===== */
.like-heart-animation {
	position: absolute;
	font-size: 160rpx;
	z-index: 15;
	pointer-events: none;
	animation: heartPop 0.8s ease-out forwards;
}

@keyframes heartPop {
	0% {
		transform: translate(-50%, -50%) scale(0.5);
		opacity: 1;
	}
	50% {
		transform: translate(-50%, -50%) scale(1.2);
		opacity: 1;
	}
	100% {
		transform: translate(-50%, -80%) scale(1);
		opacity: 0;
	}
}

/* ===== 进度条 ===== */
.progress-bar {
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	height: 2rpx;
	background: rgba(255,255,255,0.2);
	z-index: 20;
}

.progress-fill {
	height: 100%;
	background: var(--primary-green);
	transition: width 0.1s linear;
}
</style>

<script module="socialVideo" lang="renderjs">
export default {
	methods: {
		renderVideo(newVal, oldVal) {
			if (!newVal) return
			var container = document.getElementById('social-video-container')
			if (!container) return
			var data = typeof newVal === 'string' ? JSON.parse(newVal) : newVal
			if (!data || !data.url) return
			
			// 清空容器
			container.innerHTML = ''
			
			// 判断：如果是图片 → 渲染图片
			if(data.url.includes('.png') || data.url.includes('.jpg') || data.url.includes('.jpeg')){
				var img = document.createElement('img')
				img.src = data.url
				img.style.cssText = 'width:100%;height:100%;object-fit:cover;display:block;background:#000;'
				container.appendChild(img)
				return
			}
			
			// 是视频 → 渲染视频
			var video = document.createElement('video')
			video.src = data.url
			if (data.poster) video.poster = data.poster
			video.controls = false
			video.loop = true
			video.muted = true
			video.playsInline = true
			video.setAttribute('playsinline', '')
			video.setAttribute('webkit-playsinline', '')
			video.style.cssText = 'width:100%;height:100%;object-fit:cover;display:block;background:#000;'
			video.addEventListener('loadeddata', function() {
				video.play().catch(function(){})
				try { video.currentTime = 0.05 } catch(e) {}
			})
			container.appendChild(video)
		}
	}
}
</script>