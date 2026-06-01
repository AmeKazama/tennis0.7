<template>
	<Layout>
		<view class="container">
			<view class="video-section">
				<view class="top-tabs">
					<view class="tab-item" :class="{ active: videoTab === 'following' }" @tap="videoTab = 'following'">Following</view>
					<view class="tab-divider">·</view>
					<view class="tab-item" :class="{ active: videoTab === 'forYou' }" @tap="videoTab = 'forYou'">For You</view>
				</view>
				
				<swiper class="video-swiper" :vertical="true" :circular="true" @change="onVideoChange" :current="currentVideoIndex">
					<swiper-item v-for="(item, index) in mockDataList" :key="item.id">
						<view class="video-item-wrapper" @dblclick="handleDoubleClick">
							<image class="video-poster" :src="item.poster" mode="aspectFill"></image>
							
							<view class="video-overlay">
								<view class="video-info">
									<view class="author-info">
										<text class="author-name">{{ item.author }}</text>
										<text class="verified">✓</text>
									</view>
									<view class="video-desc">{{ item.desc }}</view>
									<view class="music-info">
										<text class="music-icon">🎵</text>
										<text class="music-name">{{ item.music }}</text>
									</view>
								</view>
								
								<view class="action-bar">
									<view class="action-item avatar-wrapper">
										<image class="avatar" :src="item.avatar" mode="aspectFill" @tap.stop="openUserProfile(item.userId)"></image>
										<view class="follow-badge" :class="{ followed: item.isFollowed }" @tap.stop="handleFollow(item)">
											{{ item.isFollowed ? '✓' : '+' }}
										</view>
									</view>
									<view class="action-item" @tap="toggleLike(item)" :class="{ scale: item.isLiked }">
										<view class="like-icon" :class="{ liked: item.isLiked }"></view>
										<text class="action-count">{{ formatNumber(item.likes) }}</text>
									</view>
									<view class="action-item" @tap="openComments(item)">
										<view class="comment-icon"></view>
										<text class="action-count">{{ formatNumber(item.comments) }}</text>
									</view>
									<view class="action-item" @tap="chooseFavoriteFolder(item)">
										<view class="favorite-icon" :class="{ collected: item.isCollected }"></view>
										<text class="action-count">{{ formatNumber(item.shares) }}</text>
									</view>
									<view class="action-item music-disc-wrapper">
										<view class="music-disc" :class="{ spinning: currentVideoIndex === index }">
											<image class="disc-cover" :src="item.poster" mode="aspectFill"></image>
										</view>
									</view>
								</view>
							</view>
							
							<view class="like-heart-animation" v-if="showHeart && heartIndex === index" :style="heartStyle">❤️</view>
							
							<view class="progress-bar">
								<view class="progress-fill" :style="{ width: progressPercent + '%' }"></view>
							</view>
						</view>
					</swiper-item>
				</swiper>
			</view>
		</view>
	</Layout>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import Layout from '@/components/Layout/Layout.vue'
import { addFavorite, getFavoriteFolders, isFavorited, isFollowing, removeFavorite, toggleFollow } from '@/utils/social-store/index.js'

const videoTab = ref('forYou')
const currentVideoIndex = ref(0)
const showHeart = ref(false)
const heartIndex = ref(0)
const heartStyle = ref({})
const progressPercent = ref(0)
let progressTimer = null
let lastTapTime = 0

