<template>
    <view class="container">
        <!-- 自定义导航栏 -->
        <view class="navbar">
            <view class="back-btn" @tap="goBack">
                <text class="back-icon">←</text>
            </view>
            <text class="nav-title">AI网球教练实时监控</text>
            <view class="nav-spacer"></view>
        </view>
        
        <view class="status-bar">
            <view class="status-indicator">
                <view class="status-dot" :class="statusClass"></view>
                <text class="status-text">{{ connectionStatus }}</text>
            </view>
            <view v-if="errorMessage" class="error-message">{{ errorMessage }}</view>
        </view>

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

        <view class="mode-tabs" v-if="videoSource === 'all'">
            <view class="tab" :class="{ active: activeTab === 'realtime' }" @tap="switchTab('realtime')">
                <text class="tab-text">实时摄像头</text>
            </view>
            <view class="tab" :class="{ active: activeTab === 'video' }" @tap="switchTab('video')">
                <text class="tab-text">视频分析</text>
            </view>
        </view>

        <!-- 摄像头预览区域 -->
        <view class="camera-section" v-if="activeTab === 'realtime'">
            <text class="section-title">摄像头预览</text>
            <view class="camera-preview" v-if="cameraReady">
                <video ref="videoRef" class="camera-video" autoplay playsinline></video>
                <view class="recording-indicator" v-if="isRecording">
                    <view class="recording-dot"></view>
                    <text class="recording-text">录制中...</text>
                </view>
            </view>
            <view class="camera-placeholder" v-else>
                <text class="placeholder-text">{{ cameraStatus }}</text>
            </view>
            
            <view class="camera-controls">
                <button class="camera-btn primary" @click="startCamera" :disabled="cameraReady">
                    开启摄像头
                </button>
                <button class="camera-btn warning" @click="startRecording" :disabled="!cameraReady || isRecording">
                    开始录制
                </button>
                <button class="camera-btn danger" @click="stopRecording" :disabled="!isRecording">
                    停止录制
                </button>
            </view>
            
            <!-- 录制视频预览 -->
            <view class="video-preview" v-if="recordedVideoUrl">
                <text class="section-title">录制预览</text>
                <video :src="recordedVideoUrl" class="preview-video" controls></video>
                <view class="preview-controls">
                    <button class="preview-btn secondary" @click="reRecord">重新录制</button>
                    <button class="preview-btn primary" @click="analyzeRecordedVideo" :disabled="analyzing">开始分析</button>
                </view>
            </view>
        </view>

        <view class="camera-section" v-else>
            <text class="section-title">{{ videoSourceTitle }}</text>
            <view class="camera-preview" v-if="selectedVideoPath">
                <video :src="selectedVideoPath" class="camera-video" controls></video>
            </view>
            <view class="camera-placeholder" v-else>
                <text class="placeholder-text">{{ cameraStatusVideo }}</text>
            </view>

            <view class="preview-controls" v-if="selectedVideoPath">
                <button class="preview-btn secondary" @tap="clearSelectedVideo" :disabled="analyzing">重新选择</button>
                <button class="preview-btn primary" @tap="uploadSelectedVideo" :disabled="analyzing">开始分析</button>
            </view>

            <view class="camera-controls" v-else-if="videoSource === 'album'">
                <button class="camera-btn success" @tap="chooseVideoFromAlbum" :disabled="analyzing">
                    打开相册
                </button>
            </view>

            <view class="camera-controls" v-else-if="videoSource === 'all'">
                <button class="camera-btn primary" @tap="recordVideoWithCamera" :disabled="analyzing">
                    拍摄视频
                </button>
                <button class="camera-btn success" @tap="chooseVideoFromAlbum" :disabled="analyzing">
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

        <view class="advice-section">
            <view class="advice-bubble">
                <view class="coach-avatar-container">
                    <view class="coach-avatar" v-if="!avatarError">
                        <image class="coach-img" src="/static/coach.png" mode="aspectFill" @error="onAvatarError"></image>
                    </view>
                    <view class="coach-avatar fallback" v-else>
                        <text class="avatar-emoji">🎾</text>
                    </view>
                </view>
                <view class="advice-content">
                    <view class="advice-header">
                        <text class="coach-label">🎾 AI 教练</text>
                        <view class="header-right">
                            <text class="source-badge" :class="sourceClass">
                                {{ sourceText }}
                            </text>
                            <text v-if="tts" class="tts-icon">🔊</text>
                        </view>
                    </view>
                    <text class="advice-text">{{ displayedAdvice }}<text v-if="isTyping" class="cursor">|</text></text>
                </view>
            </view>
        </view>

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
                <text class="segment-line">评分：{{ segment.analysis && segment.analysis.grade ? segment.analysis.grade : '--' }}</text>
                <text class="segment-line">相似距离：{{ formatNumber(segment.analysis && segment.analysis.distance) }}</text>
                <text class="segment-subtitle">主要问题：</text>
                <text class="issue-line" v-for="(issue, index) in getSegmentIssues(segment)" :key="index">
                    - {{ issue.joint }}：你的 {{ formatNullableNumber(issue.user_angle) }}°，标准 {{ formatNullableNumber(issue.standard_angle) }}°，{{ issue.direction }} {{ formatNumber(Math.abs(issue.signed_error)) }}°
                </text>
                <text class="segment-subtitle">教练建议：</text>
                <text class="coach-advice">{{ segment.coach_advice || '暂无建议' }}</text>
            </view>
        </view>

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
import { onLoad } from '@dcloudio/uni-app';

