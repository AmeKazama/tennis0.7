<template>
    <view class="container">
        <view class="status-bar">
            <view class="status-indicator">
                <view class="status-dot" :class="statusClass"></view>
                <text class="status-text">{{ connectionStatus }}</text>
            </view>
            <view v-if="errorMessage" class="error-message">{{ errorMessage }}</view>
        </view>

        <!-- 关节角度 -->
        <view class="joints-section">
            <text class="section-title">关节角度</text>
            <view class="joints-grid">
                <view class="joint-card">
                    <text class="joint-label">左肘</text>
                    <text class="joint-value">{{ joints.left_elbow }}°</text>
                </view>
                <view class="joint-card">
                    <text class="joint-label">右肘</text>
                    <text class="joint-value">{{ joints.right_elbow }}°</text>
                </view>
                <view class="joint-card">
                    <text class="joint-label">左膝</text>
                    <text class="joint-value">{{ joints.left_knee }}°</text>
                </view>
                <view class="joint-card">
                    <text class="joint-label">右膝</text>
                    <text class="joint-value">{{ joints.right_knee }}°</text>
                </view>
            </view>
        </view>

        <!-- 模式切换：实时摄像头 / 视频分析 -->
        <view class="mode-tabs">
            <view class="tab" :class="{ active: activeTab === 'realtime' }" @click="switchTab('realtime')">
                <text class="tab-text">实时摄像头</text>
            </view>
            <view class="tab" :class="{ active: activeTab === 'video' }" @click="switchTab('video')">
                <text class="tab-text">视频分析</text>
            </view>
        </view>

        <!-- ====================== 实时摄像头模式 ====================== -->
        <view class="camera-section" v-if="activeTab === 'realtime'">
            <view class="camera-preview" v-if="cameraReady">
                <video 
                    id="videoRef" 
                    ref="videoRef" 
                    class="camera-video" 
                    autoplay 
                    playsinline
                    disable-pause="true"
                ></video>
                <view class="recording-indicator" v-if="isRecording">
                    <view class="recording-dot"></view>
                    <text class="recording-text">录制中...</text>
                </view>
            </view>
            <view class="camera-placeholder" v-else>
                <text class="placeholder-text">{{ cameraStatus }}</text>
            </view>
            
            <view class="camera-controls">
                <button class="camera-btn primary" @click="startCamera" :disabled="cameraReady">开启摄像头</button>
                <button class="camera-btn warning" @click="startRecording" :disabled="!cameraReady || isRecording">开始录制</button>
                <button class="camera-btn danger" @click="stopRecording" :disabled="!isRecording">停止录制</button>
            </view>
            
            <view class="video-preview" v-if="recordedVideoUrl">
                <text class="section-title">录制预览</text>
                <video :src="recordedVideoUrl" class="preview-video" controls></video>
                <view class="preview-controls">
                    <button class="preview-btn secondary" @click="reRecord">重新录制</button>
                    <button class="preview-btn primary" @click="submitRecording">提交评分</button>
                </view>
            </view>
        </view>

        <!-- ====================== 视频分析模式 ====================== -->
        <view class="camera-section" v-else>
            <view class="camera-preview" v-if="selectedVideoPath">
                <video :src="selectedVideoPath" class="camera-video" controls></video>
            </view>
            <view class="camera-placeholder" v-else>
                <text class="placeholder-text">{{ cameraStatusVideo }}</text>
            </view>

            <view class="preview-controls" v-if="selectedVideoPath">
                <button class="preview-btn secondary" @click="clearSelectedVideo" :disabled="analyzing">重新选择</button>
                <button class="preview-btn primary" @click="uploadSelectedVideo" :disabled="analyzing">提交评分</button>
            </view>

            <view class="camera-controls" v-else>
                <button class="camera-btn primary" @click="recordVideoWithCamera" :disabled="analyzing">
                    拍摄视频
                </button>
                <button class="camera-btn success" @click="chooseVideoFromAlbum" :disabled="analyzing">
                    从相册选择
                </button>
            </view>

            <view class="analysis-progress" v-if="analyzing">
                <text class="progress-text">正在上传并分析视频... {{ uploadProgress }}%</text>
                <view class="progress-track">
                    <view class="progress-fill" :style="{ width: uploadProgress + '%' }"></view>
                </view>
            </view>
        </view>

        <!-- AI 教练建议 -->
        <view class="advice-section">
            <view class="advice-bubble">
                <view class="coach-avatar-container">
                    <view class="coach-avatar fallback">
                        <text class="avatar-emoji">🎾</text>
                    </view>
                </view>
                <view class="advice-content">
                    <view class="advice-header">
                        <text class="coach-label">🎾 AI 教练</text>
                        <view class="header-right">
                            <text class="source-badge" :class="sourceClass">{{ sourceText }}</text>
                            <text v-if="tts" class="tts-icon">🔊</text>
                        </view>
                    </view>
                    <text class="advice-text">{{ displayedAdvice }}<text v-if="isTyping" class="cursor">|</text></text>
                </view>
            </view>
        </view>

        <!-- 视频分析报告 -->
        <view class="analysis-section" v-if="analysisSegments.length || analysisSummary || analysisError">
            <text class="section-title">视频分析报告</text>
            <view v-if="analysisError" class="error-message">{{ analysisError }}</view>

            <view class="summary-card" v-if="analysisSummary">
                <text class="summary-title">总结</text>
                <text class="summary-text">共识别 {{ analysisSummary.num_segments || 0 }} 个动作片段</text>
                <text class="summary-text">视频时长 {{ formatTime(analysisSummary.duration || 0) }}</text>
                <text class="summary-text">帧数 {{ analysisSummary.num_frames || 0 }}，FPS {{ formatNumber(analysisSummary.fps || 0) }}</text>
            </view>

            <view class="segment-card" v-for="segment in analysisSegments" :key="segment.segment_id">
                <view class="segment-header">
                    <text class="segment-title">片段 {{ segment.segment_id }}：{{ segment.shot_type_cn || segment.shot_type }}</text>
                    <text class="segment-time">{{ formatSegmentTime(segment) }}</text>
                </view>
                <text class="segment-line">评分：{{ segment.analysis.grade }}</text>
                <text class="segment-line">相似距离：{{ formatNumber(segment.analysis.distance) }}</text>
                <text class="segment-subtitle">主要问题：</text>
                <text class="issue-line" v-for="(issue, index) in segment.analysis.top_issues" :key="index">
                    - {{ issue.joint }}：你的 {{ formatNullableNumber(issue.user_angle) }}°，标准 {{ formatNullableNumber(issue.standard_angle) }}°，{{ issue.direction }} {{ formatNumber(Math.abs(issue.signed_error)) }}°
                </text>
                <text class="segment-subtitle">教练建议：</text>
                <text class="coach-advice">{{ segment.coach_advice }}</text>
            </view>
        </view>

        <!-- 测试控制 -->
        <view class="test-section">
            <text class="section-title">测试控制</text>
            <view class="test-buttons">
                <button class="test-btn primary" @click="sendNormalPose">发送正常姿势</button>
                <button class="test-btn warning" @click="sendAbnormalPose">发送异常姿势</button>
                <button class="test-btn" :class="autoSend ? 'active' : ''" @click="toggleAutoSend">
                    {{ autoSend ? '停止自动发送' : '开启自动发送' }}
                </button>
            </view>
        </view>
    </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';

