<template>
	<view class="detail-container">
		<!-- 顶部导航 -->
		<view class="detail-header">
			<text class="iconfont icon-back" @click="goBack"></text>
			<text class="header-title">动态详情</text>
			<view class="header-actions">
				<text class="iconfont icon-more" @click="showMoreActions"></text>
			</view>
		</view>
		
		<scroll-view class="detail-content" scroll-y>
			<!-- 用户信息 -->
			<view class="detail-user">
				<view class="user-avatar">
					<image :src="moment.user_avatar || '/static/logo.png'" mode="aspectFill"></image>
				</view>
				<view class="user-info">
					<text class="user-name">{{ moment.user_name || '网球爱好者' }}</text>
					<text class="moment-time">{{ formatTime(moment.create_time) }}</text>
				</view>
			</view>
			
			<!-- 动态内容 -->
			<view class="detail-content">
				<text class="content-text">{{ moment.content }}</text>
			</view>
			
			<!-- 图片/视频 -->
			<view class="detail-media" v-if="moment.images && moment.images.length > 0">
				<view 
					class="media-grid" 
					:class="'grid-' + Math.min(moment.images.length, 3)"
				>
					<image 
						v-for="(img, idx) in moment.images" 
						:key="idx"
						:src="img" 
						mode="aspectFill"
						class="media-image"
						@click="previewImage(idx)"
					></image>
				</view>
			</view>
			
			<video 
				v-if="moment.video_url"
				:src="moment.video_url"
				class="detail-video"
				controls
			></video>
			
			<!-- 位置信息 -->
			<view class="detail-location" v-if="moment.location">
				<text class="iconfont icon-location"></text>
				<text>{{ moment.location }}</text>
			</view>
			
			<!-- 互动数据 -->
			<view class="detail-stats">
				<text class="stats-item">赞 {{ moment.likes_count || 0 }}</text>
				<text class="stats-divider">|</text>
				<text class="stats-item">评论 {{ moment.comments_count || 0 }}</text>
				<text class="stats-divider">|</text>
				<text class="stats-item">转发 {{ moment.shares_count || 0 }}</text>
			</view>
			
			<!-- 操作栏 -->
			<view class="detail-actions">
				<view class="action-item" @click="toggleLike">
					<text class="iconfont" :class="moment.is_liked ? 'icon-liked' : 'icon-like'"></text>
					<text>{{ moment.is_liked ? '已赞' : '赞' }}</text>
				</view>
				<view class="action-item" @click="focusComment">
					<text class="iconfont icon-comment"></text>
					<text>评论</text>
				</view>
				<view class="action-item" @click="shareMoment">
					<text class="iconfont icon-share"></text>
					<text>转发</text>
				</view>
			</view>
			
			<!-- 评论列表 -->
			<view class="comments-section">
				<view class="section-title">评论 ({{ comments.length }})</view>
				
				<view class="comment-list">
					<view 
						class="comment-item"
						v-for="item in comments"
						:key="item.id"
					>
						<view class="comment-user">
							<image :src="item.user_avatar || '/static/logo.png'" class="comment-avatar"></image>
							<view class="comment-info">
								<text class="comment-name">{{ item.user_name || '用户' + item.user_id }}</text>
								<text class="comment-content">{{ item.content }}</text>
								<text class="comment-time">{{ formatTime(item.create_time) }}</text>
							</view>
						</view>
						
						<!-- 回复列表 -->
						<view class="reply-list" v-if="item.replies && item.replies.length > 0">
							<view 
								class="reply-item"
								v-for="reply in item.replies"
								:key="reply.id"
							>
								<text class="reply-name">{{ reply.user_name || '用户' + reply.user_id }}：</text>
								<text class="reply-content">{{ reply.content }}</text>
							</view>
						</view>
					</view>
				</view>
				
				<view class="no-comments" v-if="comments.length === 0">
					<text>暂无评论，快来抢沙发吧~</text>
				</view>
			</view>
		</scroll-view>
		
		<!-- 评论输入框 -->
		<view class="comment-input-area">
			<input 
				type="text"
				v-model="commentText"
				:placeholder="replyTo ? '回复 ' + replyToName : '写评论...'"
				class="comment-input"
				:focus="inputFocused"
				@blur="onInputBlur"
				@confirm="submitComment"
			/>
			<text class="btn-send" :class="{ active: commentText.trim() }" @click="submitComment">发送</text>
		</view>
	</view>
</template>

<script>
import { 
	getMomentsList, 
	getComments, 
	likeMoment, 
	unlikeMoment,
	commentMoment,
	shareMoment as shareMomentApi,
	deleteMoment
} from '@/utils/moments-store/index.js'