const goBack = () => {
    uni.navigateBack();
};

const WS_URL = 'ws://192.168.1.53:9000/ws/joints';
const API_BASE_URL = 'http://192.168.1.53:9000';
const TTS_BASE_URL = API_BASE_URL.replace(':9000', ':9002');
const RECONNECT_INTERVAL = 5000;
const TYPING_SPEED = 50;
const HEARTBEAT_INTERVAL = 10000; // 心跳间隔10秒

let ws = null;
let reconnectTimer = null;
let autoSendTimer = null;
let typingTimer = null;
let heartbeatTimer = null;
let pollTimer = null;

const activeTab = ref('realtime');

const joints = ref({
    left_elbow: 180,
    right_elbow: 180,
    left_knee: 180,
    right_knee: 180
});

const fullAdvice = ref('等待连接...');
const displayedAdvice = ref('等待连接...');
const isTyping = ref(false);
const connectionStatus = ref('未连接');
const errorMessage = ref('');
const tts = ref(false);
const autoSend = ref(false);
const adviceSource = ref('初始');
const avatarError = ref(false);

const selectedVideoPath = ref('');
const cameraStatusVideo = ref('可从相册选择视频，或拍摄一段新视频');
const videoSource = ref('all');
const analyzing = ref(false);
const uploadProgress = ref(0);
const analysisSegments = ref([]);
const analysisSummary = ref(null);
const analysisError = ref('');
let audioPlayer = null;
let ttsQueue = [];
let ttsPlaying = false;

// 摄像头相关状态
const videoRef = ref(null);
const cameraReady = ref(false);
const isRecording = ref(false);
const recordedVideoUrl = ref('');
const cameraStatus = ref('点击开启摄像头');
let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];
let recordedVideoBlob = null;

const stopTTS = () => {
    ttsQueue = [];
    ttsPlaying = false;
    if (audioPlayer) {
        audioPlayer.stop();
        audioPlayer.destroy();
        audioPlayer = null;
    }
    tts.value = false;
};

const playNextTTS = () => {
    if (ttsPlaying || ttsQueue.length === 0) return;
    const text = ttsQueue.shift();
    if (!text) return;

    ttsPlaying = true;
    tts.value = true;
    uni.request({
        url: `${TTS_BASE_URL}/api/tts`,
        method: 'POST',
        header: { 'Content-Type': 'application/json' },
        data: { text },
        success: (res) => {
            const audioUrl = res.data && res.data.url;
            if (!audioUrl) {
                ttsPlaying = false;
                tts.value = false;
                setTimeout(playNextTTS, 300);
                return;
            }

            if (audioPlayer) {
                audioPlayer.stop();
                audioPlayer.destroy();
                audioPlayer = null;
            }

            audioPlayer = uni.createInnerAudioContext();
            audioPlayer.src = audioUrl;
            audioPlayer.onEnded(() => {
                ttsPlaying = false;
                tts.value = false;
                setTimeout(playNextTTS, 500);
            });
            audioPlayer.onError(() => {
                ttsPlaying = false;
                tts.value = false;
                setTimeout(playNextTTS, 300);
            });
            audioPlayer.play();
        },
        fail: () => {
            ttsPlaying = false;
            tts.value = false;
            setTimeout(playNextTTS, 500);
        }
    });
};

const speakText = (text) => {
    const cleanText = String(text || '').trim();
    if (!cleanText) return;
    ttsQueue.push(cleanText);
    playNextTTS();
};

const switchTab = (tab) => {
    activeTab.value = tab;
    resetAnalysis();
    if (tab === 'video') {
        cleanupCamera();
    } else {
        clearSelectedVideo(false);
    }
};