// ===================== 【改成你电脑的局域网IP】 =====================
const API_BASE_URL = 'http://10.24.51.159:9000';
const WS_URL = 'ws://10.24.51.159:9000/ws/joints';
// ==================================================================

// http 变成 https
//const API_BASE_URL = 'https://10.24.51.159:9000';

// ws 变成 wss
//const WS_URL = 'wss://10.24.51.159:9000/ws/joints';

const RECONNECT_INTERVAL = 3000;
const TYPING_SPEED = 50;
const HEARTBEAT_INTERVAL = 10000;

let ws = null;
let socketTask = null;
let reconnectTimer = null;
let autoSendTimer = null;
let typingTimer = null;
let heartbeatTimer = null;

// 模式切换
const activeTab = ref('realtime');

// 关节数据
const joints = ref({
    left_elbow: 180,
    right_elbow: 180,
    left_knee: 180,
    right_knee: 180
});

// AI 建议
const fullAdvice = ref('等待连接...');
const displayedAdvice = ref('等待连接...');
const isTyping = ref(false);
const connectionStatus = ref('未连接');
const errorMessage = ref('');
const tts = ref(false);
const autoSend = ref(false);
const adviceSource = ref('初始');

// 实时摄像头
const videoRef = ref(null);
const cameraReady = ref(false);
const isRecording = ref(false);
const recordedVideoUrl = ref('');
const cameraStatus = ref('点击开启摄像头');

