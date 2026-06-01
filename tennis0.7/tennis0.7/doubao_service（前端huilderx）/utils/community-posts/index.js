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

export const saveLocalFile = (tempFilePath) => {
	return new Promise((resolve) => {
		if (!tempFilePath || typeof uni.saveFile !== 'function') {
			resolve(tempFilePath)
			return
		}

		uni.saveFile({
			tempFilePath,
			success: (res) => resolve(res.savedFilePath || tempFilePath),
			fail: () => resolve(tempFilePath)
		})
	})
}