// 摄像头功能方法
const startCamera = async () => {
    try {
        cameraStatus.value = '正在请求摄像头权限...';
        
        // 检查浏览器支持
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('您的浏览器不支持摄像头功能');
        }
        
        // 请求摄像头权限
        mediaStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'environment'
            },
            audio: true
        });
        
        // 设置视频源
        if (videoRef.value) {
            videoRef.value.srcObject = mediaStream;
            videoRef.value.onloadedmetadata = () => {
                cameraReady.value = true;
                cameraStatus.value = '摄像头已就绪';
            };
        }
        
    } catch (error) {
        console.error('摄像头启动失败:', error);
        
        if (error.name === 'NotAllowedError') {
            cameraStatus.value = '摄像头权限被拒绝，请在浏览器设置中允许摄像头访问';
        } else if (error.name === 'NotFoundError') {
            cameraStatus.value = '未找到摄像头设备';
        } else if (error.name === 'NotSupportedError') {
            cameraStatus.value = '浏览器不支持摄像头功能';
        } else {
            cameraStatus.value = `摄像头启动失败: ${error.message}`;
        }
        
        // 清理资源
        if (mediaStream) {
            mediaStream.getTracks().forEach(track => track.stop());
            mediaStream = null;
        }
    }
};

const startRecording = () => {
    if (!mediaStream || !videoRef.value) {
        cameraStatus.value = '请先开启摄像头';
        return;
    }
    
    try {
        recordedChunks = [];
        
        // 检查 MediaRecorder 支持
        if (!window.MediaRecorder) {
            throw new Error('您的浏览器不支持视频录制功能');
        }
        
        // 创建 MediaRecorder
        mediaRecorder = new MediaRecorder(mediaStream, {
            mimeType: 'video/webm;codecs=vp9,opus',
            videoBitsPerSecond: 2500000 // 2.5 Mbps
        });
        
        // 录制事件处理
        mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            recordedVideoBlob = blob;
            recordedVideoUrl.value = URL.createObjectURL(blob);
            isRecording.value = false;
        };
        
        // 开始录制
        mediaRecorder.start(1000); // 每1秒收集一次数据
        isRecording.value = true;
        cameraStatus.value = '录制中...';
        
    } catch (error) {
        console.error('录制启动失败:', error);
        cameraStatus.value = `录制启动失败: ${error.message}`;
    }
};

const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        cameraStatus.value = '录制已完成';
    }
};

const reRecord = () => {
    // 清理之前的录制
    if (recordedVideoUrl.value) {
        URL.revokeObjectURL(recordedVideoUrl.value);
        recordedVideoUrl.value = '';
    }
    recordedChunks = [];
    recordedVideoBlob = null;
    cameraStatus.value = '摄像头已就绪';
};

const analyzeRecordedVideo = async () => {
    if (!recordedVideoBlob) {
        cameraStatus.value = '请先录制视频';
        return;
    }

    analyzing.value = true;
    adviceSource.value = '视频分析';
    analysisSegments.value = [];
    analysisSummary.value = null;
    analysisError.value = '';
    uploadProgress.value = 0;
    stopTTS();
    cameraStatus.value = '正在上传录制视频...';
    startTypingAnimation('正在上传录制视频...');

    try {
        const formData = new FormData();
        formData.append('file', recordedVideoBlob, `recording_${Date.now()}.webm`);
        const response = await fetch(`${API_BASE_URL}/api/analyze_video_submit`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            throw new Error(`上传失败：${response.status}`);
        }
        const { task_id } = await response.json();
        uploadProgress.value = 95;
        cameraStatus.value = '上传完成，正在分析...';
        startTypingAnimation('视频上传完成，正在逐段分析...');
        pollResults(task_id, 0);
    } catch (error) {
        analysisError.value = error.message || '上传失败';
        cameraStatus.value = '上传失败，请重试';
        startTypingAnimation('录制视频上传失败');
        analyzing.value = false;
    }
};

const formatNumber = (value) => Number.isFinite(+value) ? (+value).toFixed(2) : '0.00';
const formatNullableNumber = (value) => Number.isFinite(+value) ? (+value).toFixed(1) : '--';
const formatTime = (seconds) => {
    const total = Math.max(0, +seconds || 0);
    const minutes = Math.floor(total / 60);
    const rest = (total % 60).toFixed(1).padStart(4, '0');
    return minutes > 0 ? `${minutes}:${rest}` : `${rest}s`;
};
const formatSegmentTime = (segment) => {
    if (Array.isArray(segment.time_range)) {
        return `${formatTime(segment.time_range[0])} - ${formatTime(segment.time_range[1])}`;
    }
    if (typeof segment.impact_time === 'number') {
        return `击球点 ${formatTime(segment.impact_time)}`;
    }
    return '';
};
const getSegmentIssues = (segment) => {
    return (segment.analysis && Array.isArray(segment.analysis.top_issues)) ? segment.analysis.top_issues : [];
};

