import { API_BASE_URL, getApiBaseUrl } from '@/utils/api-config/index.js'

export { API_BASE_URL, getApiBaseUrl }

const parseUploadResponse = (res) => {
	const raw = typeof res.data === 'string' ? JSON.parse(res.data || '{}') : res.data
	if (!raw || raw.code !== 200) {
		throw new Error(raw?.message || raw?.msg || '上传失败')
	}
	return raw.data
}

const normalizeUrl = (url) => {
	if (!url) return ''
	if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('file://') || url.startsWith('blob:')) {
		return url
	}
	return `${API_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`
}

export const normalizeVideoRecord = (item = {}) => ({
	id: String(item.id || Date.now()),
	serverId: item.id,
	userId: item.user_id || item.userId || 1,
	title: item.title || '网球训练视频',
	text: item.description || item.desc || item.title || '分享一次新的网球训练',
	src: normalizeUrl(item.video_url || item.src),
	videoUrl: normalizeUrl(item.video_url || item.src),
	poster: normalizeUrl(item.cover_url || item.cover),
	type: 'video',
	visibility: item.visibility || 'private',
	status: item.status || 'uploaded',
	createdAt: item.create_time ? new Date(item.create_time.replace(/-/g, '/')).getTime() : Date.now(),
	publishTime: item.publish_time || '',
	likes: item.like_count || item.likes || 0,
	comments: item.comment_count || item.comments || 0,
	shares: item.favorite_count || item.shares || 0,
	author: item.author || `@${item.nickname || 'TennisUser'}`,
	avatar: normalizeUrl(item.avatar_url) || `https://i.pravatar.cc/150?u=${item.user_id || item.id || 1}`,
	desc: item.description || item.desc || item.title || '分享一次新的网球训练',
	music: 'Original Sound'
})

export const uploadPrivateVideo = ({ filePath, userId = 1, title = '', description = '', sourceType = 'upload' }) => new Promise((resolve, reject) => {
	uni.uploadFile({
		url: `${API_BASE_URL}/api/videos/upload`,
		filePath,
		name: 'file',
		formData: {
			user_id: userId,
			title,
			description,
			source_type: sourceType
		},
		timeout: 120000,
		success: (res) => {
			try {
				resolve(normalizeVideoRecord(parseUploadResponse(res)))
			} catch (error) {
				reject(error)
			}
		},
		fail: reject
	})
})

export const fetchMyVideos = ({ userId = 1, page = 1, pageSize = 50 } = {}) => new Promise((resolve, reject) => {
	uni.request({
		url: `${API_BASE_URL}/api/videos/my`,
		method: 'GET',
		data: {
			user_id: userId,
			page,
			page_size: pageSize
		},
		success: (res) => {
			const body = res.data || {}
			if (body.code !== 200) {
				reject(new Error(body.message || '我的视频查询失败'))
				return
			}
			const list = body.data?.list || []
			resolve(list.map(normalizeVideoRecord))
		},
		fail: reject
	})
})

export const publishVideo = ({ videoId, userId = 1, content = '' }) => new Promise((resolve, reject) => {
	uni.request({
		url: `${API_BASE_URL}/api/videos/${videoId}/publish`,
		method: 'POST',
		header: {
			'content-type': 'application/x-www-form-urlencoded'
		},
		data: {
			user_id: userId,
			content
		},
		success: (res) => {
			const body = res.data || {}
			if (body.code !== 200) {
				reject(new Error(body.message || '发布失败'))
				return
			}
			resolve(normalizeVideoRecord(body.data))
		},
		fail: reject
	})
})

export const fetchPublicFeed = ({ page = 1, pageSize = 10 } = {}) => new Promise((resolve, reject) => {
	uni.request({
		url: `${API_BASE_URL}/api/feed/list`,
		method: 'GET',
		data: {
			page,
			page_size: pageSize
		},
		success: (res) => {
			const body = res.data || {}
			if (body.code !== 200) {
				reject(new Error(body.message || body.msg || '首页视频流查询失败'))
				return
			}
			resolve((body.data || []).map(normalizeVideoRecord))
		},
		fail: reject
	})
})