// 视频分析
const selectedVideoPath = ref('');
const cameraStatusVideo = ref('可从相册选择视频，或拍摄一段新视频');
const analyzing = ref(false);
const uploadProgress = ref(0);
const analysisSegments = ref([]);
const analysisSummary = ref(null);
const analysisError = ref('');

let audioPlayer = null;

// ===================== TTS 串行队列 =====================
let ttsQueue = [];
let ttsPlaying = false;

const playNextTTS = () => {
    if (ttsPlaying || ttsQueue.length === 0) return;
    ttsPlaying = true;
    const text = ttsQueue.shift();
    console.log("🔊 播放TTS：", text);

    uni.request({
        url: "http://10.24.51.159:9002/api/tts",
        method: "POST",
        header: { "Content-Type": "application/json" },
        data: { text },
        success: (res) => {
            try {
                const audioUrl = res.data.url;
                console.log("🎵 音频URL：", audioUrl);

                if (audioPlayer) {
                    audioPlayer.stop();
                    audioPlayer.destroy();
                    audioPlayer = null;
                }

                audioPlayer = uni.createInnerAudioContext();
                audioPlayer.src = audioUrl;
                audioPlayer.onPlay(() => console.log("✅ 语音开始播放"));
                audioPlayer.onEnded(() => {
                    console.log("✅ 语音播放完成，剩余队列：", ttsQueue.length);
                    ttsPlaying = false;
                    setTimeout(playNextTTS, 800);
                });
                audioPlayer.onError((err) => {
                    console.log("❌ 播放错误：", JSON.stringify(err));
                    ttsPlaying = false;
                    setTimeout(playNextTTS, 300);
                });
                audioPlayer.play();
            } catch (e) {
                console.log("❌ 音频处理失败", e);
                ttsPlaying = false;
                playNextTTS();
            }
        },
        fail: (err) => {
            console.log("❌ TTS请求失败：", err);
            ttsPlaying = false;
            setTimeout(playNextTTS, 500);
        }
    });
};

function speakText(text) {
    if (!text || text.trim() === "") return;
    text = text.replace(/^[,，\s]+/, "");
    ttsQueue.push(text);
    console.log("📥 入队TTS，当前队列长度：", ttsQueue.length);
    playNextTTS();
}

// 点击解锁声音（APP 可留空）
function enableVoice() {}

// ===================== 模式切换 =====================
const switchTab = (tab) => {
    activeTab.value = tab;
    stopAllMedia();
    resetAnalysis();
};

const stopAllMedia = () => {
    isRecording.value = false;
    recordedVideoUrl.value = '';
};