export default {
	data() {
		return {
			momentId: null,
			moment: {},
			comments: [],
			commentText: '',
			replyTo: null,
			replyToName: '',
			inputFocused: false
		}
	},
	onLoad(options) {
		if (options.id) {
			this.momentId = parseInt(options.id)
			this.loadMomentDetail()
			this.loadComments()
		}
	},
	methods: {
		async loadMomentDetail() {
			try {
				const res = await getMomentsList(1, 100)
				const moment = res.list.find(m => m.id === this.momentId)
				if (moment) {
					this.moment = moment
				}
			} catch (e) {
				console.error('加载动态详情失败', e)
			}
		},
		
		async loadComments() {
			if (!this.momentId) return
			try {
				const res = await getComments(this.momentId)
				this.comments = res.list || []
			} catch (e) {
				console.error('加载评论失败', e)
			}
		},
		
		async toggleLike() {
			try {
				if (this.moment.is_liked) {
					await unlikeMoment(this.momentId)
					this.moment.likes_count = Math.max(0, (this.moment.likes_count || 0) - 1)
					this.moment.is_liked = false
				} else {
					await likeMoment(this.momentId)
					this.moment.likes_count = (this.moment.likes_count || 0) + 1
					this.moment.is_liked = true
				}
			} catch (e) {
				console.error('点赞失败', e)
			}
		},
		
		focusComment() {
			this.inputFocused = true
		},
		
		onInputBlur() {
			this.inputFocused = false
		},
		
		async submitComment() {
			if (!this.commentText.trim()) return
			
			try {
				await commentMoment(this.momentId, this.commentText.trim(), this.replyTo)
				this.commentText = ''
				this.replyTo = null
				this.replyToName = ''
				uni.showToast({
					title: '评论成功',
					icon: 'success'
				})
				this.loadComments()
				this.loadMomentDetail()
			} catch (e) {
				uni.showToast({
					title: '评论失败',
					icon: 'none'
				})
			}
		},
		
		async shareMoment() {
			try {
				await shareMomentApi(this.momentId)
				this.moment.shares_count = (this.moment.shares_count || 0) + 1
				uni.showToast({
					title: '转发成功',
					icon: 'success'
				})
			} catch (e) {
				console.error('转发失败', e)
			}
		},
		
		showMoreActions() {
			const isOwner = this.moment.user_id === 1 // TODO: 替换为实际用户ID
			const actions = isOwner ? ['删除', '收藏', '举报'] : ['收藏', '举报']
			
			uni.showActionSheet({
				itemList: actions,
				success: async (res) => {
					const action = actions[res.tapIndex]
					if (action === '删除' && isOwner) {
						uni.showModal({
							title: '提示',
							content: '确定删除这条动态？',
							success: async (modalRes) => {
								if (modalRes.confirm) {
									try {
										await deleteMoment(this.momentId)
										uni.showToast({
											title: '删除成功',
											icon: 'success'
										})
										setTimeout(() => {
											uni.navigateBack()
										}, 1500)
									} catch (e) {
										uni.showToast({
											title: '删除失败',
											icon: 'none'
										})
									}
								}
							}
						})
					}
				}
			})
		},
		
		previewImage(idx) {
			if (!this.moment.images) return
			uni.previewImage({
				urls: this.moment.images,
				current: idx
			})
		},
		
		goBack() {
			uni.navigateBack()
		},
		
		formatTime(timeStr) {
			if (!timeStr) return ''
			const date = new Date(timeStr)
			const now = new Date()
			const diff = now - date
			
			if (diff < 60000) return '刚刚'
			if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
			if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
			if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
			
			return `${date.getMonth() + 1}-${date.getDate()} ${date.getHours()}:${date.getMinutes()}`
		}
	}
}
</script>

<style scoped>
.detail-container {
	min-height: 100vh;
	background: #f5f5f5;
}

.detail-header {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	height: 88rpx;
	background: #fff;
	display: flex;
	align-items: center;
	padding: 0 30rpx;
	box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.05);
	z-index: 100;
}

.icon-back {
	font-size: 40rpx;
	color: #333;
}

.header-title {
	flex: 1;
	text-align: center;
	font-size: 32rpx;
	font-weight: 600;
	color: #333;
	margin-right: 40rpx;
}

.header-actions {
	display: flex;
	align-items: center;
}

.icon-more {
	font-size: 40rpx;
	color: #333;
}

.detail-content {
	padding-top: 88rpx;
	padding-bottom: 120rpx;
}

.detail-user {
	display: flex;
	align-items: flex-start;
	padding: 30rpx;
	background: #fff;
}

