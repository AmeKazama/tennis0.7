<template>
	<view class="container">
		<view class="header-section" v-if="activeTab === 'home'">
			<view class="ai-coach-card" @tap="goToAICoachSelect">
				<view class="aurora-bg"></view>
				<view class="ai-icon">
					<text class="ai-emoji">🧠</text>
				</view>
				<text class="ai-title">AI 教练</text>
				<text class="ai-subtitle">助你快速涨球</text>
			</view>
			<view class="right-cards">
				<view class="small-card highlight-card" @tap="goToHighlightEdit">
					<view class="small-icon orange-icon">✂️</view>
					<text class="small-title">回合剪辑</text>
					<text class="small-subtitle">自动生成高光</text>
				</view>
				<view class="small-card diary-card" @tap="goToDiary">
					<view class="small-icon blue-icon">📝</view>
					<text class="small-title">打球日记</text>
					<text class="small-subtitle">打完就记</text>
				</view>
			</view>
		</view>

		<view class="section-title" v-if="activeTab === 'home'">
			<text>技术工坊</text>
			<view class="mascot">🎾</view>
		</view>

		<view class="workshop-grid" v-if="activeTab === 'home'">
			<view class="workshop-card" @tap="goToServe">
				<view class="workshop-icon red-glow">
					<text class="workshop-emoji">✨</text>
				</view>
				<text class="workshop-title">高光特效</text>
			</view>
			<view class="workshop-card" @tap="goToCoach">
				<view class="workshop-icon green-glow">
					<text class="workshop-emoji">🏃</text>
				</view>
				<text class="workshop-title">动作提取</text>
			</view>
			<view class="workshop-card" @tap="goToReport">
				<view class="workshop-icon purple-glow">
					<text class="workshop-emoji">📊</text>
				</view>
				<text class="workshop-title">动作对比</text>
			</view>
			<view class="workshop-card" @tap="goToSetting">
				<view class="workshop-icon orange-glow">
					<text class="workshop-emoji">⏱️</text>
				</view>
				<text class="workshop-title">穿线磅数</text>
			</view>
			<view class="workshop-card" @tap="goToProfile">
				<view class="workshop-icon cyan-glow">
					<text class="workshop-emoji">👤</text>
				</view>
				<text class="workshop-title">教练管理</text>
			</view>
		</view>

		<view class="section-title" v-if="activeTab === 'home'">
			<text>社区互动</text>
		</view>

		<view class="community-grid" v-if="activeTab === 'home'">
			<view class="community-card" @tap="goToPublish">
				<view class="community-icon">
					<text class="community-emoji">🎥</text>
				</view>
				<text class="community-title">发视频</text>
			</view>
			<view class="community-card" @tap="showToast('求点评')">
				<view class="community-icon">
					<text class="community-emoji">❓</text>
				</view>
				<text class="community-title">求点评</text>
			</view>
			<view class="community-card" @tap="goToPublish">
				<view class="community-icon">
					<text class="community-emoji">🖼️</text>
				</view>
				<text class="community-title">发图文</text>
			</view>
		</view>

		<view class="hint-text" v-if="activeTab === 'home'">
			<text class="hint-icon">ℹ️</text>
			<text class="hint-label">功能说明</text>
		</view>

		<view class="video-section" v-if="activeTab === 'video'">
			<view class="navbar">
				<view class="back" @tap="goBack">←</view>
				<text class="title">选择视频</text>
			</view>

			<view class="video-list">
				<view class="video-item" v-for="(item, index) in videoList" :key="index" @tap="selectVideo(item)">
					<view class="video-thumb">
						<image class="thumb-img" :src="item.thumb" mode="aspectFill"></image>
						<view class="play-overlay">
							<text class="play-icon">▶</text>
						</view>
						<view class="duration">{{ item.duration }}</view>
					</view>
					<view class="video-info">
						<text class="video-title">{{ item.title }}</text>
						<text class="video-date">{{ item.date }}</text>
					</view>
				</view>
			</view>
		</view>

		<view class="tab-content" v-if="activeTab === 'record'">
			<view class="message-header">
				<text class="message-title">消息</text>
				<view class="header-line"></view>
			</view>

			<view class="message-icons">
				<view class="message-icon-item">
					<view class="icon-circle pink-bg">
						<text class="icon-emoji">❤️</text>
					</view>
					<text class="icon-label">赞和收藏</text>
				</view>
				<view class="message-icon-item">
					<view class="icon-circle blue-bg">
						<text class="icon-emoji">👤</text>
						<text class="icon-plus">+</text>
					</view>
					<text class="icon-label">新增关注</text>
				</view>
				<view class="message-icon-item">
					<view class="icon-circle green-bg">
						<text class="icon-emoji">💬</text>
						<text class="icon-mascot">🎾</text>
					</view>
					<text class="icon-label">评论和@</text>
				</view>
			</view>

			<view class="message-list">
				<view class="message-item">
					<view class="item-icon orange-bg">
						<text class="item-emoji">⚙️</text>
					</view>
					<view class="item-content">
						<text class="item-title">系统消息</text>
						<text class="item-desc">暂无系统消息</text>
					</view>
					<text class="item-arrow">></text>
				</view>

				<view class="message-item">
					<view class="item-icon purple-bg">
						<text class="item-emoji">💡</text>
					</view>
					<view class="item-content">
						<text class="item-title">指导消息</text>
						<text class="item-desc">暂无指导消息</text>
					</view>
					<text class="item-arrow">></text>
				</view>

				<view class="message-item">
					<view class="item-icon purple-light-bg">
						<text class="item-emoji">💬</text>
					</view>
					<view class="item-content">
						<text class="item-title">聊天</text>
						<text class="item-desc">进入会话列表</text>
					</view>
					<text class="item-arrow">></text>
				</view>
			</view>
		</view>

		<view class="tab-content" v-if="activeTab === 'compete'">
			<view class="page-header">
				<text class="title">训练数据</text>
				<text class="sub-title">本周训练表现</text>
			</view>

			<view class="summary-card">
				<view class="summary-item">
					<text class="num">12</text>
					<text class="label">训练次数</text>
				</view>
				<view class="summary-item">
					<text class="num">4.8h</text>
					<text class="label">总时长</text>
				</view>
				<view class="summary-item">
					<text class="num">89</text>
					<text class="label">平均评分</text>
				</view>
			</view>

			<view class="card-list">
				<view class="data-card" @tap="goToReport('发球训练')">
					<view class="card-icon">🎾</view>
					<view class="card-info">
						<text class="card-title">发球训练</text>
						<text class="card-desc">共8次 · 平均87分</text>
					</view>
					<view class="card-arrow">></view>
				</view>

				<view class="data-card" @tap="goToReport('正手击球')">
					<view class="card-icon">🏸</view>
					<view class="card-info">
						<text class="card-title">正手击球</text>
						<text class="card-desc">共6次 · 平均91分</text>
					</view>
					<view class="card-arrow">></view>
				</view>

				<view class="data-card" @tap="goToReport('反手击球')">
					<view class="card-icon">🥎</view>
					<view class="card-info">
						<text class="card-title">反手击球</text>
						<text class="card-desc">共5次 · 平均85分</text>
					</view>
					<view class="card-arrow">></view>
				</view>

				<view class="data-card" @tap="goToReport('脚步训练')">
					<view class="card-icon">👟</view>
					<view class="card-info">
						<text class="card-title">脚步训练</text>
						<text class="card-desc">共4次 · 平均83分</text>
					</view>
					<view class="card-arrow">></view>
				</view>
			</view>
		</view>

		<view class="tab-content" v-if="activeTab === 'profile'">
			<view class="page-header">
				<text class="title">我的</text>
			</view>

			<view class="user-card">
				<view class="avatar">U</view>
				<view class="info">
					<text class="name">网球训练者</text>
					<text class="level">业余3级 · 正在提升</text>
				</view>
			</view>

			<view class="stat-row">
				<view class="stat">
					<text class="num">24</text>
					<text class="label">总训练</text>
				</view>
				<view class="stat">
					<text class="num">9.3h</text>
					<text class="label">总时长</text>
				</view>
				<view class="stat">
					<text class="num">86</text>
					<text class="label">平均分</text>
				</view>
			</view>

			<view class="menu">
				<view class="item" @tap="goToGrowth">
					<text>成长数据</text>
					<text>&gt;</text>
				</view>
				<view class="item" @tap="goToAchievement">
					<text>成就墙</text>
					<text>&gt;</text>
				</view>
				<view class="item" @tap="goToSetting">
					<text>设置</text>
					<text>&gt;</text>
				</view>
			</view>
		</view>

		<view class="bottom-nav">
			<view class="nav-item" :class="{ active: activeTab === 'video' }" @tap="setTab('video')">
			<text class="nav-icon">🏠</text>
			<text class="nav-label">首页</text>
		</view>
			<view class="nav-item" :class="{ active: activeTab === 'record' }" @tap="setTab('record')">
				<text class="nav-icon">👥</text>
				<text class="nav-label">社交圈</text>
			</view>
			<view class="nav-center-btn" @tap="setTab('home')">
			<view class="center-btn-inner">
				<text class="center-btn-icon">+</text>
			</view>
			<text class="center-btn-label">复盘</text>
		</view>
			<view class="nav-item" :class="{ active: activeTab === 'compete' }" @tap="setTab('compete')">
				<text class="nav-icon">📊</text>
				<text class="nav-label">数据</text>
			</view>
			<view class="nav-item" :class="{ active: activeTab === 'profile' }" @tap="setTab('profile')">
				<text class="nav-icon">👤</text>
				<text class="nav-label">我的</text>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	data() {
			return {
				activeTab: 'video',
				currentType: 0,
				modeList: [
				{ label: "练习模式", icon: "🏃" },
				{ label: "比赛模式", icon: "🤝" },
				{ label: "发球专项", icon: "🎾" },
				{ label: "发球机模拟", icon: "🤖" }
			],
			players: [
				{ avatar: "JL", name: "Jean Lee" }
			],
			videoList: [
				{
					title: '正手击球练习',
					date: '2026-04-12 15:30',
					duration: '3:25',
					thumb: '/static/logo.png'
				},
				{
					title: '反手击球练习',
					date: '2026-04-11 16:45',
					duration: '2:48',
					thumb: '/static/logo.png'
				},
				{
					title: '发球训练',
					date: '2026-04-10 14:20',
					duration: '4:12',
					thumb: '/static/logo.png'
				},
				{
					title: '比赛录像',
					date: '2026-04-09 19:10',
					duration: '15:30',
					thumb: '/static/logo.png'
				}
			]
			}
		},
	methods: {
		setTab(tab) {
			this.activeTab = tab
		},
		showToast(title) {
			uni.showToast({
				title: title,
				icon: 'none'
			})
		},
		goToVideoList() {
			uni.navigateTo({
				url: '/pages/video-list/video-list'
			})
		},
		goToHighlightEdit() {
			uni.navigateTo({
				url: '/pages/highlight-edit/highlight-edit'
			})
		},
		goToDiary() {
			uni.navigateTo({
				url: '/pages/content/diary/diary'
			})
		},
		goToAICoachSelect() {
			uni.navigateTo({
				url: '/pages/ai-coach-select/ai-coach-select'
			})
		},
		goToCoach() {
			uni.navigateTo({
				url: '/pages/action-extraction/action-extraction'
			})
		},
		goToPublish() {
			uni.navigateTo({
				url: '/pages/publish/publish'
			})
		},
		goToRecord() {
			this.activeTab = 'record'
		},
		goToGrowth() {
			uni.navigateTo({
				url: '/pages/growth/growth'
			})
		},
		goToServe() {
			uni.navigateTo({
				url: '/pages/serve/serve'
			})
		},
		goToReport(type) {
			uni.navigateTo({
				url: '/pages/action-comparison/action-comparison'
			})
		},
		goToSetting() {
			uni.navigateTo({
				url: '/pages/setting/setting'
			})
		},
		goToProfile() {
			this.activeTab = 'profile'
		},
		goToAchievement() {
			uni.navigateTo({
				url: '/pages/achievement/achievement'
			})
		},
		selectType(idx) {
			this.currentType = idx
		},
		removePlayer(idx) {
				uni.showModal({
					title: "删除球员",
					content: "确定要删除该球员吗？",
					success: (res) => {
						if (res.confirm) {
							this.players.splice(idx, 1)
						}
					}
				})
			},
			addPlayer() {
				uni.showToast({
					title: "添加球员功能",
					icon: "none"
				})
			},
			goBack() {
				uni.navigateBack()
			},
			selectVideo(item) {
				uni.showToast({
					title: `选择了视频: ${item.title}`,
					icon: "none"
				})
			}
	}
}
</script>

