<template>
	<view class="moments-container">
		<!-- 顶部导航 -->
		<view class="moments-header">
			<view class="header-left" @click="goStats">
				<text class="iconfont icon-chart"></text>
			</view>
			<text class="header-title">朋友圈</text>
			<view class="header-right" @click="goPublish">
				<text class="iconfont icon-add"></text>
			</view>
		</view>
		
		<!-- 朋友圈列表 -->
		<scroll-view 
			class="moments-list" 
			scroll-y 
			@scrolltolower="loadMore"
			:refresher-enabled="true"
			@refresherrefresh="onRefresh"
			:refresher-triggered="isRefreshing"
		>
			<!-- 发布入口 -->
			<view class="publish-entry" @click="goPublish">
				<view class="entry-avatar">
					<image src="/static/logo.png" mode="aspectFill"></image>
				</view>
				<view class="entry-text">分享你的网球时刻...</view>
			</view>
			
			<!-- 动态列表 -->
			<view 
				class="moment-item" 
				v-for="item in momentsList" 
				:key="item.id"
				@click="goDetail(item.id)"
			>
				<!-- 用户信息 -->
				<view class="moment-user">
					<view class="user-avatar">
						<image :src="item.user_avatar || '/static/logo.png'" mode="aspectFill"></image>
					</view>
					<view class="user-info">
						<text class="user-name">{{ item.user_name || '网球爱好者' }}</text>
						<text class="moment-time">{{ formatTime(item.create_time) }}</text>
					</view>
				</view>
				
				<!-- 动态内容 -->
				<view class="moment-content">
					<text class="content-text">{{ item.content }}</text>
				</view>
				
				<!-- 图片/视频 -->
				<view class="moment-media" v-if="item.images && item.images.length > 0">
					<view 
						class="media-grid" 
						:class="'grid-' + Math.min(item.images.length, 3)"
					>
						<image 
							v-for="(img, idx) in item.images.slice(0, 9)" 
							:key="idx"
							:src="img" 
							mode="aspectFill"
							class="media-image"
							@click.stop="previewImage(item.images, idx)"
						></image>
					</view>
				</view>
				
				<!-- 位置信息 -->
				<view class="moment-location" v-if="item.location">
					<text class="iconfont icon-location"></text>
					<text>{{ item.location }}</text>
				</view>
				
				<!-- 互动栏 -->
				<view class="moment-actions">
					<view class="action-item" @click.stop="toggleLike(item)">
						<text class="iconfont" :class="item.is_liked ? 'icon-liked' : 'icon-like'"></text>
						<text>{{ item.likes_count || 0 }}</text>
					</view>
					<view class="action-item" @click.stop="goDetail(item.id)">
						<text class="iconfont icon-comment"></text>
						<text>{{ item.comments_count || 0 }}</text>
					</view>
					<view class="action-item" @click.stop="shareMoment(item)">
						<text class="iconfont icon-share"></text>
						<text>{{ item.shares_count || 0 }}</text>
					</view>
				</view>
			</view>
			
			<!-- 加载更多 -->
			<view class="load-more" v-if="momentsList.length > 0">
				<text v-if="loadingMore">加载中...</text>
				<text v-else-if="noMore">没有更多了</text>
				<text v-else @click="loadMore">加载更多</text>
			</view>
			
			<!-- 空状态 -->
			<view class="empty-state" v-if="!loading && momentsList.length === 0">
				<image src="/static/empty.png" mode="aspectFit"></image>
				<text>还没有动态，快去发布第一条吧</text>
				<button class="btn-publish" @click="goPublish">发布动态</button>
			</view>
		</scroll-view>
	</view>
</template>

<script>
import { 
	getMomentsList, 
	likeMoment, 
	unlikeMoment,
	shareMoment as shareMomentApi 
} from '@/utils/moments-store/index.js'

