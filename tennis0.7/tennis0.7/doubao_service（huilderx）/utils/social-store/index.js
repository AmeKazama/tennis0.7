const PROFILE_KEY = 'courtvision_profile'
const FOLLOWING_KEY = 'courtvision_following'
const FAVORITE_FOLDERS_KEY = 'courtvision_favorite_folders'
const FAVORITES_KEY = 'courtvision_favorites'
const COMMENTS_KEY = 'courtvision_comments'

const defaultProfile = {
	id: 'me',
	nickname: 'VolleyVibe802',
	bio: '追求极致的底线进攻手',
	gender: '男',
	region: '中国, 北京',
	avatar: '/static/coach.png'
}

const defaultFavoriteFolders = [
	{ id: 'default', name: '默认收藏夹' },
	{ id: 'forehand', name: '正手学习' },
	{ id: 'serve', name: '发球灵感' }
]

export const regionTree = {
	中国: ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安'],
	美国: ['纽约', '洛杉矶', '旧金山', '西雅图', '波士顿'],
	英国: ['伦敦', '曼彻斯特', '伯明翰'],
	法国: ['巴黎', '里昂', '马赛'],
	澳大利亚: ['悉尼', '墨尔本', '布里斯班']
}

const demoUsers = {
	u1: { id: 'u1', name: 'TennisPro_Jack', avatar: 'https://i.pravatar.cc/150?u=1', region: '美国, 洛杉矶', bio: '发球与上旋训练内容创作者' },
	u2: { id: 'u2', name: 'TennisQueen_Lily', avatar: 'https://i.pravatar.cc/150?u=2', region: '中国, 上海', bio: '双反和底线节奏爱好者' },
	u3: { id: 'u3', name: 'Coach_Mike', avatar: 'https://i.pravatar.cc/150?u=3', region: '英国, 伦敦', bio: '职业教练，专注动作纠错' },
	u4: { id: 'u4', name: 'Match_Highlight', avatar: 'https://i.pravatar.cc/150?u=4', region: '澳大利亚, 墨尔本', bio: '网球比赛高光剪辑' },
	u5: { id: 'u5', name: 'Training_Warrior', avatar: 'https://i.pravatar.cc/150?u=5', region: '中国, 北京', bio: '清晨训练打卡' },
	zhang: { id: 'zhang', name: '张凡', avatar: 'https://i.pravatar.cc/120?u=chat1', region: '中国, 杭州', bio: '周末双打搭子' },
	li: { id: 'li', name: '李娅', avatar: 'https://i.pravatar.cc/120?u=chat2', region: '中国, 上海', bio: '喜欢网前截击' },
	wang: { id: 'wang', name: '王强', avatar: 'https://i.pravatar.cc/120?u=chat3', region: '中国, 北京', bio: '发球练习中' },
	chen: { id: 'chen', name: '陈芳', avatar: 'https://i.pravatar.cc/120?u=chat4', region: '中国, 广州', bio: '底线相持型球员' },
	lin: { id: 'lin', name: '林子涵', avatar: 'https://i.pravatar.cc/120?u=lin', region: '中国, 成都', bio: '经常约练中心场' },
	fan: { id: 'fan', name: '樊晓', avatar: 'https://i.pravatar.cc/120?u=fan', region: '中国, 武汉', bio: '正手进步很快' },
	zhao: { id: 'zhao', name: '赵霖', avatar: 'https://i.pravatar.cc/120?u=zhao', region: '中国, 西安', bio: '球拍装备研究党' },
	sun: { id: 'sun', name: '孙浩', avatar: 'https://i.pravatar.cc/120?u=sun', region: '中国, 深圳', bio: '夜训固定选手' }
}

const read = (key, fallback) => {
	const value = uni.getStorageSync(key)
	return value || fallback
}

const write = (key, value) => {
	uni.setStorageSync(key, value)
	return value
}

export const getProfile = () => ({
	...defaultProfile,
	...(read(PROFILE_KEY, {}) || {})
})

export const updateProfile = (profile) => write(PROFILE_KEY, {
	...getProfile(),
	...profile
})

export const getUserProfile = (id) => {
	if (id === 'me') return getProfile()
	return demoUsers[id] || {
		id,
		name: '网球用户',
		avatar: 'https://i.pravatar.cc/120?u=unknown',
		region: '中国, 北京',
		bio: '热爱网球训练'
	}
}

export const getFollowing = () => read(FOLLOWING_KEY, [])

export const isFollowing = (userId) => getFollowing().includes(userId)

export const toggleFollow = (userId) => {
	const following = getFollowing()
	const next = following.includes(userId)
		? following.filter((id) => id !== userId)
		: [...following, userId]
	write(FOLLOWING_KEY, next)
	return next.includes(userId)
}

export const getFavoriteFolders = () => read(FAVORITE_FOLDERS_KEY, defaultFavoriteFolders)

export const getFavorites = () => read(FAVORITES_KEY, [])

export const isFavorited = (postId) => getFavorites().some((item) => item.postId === postId)

export const addFavorite = (folderId, post) => {
	const favorites = getFavorites().filter((item) => item.postId !== post.id)
	const folder = getFavoriteFolders().find((item) => item.id === folderId) || defaultFavoriteFolders[0]
	const next = [{
		id: `${post.id}_${Date.now()}`,
		postId: post.id,
		folderId: folder.id,
		folderName: folder.name,
		title: post.desc,
		author: post.author,
		avatar: post.avatar,
		poster: post.poster,
		createdAt: Date.now()
	}, ...favorites]
	write(FAVORITES_KEY, next)
	return next
}

export const removeFavorite = (postId) => write(
	FAVORITES_KEY,
	getFavorites().filter((item) => item.postId !== postId)
)

export const getComments = (postId) => {
	const all = read(COMMENTS_KEY, {})
	return all[postId] || [
		{ id: `${postId}_c1`, userId: 'lin', name: '林子涵', avatar: 'https://i.pravatar.cc/120?u=lin', content: '这个击球点很舒服，学习了。', createdAt: Date.now() - 3600000 },
		{ id: `${postId}_c2`, userId: 'fan', name: '樊晓', avatar: 'https://i.pravatar.cc/120?u=fan', content: '能不能也讲一下重心转移？', createdAt: Date.now() - 1800000 }
	]
}

export const addComment = (postId, content) => {
	const all = read(COMMENTS_KEY, {})
	const profile = getProfile()
	const next = [{
		id: `${postId}_${Date.now()}`,
		userId: 'me',
		name: profile.nickname,
		avatar: profile.avatar,
		content,
		createdAt: Date.now()
	}, ...(all[postId] || getComments(postId))]
	all[postId] = next
	write(COMMENTS_KEY, all)
	return next
}