const resetAnalysis = () => {
    uploadProgress.value = 0;
    analysisSegments.value = [];
    analysisSummary.value = null;
    analysisError.value = '';
    stopTTS();
    if (pollTimer) {
        clearTimeout(pollTimer);
        pollTimer = null;
    }
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

const clearSelectedVideo = (resetMessage = true) => {
    selectedVideoPath.value = '';
    resetAnalysis();
    if (resetMessage) {
        cameraStatusVideo.value = '可从相册选择视频，或拍摄一段新视频';
    }
};

const uploadSelectedVideo = () => {
    if (!selectedVideoPath.value) {
        uni.showToast({ title: '请先选择视频', icon: 'none' });
        return;
    }

    analyzing.value = true;
    adviceSource.value = '视频分析';
    analysisSegments.value = [];
    analysisSummary.value = null;
    analysisError.value = '';
    uploadProgress.value = 0;
    stopTTS();
    startTypingAnimation('正在上传视频...');

    const task = uni.uploadFile({
        url: `${API_BASE_URL}/api/analyze_video_submit`,
        filePath: selectedVideoPath.value,
        name: 'file',
        timeout: 300000,
        success: (res) => {
            try {
                const { task_id } = JSON.parse(res.data);
                startTypingAnimation('视频上传完成，正在逐段分析...');
                pollResults(task_id, 0);
            } catch (e) {
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

    if (task && task.onProgressUpdate) {
        task.onProgressUpdate((res) => {
            uploadProgress.value = Math.min(95, res.progress);
        });
    }
};

const pollResults = (taskId, offset) => {
    uni.request({
        url: `${API_BASE_URL}/api/analyze_video_poll/${taskId}?offset=${offset}`,
        method: 'GET',
        success: (res) => {
            const { items = [], done = false, total = offset } = res.data || {};

            for (const result of items) {
                if (result.type === 'segment') {
                    const segment = result.data || {};
                    analysisSegments.value.push(segment);
                    if (segment.coach_advice) {
                        startTypingAnimation(`片段${segment.segment_id || ''}（${segment.shot_type_cn || segment.shot_type || '动作'}）：${segment.coach_advice}`);
                        speakText(segment.coach_advice);
                    }
                } else if (result.type === 'summary') {
                    analysisSummary.value = result.data;
                } else if (result.type === 'error') {
                    analysisError.value = result.message || '分析失败';
                }
            }

            if (done) {
                analyzing.value = false;
                uploadProgress.value = 100;
                startTypingAnimation('视频分析完成');
            } else {
                pollTimer = setTimeout(() => pollResults(taskId, total), 1500);
            }
        },
        fail: () => {
            pollTimer = setTimeout(() => pollResults(taskId, offset), 2000);
        }
    });
};

// 页面卸载时清理资源
const cleanupCamera = () => {
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    
    if (recordedVideoUrl.value) {
        URL.revokeObjectURL(recordedVideoUrl.value);
    }
    
    cameraReady.value = false;
    isRecording.value = false;
};

// 页面加载时自动开启摄像头
onMounted(() => {
    // 可以在这里添加自动开启摄像头的逻辑
    // startCamera(); // 取消注释以自动开启摄像头
});

// 页面卸载时清理资源
onUnmounted(() => {
    cleanupCamera();
});

const statusClass = computed(() => {
    switch (connectionStatus.value) {
        case '已连接':
            return 'connected';
        case '连接中':
            return 'connecting';
        default:
            return 'disconnected';
    }
});

const videoSourceTitle = computed(() => {
    if (videoSource.value === 'camera') return '拍摄视频分析';
    if (videoSource.value === 'album') return '相册视频分析';
    return '视频分析';
});

const sourceText = computed(() => {
    switch (adviceSource.value) {
        case '视频分析':
            return '视频分析';
        case '豆包':
            return '🤖 豆包';
        case '默认':
            return '📋 默认';
        case '超时':
            return '⏰ 超时';
        case '错误':
            return '❌ 错误';
        default:
            return '📌 初始';
    }
});

const sourceClass = computed(() => {
    switch (adviceSource.value) {
        case '视频分析':
            return 'video';
        case '豆包':
            return 'doubao';
        case '默认':
            return 'default';
        case '超时':
            return 'timeout';
        case '错误':
            return 'error';
        default:
            return 'initial';
    }
});

const startTypingAnimation = (text) => {
    if (typingTimer) {
        clearTimeout(typingTimer);
        typingTimer = null;
    }
    
    fullAdvice.value = text;
    displayedAdvice.value = '';
    isTyping.value = true;
    let index = 0;
    
    const typeChar = () => {
        if (index < text.length) {
            displayedAdvice.value = text.substring(0, index + 1);
            index++;
            typingTimer = setTimeout(typeChar, TYPING_SPEED);
        } else {
            isTyping.value = false;
            typingTimer = null;
        }
    };
    
    typeChar();
};

const stopTypingAnimation = () => {
    if (typingTimer) {
        clearTimeout(typingTimer);
        typingTimer = null;
    }
    isTyping.value = false;
};

const onAvatarError = () => {
    console.log('⚠️ 教练头像加载失败，使用备用头像');
    avatarError.value = true;
};

const connect = () => {
    connectionStatus.value = '连接中';
    errorMessage.value = '';

    try {
        ws = uni.connectSocket({
            url: WS_URL,
            success: () => {
                console.log('WebSocket 连接请求已发送');
            },
            fail: (err) => {
                console.error('WebSocket 连接失败:', err);
                connectionStatus.value = '连接失败';
                errorMessage.value = '连接失败，请检查服务器是否启动';
                scheduleReconnect();
            }
        });

        ws.onOpen(() => {
            console.log('✅ WebSocket 已连接');
            connectionStatus.value = '已连接';
            errorMessage.value = '';
            startTypingAnimation('连接成功，等待数据...');
            
            // 【关键】连接成功后立即发送一组初始数据，避免被底层认为空闲而断开
            const initData = {
                left_elbow: 160,
                right_elbow: 165,
                left_knee: 120,
                right_knee: 125
            };
            ws.send({
                data: JSON.stringify(initData),
                success: () => console.log('📤 初始数据发送成功'),
                fail: (err) => console.error('初始数据发送失败', err)
            });
            
            // 启动心跳：每10秒发送一个ping，保持连接活跃
            if (heartbeatTimer) clearInterval(heartbeatTimer);
            heartbeatTimer = setInterval(() => {
                if (ws && ws.readyState === 1) { // 1 = WebSocket.OPEN
                    ws.send({
                        data: JSON.stringify({ type: 'ping' }),
                        success: () => console.log('💓 心跳发送'),
                        fail: (err) => console.error('心跳发送失败', err)
                    });
                }
            }, HEARTBEAT_INTERVAL);
        });

        ws.onMessage((res) => {
            try {
                const data = JSON.parse(res.data);
                console.log('📦 收到数据:', data);

                if (data.left_elbow !== undefined) {
                    joints.value = {
                        left_elbow: data.left_elbow,
                        right_elbow: data.right_elbow,
                        left_knee: data.left_knee,
                        right_knee: data.right_knee
                    };
                }

                if (data.content) {
                    startTypingAnimation(data.content);
                    if (data.tts === true) {
                        speakText(data.content);
                    }
                }

                if (data.tts !== undefined) {
                    tts.value = data.tts;
                }

                if (data.source) {
                    adviceSource.value = data.source;
                    console.log('📍 建议来源:', data.source);
                }
            } catch (e) {
                console.error('解析数据失败:', e);
            }
        });

        ws.onClose((res) => {
            console.log('WebSocket 已关闭:', res.code, res.reason);
            if (heartbeatTimer) {
                clearInterval(heartbeatTimer);
                heartbeatTimer = null;
            }
            connectionStatus.value = '已断开';
            scheduleReconnect();
        });

        ws.onError((err) => {
            console.error('WebSocket 错误:', err);
            connectionStatus.value = '连接错误';
            errorMessage.value = '连接出错，请稍后重试';
            scheduleReconnect();
        });
    } catch (e) {
        console.error('WebSocket 初始化失败:', e);
        connectionStatus.value = '连接失败';
        errorMessage.value = '初始化失败';
        scheduleReconnect();
    }
};

const scheduleReconnect = () => {
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
    }
    reconnectTimer = setTimeout(() => {
        console.log('🔄 尝试重连...');
        connect();
    }, RECONNECT_INTERVAL);
};

const closeConnection = () => {
    stopTypingAnimation();
    if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
    }
    if (autoSendTimer) {
        clearInterval(autoSendTimer);
        autoSendTimer = null;
        autoSend.value = false;
    }
    if (heartbeatTimer) {
        clearInterval(heartbeatTimer);
        heartbeatTimer = null;
    }
    if (ws) {
        ws.close();
        ws = null;
    }
};

const sendTestData = (data) => {
    // 检查 WebSocket 状态：readyState === 1 表示 OPEN
    if (!ws || ws.readyState !== 1) {
        uni.showToast({
            title: 'WebSocket 未连接',
            icon: 'none'
        });
        console.warn('发送失败：WebSocket 未处于 OPEN 状态', ws ? ws.readyState : 'null');
        return;
    }
    try {
        ws.send({
            data: JSON.stringify(data),
            success: () => {
                console.log('📤 发送数据成功:', data);
                // 可选：更新界面显示的关节角度
                joints.value = {
                    left_elbow: data.left_elbow,
                    right_elbow: data.right_elbow,
                    left_knee: data.left_knee,
                    right_knee: data.right_knee
                };
            },
            fail: (err) => {
                console.error('发送数据失败:', err);
            }
        });
    } catch (e) {
        console.error('发送数据异常:', e);
    }
};

const sendNormalPose = () => {
    const random1 = Math.floor(Math.random() * 10) - 5;
    const random2 = Math.floor(Math.random() * 10) - 5;
    const random3 = Math.floor(Math.random() * 10) - 5;
    const random4 = Math.floor(Math.random() * 10) - 5;
    sendTestData({
        left_elbow: 160 + random1,
        right_elbow: 165 + random2,
        left_knee: 120 + random3,
        right_knee: 125 + random4
    });
    uni.showToast({
        title: '已发送正常姿势',
        icon: 'success'
    });
};

const sendAbnormalPose = () => {
    const random1 = Math.floor(Math.random() * 10) - 5;
    const random2 = Math.floor(Math.random() * 10) - 5;
    const random3 = Math.floor(Math.random() * 15) - 7;
    const random4 = Math.floor(Math.random() * 15) - 7;
    sendTestData({
        left_elbow: 150 + random1,
        right_elbow: 155 + random2,
        left_knee: 75 + random3,
        right_knee: 80 + random4
    });
    uni.showToast({
        title: '已发送异常姿势',
        icon: 'success'
    });
};

const toggleAutoSend = () => {
    if (autoSend.value) {
        if (autoSendTimer) {
            clearInterval(autoSendTimer);
            autoSendTimer = null;
        }
        autoSend.value = false;
        uni.showToast({
            title: '已停止自动发送',
            icon: 'none'
        });
    } else {
        if (!ws || ws.readyState !== 1) {
            uni.showToast({
                title: 'WebSocket 未连接',
                icon: 'none'
            });
            return;
        }
        autoSend.value = true;
        let count = 0;
        autoSendTimer = setInterval(() => {
            count++;
            const isAbnormal = count % 3 === 0;
            const data = {
                left_elbow: 150 + Math.floor(Math.random() * 20),
                right_elbow: 150 + Math.floor(Math.random() * 20),
                left_knee: isAbnormal ? 70 + Math.floor(Math.random() * 20) : 110 + Math.floor(Math.random() * 20),
                right_knee: isAbnormal ? 70 + Math.floor(Math.random() * 20) : 110 + Math.floor(Math.random() * 20)
            };
            sendTestData(data);
        }, 4000);
        uni.showToast({
            title: '已开启自动发送',
            icon: 'success'
        });
    }
};

onMounted(() => {
    connect();
});

onLoad((options = {}) => {
    if (options.mode === 'video') {
        const source = options.source;
        if (source === 'camera' || source === 'album') {
            videoSource.value = source;
            if (source === 'camera') {
                activeTab.value = 'realtime';
                cameraStatus.value = '点击开启摄像头后开始录制';
            } else {
                activeTab.value = 'video';
                cameraStatusVideo.value = '请点击下方按钮从相册选择视频进行分析';
            }
        } else {
            activeTab.value = 'video';
            videoSource.value = 'all';
            cameraStatusVideo.value = '可从相册选择视频，或拍摄一段新视频';
        }
    }
});

onUnmounted(() => {
    if (pollTimer) {
        clearTimeout(pollTimer);
        pollTimer = null;
    }
    closeConnection();
    cleanupCamera();
    stopTTS();
});
</script>

<style>
/* 自定义导航栏样式 */
.navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--status-bar-height, 0) 32rpx 20rpx;
    background: rgba(26, 26, 46, 0.95);
    backdrop-filter: blur(10rpx);
}

.back-btn {
    width: 64rpx;
    height: 64rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 32rpx;
    background: rgba(255, 255, 255, 0.1);
}

.back-icon {
    font-size: 44rpx;
    color: #ffffff;
    font-weight: bold;
    line-height: 1;
}

.nav-title {
    font-size: 32rpx;
    font-weight: 600;
    color: #ffffff;
    flex: 1;
    text-align: center;
}

.nav-spacer {
    width: 64rpx;
}

/* 主容器样式 */
.container {
    min-height: 100vh;
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f0f23 100%);
    padding: 0 40rpx 40rpx;
    display: flex;
    flex-direction: column;
}