const mockDataList = reactive([
	{
		id: 'feed_serve_jack',
		userId: 'u1',
		poster: 'https://picsum.photos/720/1280?random=1',
		avatar: 'https://i.pravatar.cc/150?u=1',
		author: '@TennisPro_Jack',
		desc: 'Mastering the kick serve today! Notice the racket drop and weight transfer...',
		music: 'Original Sound - Tennis',
		likes: 125000,
		comments: 4567,
		shares: 890,
		isLiked: false
	},
	{
		id: 'feed_backhand_lily',
		userId: 'u2',
		poster: 'https://picsum.photos/720/1280?random=2',
		avatar: 'https://i.pravatar.cc/150?u=2',
		author: '@TennisQueen_Lily',
		desc: 'Backhand tips! The key is keeping your eyes on the ball and rotating your hips.',
		music: 'Background Music - Sports',
		likes: 89500,
		comments: 3456,
		shares: 567,
		isLiked: false
	},
	{
		id: 'feed_coach_mike',
		userId: 'u3',
		poster: 'https://picsum.photos/720/1280?random=3',
		avatar: 'https://i.pravatar.cc/150?u=3',
		author: '@Coach_Mike',
		desc: 'Pro serve lesson! Start from the toss and work your way up.',
		music: 'Original Sound - Coach',
		likes: 234000,
		comments: 6789,
		shares: 1234,
		isLiked: false
	},
	{
		id: 'feed_match_highlight',
		userId: 'u4',
		poster: 'https://picsum.photos/720/1280?random=4',
		avatar: 'https://i.pravatar.cc/150?u=4',
		author: '@Match_Highlight',
		desc: 'Epic match point! The final was intense!',
		music: 'Epic Music - Match',
		likes: 567000,
		comments: 12345,
		shares: 3456,
		isLiked: false
	},
	{
		id: 'feed_training_warrior',
		userId: 'u5',
		poster: 'https://picsum.photos/720/1280?random=5',
		avatar: 'https://i.pravatar.cc/150?u=5',
		author: '@Training_Warrior',
		desc: '5am training grind! Success doesn\'t come easy. 💪',
		music: 'Motivational Music',
		likes: 345000,
		comments: 8901,
		shares: 2345,
		isLiked: false
	}
])