export default {
	data() {
		return {
			momentsList: [],
			page: 1,
			pageSize: 10,
			loading: false,
			loadingMore: false,
			noMore: false,
			isRefreshing: false
		}
	},
	onLoad() {
		this.loadMoments()
	},
	methods: {
		async loadMoments() {
			if (this.loading) return
			this.loading = true
			
			try {
				const res = await getMomentsList(this.page, this.pageSize)
				if (this.page === 1) {
					this.momentsList = res.list || []
				} else {
					this.momentsList = [...this.momentsList, ...(res.list || [])]
				}
				this.noMore = this.momentsList.length >= res.total
			} catch (e) {
				console.error('加载动态失败', e)
				uni.showToast({
					title: '加载失败',
					icon: 'none'
				})
			} finally {
				this.loading = false
			}
		},
		
		async onRefresh() {
			this.isRefreshing = true
			this.page = 1
			this.noMore = false
			await this.loadMoments()
			this.isRefreshing = false
		},
		
		async loadMore() {
			if (this.noMore || this.loadingMore) return
			this.loadingMore = true
			this.page++
			await this.loadMoments()
			this.loadingMore = false
		},
		
		async toggleLike(item) {
			try {
				if (item.is_liked) {
					await unlikeMoment(item.id)
					item.likes_count = Math.max(0, (item.likes_count || 0) - 1)
					item.is_liked = false
				} else {
					await likeMoment(item.id)
					item.likes_count = (item.likes_count || 0) + 1
					item.is_liked = true
				}
			} catch (e) {
				console.error('点赞操作失败', e)
			}
		},
		
		goPublish() {
			uni.navigateTo({
				url: '/pages/moments/publish'
			})
		},
		
		goDetail(id) {
			uni.navigateTo({
				url: `/pages/moments/moments-detail?id=${id}`
			})
		},
		
		goStats() {
			uni.navigateTo({
				url: '/pages/moments/moments-stats'
			})
		},
		
		previewImage(images, current) {
			uni.previewImage({
				urls: images,
				current
			})
		},
		
		async shareMoment(item) {
			try {
				await shareMomentApi(item.id)
				item.shares_count = (item.shares_count || 0) + 1
				uni.showToast({
					title: '分享成功',
					icon: 'success'
				})
			} catch (e) {
				console.error('分享失败', e)
			}
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
			
			return `${date.getMonth() + 1}-${date.getDate()}`
		}
	}
}
</script>

<style scoped>
.moments-container {
	min-height: 100vh;
	background: #f5f5f5;
}

.moments-header {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	height: 88rpx;
	background: #fff;
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 0 30rpx;
	box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.05);
	z-index: 100;
}

.header-title {
	font-size: 32rpx;
	font-weight: 600;
	color: #333;
}

.header-left,
.header-right {
	width: 80rpx;
	height: 80rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.iconfont {
	font-size: 40rpx;
	color: #333;
}

.moments-list {
	padding-top: 88rpx;
}

.publish-entry {
	display: flex;
	align-items: center;
	padding: 24rpx 30rpx;
	background: #fff;
	margin-bottom: 16rpx;
}

.entry-avatar {
	width: 80rpx;
	height: 80rpx;
	border-radius: 8rpx;
	overflow: hidden;
	margin-right: 20rpx;
}

.entry-avatar image {
	width: 100%;
	height: 100%;
}

.entry-text {
	flex: 1;
	height: 72rpx;
	line-height: 72rpx;
	background: #f5f5f5;
	border-radius: 8rpx;
	padding: 0 24rpx;
	color: #999;
	font-size: 28rpx;
}

.moment-item {
	background: #fff;
	margin-bottom: 16rpx;
	padding: 24rpx 30rpx;
}

.moment-user {
	display: flex;
	align-items: flex-start;
	margin-bottom: 20rpx;
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

.moment-content {
	margin-bottom: 20rpx;
}

.content-text {
	font-size: 30rpx;
	color: #333;
	line-height: 1.6;
	word-break: break-all;
}

.moment-media {
	margin-bottom: 20rpx;
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

.moment-location {
	display: flex;
	align-items: center;
	margin-bottom: 20rpx;
	color: #666;
	font-size: 24rpx;
}

.moment-location .iconfont {
	margin-right: 8rpx;
}

.moment-actions {
	display: flex;
	align-items: center;
	padding-top: 20rpx;
	border-top: 1rpx solid #f0f0f0;
}

.action-item {
	display: flex;
	align-items: center;
	margin-right: 40rpx;
	color: #666;
	font-size: 26rpx;
}

.action-item .iconfont {
	margin-right: 8rpx;
	font-size: 36rpx;
}

.action-item .icon-liked {
	color: #ff4d4f;
}

.load-more {
	text-align: center;
	padding: 30rpx;
	color: #999;
	font-size: 26rpx;
}

.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 100rpx 0;
}

.empty-state image {
	width: 300rpx;
	height: 300rpx;
	margin-bottom: 30rpx;
}

.empty-state text {
	color: #999;
	font-size: 28rpx;
	margin-bottom: 40rpx;
}

.btn-publish {
	width: 240rpx;
	height: 80rpx;
	line-height: 80rpx;
	background: linear-gradient(135deg, #07c160, #04bf56);
	color: #fff;
	font-size: 28rpx;
	border-radius: 40rpx;
}
</style>
