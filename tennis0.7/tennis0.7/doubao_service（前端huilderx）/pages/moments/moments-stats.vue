<template>
	<view class="stats-container">
		<!-- 顶部导航 -->
		<view class="stats-header">
			<text class="iconfont icon-back" @click="goBack"></text>
			<text class="header-title">数据统计</text>
			<view class="header-right"></view>
		</view>
		
		<scroll-view class="stats-content" scroll-y>
			<!-- 总览卡片 -->
			<view class="overview-cards">
				<view class="card-item">
					<view class="card-icon posts">
						<text class="iconfont icon-edit"></text>
					</view>
					<view class="card-info">
						<text class="card-value">{{ overview.total_posts || 0 }}</text>
						<text class="card-label">发布动态</text>
					</view>
				</view>
				<view class="card-item">
					<view class="card-icon likes">
						<text class="iconfont icon-like"></text>
					</view>
					<view class="card-info">
						<text class="card-value">{{ overview.total_likes || 0 }}</text>
						<text class="card-label">获赞总数</text>
					</view>
				</view>
				<view class="card-item">
					<view class="card-icon comments">
						<text class="iconfont icon-comment"></text>
					</view>
					<view class="card-info">
						<text class="card-value">{{ overview.total_comments || 0 }}</text>
						<text class="card-label">评论总数</text>
					</view>
				</view>
				<view class="card-item">
					<view class="card-icon shares">
						<text class="iconfont icon-share"></text>
					</view>
					<view class="card-info">
						<text class="card-value">{{ overview.total_shares || 0 }}</text>
						<text class="card-label">转发总数</text>
					</view>
				</view>
			</view>
			
			<!-- 趋势图表区域 -->
			<view class="chart-section">
				<view class="section-header">
					<text class="section-title">互动趋势</text>
					<view class="time-tabs">
						<text 
							v-for="item in timeOptions" 
							:key="item.value"
							:class="{ active: timeRange === item.value }"
							@click="changeTimeRange(item.value)"
						>{{ item.label }}</text>
					</view>
				</view>
				
				<!-- 简单柱状图 -->
				<view class="bar-chart">
					<view class="chart-y-axis">
						<text v-for="n in 5" :key="n">{{ Math.max(...trendData.map(t => t.likes_received), 0) * (6 - n) / 5 || 0 }}</text>
					</view>
					<view class="chart-bars">
						<view 
							class="bar-group"
							v-for="(item, idx) in trendData" 
							:key="idx"
						>
							<view class="bar-stack">
								<view 
									class="bar bar-likes" 
									:style="{ height: (item.likes_received / Math.max(...trendData.map(t => t.likes_received), 1) * 100) + '%' }"
								></view>
								<view 
									class="bar bar-comments" 
									:style="{ height: (item.comments_received / Math.max(...trendData.map(t => t.likes_received), 1) * 100) + '%' }"
								></view>
								<view 
									class="bar bar-shares" 
									:style="{ height: (item.shares_received / Math.max(...trendData.map(t => t.likes_received), 1) * 100) + '%' }"
								></view>
							</view>
							<text class="bar-label">{{ formatDate(item.date) }}</text>
						</view>
					</view>
				</view>
				
				<!-- 图例 -->
				<view class="chart-legend">
					<view class="legend-item">
						<view class="legend-dot likes"></view>
						<text>获赞</text>
					</view>
					<view class="legend-item">
						<view class="legend-dot comments"></view>
						<text>评论</text>
					</view>
					<view class="legend-item">
						<view class="legend-dot shares"></view>
						<text>转发</text>
					</view>
				</view>
			</view>
			
			<!-- 今日数据 -->
			<view class="today-section">
				<view class="section-title">今日数据</view>
				<view class="today-cards">
					<view class="today-item">
						<text class="today-value">{{ todayStats.posts_count || 0 }}</text>
						<text class="today-label">发布</text>
					</view>
					<view class="today-item">
						<text class="today-value">{{ todayStats.likes_received || 0 }}</text>
						<text class="today-label">获赞</text>
					</view>
					<view class="today-item">
						<text class="today-value">{{ todayStats.comments_received || 0 }}</text>
						<text class="today-label">评论</text>
					</view>
					<view class="today-item">
						<text class="today-value">{{ todayStats.likes_given || 0 }}</text>
						<text class="today-label">点赞</text>
					</view>
				</view>
			</view>
			
			<!-- 互动率分析 -->
			<view class="engagement-section">
				<view class="section-title">互动分析</view>
				<view class="engagement-content">
					<view class="engagement-rate">
						<view class="rate-circle">
							<text class="rate-value">{{ engagementRate }}%</text>
							<text class="rate-label">互动率</text>
						</view>
					</view>
					<view class="engagement-detail">
						<view class="detail-row">
							<text class="row-label">平均点赞</text>
							<text class="row-value">{{ avgLikes }}</text>
						</view>
						<view class="detail-row">
							<text class="row-label">平均评论</text>
							<text class="row-value">{{ avgComments }}</text>
						</view>
						<view class="detail-row">
							<text class="row-label">平均转发</text>
							<text class="row-value">{{ avgShares }}</text>
						</view>
					</view>
				</view>
			</view>
			
			<!-- 热门动态 -->
			<view class="hot-posts-section">
				<view class="section-title">热门动态</view>
				<view class="hot-list">
					<view 
						class="hot-item"
						v-for="(item, idx) in hotPosts"
						:key="item.id"
						@click="goDetail(item.id)"
					>
						<view class="hot-rank" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</view>
						<view class="hot-info">
							<text class="hot-content">{{ item.content }}</text>
							<text class="hot-stats">赞 {{ item.likes_count || 0 }} · 评论 {{ item.comments_count || 0 }}</text>
						</view>
					</view>
				</view>
				<view class="no-data" v-if="hotPosts.length === 0">
					<text>暂无热门动态</text>
				</view>
			</view>
		</scroll-view>
	</view>
