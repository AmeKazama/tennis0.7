<template>
	<view class="container">
		<view class="navbar">
			<text @tap="goBack">← 返回</text>
		</view>
		<view class="title">语音转文字</view>
		<view class="record-btn" @tap="toggleRecord">
			<text class="mic">🎤</text>
			<text class="tip">{{ isRecording ? '停止录音' : '点击录音' }}</text>
		</view>
		<view class="result" v-if="resultText">
			{{ resultText }}
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			isRecording: false,
			resultText: "",
			recorder: null
		};
	},
	onLoad() {
		console.log("✅ 日记页面加载完成");
		this.recorder = uni.getRecorderManager();
		this.recorder.onStop((res) => {
			console.log("✅ 录音结束，路径:", res.tempFilePath);
			this.uploadToServer(res.tempFilePath);
		});
		this.recorder.onError((err) => {
			console.log("❌ 录音错误:", err);
			uni.showToast({title:"录音失败",icon:"none"});
			this.isRecording = false;
		});
	},
	methods: {
		goBack() {
			uni.navigateBack();
		},
		toggleRecord() {
			if (this.isRecording) {
				this.recorder.stop();
				this.isRecording = false;
			} else {
				this.isRecording = true;
				uni.showToast({title:"录音中...",icon:"none"});
				// 适配安卓5.1 + 阿里云标准 wav 16000
				this.recorder.start({
					sampleRate: 16000,
					format: "wav",
					duration: 60000
				});
			}
		},
		uploadToServer(filePath) {
			uni.showLoading({title:"识别中..."});
			uni.uploadFile({
				url: "http://192.168.1.53:9002/api/ali_asr",
				filePath: filePath,
				name: "audio",
				success: (res) => {
					uni.hideLoading();
					console.log("✅ 上传返回原始数据:", res.data);
					try {
						let data = JSON.parse(res.data);
						if(data.result){
							this.resultText = data.result; 
						}else{
							this.resultText = "识别无结果";
						}
					} catch (e) {
						console.log("❌ 解析失败:", e);
						this.resultText = "解析失败";
					}
				},
				fail: (err) => {
					uni.hideLoading();
					console.log("❌ 上传请求失败:", err);
					this.resultText = "网络请求失败";
				}
			});
		}
	}
};
</script>

<style scoped>
.container {
	background: #0c131f;
	padding: 40rpx;
	color: #fff;
	min-height: 100vh;
}
.navbar {
	font-size: 32rpx;
	margin-bottom: 40rpx;
}
.title {
	font-size: 36rpx;
	text-align: center;
	margin-bottom: 60rpx;
}
.record-btn {
	width: 280rpx;
	height: 280rpx;
	background: #007aff;
	border-radius: 50%;
	margin: 0 auto;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
}
.mic {
	font-size: 60rpx;
	margin-bottom: 10rpx;
}
.tip {
	font-size: 24rpx;
	color: #fff;
}
.result {
	margin-top: 60rpx;
	font-size: 32rpx;
	text-align: center;
}
</style>