const onVideoChange = (e) => {
	currentVideoIndex.value = e.detail.current
	progressPercent.value = 0
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

const handleDoubleClick = (e) => {
	const now = Date.now()
	if (now - lastTapTime < 300) {
		const item = mockDataList[currentVideoIndex.value]
		if (!item.isLiked) {
			item.isLiked = true
			item.likes += 1
		}
		
		showHeart.value = true
		heartIndex.value = currentVideoIndex.value
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

onMounted(() => {
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
	min-height: 100vh;
	background: #000;
	color: #fff;
}

.video-section {
	width: 100%;
	height: 100vh;
	background: #000;
	overflow: hidden;
}

.top-tabs {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	z-index: 100;
	display: flex;
	justify-content: center;
	align-items: center;
	gap: 30rpx;
	padding-top: calc(var(--status-bar-height) + 20rpx);
	padding-bottom: 20rpx;
	background: linear-gradient(180deg, rgba(0,0,0,0.6) 0%, transparent 100%);
	backdrop-filter: blur(10px);
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

.video-swiper {
	width: 100%;
	height: 100vh;
}

.video-item-wrapper {
	width: 100%;
	height: 100vh;
	position: relative;
}

.video-poster {
	width: 100%;
	height: 100%;
}

.video-overlay {
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	top: 0;
	display: flex;
	justify-content: space-between;
	align-items: flex-end;
	padding: 0 24rpx;
	padding-bottom: calc(140rpx + env(safe-area-inset-bottom));
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
}

.verified {
	font-size: 28rpx;
}

.video-desc {
	font-size: 28rpx;
	line-height: 1.5;
	margin-bottom: 16rpx;
}

.music-info {
	display: flex;
	align-items: center;
	gap: 12rpx;
	font-size: 24rpx;
}

.music-icon {
	font-size: 28rpx;
}

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
	transition: transform 0.2s ease;
}

.action-item.scale {
	animation: likeScale 0.3s ease;
}

@keyframes likeScale {
	0% {
		transform: scale(1);
	}
	50% {
		transform: scale(1.3);
	}
	100% {
		transform: scale(1);
	}
}

.avatar-wrapper {
	position: relative;
}

.action-bar .avatar {
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
	width: 56rpx;
	height: 56rpx;
	background-size: contain;
	background-repeat: no-repeat;
	background-position: center;
	transition: all 0.3s ease;
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1024 1024'%3E%3Cpath d='M190.2 471.4c14.4 0 26.1-11.7 26.1-26.1s-11.7-26.2-26.1-26.2l-62.5.1c-1.4-.2-2.9-.3-4.4-.3-19.7 0-35.6 16.1-35.6 36.1v407.2c0 19.9 16 35.6 35.7 35.6 1.9 0 3.8.3 5.6 0l61 .1c.1 0 .2.1.3.1s.2 0 .2-.1l.7-.1c13.4-.5 24.2-11.4 24.2-25s-10.8-24.5-24.2-25l-.4-.4-50.9 0 1.5-402.3 62.1.1z' fill='rgba(255,255,255,0.6)'/%3E%3Cpath d='M926.5 433.9c-19.3-31.4-47.3-44.2-81.3-45.5-1.8-.2-3.5-.4-5.4-.4l-205.4-.7c13.5-39 22.7-85.6 22.7-129.3 0-28.3-3.2-56-9-82.6l-.5.1c-10.6-46.6-51.7-81.3-101-81.3-57.3 0-95.5 48.2-95.5 106.1 0 3.2-.3 6.4 0 9.5-3 108.4-91.2 195.5-196.2 207.5l0 54.9-.8 222.2 0 229.7 10.7 0 500 .2 8.7-.2c19.4.1 30.2-4.8 47.8-16.1 16.7-10.8 29.2-25.5 37.5-42.2 2.3-3.3 4-7.1 5.1-11.2l77-344.3c1-4.1 1.3-8.2 1-12.2-0.5-42.5-5.3-65-17.6-85zM893.8 486.8l-83 367.8-.1-.1c-2.6 6.1-6.9 11.6-12.9 15.4-4.2 2.7-8.8 4.3-13.4 5-1.5-.2-3 0-4.6 0l-477-.5-.2-407.4c89.3-40.3 154.8-79.7 188.6-173.7.1 0 .1.1.2.1 3-9.1 6.3-20.7 8.7-33.2 5.6-29.2 5.3-58.1 5.3-58.1-4.9-38 25.9-53 44.4-53 25.3.9 50.3 33.7 50.3 52.3 0 0 5.6 27.6 5.6 57.2.1 37.4-4.7 56.8-4.7 56.8l-.5 0c-5.9 30.9-16.2 60.1-30.5 87l.4.3c-2.4 4.8-3.7 10.2-3.7 15.9 0 19.9 19.1 21.7 38.8 21.7l238.8.3c0 0 14.7.5 14.7.5l0 .1c12.1-.6 24.2 5.2 31.1 16.4 5.5 9 6.4 19.6 3.5 29L893.8 486.8z' fill='rgba(255,255,255,0.6)'/%3E%3C/svg%3E");
}

.like-icon.liked {
	background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1024 1024'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:%231e90ff'/%3E%3Cstop offset='50%25' style='stop-color:%234169e1'/%3E%3Cstop offset='100%25' style='stop-color:%230000cd'/%3E%3C/linearGradient%3E%3C/defs%3E%3Cpath d='M190.2 471.4c14.4 0 26.1-11.7 26.1-26.1s-11.7-26.2-26.1-26.2l-62.5.1c-1.4-.2-2.9-.3-4.4-.3-19.7 0-35.6 16.1-35.6 36.1v407.2c0 19.9 16 35.6 35.7 35.6 1.9 0 3.8.3 5.6 0l61 .1c.1 0 .2.1.3.1s.2 0 .2-.1l.7-.1c13.4-.5 24.2-11.4 24.2-25s-10.8-24.5-24.2-25l-.4-.4-50.9 0 1.5-402.3 62.1.1z' fill='url(%23g)'/%3E%3Cpath d='M926.5 433.9c-19.3-31.4-47.3-44.2-81.3-45.5-1.8-.2-3.5-.4-5.4-.4l-205.4-.7c13.5-39 22.7-85.6 22.7-129.3 0-28.3-3.2-56-9-82.6l-.5.1c-10.6-46.6-51.7-81.3-101-81.3-57.3 0-95.5 48.2-95.5 106.1 0 3.2-.3 6.4 0 9.5-3 108.4-91.2 195.5-196.2 207.5l0 54.9-.8 222.2 0 229.7 10.7 0 500 .2 8.7-.2c19.4.1 30.2-4.8 47.8-16.1 16.7-10.8 29.2-25.5 37.5-42.2 2.3-3.3 4-7.1 5.1-11.2l77-344.3c1-4.1 1.3-8.2 1-12.2-0.5-42.5-5.3-65-17.6-85zM893.8 486.8l-83 367.8-.1-.1c-2.6 6.1-6.9 11.6-12.9 15.4-4.2 2.7-8.8 4.3-13.4 5-1.5-.2-3 0-4.6 0l-477-.5-.2-407.4c89.3-40.3 154.8-79.7 188.6-173.7.1 0 .1.1.2.1 3-9.1 6.3-20.7 8.7-33.2 5.6-29.2 5.3-58.1 5.3-58.1-4.9-38 25.9-53 44.4-53 25.3.9 50.3 33.7 50.3 52.3 0 0 5.6 27.6 5.6 57.2.1 37.4-4.7 56.8-4.7 56.8l-.5 0c-5.9 30.9-16.2 60.1-30.5 87l.4.3c-2.4 4.8-3.7 10.2-3.7 15.9 0 19.9 19.1 21.7 38.8 21.7l238.8.3c0 0 14.7.5 14.7.5l0 .1c12.1-.6 24.2 5.2 31.1 16.4 5.5 9 6.4 19.6 3.5 29L893.8 486.8z' fill='url(%23g)'/%3E%3C/svg%3E");
	filter: drop-shadow(0 0 12rpx rgba(30, 144, 255, 0.6));
}

.comment-icon {
	width: 56rpx;
	height: 56rpx;
	background-size: contain;
	background-repeat: no-repeat;
	background-position: center;
	background-image: url("data:image/svg+xml,%3Csvg t='1778207282879' class='icon' viewBox='0 0 1024 1024' version='1.1' xmlns='http://www.w3.org/2000/svg' p-id='2642'%3E%3Cpath d='M512 0C229.696 0 0 196.672 0 438.421333c0 144.384 82.282667 278.336 220.778667 360.469333l0 203.733333c0 8.213333 4.714667 15.744 12.181333 19.285333C235.882667 1023.338667 239.04 1024 242.154667 1024c4.8 0 9.578667-1.621333 13.461333-4.8l181.589333-147.456c26.794667 3.413333 51.370667 5.077333 74.794667 5.077333 282.282667 0 512-196.693333 512-438.421333C1024 196.672 794.282667 0 512 0zM512.021333 834.090667c-24.106667 0-49.664-1.941333-78.144-5.952-5.845333-0.874667-11.84 0.832-16.448 4.586667l-153.92 125.034667 0-171.2c0-7.701333-4.16-14.848-10.901333-18.602667-131.413333-73.813333-209.877333-197.013333-209.877333-329.514667C42.730667 220.245333 253.269333 42.730667 512 42.730667s469.312 177.472 469.312 395.648S770.773333 834.090667 512.021333 834.090667z' p-id='2643' fill='rgba(255,255,255,0.6)'%3E%3C/path%3E%3Cpath d='M512 438.4m-49.066667 0a2.3 2.3 0 1 0 98.133333 0 2.3 2.3 0 1 0-98.133333 0Z' p-id='2644' fill='rgba(255,255,255,0.6)'%3E%3C/path%3E%3Cpath d='M266.709333 438.4m-49.066667 0a2.3 2.3 0 1 0 98.133333 0 2.3 2.3 0 1 0-98.133333 0Z' p-id='2645' fill='rgba(255,255,255,0.6)'%3E%3C/path%3E%3Cpath d='M757.290667 389.333333c-27.114667 0-49.024 21.952-49.024 49.088 0 27.136 21.888 49.045333 49.024 49.045333 27.157333 0 49.088-21.909333 49.088-49.045333C806.378667 411.285333 784.448 389.333333 757.290667 389.333333z' p-id='2646' fill='rgba(255,255,255,0.6)'%3E%3C/path%3E%3C/svg%3E");
}

.favorite-icon {
	width: 56rpx;
	height: 56rpx;
	background-size: contain;
	background-repeat: no-repeat;
	background-position: center;
	background-image: url("data:image/svg+xml,%3Csvg t='1778207401863' class='icon' viewBox='0 0 1024 1024' version='1.1' xmlns='http://www.w3.org/2000/svg' p-id='3668'%3E%3Cpath d='M536.9344 860.3136c-26.8288-14.7968-70.5024-14.6944-97.1776 0L251.2384 964.096c-53.6064 29.5424-88.7808 2.56-78.5408-59.8016l35.9936-219.8016c5.12-31.3344-8.448-74.752-30.0544-96.768L26.1632 431.9744c-43.4176-44.288-29.696-87.6544 30.0032-96.768l210.7392-32c30.0032-4.608 65.28-31.5392 78.6432-59.8528L439.808 43.4176c26.8288-56.8832 70.4512-56.6784 97.1264 0l94.208 199.9872c13.4656 28.4672 48.896 55.296 78.6944 59.8528l210.7392 32.0512c60.0064 9.1136 73.216 52.5824 30.0544 96.7168l-152.5248 155.648c-21.7088 22.1696-35.1232 65.6896-30.0544 96.8192l35.9936 219.8016c10.24 62.5664-25.1392 89.1904-78.5408 59.8016l-188.5696-103.7824z' fill='rgba(255,255,255,0.6)' p-id='3669'%3E%3C/path%3E%3C/svg%3E");
}

.favorite-icon.collected {
	background-image: url("data:image/svg+xml,%3Csvg t='1778207401863' class='icon' viewBox='0 0 1024 1024' version='1.1' xmlns='http://www.w3.org/2000/svg' p-id='3668'%3E%3Cpath d='M536.9344 860.3136c-26.8288-14.7968-70.5024-14.6944-97.1776 0L251.2384 964.096c-53.6064 29.5424-88.7808 2.56-78.5408-59.8016l35.9936-219.8016c5.12-31.3344-8.448-74.752-30.0544-96.768L26.1632 431.9744c-43.4176-44.288-29.696-87.6544 30.0032-96.768l210.7392-32c30.0032-4.608 65.28-31.5392 78.6432-59.8528L439.808 43.4176c26.8288-56.8832 70.4512-56.6784 97.1264 0l94.208 199.9872c13.4656 28.4672 48.896 55.296 78.6944 59.8528l210.7392 32.0512c60.0064 9.1136 73.216 52.5824 30.0544 96.7168l-152.5248 155.648c-21.7088 22.1696-35.1232 65.6896-30.0544 96.8192l35.9936 219.8016c10.24 62.5664-25.1392 89.1904-78.5408 59.8016l-188.5696-103.7824z' fill='%23deff9a' p-id='3669'%3E%3C/path%3E%3C/svg%3E");
	filter: drop-shadow(0 0 12rpx rgba(222, 255, 154, 0.7));
}

.action-icon {
	font-size: 56rpx;
}

.action-icon.liked {
	color: #fe2c55;
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
	overflow: hidden;
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
	from {
		transform: rotate(0deg);
	}
	to {
		transform: rotate(360deg);
	}
}

.like-heart-animation {
	position: absolute;
	font-size: 160rpx;
	animation: heartPop 0.8s ease-out forwards;
	pointer-events: none;
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

.progress-bar {
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	height: 2rpx;
	background: rgba(255,255,255,0.2);
}

.progress-fill {
	height: 100%;
	background: var(--primary-green);
	transition: width 0.1s linear;
}
</style>