</template>

<script>
import { 
	getStatsOverview, 
	getStatsTrend,
	getStatsSummary,
	getMomentsList
} from '@/utils/moments-store/index.js'

export default {
	data() {
		return {
			timeOptions: [
				{ label: '7天', value: 7 },
				{ label: '14天', value: 14 },
				{ label: '30天', value: 30 }
			],
			timeRange: 7,
			overview: {},
			trendData: [],
			todayStats: {},
			hotPosts: []
		}
	},
	computed: {
		engagementRate() {
			if (!this.overview.total_posts || this.overview.total_posts === 0) return 0
			const total = (this.overview.total_likes || 0) + 
				(this.overview.total_comments || 0) + 
				(this.overview.total_shares || 0)
			return Math.round((total / this.overview.total_posts) * 100)
		},
		avgLikes() {
			if (!this.overview.total_posts) return 0
			return (this.overview.total_likes / this.overview.total_posts).toFixed(1)
		},
		avgComments() {
			if (!this.overview.total_posts) return 0
			return (this.overview.total_comments / this.overview.total_posts).toFixed(1)
		},
		avgShares() {
			if (!this.overview.total_posts) return 0
			return (this.overview.total_shares / this.overview.total_posts).toFixed(1)
		}
	},
	onLoad() {
		this.loadData()
	},
	methods: {
		async loadData() {
			await Promise.all([
				this.loadOverview(),
				this.loadTrend(),
				this.loadTodayStats(),
				this.loadHotPosts()
			])
		},
		
		async loadOverview() {
			try {
				this.overview = await getStatsOverview()
			} catch (e) {
				console.error('加载总览失败', e)
			}
		},
		
		async loadTrend() {
			try {
				const res = await getStatsTrend(this.timeRange)
				this.trendData = res.trend || []
			} catch (e) {
				console.error('加载趋势失败', e)
				this.trendData = []
			}
		},
		
		async loadTodayStats() {
			try {
				const res = await getStatsSummary()
				const today = res.daily_stats?.[0] || {}
				this.todayStats = today
			} catch (e) {
				console.error('加载今日数据失败', e)
			}
		},
		
		async loadHotPosts() {
			try {
				const res = await getMomentsList(1, 20)
				this.hotPosts = (res.list || [])
					.filter(m => m.likes_count > 0 || m.comments_count > 0)
					.sort((a, b) => (b.likes_count + b.comments_count) - (a.likes_count + a.comments_count))
					.slice(0, 5)
			} catch (e) {
				console.error('加载热门动态失败', e)
			}
		},
		
		changeTimeRange(days) {
			this.timeRange = days
			this.loadTrend()
		},
		
		formatDate(dateStr) {
			if (!dateStr) return ''
			const date = new Date(dateStr)
			return `${date.getMonth() + 1}/${date.getDate()}`
		},
		
		goBack() {
			uni.navigateBack()
		},
		
		goDetail(id) {
			uni.navigateTo({
				url: `/pages/moments/moments-detail?id=${id}`
			})
		}
	}
}
</script>