// ===================== 实时摄像头 =====================
const startCamera = async () => {
    cameraStatus.value = "启动中...";
    try {
        // #ifdef APP-PLUS
        const ctx = uni.createVideoContext('videoRef');
        ctx.startPreview({
            success: () => {
                cameraReady.value = true;
                cameraStatus.value = "摄像头已就绪";
            }
        });
        // #endif

        // #ifdef H5
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        videoRef.value.srcObject = stream;
        cameraReady.value = true;
        cameraStatus.value = "摄像头已就绪";
        // #endif
    } catch (e) {
        cameraStatus.value = "权限不足或摄像头异常";
    }
};

const startRecording = () => { isRecording.value = true; };
const stopRecording = () => { isRecording.value = false; };
const reRecord = () => { recordedVideoUrl.value = ''; };
const submitRecording = () => { uni.showToast({ title: "提交成功" }); };

// ===================== 视频分析工具 =====================
const formatNumber = (value) => Number.isFinite(+value) ? (+value).toFixed(2) : '0.00';
const formatNullableNumber = (value) => Number.isFinite(+value) ? (+value).toFixed(1) : '--';
const formatTime = (seconds) => {
    const total = Math.max(0, +seconds || 0);
    const m = Math.floor(total / 60);
    const s = (total % 60).toFixed(1).padStart(4, '0');
    return m > 0 ? `${m}:${s}` : `${s}s`;
};
const formatSegmentTime = (seg) => {
    if (Array.isArray(seg.time_range)) return `${formatTime(seg.time_range[0])} - ${formatTime(seg.time_range[1])}`;
    if (typeof seg.impact_time === 'number') return `击球点 ${formatTime(seg.impact_time)}`;
    return '';
};

// ===================== 视频分析 =====================
const resetAnalysis = () => {
    uploadProgress.value = 0;
    analysisSegments.value = [];
    analysisSummary.value = null;
    analysisError.value = '';
};

const chooseVideoFromAlbum = () => {
    uni.chooseVideo({
        sourceType: ['album'],
        compressed: false,
        success: (res) => {
            selectedVideoPath.value = res.tempFilePath;
            resetAnalysis();
            startTypingAnimation('视频已选择，准备上传分析');
        }
    });
};

const clearSelectedVideo = () => {
    selectedVideoPath.value = '';
    resetAnalysis();
};

const recordVideoWithCamera = () => {
    uni.chooseVideo({
        sourceType: ['camera'],
        compressed: false,
        maxDuration: 60,
        success: (res) => {
            selectedVideoPath.value = res.tempFilePath;
            resetAnalysis();
            startTypingAnimation('视频拍摄完成，准备上传分析');
        }
    });
};

const uploadSelectedVideo = () => {
    if (!selectedVideoPath.value) return uni.showToast({ title: '请先选择视频', icon: 'none' });
    analyzing.value = true;
    adviceSource.value = '视频分析';
    analysisSegments.value = [];
    analysisSummary.value = null;
    analysisError.value = '';
    uploadProgress.value = 0;
    // 清空TTS队列，避免和上次残留混在一起
    ttsQueue = [];
    ttsPlaying = false;
    startTypingAnimation('正在上传视频...');

    const task = uni.uploadFile({
        url: `${API_BASE_URL}/api/analyze_video_submit`,
        filePath: selectedVideoPath.value,
        name: 'file',
        timeout: 300000,
        success: (res) => {
            try {
                const { task_id } = JSON.parse(res.data);
                console.log("📋 任务ID：", task_id);
                startTypingAnimation('视频上传完成，正在逐段分析...');
                pollResults(task_id, 0);
            } catch(e) {
                analysisError.value = '提交失败';
                analyzing.value = false;
            }
        },
        fail: () => {
            analysisError.value = '上传失败';
            startTypingAnimation('视频上传失败');
            analyzing.value = false;
        }
    });

    task.onProgressUpdate((res) => {
        uploadProgress.value = Math.min(95, res.progress);
    });
};

let pollTimer = null;

