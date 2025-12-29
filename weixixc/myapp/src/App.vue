<script>
export default {
  onLaunch() {
    console.log('App Launch')

    // 检查小程序更新
    this.checkUpdate()

    // 获取系统信息
    this.getSystemInfo()
  },

  onShow() {
    console.log('App Show')
  },

  onHide() {
    console.log('App Hide')
  },

  methods: {
    /**
     * 检查小程序更新
     */
    checkUpdate() {
      // #ifdef MP-WEIXIN
      const updateManager = uni.getUpdateManager()

      updateManager.onCheckForUpdate((res) => {
        console.log('检查更新结果:', res.hasUpdate)
      })

      updateManager.onUpdateReady(() => {
        uni.showModal({
          title: '更新提示',
          content: '新版本已经准备好，是否重启应用？',
          success: (res) => {
            if (res.confirm) {
              updateManager.applyUpdate()
            }
          }
        })
      })

      updateManager.onUpdateFailed(() => {
        console.log('新版本下载失败')
      })
      // #endif
    },

    /**
     * 获取系统信息
     */
    getSystemInfo() {
      uni.getSystemInfo({
        success: (res) => {
          console.log('系统信息:', res)
          this.globalData.systemInfo = res
        }
      })
    }
  },

  globalData: {
    systemInfo: null,
    userLocation: null,
    apiBaseUrl: 'https://your-domain.com:8082',
    sightServerUrl: 'https://your-domain.com:8001'
  }
}
</script>

<style lang="scss">
/* 注意：uni-app 不支持 * 选择器 */
page {
  height: 100%;
  background-color: #f8f8f8;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
}

/* 全局样式 */
.container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 按钮样式 */
button {
  font-size: 28rpx;
}

/* 输入框样式 */
input {
  font-size: 28rpx;
}

/* 文本样式 */
text {
  font-size: 28rpx;
  color: #333;
}

/* Loading状态 */
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
}

/* 空状态 */
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 40rpx;
  color: #999;

  .empty-icon {
    font-size: 80rpx;
    margin-bottom: 20rpx;
  }

  .empty-text {
    font-size: 28rpx;
    color: #999;
  }
}
</style>
