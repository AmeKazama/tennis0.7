/**
 * 朋友圈数据管理
 */
const API_BASE_URL = 'http://localhost:8000/api/moments'
const STORAGE_KEY = 'tennis_moments_cache'

export const getMomentsList = (page = 1, pageSize = 10, visibility = null) => {
	return new Promise((resolve, reject) => {
		let url = `${API_BASE_URL}/list?page=${page}&page_size=${pageSize}`
		if (visibility) {
			url += `&visibility=${visibility}`
		}
		
		uni.request({
			url,
			method: 'GET',
			success: (res) => {
				if (res.data.code === 0) {
					resolve(res.data.data)
				} else {
					reject(new Error(res.data.message || '获取动态列表失败'))
				}
			},
			fail: (err) => {
				// 降级到本地存储
				const localData = getLocalMoments()
				if (localData.length > 0) {
					resolve({
						list: localData.slice((page - 1) * pageSize, page * pageSize),
						total: localData.length,
						page,
						page_size: pageSize
					})
				} else {
					reject(err)
				}
			}
		})
	})
}

export const publishMoment = (data) => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: `${API_BASE_URL}/publish`,
			method: 'POST',
			data: {
				content: data.content,
				images: data.images ? JSON.stringify(data.images) : null,
				video_url: data.videoUrl,
				location: data.location,
				visibility: data.visibility || 'public'
			},
			success: (res) => {
				if (res.data.code === 0) {
					// 同步到本地存储
					saveMomentToLocal({
						id: res.data.data.id,
						...data,
						likes_count: 0,
						comments_count: 0,
						shares_count: 0,
						create_time: new Date().toISOString()
					})
					resolve(res.data.data)
				} else {
					reject(new Error(res.data.message || '发布失败'))
				}
			},
			fail: (err) => {
				// 降级到本地存储
				const localMoment = saveMomentToLocal({
					...data,
					likes_count: 0,
					comments_count: 0,
					shares_count: 0,
					create_time: new Date().toISOString()
				})
				resolve({ id: localMoment.id, message: '本地发布成功' })
			}
		})
	})
}

export const deleteMoment = (momentId) => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: `${API_BASE_URL}/${momentId}`,
			method: 'DELETE',
			success: (res) => {
				if (res.data.code === 0) {
					removeMomentFromLocal(momentId)
					resolve(res.data.data)
				} else {
					reject(new Error(res.data.message || '删除失败'))
				}
			},
			fail: (err) => {
				removeMomentFromLocal(momentId)
				resolve({ message: '本地删除成功' })
			}
		})
	})
}

export const likeMoment = (momentId) => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: `${API_BASE_URL}/${momentId}/like`,
			method: 'POST',
			success: (res) => {
				if (res.data.code === 0) {
					resolve(res.data.data)
				} else {
					reject(new Error(res.data.message || '点赞失败'))
				}
			},
			fail: () => {
				// 本地点赞
				updateLocalMomentLike(momentId, 1)
				resolve({ likes_count: 1 })
			}
		})
	})
}

export const unlikeMoment = (momentId) => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: `${API_BASE_URL}/${momentId}/like`,
			method: 'DELETE',
			success: (res) => {
				if (res.data.code === 0) {
					resolve(res.data.data)
				} else {
					reject(new Error(res.data.message || '取消点赞失败'))
				}
			},
			fail: () => {
				updateLocalMomentLike(momentId, -1)
				resolve({ likes_count: 0 })
			}
		})
	})
}

export const commentMoment = (momentId, content, parentId = null) => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: `${API_BASE_URL}/${momentId}/comment`,
			method: 'POST',
			data: {
				content,
				parent_id: parentId
			},
			success: (res) => {
				if (res.data.code === 0) {
					resolve(res.data.data)
				} else {
					reject(new Error(res.data.message || '评论失败'))
				}
			},
			fail: () => {
				resolve({ id: Date.now(), comments_count: 0 })
			}
		})
	})
}