const pollResults = (task_id, offset) => {
    uni.request({
        url: `${API_BASE_URL}/api/analyze_video_poll/${task_id}?offset=${offset}`,
        method: 'GET',
        success: (res) => {
            const { items, done, total } = res.data;

            for (const result of items) {
                if (result.type === 'segment') {
                    const seg = result.data;
                    analysisSegments.value.push(seg);

                    const advice = seg.coach_advice || '';
                    if (advice) {
                        // 显示当前这条建议
                        startTypingAnimation(`片段${seg.segment_id}（${seg.shot_type_cn}）：${advice}`);
                        // 入队串行播放
                        speakText(advice);
                    }
                } else if (result.type === 'summary') {
                    analysisSummary.value = result.data;
                } else if (result.type === 'error') {
                    analysisError.value = result.message;
                }
            }

            if (done) {
                analyzing.value = false;
                uploadProgress.value = 100;
                console.log("✅ 分析全部完成");
            } else {
                pollTimer = setTimeout(() => pollResults(task_id, total), 1500);
            }
        },
        fail: () => {
            pollTimer = setTimeout(() => pollResults(task_id, offset), 2000);
        }
    });
};

// ===================== 打字动画 =====================
const startTypingAnimation = (text) => {
    if (typingTimer) clearTimeout(typingTimer);
    displayedAdvice.value = '';
    isTyping.value = true;
    let i = 0;
    const run = () => {
        if (i < text.length) {
            displayedAdvice.value += text[i++];
            typingTimer = setTimeout(run, TYPING_SPEED);
        } else isTyping.value = false;
    };
    run();
};

// ===================== WebSocket =====================
const statusClass = computed(() => {
    switch (connectionStatus.value) {
        case '已连接': return 'connected';
        case '连接中': return 'connecting';
        default: return 'disconnected';
    }
});

const sourceText = computed(() => {
    const map = {doubao:'🤖 豆包', default:'📋 默认', timeout:'⏰ 超时', error:'❌ 错误', video:'视频分析'};
    return map[adviceSource.value] || '📌 初始';
});

const sourceClass = computed(() => adviceSource.value);

let nativeWS = null;
let isConnecting = false;

// 【APP / 浏览器 双兼容】稳定 WebSocket 连接
const connect = () => {
    // 防止重复连接
    if (socketTask) {
        try { socketTask.close() } catch {}
    }
    
    connectionStatus.value = '连接中'
    console.log("🔌 正在连接 WS：", WS_URL)

    // ✅ uni.connectSocket 全端兼容（APP / 浏览器 / 模拟器）
    socketTask = uni.connectSocket({
        url: WS_URL,
        success: () => console.log("✅ WS 发起成功")
    })

    // 连接成功
    uni.onSocketOpen(() => {
      connectionStatus.value = '已连接';
      console.log("✅ WS 已连接");
    
      // ✅ 这里就是你要的：欢迎语 + 开始训练
      speakText("欢迎使用网球AI教练，开始训练！");
    
      startTypingAnimation('网络已连接，可以开始检测姿势');
    });

    // 收到消息
    uni.onSocketMessage((res) => {
        try {
            const data = JSON.parse(res.data)
            if (data.left_elbow !== undefined) joints.value = data
            if (data.content) {
                startTypingAnimation(data.content)
                speakText(data.content) // 语音播报
            }
            if (data.source) adviceSource.value = data.source
        } catch (e) {}
    })

    // 错误
    uni.onSocketError((err) => {
        console.log("❌ WS 错误", err)
        connectionStatus.value = '连接错误'
    })

    // 断开重连
    uni.onSocketClose(() => {
        console.log("🔌 断开，2秒后重连")
        connectionStatus.value = '已断开'
        setTimeout(connect, 2000)
    })
}
// ===================== 测试数据 =====================
const sendTestData = (data) => {
    try { socketTask.send({ data: JSON.stringify(data) }) } catch {}
};
const sendNormalPose = () => sendTestData({ left_elbow:160, right_elbow:165, left_knee:120, right_knee:125 });
const sendAbnormalPose = () => sendTestData({ left_elbow:150, right_elbow:155, left_knee:72, right_knee:78 });
const toggleAutoSend = () => {
    if (autoSend.value) {
        clearInterval(autoSendTimer);
        autoSend.value = false;
    } else {
        autoSend.value = true;
        autoSendTimer = setInterval(sendAbnormalPose, 4000);
    }
};