<style>
.container {
	min-height: 100vh;
	background: #121212;
	padding: 32rpx;
	padding-bottom: 160rpx;
}

.status-bar {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 32rpx;
}

.time {
	color: #ffffff;
	font-size: 32rpx;
	font-weight: 600;
}

.status-icons {
	display: flex;
	gap: 16rpx;
}

.status-icon {
	font-size: 32rpx;
}

.header-section {
	display: flex;
	gap: 24rpx;
	margin-bottom: 48rpx;
}

.ai-coach-card {
	flex: 1.3;
	background: linear-gradient(135deg, rgba(138, 43, 226, 0.3) 0%, rgba(18, 18, 18, 1) 100%);
	border-radius: 28rpx;
	padding: 48rpx 32rpx;
	position: relative;
	overflow: hidden;
	border: 1px solid rgba(163, 255, 18, 0.1);
	box-shadow: 0 4px 20px rgba(163, 255, 18, 0.05);
	transition: transform 0.3s;
}

.ai-coach-card:active {
	transform: scale(1.02);
}

.aurora-bg {
	position: absolute;
	top: -50%;
	left: -50%;
	width: 200%;
	height: 200%;
	background: radial-gradient(ellipse at center, rgba(138, 43, 226, 0.4) 0%, transparent 70%);
	animation: aurora 8s ease-in-out infinite;
}

