export const API_ENV = 'server'

export const API_HOSTS = {
	local: {
		name: 'local',
		baseUrl: 'http://172.20.27.216:9000',
		asrBaseUrl: 'http://172.20.27.216:9002'
	},
	server: {
		name: 'server',
		baseUrl: 'https://u818190-ac90-0c476376.westb.seetacloud.com:8443',
		asrBaseUrl: 'https://u818190-ac90-0c476376.westb.seetacloud.com:8443'
	}
}

const getActiveApiHost = () => API_HOSTS[API_ENV] || API_HOSTS.local

export const getApiBaseUrl = () => {
	// #ifdef H5
	if (typeof window !== 'undefined') {
		const host = window.location.hostname
		if (host === 'localhost' || host === '127.0.0.1') {
			return 'http://127.0.0.1:9000'
		}
		if (API_ENV === 'local' && host) {
			return `${window.location.protocol}//${host}:9000`
		}
	}
	// #endif
	return getActiveApiHost().baseUrl
}

export const API_BASE_URL = getApiBaseUrl()

export const ASR_API_BASE_URL = API_ENV === 'local'
	? API_BASE_URL.replace(':9000', ':9002')
	: getActiveApiHost().asrBaseUrl

export const WS_URL = API_BASE_URL.replace(/^http/, 'ws') + '/ws/joints'

export const normalizeMediaUrl = (url) => {
	if (!url || typeof url !== 'string') return ''
	if (/^(https?:|file:|blob:)/.test(url)) return url
	return `${API_BASE_URL}${url.startsWith('/') ? '' : '/'}${url}`
}
