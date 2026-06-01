<script>
	export default {
		onLaunch: function() {
			console.log('App Launch')
		},
		onShow: function() {
			console.log('App Show')
		},
		onHide: function() {
			console.log('App Hide')
		}
	}
</script>

<style>
	/*每个页面公共css */
	:root {
		--primary-green: #DEFF9A;
		--dark-bg: #000000;
		--card-bg: #1A1A1A;
		--text-gray: rgba(255, 255, 255, 0.5);
		--text-light: rgba(255, 255, 255, 0.9);
	}
</style>