@keyframes aurora {
	0%, 100% { transform: translate(0, 0) rotate(0deg); }
	50% { transform: translate(10%, 10%) rotate(10deg); }
}

.ai-icon {
	width: 96rpx;
	height: 96rpx;
	border-radius: 48rpx;
	background: rgba(255, 255, 255, 0.1);
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 24rpx;
	position: relative;
	z-index: 1;
}

.ai-emoji {
	font-size: 48rpx;
}

.ai-title {
	display: block;
	color: #ffffff;
	font-size: 44rpx;
	font-weight: 700;
	margin-bottom: 8rpx;
	position: relative;
	z-index: 1;
}

.ai-subtitle {
	display: block;
	color: #888888;
	font-size: 28rpx;
	position: relative;
	z-index: 1;
}

.right-cards {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}

.small-card {
	flex: 1;
	background: rgba(30, 30, 30, 0.8);
	border-radius: 24rpx;
	padding: 32rpx 24rpx;
	border: 1px solid rgba(255, 255, 255, 0.05);
	backdrop-filter: blur(10rpx);
	transition: transform 0.3s;
}

.small-card:active {
	transform: scale(1.02);
}

.small-icon {
	width: 64rpx;
	height: 64rpx;
	border-radius: 32rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 16rpx;
	font-size: 32rpx;
}