.status-bar {
    display: flex;
    flex-direction: column;
    gap: 20rpx;
    margin-bottom: 40rpx;
}

.status-indicator {
    display: flex;
    align-items: center;
    gap: 16rpx;
}

.status-dot {
    width: 20rpx;
    height: 20rpx;
    border-radius: 50%;
    transition: all 0.3s;
}

.status-dot.connected {
    background: var(--primary-green);
    box-shadow: 0 0 20rpx rgba(222, 255, 154, 0.6);
}

.status-dot.connecting {
    background: #ffaa00;
    box-shadow: 0 0 20rpx rgba(255, 170, 0, 0.6);
    animation: pulse 1.5s infinite;
}

.status-dot.disconnected {
    background: #ff4757;
    box-shadow: 0 0 20rpx rgba(255, 71, 87, 0.6);
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.status-text {
    color: #ffffff;
    font-size: 28rpx;
    font-weight: 500;
}

.error-message {
    color: #ff4757;
    font-size: 24rpx;
    background: rgba(255, 71, 87, 0.1);
    padding: 16rpx 24rpx;
    border-radius: 16rpx;
    border: 1px solid rgba(255, 71, 87, 0.3);
}

.joints-section {
    margin-bottom: 40rpx;
}

.section-title {
    color: #ffffff;
    font-size: 32rpx;
    font-weight: 600;
    margin-bottom: 30rpx;
    display: block;
}

.joints-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24rpx;
}