onMounted(() => connect());
onUnmounted(() => {
    if (socketTask) try { socketTask.close() } catch {}
});
</script>

<style>
.container {
    min-height: 100vh;
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f0f23 100%);
    padding: 40rpx;
    display: flex;
    flex-direction: column;
}
.status-bar { margin-bottom: 30rpx; }
.status-indicator { display: flex; align-items: center; gap: 16rpx; }
.status-dot { width: 20rpx; height: 20rpx; border-radius: 50%; }
.status-dot.connected { background: #00ff88; }
.status-dot.connecting { background: #ffaa00; animation: pulse 1.5s infinite; }
.status-dot.disconnected { background: #ff4757; }
.status-text { color: #fff; font-size: 28rpx; font-weight: 500; }
.error-message { color: #ff4757; font-size: 24rpx; background: rgba(255,71,87,0.1); padding: 16rpx 24rpx; border-radius: 16rpx; margin-top: 10rpx; }

/* 模式切换 */
.mode-tabs {
    display: flex;
    background: rgba(255,255,255,0.08);
    border-radius: 20rpx;
    padding: 8rpx;
    margin-bottom: 30rpx;
    gap: 8rpx;
}
.tab {
    flex: 1;
    text-align: center;
    padding: 20rpx;
    border-radius: 16rpx;
    color: rgba(255,255,255,0.6);
    font-size: 28rpx;
}
.tab.active {
    background: #6366f1;
    color: #fff;
    font-weight: 600;
}

/* 关节 */
.joints-section { margin-bottom: 40rpx; }
.section-title { color: #fff; font-size: 32rpx; font-weight: 600; margin-bottom: 24rpx; }
.joints-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24rpx; }
.joint-card { background: rgba(255,255,255,0.08); border-radius: 32rpx; padding: 40rpx 20rpx; text-align: center; }
.joint-label { color: #8892b0; font-size: 26rpx; }
.joint-value { color: #00ff88; font-size: 52rpx; font-weight: 700; margin-top: 10rpx; }

/* 摄像头 */
.camera-section { margin-bottom: 40rpx; }
.camera-preview { position: relative; width: 100%; height: 500rpx; background: rgba(0,0,0,0.3); border-radius: 24rpx; overflow: hidden; margin-bottom: 24rpx; }
.camera-video { width: 100%; height: 100%; object-fit: cover; }
.recording-indicator { position: absolute; top: 20rpx; left: 20rpx; display: flex; align-items: center; gap: 12rpx; background: rgba(255,0,0,0.8); padding: 12rpx 20rpx; border-radius: 20rpx; }
.recording-dot { width: 16rpx; height: 16rpx; background: #fff; border-radius: 50%; animation: pulse 1s infinite; }
.recording-text { color: #fff; font-size: 24rpx; }
.camera-placeholder { width: 100%; height: 500rpx; background: rgba(255,255,255,0.05); border-radius: 24rpx; display: flex; align-items: center; justify-content: center; margin-bottom: 24rpx; border: 2rpx dashed rgba(255,255,255,0.2); }
.placeholder-text { color: rgba(255,255,255,0.6); font-size: 28rpx; text-align: center; padding: 0 30rpx; }

/* 按钮 */
.camera-controls, .preview-controls { display: flex; gap: 20rpx; margin-bottom: 20rpx; flex-wrap: wrap; }
.camera-btn, .preview-btn, .test-btn { flex: 1; min-width: 200rpx; padding: 24rpx; border-radius: 16rpx; font-size: 28rpx; color: #fff; border: none; }
.camera-btn.primary { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
.camera-btn.warning { background: linear-gradient(135deg, #f59e0b, #d97706); }
.camera-btn.danger { background: linear-gradient(135deg, #ef4444, #dc2626); }
.camera-btn.success { background: linear-gradient(135deg, #10b981, #059669); }
.preview-btn.secondary { background: rgba(255,255,255,0.1); }
.preview-btn.primary { background: linear-gradient(135deg, #10b981, #059669); }

/* 进度条 */
.analysis-progress { margin-top: 20rpx; }
.progress-text { color: #fff; font-size: 26rpx; margin-bottom: 10rpx; }
.progress-track { height: 14rpx; background: rgba(255,255,255,0.1); border-radius: 99rpx; }
.progress-fill { height: 100%; background: linear-gradient(135deg, #00ff88, #00d4ff); border-radius: 99rpx; }

/* 预览 */
.video-preview { background: rgba(255,255,255,0.05); border-radius: 24rpx; padding: 32rpx; margin-top: 20rpx; }
.preview-video { width: 100%; height: 400rpx; border-radius: 16rpx; background: #000; margin-bottom: 20rpx; }

/* AI 建议 */
.advice-section { margin-bottom: 40rpx; }
.advice-bubble { display: flex; gap: 24rpx; background: linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,212,255,0.15)); border-radius: 40rpx; padding: 40rpx; }
.coach-avatar-container { flex-shrink: 0; }
.coach-avatar { width: 120rpx; height: 120rpx; border: 4rpx solid #00ff88; background: rgba(0,255,136,0.1); display: flex; align-items: center; justify-content: center; border-radius: 50%; }
.avatar-emoji { font-size: 60rpx; }
.advice-content { flex: 1; display: flex; flex-direction: column; gap: 16rpx; }
.advice-header { display: flex; align-items: center; justify-content: space-between; }
.coach-label { color: #00ff88; font-size: 28rpx; font-weight: 600; }
.source-badge { font-size: 22rpx; padding: 8rpx 16rpx; border-radius: 16rpx; background: rgba(255,255,255,0.1); }
.source-badge.doubao { background: rgba(0,255,136,0.2); color: #00ff88; }
.advice-text { color: #fff; font-size: 32rpx; line-height: 1.6; }
.cursor { display: inline-block; width: 4rpx; height: 36rpx; background: #00ff88; animation: blink 0.8s infinite; margin-left: 4rpx; }

/* 分析报告 */
.analysis-section { margin-bottom: 40rpx; }
.summary-card, .segment-card { background: rgba(255,255,255,0.07); border-radius: 24rpx; padding: 32rpx; margin-bottom: 20rpx; }
.summary-title, .segment-title { color: #fff; font-size: 30rpx; font-weight: 600; margin-bottom: 16rpx; }
.summary-text, .segment-line, .issue-line { color: rgba(255,255,255,0.8); font-size: 26rpx; line-height: 1.6; margin-bottom: 8rpx; }
.segment-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16rpx; }
.segment-time { color: #00d4ff; font-size: 24rpx; }
.segment-subtitle { color: #00ff88; font-size: 26rpx; font-weight: 600; margin: 16rpx 0 8rpx; }
.coach-advice { color: #fff; font-size: 28rpx; line-height: 1.6; margin-top: 8rpx; }

/* 测试按钮 */
.test-section { margin-top: 20rpx; }
.test-buttons { display: flex; flex-direction: column; gap: 20rpx; }
.test-btn { background: rgba(255,255,255,0.1); }
.test-btn.primary { background: linear-gradient(135deg, #00ff88, #00d4ff); color: #000; font-weight: 600; }
.test-btn.warning { background: linear-gradient(135deg, #ffaa00, #ff6b35); color: #000; font-weight: 600; }
.test-btn.active { background: linear-gradient(135deg, #ff4757, #ff6b81); }

@keyframes pulse {
    0%,100%{opacity:1;}50%{opacity:0.4;}
}
@keyframes blink {
    0%,50%{opacity:1;}51%,100%{opacity:0;}
}
</style>