.orange-icon {
	background: rgba(255, 165, 0, 0.2);
}

.blue-icon {
	background: rgba(0, 136, 255, 0.2);
}

.small-title {
	display: block;
	color: #ffffff;
	font-size: 32rpx;
	font-weight: 600;
	margin-bottom: 8rpx;
}

.small-subtitle {
	display: block;
	color: #666666;
	font-size: 24rpx;
}

.section-title {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 24rpx;
}

.section-title text {
	color: #ffffff;
	font-size: 36rpx;
	font-weight: 600;
}

.mascot {
	width: 64rpx;
	height: 64rpx;
	border-radius: 32rpx;
	background: rgba(255, 255, 255, 0.1);
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 32rpx;
}

.workshop-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 24rpx;
	margin-bottom: 48rpx;
}

.workshop-card {
	background: rgba(30, 30, 30, 0.8);
	border-radius: 24rpx;
	padding: 48rpx 32rpx;
	border: 1px solid rgba(255, 255, 255, 0.05);
	backdrop-filter: blur(10rpx);
	display: flex;
	flex-direction: column;
	align-items: center;
	transition: transform 0.3s;
}

.workshop-card:active {
	transform: scale(1.02);
}

.workshop-icon {
	width: 96rpx;
	height: 96rpx;
	border-radius: 48rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 20rpx;
	font-size: 40rpx;
	animation: breathe 3s ease-in-out infinite;
}

