const STORAGE_KEY = 'courtvision_community_posts'

export const getCommunityPosts = () => {
	try {
		return uni.getStorageSync(STORAGE_KEY) || []
	} catch (error) {
		console.error('读取发布内容失败', error)
		return []
	}
}

export const addCommunityPost = (post) => {
	const posts = getCommunityPosts()
	const nextPost = {
		id: Date.now().toString(),
		createdAt: Date.now(),
		...post
	}

	uni.setStorageSync(STORAGE_KEY, [nextPost, ...posts])
	return nextPost
}

// 【改进版】确保返回可用的本地路径
export const saveLocalFile = (tempFilePath) => {
	return new Promise((resolve) => {
		// 如果已经是本地持久路径，直接返回
		if (tempFilePath && tempFilePath.startsWith('file://')) {
			return resolve(tempFilePath)
		}
		if (!tempFilePath || typeof uni.saveFile !== 'function') {
			return resolve(tempFilePath)
		}

		uni.saveFile({
			tempFilePath,
			success: (res) => {
				console.log('saveFile 成功：', res.savedFilePath)
				resolve(res.savedFilePath)
			},
			fail: (err) => {
				console.error('saveFile 失败：', err)
				resolve(tempFilePath) // 失败时降级用原临时路径
			}
		})
	})
}