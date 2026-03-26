const app = getApp()
const api = require('../../utils/api')
const util = require('../../utils/util')

Page({
  data: {
    wardrobeList: [],     // 衣橱列表
    loading: true,        // 加载状态
    selectMode: false,    // 选择模式
    selectedCount: 0,     // 已选数量
  },

  onShow() {
    // 每次显示页面都刷新衣橱（从上传页返回时能看到新衣物）
    this.loadWardrobe()
  },

  /**
   * 加载衣橱数据
   */
  async loadWardrobe() {
    const openid = app.getOpenid()
    this.setData({ loading: true })

    try {
      const res = await api.getWardrobe(openid)
      const items = (res.items || []).map(item => ({
        ...item,
        _selected: false
      }))
      this.setData({
        wardrobeList: items,
        loading: false
      })
    } catch (err) {
      console.error('[首页] 加载衣橱失败:', err)
      this.setData({ loading: false })
      // 首次可能没有数据，不报错
    }
  },

  /**
   * 跳转到上传页
   */
  goToUpload() {
    wx.navigateTo({ url: '/pages/upload/upload' })
  },

  /**
   * 衣物卡片点击
   */
  onClothingTap(e) {
    const { index } = e.currentTarget.dataset

    if (this.data.selectMode) {
      // 选择模式：切换选中状态
      const key = `wardrobeList[${index}]._selected`
      const newVal = !this.data.wardrobeList[index]._selected
      this.setData({ [key]: newVal })
      this._updateSelectedCount()
    } else {
      // 非选择模式：可以做查看详情等（MVP 先不做）
    }
  },

  /**
   * 切换选择模式
   */
  toggleSelectMode() {
    const newMode = !this.data.selectMode
    if (!newMode) {
      // 退出选择模式，清空选中
      const list = this.data.wardrobeList.map(item => ({
        ...item,
        _selected: false
      }))
      this.setData({
        selectMode: false,
        wardrobeList: list,
        selectedCount: 0
      })
    } else {
      this.setData({ selectMode: true })
    }
  },

  /**
   * 更新已选数量
   */
  _updateSelectedCount() {
    const count = this.data.wardrobeList.filter(i => i._selected).length
    this.setData({ selectedCount: count })
  },

  /**
   * 使用全部衣物搭配
   */
  goRecommend() {
    wx.navigateTo({ url: '/pages/result/result' })
  },

  /**
   * 使用选中衣物搭配
   */
  goRecommendSelected() {
    if (this.data.selectedCount < 2) {
      util.showError('至少选择 2 件衣物哦～')
      return
    }

    const selectedIds = this.data.wardrobeList
      .filter(i => i._selected)
      .map(i => i.id)

    wx.navigateTo({
      url: `/pages/result/result?item_ids=${selectedIds.join(',')}`
    })
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadWardrobe().then(() => {
      wx.stopPullDownRefresh()
    })
  }
})