@keyframes breathe {
	0%, 100% { box-shadow: 0 0 20rpx rgba(163, 255, 18, 0.3); }
	50% { box-shadow: 0 0 40rpx rgba(163, 255, 18, 0.6); }
}

.red-glow {
	background: rgba(255, 100, 100, 0.2);
	animation: breatheRed 3s ease-in-out infinite;
}

@keyframes breatheRed {
	0%, 100% { box-shadow: 0 0 20rpx rgba(255, 100, 100, 0.3); }
	50% { box-shadow: 0 0 40rpx rgba(255, 100, 100, 0.6); }
}

.green-glow {
	background: rgba(100, 255, 100, 0.2);
	animation: breatheGreen 3s ease-in-out infinite;
}

@keyframes breatheGreen {
	0%, 100% { box-shadow: 0 0 20rpx rgba(100, 255, 100, 0.3); }
	50% { box-shadow: 0 0 40rpx rgba(100, 255, 100, 0.6); }
}

.purple-glow {
	background: rgba(180, 100, 255, 0.2);
	animation: breathePurple 3s ease-in-out infinite;
}

@keyframes breathePurple {
	0%, 100% { box-shadow: 0 0 20rpx rgba(180, 100, 255, 0.3); }
	50% { box-shadow: 0 0 40rpx rgba(180, 100, 255, 0.6); }
}

.orange-glow {
	background: rgba(255, 180, 100, 0.2);
	animation: breatheOrange 3s ease-in-out infinite;
}

@keyframes breatheOrange {
	0%, 100% { box-shadow: 0 0 20rpx rgba(255, 180, 100, 0.3); }
	50% { box-shadow: 0 0 40rpx rgba(255, 180, 100, 0.6); }
}

.cyan-glow {
	background: rgba(100, 200, 255, 0.2);
	animation: breatheCyan 3s ease-in-out infinite;
}

@keyframes breatheCyan {
	0%, 100% { box-shadow: 0 0 20rpx rgba(100, 200, 255, 0.3); }
	50% { box-shadow: 0 0 40rpx rgba(100, 200, 255, 0.6); }
}

.workshop-emoji {
	font-size: 40rpx;
}

.workshop-title {
	color: #ffffff;
	font-size: 32rpx;
	font-weight: 600;
}

.community-grid {
	display: grid;
	grid-template-columns: 1fr 1fr 1fr;
	gap: 24rpx;
	margin-bottom: 48rpx;
}

.community-card {
	background: rgba(30, 30, 30, 0.8);
	border-radius: 24rpx;
	padding: 48rpx 24rpx;
	border: 1px solid rgba(163, 255, 18, 0.1);
	backdrop-filter: blur(10rpx);
	display: flex;
	flex-direction: column;
	align-items: center;
	transition: transform 0.3s;
}

.community-card:active {
	transform: scale(1.02);
}

.community-icon {
	width: 96rpx;
	height: 96rpx;
	border-radius: 48rpx;
	background: rgba(163, 255, 18, 0.1);
	border: 2px solid rgba(163, 255, 18, 0.3);
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 20rpx;
}

.community-emoji {
	font-size: 40rpx;
}

.community-title {
	color: #ffffff;
	font-size: 28rpx;
	font-weight: 500;
}

.hint-text {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 8rpx;
	margin-bottom: 32rpx;
}

.hint-icon {
	font-size: 28rpx;
}

.hint-label {
	color: #444444;
	font-size: 24rpx;
}

.tab-content {
	margin-top: 0;
}

.page-header {
	margin-bottom: 30rpx;
}

.title {
	font-size: 36rpx;
	font-weight: bold;
	color: #fff;
}

.sub-title {
	font-size: 24rpx;
	color: #888;
	margin-top: 10rpx;
	display: block;
}

