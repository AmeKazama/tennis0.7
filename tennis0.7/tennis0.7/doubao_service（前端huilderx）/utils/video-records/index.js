const STORAGE_KEY = 'courtvision_video_records'

export const getVideoRecords = () => {
	try {
		return uni.getStorageSync(STORAGE_KEY) || []
	} catch (error) {
		console.error('读取视频记录失败', error)
		return []
	}
}

export const addVideoRecord = (record) => {
	const records = getVideoRecords()
	const nextRecord = {
		id: Date.now().toString(),
		createdAt: Date.now(),
		...record
	}

	uni.setStorageSync(STORAGE_KEY, [nextRecord, ...records])
	return nextRecord
}

export const saveLocalVideo = (tempFilePath) => {
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
