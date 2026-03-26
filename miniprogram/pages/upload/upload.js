const app = getApp()
const api = require('../../utils/api')
const util = require('../../utils/util')

// 颜色映射
const colorMap = {
  '白色': '#F5F5F5', '黑色': '#333333', '灰色': '#999999',
  '红色': '#FF4D4F', '粉色': '#FF85C0', '橙色': '#FF8C00',
  '黄色': '#FFD700', '绿色': '#52C41A', '蓝色': '#1890FF',
  '深蓝': '#003A8C', '紫色': '#722ED1', '棕色': '#8B4513',
  '米色': '#F5DEB3', '卡其': '#C3B091', '酒红': '#722F37'
}

Page({
  data: {
    step: 'choose',         // choose → recognizing → result → success
    tempImagePath: '',       // 临时图片路径
    result: null,            // AI 识别结果
    resultImageUrl: '',      // 识别后的图片 URL
    colorDot: '#CCCCCC',     // 颜色圆点
  },

  /**
   * 拍照
   */
  takePhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera'],
      camera: 'back',
      success: (res) => {
        const tempFilePath = res.tempFiles[0].tempFilePath
        this.uploadAndRecognize(tempFilePath)
      }
    })
  },

  /**
   * 从相册选择
   */
  chooseFromAlbum() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album'],
      success: (res) => {
        const tempFilePath = res.tempFiles[0].tempFilePath
        this.uploadAndRecognize(tempFilePath)
      }
    })
  },

  /**
   * 上传图片并 AI 识别
   */
  async uploadAndRecognize(filePath) {
    this.setData({
      step: 'recognizing',
      tempImagePath: filePath
    })

    try {
      const openid = app.getOpenid()
      const result = await api.uploadClothing(filePath, openid)

      console.log('[上传页] AI 识别结果:', result)

      this.setData({
        step: 'result',
        result: result,
        resultImageUrl: api.getImageUrl(result.thumbnail_url || result.image_url),
        colorDot: colorMap[result.color] || '#CCCCCC'
      })

    } catch (err) {
      console.error('[上传页] 上传失败:', err)
      wx.showModal({
        title: '识别失败',
        content: err.message || '请检查网络连接后重试',
        confirmText: '重试',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            this.uploadAndRecognize(filePath)
          } else {
            this.setData({ step: 'choose' })
          }
        }
      })
    }
  },

  /**
   * 确认添加到衣橱（已在上传时入库，直接跳转成功）
   */
  confirmAdd() {
    this.setData({ step: 'success' })
    wx.vibrateShort({ type: 'medium' })
  },

  /**
   * 重新拍摄
   */
  retake() {
    this.setData({
      step: 'choose',
      tempImagePath: '',
      result: null
    })
  },

  /**
   * 继续添加
   */
  continueAdd() {
    this.setData({
      step: 'choose',
      tempImagePath: '',
      result: null
    })
  },

  /**
   * 返回衣橱
   */
  goBack() {
    wx.navigateBack()
  }
})