.card {
	background: #111;
	border-radius: 24rpx;
	padding: 30rpx;
	margin-bottom: 24rpx;
}

.card-title {
	font-size: 28rpx;
	color: #38bdf8;
	margin-bottom: 24rpx;
	display: block;
}

.type-grid {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 20rpx;
}

.type-item {
	background: #1a1a1a;
	border-radius: 16rpx;
	padding: 25rpx;
	display: flex;
	align-items: center;
	gap: 15rpx;
	transition: all 0.2s ease;
}

.type-item.active {
	background: linear-gradient(135deg, #22c55e, #a3e635);
	color: #000;
}

.type-icon {
	font-size: 30rpx;
	flex-shrink: 0;
}

.type-text {
	font-size: 26rpx;
	font-weight: 500;
}

.player-item {
	display: flex;
	align-items: center;
	gap: 20rpx;
	background: #1a1a1a;
	padding: 25rpx;
	border-radius: 16rpx;
	margin-bottom: 15rpx;
}

.player-avatar {
	width: 60rpx;
	height: 60rpx;
	background: #38bdf8;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 20rpx;
	color: #fff;
	font-weight: bold;
	flex-shrink: 0;
}

.player-name {
	flex: 1;
	font-size: 26rpx;
	color: #fff;
}

.player-close {
	color: #ef4444;
	font-size: 24rpx;
	flex-shrink: 0;
}

.add-player {
	text-align: center;
	padding: 25rpx;
	border: 1rpx dashed #333;
	border-radius: 16rpx;
	color: #888;
	font-size: 24rpx;
}

.list-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 28rpx 0;
	font-size: 26rpx;
	color: #fff;
	border-bottom: 1rpx solid #222;
}

.list-item:last-child {
	border-bottom: none;
}

.arrow {
	color: #888;
	font-size: 24rpx;
}

