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
	poster: currentVideo.value.poster || ''
}))

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

// ======================
// 对接你的后端：GET 视频列表（只加这段，别的不动）
// ======================
// ======================
// 对接你的后端：GET 视频列表（只加这段，别的不动）
// ======================
const fetchVideoList = async () => {
	try {
		const res = await uni.request({
			// 把这里改成你电脑的局域网 IP！！
			url: "http://10.24.51.159:8003/api/feed/list", 
			method: "GET",
			data: { page: 1, page_size: 5 }
		})

		// 👇 只改了这里！！！ res.data 而不是 res[1].data
		if (res.data.code === 200) {
			mockDataList.length = 0 
			res.data.data.forEach(item => {
				mockDataList.push({
					id: 'feed_' + item.id,
					userId: 'u' + item.id,
					videoUrl: "http://10.24.51.159:8003" + item.video_url,
					poster: "http://10.24.51.159:8003" + item.cover_url,
					avatar: "https://i.pravatar.cc/150?u=" + item.id,
					author: '@TennisCoach_' + item.id,
					desc: item.desc,
					music: 'Original Sound - Tennis',
					likes: 125000,
					comments: 4567,
					shares: 890,
					isLiked: false,
					isFollowed: false,
					isCollected: false
				})
			})
		}
	} catch (e) {
		console.error("请求视频失败", e)
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
			container.innerHTML = ''
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