<style scoped>
.stats-container {
	min-height: 100vh;
	background: #f5f5f5;
}

.stats-header {
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

.icon-back {
	font-size: 40rpx;
	color: #333;
}

.header-title {
	font-size: 32rpx;
	font-weight: 600;
	color: #333;
}

.header-right {
	width: 80rpx;
}

.stats-content {
	padding-top: 88rpx;
}

.overview-cards {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 24rpx;
	padding: 30rpx;
}

.card-item {
	background: #fff;
	border-radius: 16rpx;
	padding: 30rpx;
	display: flex;
	align-items: center;
}

.card-icon {
	width: 80rpx;
	height: 80rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 20rpx;
}

.card-icon.posts {
	background: #e8f4ff;
}

.card-icon.posts .iconfont {
	color: #1890ff;
}

.card-icon.likes {
	background: #fff2e8;
}

.card-icon.likes .iconfont {
	color: #fa8c16;
}

.card-icon.comments {
	background: #f6ffed;
}

.card-icon.comments .iconfont {
	color: #52c41a;
}

.card-icon.shares {
	background: #fff0f0;
}

.card-icon.shares .iconfont {
	color: #ff4d4f;
}

.card-icon .iconfont {
	font-size: 36rpx;
}

.card-info {
	display: flex;
	flex-direction: column;
}

.card-value {
	font-size: 40rpx;
	font-weight: 700;
	color: #333;
}

.card-label {
	font-size: 24rpx;
	color: #999;
	margin-top: 4rpx;
}

.chart-section {
	background: #fff;
	margin: 0 30rpx 30rpx;
	border-radius: 16rpx;
	padding: 30rpx;
}

.section-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 30rpx;
}

.section-title {
	font-size: 30rpx;
	font-weight: 600;
	color: #333;
}

.time-tabs {
	display: flex;
	gap: 20rpx;
}

.time-tabs text {
	font-size: 24rpx;
	color: #999;
	padding: 8rpx 16rpx;
	border-radius: 20rpx;
}

.time-tabs text.active {
	background: #e8f8ee;
	color: #07c160;
}

.bar-chart {
	display: flex;
	height: 300rpx;
}

.chart-y-axis {
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	padding-right: 20rpx;
	padding-top: 10rpx;
	padding-bottom: 40rpx;
}

.chart-y-axis text {
	font-size: 20rpx;
	color: #999;
	text-align: right;
}

.chart-bars {
	flex: 1;
	display: flex;
	align-items: flex-end;
	justify-content: space-around;
	padding-bottom: 40rpx;
}

.bar-group {
	display: flex;
	flex-direction: column;
	align-items: center;
	flex: 1;
}

.bar-stack {
	display: flex;
	align-items: flex-end;
	justify-content: center;
	gap: 4rpx;
	height: 220rpx;
}

