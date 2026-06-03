<template>
	<view class="publish-container">
		<!-- 顶部导航 -->
		<view class="publish-header">
			<text class="btn-cancel" @click="cancel">取消</text>
			<text class="header-title">发布动态</text>
			<text 
				class="btn-publish" 
				:class="{ active: canPublish }"
				@click="submit"
			>发布</text>
		</view>
		
		<!-- 内容输入 -->
		<view class="content-area">
			<textarea 
				v-model="content" 
				placeholder="分享你的网球时刻..."
				maxlength="500"
				class="content-input"
				@input="checkContent"
			></textarea>
			<text class="word-count">{{ content.length }}/500</text>
		</view>
		
		<!-- 图片/视频上传 -->
		<view class="media-section">
			<view class="section-title">添加图片/视频</view>
			<view class="media-grid">
				<view 
					v-for="(item, idx) in mediaList" 
					:key="idx"
					class="media-item"
				>
					<video 
						v-if="item.type === 'video'" 
						:src="item.url"
						class="media-preview"
						controls
					></video>
					<image 
						v-else 
						:src="item.url" 
						mode="aspectFill"
						class="media-preview"
						@click="previewImage(idx)"
					></image>
					<view class="media-delete" @click="deleteMedia(idx)">
						<text class="iconfont icon-close"></text>
					</view>
				</view>
				
				<!-- 添加按钮 -->
				<view 
					class="add-btn" 
					v-if="mediaList.length < 9"
					@click="showAddOptions"
				>
					<text class="iconfont icon-add"></text>
					<text class="add-text">添加</text>
				</view>
			</view>
		</view>
		
		<!-- 位置 -->
		<view class="location-section">
			<view class="section-item" @click="chooseLocation">
				<text class="iconfont icon-location"></text>
				<text class="item-label">{{ location || '添加位置' }}</text>
				<text class="iconfont icon-arrow"></text>
			</view>
		</view>
		
		<!-- 可见性 -->
		<view class="visibility-section">
			<view class="section-title">谁可以看</view>
			<view class="visibility-options">
				<view 
					class="visibility-item"
					:class="{ active: visibility === 'public' }"
					@click="setVisibility('public')"
				>
					<text class="iconfont icon-global"></text>
					<text>公开</text>
				</view>
				<view 
					class="visibility-item"
					:class="{ active: visibility === 'friends' }"
					@click="setVisibility('friends')"
				>
					<text class="iconfont icon-team"></text>
					<text>好友</text>
				</view>
				<view 
					class="visibility-item"
					:class="{ active: visibility === 'private' }"
					@click="setVisibility('private')"
				>
					<text class="iconfont icon-lock"></text>
					<text>私密</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
import { publishMoment } from '@/utils/moments-store/index.js'

export default {
	data() {
		return {
			content: '',
			mediaList: [],
			location: '',
			visibility: 'public',
			isSubmitting: false
		}
	},
	computed: {
		canPublish() {
			return this.content.trim().length > 0 || this.mediaList.length > 0
		}
	},
	methods: {
		checkContent() {
			// 内容检查
		},
		
		cancel() {
			if (this.content.trim() || this.mediaList.length > 0) {
				uni.showModal({
					title: '提示',
					content: '确定放弃发布吗？',
					success: (res) => {
						if (res.confirm) {
							uni.navigateBack()
						}
					}
				})
			} else {
				uni.navigateBack()
			}
		},
		
		async submit() {
			if (this.isSubmitting) return
			if (!this.canPublish) {
				uni.showToast({
					title: '请输入内容',
					icon: 'none'
				})
				return
			}
			
			this.isSubmitting = true
			uni.showLoading({ title: '发布中...' })
			
			try {
				const images = this.mediaList
					.filter(m => m.type === 'image')
					.map(m => m.url)
				
				const videoUrl = this.mediaList
					.find(m => m.type === 'video')?.url
				
				const res = await publishMoment({
					content: this.content,
					images,
					videoUrl,
					location: this.location,
					visibility: this.visibility
				})
				
				uni.hideLoading()
				uni.showToast({
					title: '发布成功',
					icon: 'success'
				})
				
				setTimeout(() => {
					uni.navigateBack()
				}, 1500)
			} catch (e) {
				uni.hideLoading()
				uni.showToast({
					title: e.message || '发布失败',
					icon: 'none'
				})
			} finally {
				this.isSubmitting = false
			}
		},
		
		showAddOptions() {
			uni.showActionSheet({
				itemList: ['添加图片', '添加视频'],
				success: (res) => {
					if (res.tapIndex === 0) {
						this.chooseImage()
					} else {
						this.chooseVideo()
					}
				}
			})
		},
		
		chooseImage() {
			const count = 9 - this.mediaList.length
			uni.chooseImage({
				count,
				success: (res) => {
					res.tempFiles.forEach(file => {
						if (this.mediaList.length < 9) {
							this.mediaList.push({
								type: 'image',
								url: file.path
							})
						}
					})
				}
			})
		},
		
		chooseVideo() {
			uni.chooseVideo({
				sourceType: ['album', 'camera'],
				maxDuration: 60,
				camera: 'back',
				success: (res) => {
					if (this.mediaList.length < 9) {
						this.mediaList.push({
							type: 'video',
							url: res.tempFilePath
						})
					}
				}
			})
		},
		
		deleteMedia(idx) {
			this.mediaList.splice(idx, 1)
		},
		
		previewImage(idx) {
			const urls = this.mediaList
				.filter(m => m.type === 'image')
				.map(m => m.url)
			uni.previewImage({
				urls,
				current: idx
			})
		},
		
		chooseLocation() {
			uni.chooseLocation({
				success: (res) => {
					this.location = res.name || res.address
				}
			})
		},
		
		setVisibility(type) {
			this.visibility = type
		}
	}
}
</script>