.start-btn {
	margin-top: 30rpx;
	background: linear-gradient(135deg, #22c55e, #a3e635);
	text-align: center;
	padding: 30rpx;
	border-radius: 100rpx;
	font-size: 30rpx;
	font-weight: bold;
	color: #000;
}

.summary-card {
	background: #111;
	border-radius: 24rpx;
	padding: 40rpx 30rpx;
	display: flex;
	justify-content: space-around;
	margin-bottom: 30rpx;
}

.summary-item {
	text-align: center;
}

.num {
	font-size: 40rpx;
	font-weight: bold;
	color: #38bdf8;
}

.label {
	font-size: 24rpx;
	color: #999;
	margin-top: 10rpx;
	display: block;
}

.card-list {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.data-card {
	background: #1a1a1a;
	border-radius: 24rpx;
	padding: 30rpx;
	display: flex;
	align-items: center;
}

.card-icon {
	font-size: 40rpx;
	margin-right: 20rpx;
}

.card-info {
	flex: 1;
}

.card-title {
	font-size: 30rpx;
	font-weight: 500;
	color: #fff;
}

.card-desc {
	font-size: 24rpx;
	color: #888;
	margin-top: 8rpx;
	display: block;
}

.card-arrow {
	font-size: 30rpx;
	color: #666;
}

.user-card {
	display: flex;
	align-items: center;
	gap: 24rpx;
	margin-bottom: 30rpx;
}

.avatar {
	width: 100rpx;
	height: 100rpx;
	background: #22c55e;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 40rpx;
	color: #fff;
}

.info {
	flex: 1;
}

.name {
	font-size: 36rpx;
	font-weight: bold;
	color: #fff;
	display: block;
}

.level {
	color: #888;
	font-size: 24rpx;
	display: block;
	margin-top: 8rpx;
}

.stat-row {
	background: #111;
	border-radius: 24rpx;
	padding: 40rpx 30rpx;
	display: flex;
	justify-content: space-around;
	margin-bottom: 30rpx;
}

.stat {
	text-align: center;
}

.stat .num {
	font-size: 36rpx;
	font-weight: bold;
	color: #fff;
}

.stat .label {
	font-size: 22rpx;
	color: #888;
	margin-top: 10rpx;
	display: block;
}

.menu {
	background: #111;
	border-radius: 24rpx;
	overflow: hidden;
}

.menu .item {
	display: flex;
	justify-content: space-between;
	padding: 30rpx;
	font-size: 28rpx;
	color: #fff;
	border-bottom: 1px solid #222;
}

.menu .item:last-child {
	border-bottom: 0;
}

.bottom-nav {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	background: rgba(18, 18, 18, 0.9);
	backdrop-filter: blur(20rpx);
	display: flex;
	align-items: center;
	justify-content: space-around;
	padding: 24rpx 32rpx;
	padding-bottom: 48rpx;
	border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.nav-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8rpx;
}

.nav-icon {
	font-size: 40rpx;
	opacity: 0.5;
}

.nav-item.active .nav-icon {
	opacity: 1;
}

.nav-label {
	color: #666666;
	font-size: 22rpx;
}

.nav-item.active .nav-label {
	color: #A3FF12;
}

.nav-center-btn {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 8rpx;
	margin-top: -40rpx;
}

.center-btn-inner {
	width: 120rpx;
	height: 120rpx;
	border-radius: 60rpx;
	background: linear-gradient(135deg, #A3FF12 0%, #85CC0F 100%);
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 8rpx 32rpx rgba(163, 255, 18, 0.4);
	transition: transform 0.3s;
}

.center-btn-inner:active {
	transform: scale(0.95);
}

.center-btn-icon {
	color: #121212;
	font-size: 48rpx;
	font-weight: 700;
}

.center-btn-label {
	color: #A3FF12;
	font-size: 22rpx;
	font-weight: 500;
}

.status-bar-message {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 40rpx;
	padding-top: 20rpx;
}

.message-header {
	text-align: center;
	margin-bottom: 48rpx;
	position: relative;
}

.message-title {
	font-size: 36rpx;
	font-weight: bold;
	color: #fff;
}

.header-line {
	width: 200rpx;
	height: 6rpx;
	background: #3b82f6;
	margin: 16rpx auto 0;
	border-radius: 3rpx;
}

.message-icons {
	display: flex;
	justify-content: space-around;
	margin-bottom: 48rpx;
}

.message-icon-item {
	display: flex;
	flex-direction: column;
	align-items: center;
}

.icon-circle {
	width: 120rpx;
	height: 120rpx;
	border-radius: 60rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 16rpx;
	position: relative;
}

.pink-bg {
	background: rgba(255, 107, 129, 0.2);
}

.blue-bg {
	background: rgba(59, 130, 246, 0.2);
}

.green-bg {
	background: rgba(74, 222, 128, 0.2);
}

.icon-emoji {
	font-size: 56rpx;
}

.icon-plus {
	position: absolute;
	bottom: 8rpx;
	right: 8rpx;
	font-size: 24rpx;
	background: #3b82f6;
	color: #fff;
	width: 32rpx;
	height: 32rpx;
	border-radius: 16rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.icon-mascot {
	position: absolute;
	bottom: 0;
	right: -8rpx;
	font-size: 40rpx;
	background: rgba(255, 182, 193, 0.8);
	width: 60rpx;
	height: 60rpx;
	border-radius: 30rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.icon-label {
	font-size: 26rpx;
	color: #fff;
}

.message-list {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
}

.message-item {
	background: #1a1a1a;
	border-radius: 24rpx;
	padding: 32rpx;
	display: flex;
	align-items: center;
}

.item-icon {
	width: 88rpx;
	height: 88rpx;
	border-radius: 44rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 24rpx;
}

.orange-bg {
	background: rgba(251, 146, 60, 0.2);
}

.purple-bg {
	background: rgba(167, 139, 250, 0.2);
}

.purple-light-bg {
	background: rgba(192, 132, 252, 0.2);
}

.item-emoji {
	font-size: 44rpx;
}

.item-content {
	flex: 1;
}

.item-title {
	display: block;
	font-size: 30rpx;
	font-weight: 500;
	color: #fff;
	margin-bottom: 8rpx;
}

.item-desc {
	display: block;
	font-size: 26rpx;
	color: #888;
}

.item-arrow {
	font-size: 32rpx;
	color: #666;
}
</style>