.bar {
	width: 24rpx;
	min-height: 4rpx;
	border-radius: 4rpx 4rpx 0 0;
}

.bar-likes {
	background: #1890ff;
}

.bar-comments {
	background: #52c41a;
}

.bar-shares {
	background: #ff4d4f;
}

.bar-label {
	font-size: 20rpx;
	color: #999;
	margin-top: 8rpx;
}

.chart-legend {
	display: flex;
	justify-content: center;
	gap: 40rpx;
	margin-top: 30rpx;
	padding-top: 20rpx;
	border-top: 1rpx solid #f0f0f0;
}

.legend-item {
	display: flex;
	align-items: center;
	gap: 8rpx;
	font-size: 24rpx;
	color: #666;
}

.legend-dot {
	width: 16rpx;
	height: 16rpx;
	border-radius: 50%;
}

.legend-dot.likes {
	background: #1890ff;
}

.legend-dot.comments {
	background: #52c41a;
}

.legend-dot.shares {
	background: #ff4d4f;
}

.today-section {
	background: #fff;
	margin: 0 30rpx 30rpx;
	border-radius: 16rpx;
	padding: 30rpx;
}

.today-cards {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 20rpx;
	margin-top: 24rpx;
}

.today-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 20rpx;
	background: #f8f8f8;
	border-radius: 12rpx;
}

.today-value {
	font-size: 36rpx;
	font-weight: 700;
	color: #333;
}

.today-label {
	font-size: 22rpx;
	color: #999;
	margin-top: 4rpx;
}

.engagement-section {
	background: #fff;
	margin: 0 30rpx 30rpx;
	border-radius: 16rpx;
	padding: 30rpx;
}

.engagement-content {
	display: flex;
	align-items: center;
	margin-top: 24rpx;
}

.engagement-rate {
	width: 200rpx;
	height: 200rpx;
	background: linear-gradient(135deg, #07c160, #04bf56);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 40rpx;
}

.rate-circle {
	display: flex;
	flex-direction: column;
	align-items: center;
}

.rate-value {
	font-size: 48rpx;
	font-weight: 700;
	color: #fff;
}

.rate-label {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.8);
	margin-top: 4rpx;
}

.engagement-detail {
	flex: 1;
}

.detail-row {
	display: flex;
	justify-content: space-between;
	padding: 16rpx 0;
	border-bottom: 1rpx solid #f0f0f0;
}

.detail-row:last-child {
	border-bottom: none;
}

.row-label {
	font-size: 26rpx;
	color: #666;
}

.row-value {
	font-size: 26rpx;
	color: #333;
	font-weight: 600;
}

.hot-posts-section {
	background: #fff;
	margin: 0 30rpx 30rpx;
	border-radius: 16rpx;
	padding: 30rpx;
}

.hot-list {
	margin-top: 24rpx;
}

.hot-item {
	display: flex;
	align-items: flex-start;
	padding: 20rpx 0;
	border-bottom: 1rpx solid #f0f0f0;
}

.hot-item:last-child {
	border-bottom: none;
}

.hot-rank {
	width: 48rpx;
	height: 48rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24rpx;
	font-weight: 700;
	color: #fff;
	background: #ddd;
	margin-right: 20rpx;
}

.hot-rank.rank-1 {
	background: linear-gradient(135deg, #ffd700, #ffa500);
}

.hot-rank.rank-2 {
	background: linear-gradient(135deg, #c0c0c0, #a0a0a0);
}

.hot-rank.rank-3 {
	background: linear-gradient(135deg, #cd7f32, #b8860b);
}

.hot-info {
	flex: 1;
	display: flex;
	flex-direction: column;
}

.hot-content {
	font-size: 26rpx;
	color: #333;
	line-height: 1.4;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	margin-bottom: 8rpx;
}

.hot-stats {
	font-size: 22rpx;
	color: #999;
}

.no-data {
	text-align: center;
	padding: 40rpx;
	color: #999;
	font-size: 26rpx;
}
</style>