export const getComments = (momentId, page = 1, pageSize = 20) => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: `${API_BASE_URL}/${momentId}/comments?page=${page}&page_size=${pageSize}`,
			method: 'GET',
			success: (res) => {
				if (res.data.code === 0) {
					resolve(res.data.data)
				} else {
					reject(new Error(res.data.message || '获取评论失败'))
				}
			},
			fail: reject
		})
	})
}

export const shareMoment = (momentId, shareType = 'internal') => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: `${API_BASE_URL}/${momentId}/share`,
			method: 'POST',
			data: { share_type: shareType },
			success: (res) => {
				if (res.data.code === 0) {
					resolve(res.data.data)
				} else {
					reject(new Error(res.data.message || '分享失败'))
				}
			},
			fail: () => {
				resolve({ shares_count: 0 })
			}
		})
	})
}

// 数据统计相关
export const getStatsSummary = () => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: `${API_BASE_URL}/stats/summary`,
			method: 'GET',
			success: (res) => {
				if (res.data.code === 0) {
					resolve(res.data.data)
				} else {
					reject(new Error(res.data.message || '获取统计失败'))
				}
			},
			fail: () => {
				resolve(getLocalStats())
			}
		})
	})
}

export const getStatsTrend = (days = 7) => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: `${API_BASE_URL}/stats/trend?days=${days}`,
			method: 'GET',
			success: (res) => {
				if (res.data.code === 0) {
					resolve(res.data.data)
				} else {
					reject(new Error(res.data.message || '获取趋势失败'))
				}
			},
			fail: reject
		})
	})
}

export const getStatsOverview = () => {
	return new Promise((resolve, reject) => {
		uni.request({
			url: `${API_BASE_URL}/stats/overview`,
			method: 'GET',
			success: (res) => {
				if (res.data.code === 0) {
					resolve(res.data.data)
				} else {
					reject(new Error(res.data.message || '获取总览失败'))
				}
			},
			fail: () => {
				resolve(getLocalStats())
			}
		})
	})
}

// 本地存储操作
const getLocalMoments = () => {
	try {
		const data = uni.getStorageSync(STORAGE_KEY)
		return data ? JSON.parse(data) : []
	} catch (e) {
		return []
	}
}

const saveMomentToLocal = (moment) => {
	try {
		const moments = getLocalMoments()
		const newMoment = {
			id: moment.id || Date.now().toString(),
			...moment,
			create_time: moment.create_time || new Date().toISOString()
		}
		uni.setStorageSync(STORAGE_KEY, JSON.stringify([newMoment, ...moments]))
		return newMoment
	} catch (e) {
		console.error('保存本地动态失败', e)
		return moment
	}
}

const removeMomentFromLocal = (momentId) => {
	try {
		const moments = getLocalMoments()
		const filtered = moments.filter(m => m.id !== momentId)
		uni.setStorageSync(STORAGE_KEY, JSON.stringify(filtered))
	} catch (e) {
		console.error('删除本地动态失败', e)
	}
}

const updateLocalMomentLike = (momentId, delta) => {
	try {
		const moments = getLocalMoments()
		const updated = moments.map(m => {
			if (m.id === momentId) {
				return {
					...m,
					likes_count: Math.max(0, (m.likes_count || 0) + delta),
					is_liked: delta > 0 ? true : false
				}
			}
			return m
		})
		uni.setStorageSync(STORAGE_KEY, JSON.stringify(updated))
	} catch (e) {
		console.error('更新本地点赞失败', e)
	}
}

const getLocalStats = () => {
	return {
		total_posts: 0,
		total_likes_received: 0,
		total_comments_received: 0,
		total_shares_received: 0,
		daily_stats: []
	}
}

export default {
	getMomentsList,
	publishMoment,
	deleteMoment,
	likeMoment,
	unlikeMoment,
	commentMoment,
	getComments,
	shareMoment,
	getStatsSummary,
	getStatsTrend,
	getStatsOverview
}