<style scoped>
.publish-container {
	min-height: 100vh;
	background: #f5f5f5;
}

.publish-header {
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

.btn-cancel {
	font-size: 28rpx;
	color: #666;
}

.header-title {
	font-size: 32rpx;
	font-weight: 600;
	color: #333;
}

.btn-publish {
	font-size: 28rpx;
	color: #999;
	font-weight: 600;
}

.btn-publish.active {
	color: #07c160;
}

.content-area {
	padding: 108rpx 30rpx 30rpx;
	background: #fff;
	position: relative;
}

.content-input {
	width: 100%;
	min-height: 300rpx;
	font-size: 30rpx;
	line-height: 1.6;
	color: #333;
}

.word-count {
	position: absolute;
	right: 40rpx;
	bottom: 40rpx;
	font-size: 24rpx;
	color: #999;
}

.media-section {
	background: #fff;
	padding: 30rpx;
	margin-top: 16rpx;
}

.section-title {
	font-size: 28rpx;
	color: #333;
	font-weight: 600;
	margin-bottom: 24rpx;
}

.media-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 16rpx;
}

.media-item {
	position: relative;
	aspect-ratio: 1;
	border-radius: 8rpx;
	overflow: hidden;
}

.media-preview {
	width: 100%;
	height: 100%;
}

.media-delete {
	position: absolute;
	top: 8rpx;
	right: 8rpx;
	width: 40rpx;
	height: 40rpx;
	background: rgba(0, 0, 0, 0.5);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
}

.media-delete .iconfont {
	color: #fff;
	font-size: 24rpx;
}

.add-btn {
	aspect-ratio: 1;
	background: #f5f5f5;
	border-radius: 8rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	border: 2rpx dashed #ddd;
}

.add-btn .iconfont {
	font-size: 60rpx;
	color: #999;
	margin-bottom: 8rpx;
}

.add-text {
	font-size: 24rpx;
	color: #999;
}

.location-section {
	background: #fff;
	margin-top: 16rpx;
}

.section-item {
	display: flex;
	align-items: center;
	padding: 30rpx;
	background: #fff;
}

.section-item .iconfont {
	font-size: 36rpx;
	color: #666;
	margin-right: 16rpx;
}

.item-label {
	flex: 1;
	font-size: 28rpx;
	color: #333;
}

.visibility-section {
	background: #fff;
	margin-top: 16rpx;
	padding: 30rpx;
}

.visibility-options {
	display: flex;
	gap: 30rpx;
}

.visibility-item {
	flex: 1;
	height: 80rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #f5f5f5;
	border-radius: 8rpx;
	border: 2rpx solid transparent;
}

.visibility-item.active {
	background: #e8f8ee;
	border-color: #07c160;
}

.visibility-item .iconfont {
	font-size: 32rpx;
	color: #666;
	margin-right: 8rpx;
}

.visibility-item.active .iconfont {
	color: #07c160;
}

.visibility-item text:last-child {
	font-size: 26rpx;
	color: #666;
}

.visibility-item.active text:last-child {
	color: #07c160;
}
</style>