.user-avatar {
	width: 80rpx;
	height: 80rpx;
	border-radius: 8rpx;
	overflow: hidden;
	margin-right: 20rpx;
}

.user-avatar image {
	width: 100%;
	height: 100%;
}

.user-info {
	flex: 1;
	display: flex;
	flex-direction: column;
}

.user-name {
	font-size: 30rpx;
	font-weight: 600;
	color: #333;
	margin-bottom: 8rpx;
}

.moment-time {
	font-size: 24rpx;
	color: #999;
}

.detail-content {
	padding: 30rpx;
	background: #fff;
}

.content-text {
	font-size: 30rpx;
	color: #333;
	line-height: 1.6;
	word-break: break-all;
}

.detail-media {
	padding: 0 30rpx 30rpx;
	background: #fff;
}

.media-grid {
	display: grid;
	gap: 8rpx;
}

.grid-1 {
	grid-template-columns: 1fr;
}

.grid-2 {
	grid-template-columns: repeat(2, 1fr);
}

.grid-3 {
	grid-template-columns: repeat(3, 1fr);
}

.media-image {
	width: 100%;
	aspect-ratio: 1;
	border-radius: 8rpx;
}

.detail-video {
	width: 100%;
	margin-top: 20rpx;
}

.detail-location {
	padding: 20rpx 30rpx;
	background: #fff;
	display: flex;
	align-items: center;
	color: #666;
	font-size: 26rpx;
}

.detail-location .iconfont {
	margin-right: 8rpx;
}

.detail-stats {
	padding: 24rpx 30rpx;
	background: #fff;
	display: flex;
	align-items: center;
	border-bottom: 1rpx solid #f0f0f0;
}

.stats-item {
	font-size: 26rpx;
	color: #666;
}

.stats-divider {
	margin: 0 20rpx;
	color: #ddd;
}

.detail-actions {
	display: flex;
	align-items: center;
	padding: 20rpx 30rpx;
	background: #fff;
}

.action-item {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	height: 80rpx;
	border-right: 1rpx solid #f0f0f0;
}

.action-item:last-child {
	border-right: none;
}

.action-item .iconfont {
	font-size: 40rpx;
	color: #666;
	margin-right: 8rpx;
}

.action-item .icon-liked {
	color: #ff4d4f;
}

.action-item text {
	font-size: 28rpx;
	color: #666;
}

.comments-section {
	padding: 30rpx;
	background: #fff;
	margin-top: 16rpx;
}

.section-title {
	font-size: 28rpx;
	font-weight: 600;
	color: #333;
	margin-bottom: 24rpx;
}

.comment-list {
	
}

.comment-item {
	padding-bottom: 30rpx;
	margin-bottom: 30rpx;
	border-bottom: 1rpx solid #f0f0f0;
}

.comment-item:last-child {
	border-bottom: none;
}

.comment-user {
	display: flex;
	align-items: flex-start;
}

.comment-avatar {
	width: 64rpx;
	height: 64rpx;
	border-radius: 50%;
	margin-right: 16rpx;
}

.comment-info {
	flex: 1;
	display: flex;
	flex-direction: column;
}

.comment-name {
	font-size: 26rpx;
	color: #576b95;
	margin-bottom: 8rpx;
}

.comment-content {
	font-size: 28rpx;
	color: #333;
	line-height: 1.5;
	margin-bottom: 8rpx;
}

.comment-time {
	font-size: 22rpx;
	color: #999;
}

.reply-list {
	margin-top: 16rpx;
	padding: 16rpx;
	background: #f8f8f8;
	border-radius: 8rpx;
}

.reply-item {
	font-size: 26rpx;
	color: #333;
	line-height: 1.5;
	margin-bottom: 8rpx;
}

.reply-item:last-child {
	margin-bottom: 0;
}

.reply-name {
	color: #576b95;
}

.no-comments {
	text-align: center;
	padding: 40rpx;
	color: #999;
	font-size: 26rpx;
}

.comment-input-area {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	height: 100rpx;
	background: #fff;
	display: flex;
	align-items: center;
	padding: 0 30rpx;
	box-shadow: 0 -2rpx 10rpx rgba(0, 0, 0, 0.05);
}

.comment-input {
	flex: 1;
	height: 72rpx;
	padding: 0 24rpx;
	background: #f5f5f5;
	border-radius: 36rpx;
	font-size: 28rpx;
}

.btn-send {
	margin-left: 20rpx;
	padding: 0 30rpx;
	height: 72rpx;
	line-height: 72rpx;
	background: #f5f5f5;
	border-radius: 36rpx;
	font-size: 28rpx;
	color: #999;
}

.btn-send.active {
	background: #07c160;
	color: #fff;
}
</style>
