App({
  globalData: {
    openid: '',
    userInfo: null,
  },

  onLaunch() {
    // 静默登录：获取用户标识
    this.silentLogin()
  },

  /**
   * 静默登录
   * MVP 阶段使用 wx.login 获取 code，简化为本地生成唯一标识
   * 正式上线后替换为真实的微信登录流程
   */
  silentLogin() {
    // 先检查本地缓存
    const cachedOpenid = wx.getStorageSync('openid')
    if (cachedOpenid) {
      this.globalData.openid = cachedOpenid
      console.log('[App] 使用缓存 openid:', cachedOpenid)
      return
    }

    // MVP 模式：生成本地唯一标识（正式版替换为 wx.login → 后端换 openid）
    wx.login({
      success: (res) => {
        if (res.code) {
          // 正式环境：发送 code 到后端换取 openid
          // 这里 MVP 用 code 的 hash 作为临时标识
          const openid = 'user_' + this._simpleHash(res.code + Date.now())
          this.globalData.openid = openid
          wx.setStorageSync('openid', openid)
          console.log('[App] 新用户 openid:', openid)
        }
      },
      fail: () => {
        // 兜底：随机生成
        const openid = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 8)
        this.globalData.openid = openid
        wx.setStorageSync('openid', openid)
      }
    })
  },

  /**
   * 获取 openid（确保已登录）
   */
  getOpenid() {
    if (this.globalData.openid) {
      return this.globalData.openid
    }
    const cached = wx.getStorageSync('openid')
    if (cached) {
      this.globalData.openid = cached
      return cached
    }
    // 兜底
    const openid = 'user_' + Date.now()
    this.globalData.openid = openid
    wx.setStorageSync('openid', openid)
    return openid
  },

  _simpleHash(str) {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    return Math.abs(hash).toString(36)
  }
})