.joint-card {
    background: rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(10rpx);
    border-radius: 32rpx;
    padding: 40rpx 20rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16rpx;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s;
}

.joint-card:active {
    transform: scale(0.98);
    background: rgba(255, 255, 255, 0.12);
}

.joint-label {
    color: #8892b0;
    font-size: 26rpx;
}

.joint-value {
    color: #ffffff;
    font-size: 56rpx;
    font-weight: 700;
    background: linear-gradient(135deg, var(--primary-green) 0%, #00d4ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.mode-tabs {
    display: flex;
    background: rgba(255, 255, 255, 0.08);
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
    color: rgba(255, 255, 255, 0.6);
    font-size: 28rpx;
    transition: all 0.2s;
}

.tab.active {
    background: #6366f1;
    color: #ffffff;
    font-weight: 600;
}

/* 摄像头区域样式 */
.camera-section {
    margin-bottom: 40rpx;
}

.camera-preview {
    position: relative;
    width: 100%;
    height: 500rpx;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 24rpx;
    overflow: hidden;
    margin-bottom: 30rpx;
    border: 2rpx solid rgba(255, 255, 255, 0.1);
}

.camera-video {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.recording-indicator {
    position: absolute;
    top: 20rpx;
    left: 20rpx;
    display: flex;
    align-items: center;
    gap: 12rpx;
    background: rgba(255, 0, 0, 0.8);
    padding: 12rpx 20rpx;
    border-radius: 20rpx;
    backdrop-filter: blur(10rpx);
}

.recording-dot {
    width: 16rpx;
    height: 16rpx;
    background: #ffffff;
    border-radius: 50%;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

.recording-text {
    color: #ffffff;
    font-size: 24rpx;
    font-weight: 500;
}

.camera-placeholder {
    width: 100%;
    height: 500rpx;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 24rpx;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 30rpx;
    border: 2rpx dashed rgba(255, 255, 255, 0.2);
}

.placeholder-text {
    color: rgba(255, 255, 255, 0.6);
    font-size: 28rpx;
    text-align: center;
}

.camera-controls {
    display: flex;
    gap: 20rpx;
    margin-bottom: 40rpx;
    flex-wrap: wrap;
}

.camera-btn {
    flex: 1;
    min-width: 200rpx;
    padding: 24rpx 32rpx;
    border-radius: 16rpx;
    border: none;
    font-size: 28rpx;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s;
    text-align: center;
}

.camera-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.camera-btn.primary {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #ffffff;
}

.camera-btn.warning {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #ffffff;
}

.camera-btn.danger {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: #ffffff;
}

.camera-btn.success {
    background: linear-gradient(135deg, #10b981, #059669);
    color: #ffffff;
}

.camera-btn:active:not(:disabled) {
    transform: scale(0.95);
}

.video-preview {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 24rpx;
    padding: 32rpx;
    border: 1rpx solid rgba(255, 255, 255, 0.1);
}

.preview-video {
    width: 100%;
    height: 400rpx;
    border-radius: 16rpx;
    background: #000;
    margin-bottom: 30rpx;
}

.preview-controls {
    display: flex;
    gap: 20rpx;
}

.preview-btn {
    flex: 1;
    padding: 24rpx 32rpx;
    border-radius: 16rpx;
    border: none;
    font-size: 28rpx;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.3s;
}

.preview-btn.secondary {
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff;
}

.preview-btn.primary {
    background: linear-gradient(135deg, #10b981, #059669);
    color: #ffffff;
}

.preview-btn:active {
    transform: scale(0.95);
}

.analysis-progress {
    margin-top: 20rpx;
}

.progress-text {
    color: #ffffff;
    font-size: 26rpx;
    margin-bottom: 12rpx;
    display: block;
}

.progress-track {
    height: 14rpx;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 99rpx;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(135deg, var(--primary-green), #00d4ff);
    border-radius: 99rpx;
    transition: width 0.2s ease;
}

.advice-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.advice-bubble {
    display: flex;
    gap: 24rpx;
    background: linear-gradient(135deg, rgba(222, 255, 154, 0.15) 0%, rgba(0, 212, 255, 0.15) 100%);
    backdrop-filter: blur(10rpx);
    border-radius: 40rpx;
    padding: 40rpx;
    border: 2px solid rgba(222, 255, 154, 0.3);
    box-shadow: 0 0 40rpx rgba(222, 255, 154, 0.15);
}

.coach-avatar-container {
    flex-shrink: 0;
}

.coach-avatar {
    width: 120rpx;
    height: 120rpx;
    border-radius: 0;
    border: 4rpx solid var(--primary-green);
    box-shadow: 0 0 30rpx rgba(222, 255, 154, 0.4);
    background: rgba(222, 255, 154, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

.coach-img {
    width: 100%;
    height: 100%;
    border-radius: 0;
}

.coach-avatar.fallback {
    background: linear-gradient(135deg, rgba(222, 255, 154, 0.3) 0%, rgba(0, 212, 255, 0.3) 100%);
}

.avatar-emoji {
    font-size: 60rpx;
    line-height: 1;
}

.advice-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16rpx;
}

.advice-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12rpx;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 12rpx;
}

.coach-label {
    color: var(--primary-green);
    font-size: 28rpx;
    font-weight: 600;
}

.source-badge {
    font-size: 22rpx;
    padding: 8rpx 16rpx;
    border-radius: 16rpx;
    font-weight: 500;
}

.source-badge.doubao {
    background: linear-gradient(135deg, rgba(222, 255, 154, 0.3) 0%, rgba(0, 212, 255, 0.3) 100%);
    color: var(--primary-green);
    border: 1px solid rgba(222, 255, 154, 0.4);
}

.source-badge.video {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.4);
}

.source-badge.default {
    background: rgba(255, 255, 255, 0.15);
    color: #8892b0;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.source-badge.timeout {
    background: rgba(255, 170, 0, 0.2);
    color: #ffaa00;
    border: 1px solid rgba(255, 170, 0, 0.4);
}

.source-badge.error {
    background: rgba(255, 71, 87, 0.2);
    color: #ff4757;
    border: 1px solid rgba(255, 71, 87, 0.4);
}

.source-badge.initial {
    background: rgba(136, 146, 176, 0.2);
    color: #8892b0;
    border: 1px solid rgba(136, 146, 176, 0.3);
}

.tts-icon {
    font-size: 32rpx;
}

.advice-text {
    color: #ffffff;
    font-size: 32rpx;
    line-height: 1.6;
    display: block;
}

.cursor {
    display: inline-block;
    width: 4rpx;
    height: 36rpx;
    background: var(--primary-green);
    margin-left: 4rpx;
    animation: blink 0.8s infinite;
    vertical-align: middle;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}

.analysis-section {
    margin-bottom: 40rpx;
}

.summary-card,
.segment-card {
    background: rgba(255, 255, 255, 0.07);
    border-radius: 24rpx;
    padding: 32rpx;
    margin-bottom: 20rpx;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.summary-title,
.segment-title {
    color: #ffffff;
    font-size: 30rpx;
    font-weight: 600;
    margin-bottom: 16rpx;
}

.summary-text,
.segment-line,
.issue-line {
    color: rgba(255, 255, 255, 0.8);
    font-size: 26rpx;
    line-height: 1.6;
    margin-bottom: 8rpx;
}

.segment-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20rpx;
    margin-bottom: 16rpx;
}

.segment-title {
    flex: 1;
}

.segment-time {
    color: #00d4ff;
    font-size: 24rpx;
}

.segment-subtitle {
    color: var(--primary-green);
    font-size: 26rpx;
    font-weight: 600;
    margin: 16rpx 0 8rpx;
}

.coach-advice {
    color: #ffffff;
    font-size: 28rpx;
    line-height: 1.6;
    margin-top: 8rpx;
}

.test-section {
    margin-top: 40rpx;
}

.test-buttons {
    display: flex;
    flex-direction: column;
    gap: 20rpx;
}

.test-btn {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #ffffff;
    font-size: 28rpx;
    padding: 24rpx;
    border-radius: 24rpx;
    transition: all 0.3s;
}

.test-btn.primary {
    background: linear-gradient(135deg, var(--primary-green) 0%, #00d4ff 100%);
    border: none;
    color: #1a1a2e;
    font-weight: 600;
}

.test-btn.warning {
    background: linear-gradient(135deg, #ffaa00 0%, #ff6b35 100%);
    border: none;
    color: #1a1a2e;
    font-weight: 600;
}

.test-btn.active {
    background: linear-gradient(135deg, #ff4757 0%, #ff6b81 100%);
    border: none;
    color: #ffffff;
    font-weight: 600;
}

.test-btn:active {
    transform: scale(0.98);
}
</style>
