const app = getApp()
const api = require('../../utils/api')
const util = require('../../utils/util')

Page({
  data: {
    loading: true,
    outfits: [],        // 搭配方案列表
    error: false,
    errorMsg: '',
    itemIds: null,      // 指定的衣物 ID
  },

  onLoad(options) {
    // 解析指定的衣物 ID
    if (options.item_ids) {
      const ids = options.item_ids.split(',').map(Number).filter(Boolean)
      this.setData({ itemIds: ids })
    }

    this.fetchRecommend()
  },

  /**
   * 请求 AI 搭配推荐
   */
  async fetchRecommend() {
    this.setData({ loading: true, error: false })

    try {
      const openid = app.getOpenid()
      const res = await api.getRecommend(openid, this.data.itemIds)

      console.log('[结果页] AI 搭配结果:', res)

      if (res.outfits && res.outfits.length > 0) {
        this.setData({
          outfits: res.outfits,
          loading: false
        })
      } else {
        this.setData({
          loading: false,
          error: true,
          errorMsg: '暂时没有生成搭配方案，试试添加更多衣物？'
        })
      }

    } catch (err) {
      console.error('[结果页] 搭配推荐失败:', err)
      this.setData({
        loading: false,
        error: true,
        errorMsg: err.message || '网络异常，请稍后重试'
      })
    }
  },

  /**
   * 换一批搭配
   */
  refreshRecommend() {
    wx.vibrateShort({ type: 'light' })
    this.fetchRecommend()
  },

  /**
   * 搭配点赞
   */
  onOutfitLike(e) {
    const { outfit, liked } = e.detail
    console.log('[结果页] 搭配点赞:', outfit.id, liked)
    // MVP 先只记录日志，后续可以做反馈收集
  },

  /**
   * 返回衣橱
   */
  goBack() {
    wx.navigateBack()
  },

  /**
   * 分享
   */
  onShareAppMessage() {
    return {
      title: '✨ AI 帮我搭了几套穿搭，你也来试试！',
      path: '/pages/index/index'
    }
  }
})
