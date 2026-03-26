const api = require('../../utils/api')

Component({
  properties: {
    outfit: { type: Object, value: {} },
    index: { type: Number, value: 0 }
  },

  observers: {
    'outfit': function (outfit) {
      if (outfit && outfit.items) {
        const itemImages = outfit.items.map(item => ({
          id: item.id,
          url: api.getImageUrl(item.thumbnail_url),
          category: item.category
        }))
        this.setData({ itemImages })
      }
    }
  },

  data: {
    itemImages: [],
    liked: false
  },

  methods: {
    /** 保存搭配卡片到相册 */
    onSaveCard() {
      const cardUrl = this.properties.outfit.card_url
      if (!cardUrl) {
        wx.showToast({ title: '卡片生成中...', icon: 'none' })
        return
      }

      const fullUrl = api.getImageUrl(cardUrl)

      wx.showLoading({ title: '保存中...' })

      // 先下载图片，再保存到相册
      wx.downloadFile({
        url: fullUrl,
        success: (res) => {
          if (res.statusCode === 200) {
            wx.saveImageToPhotosAlbum({
              filePath: res.tempFilePath,
              success: () => {
                wx.hideLoading()
                wx.showToast({ title: '已保存到相册 🎉', icon: 'success' })
              },
              fail: (err) => {
                wx.hideLoading()
                // 可能是权限问题
                if (err.errMsg.indexOf('auth deny') !== -1) {
                  wx.showModal({
                    title: '需要相册权限',
                    content: '请在设置中允许访问相册，才能保存搭配卡片',
                    confirmText: '去设置',
                    success: (res) => {
                      if (res.confirm) wx.openSetting()
                    }
                  })
                } else {
                  wx.showToast({ title: '保存失败', icon: 'none' })
                }
              }
            })
          }
        },
        fail: () => {
          wx.hideLoading()
          wx.showToast({ title: '下载失败', icon: 'none' })
        }
      })
    },

    /** 点赞/取消点赞 */
    onLike() {
      this.setData({ liked: !this.data.liked })
      if (this.data.liked) {
        wx.vibrateShort({ type: 'light' })
      }
      this.triggerEvent('like', {
        outfit: this.properties.outfit,
        liked: this.data.liked
      })
    }
  }
})
