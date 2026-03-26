/**
 * StyleMate API 请求封装
 */

// ⚠️ 开发时改成你的后端地址，上线后改成正式域名
const BASE_URL = 'http://10.64.85.37:8000'

/**
 * 通用请求方法
 */
function request(options) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${BASE_URL}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': options.contentType || 'application/json',
        ...options.header
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          const errMsg = (res.data && res.data.detail) || '请求失败'
          reject({ statusCode: res.statusCode, message: errMsg })
        }
      },
      fail(err) {
        reject({ statusCode: -1, message: '网络错误，请检查网络连接' })
      }
    })
  })
}

/**
 * 上传衣物图片
 * @param {string} filePath 本地图片路径
 * @param {string} openid 用户标识
 * @returns {Promise} 识别结果
 */
function uploadClothing(filePath, openid) {
  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: `${BASE_URL}/api/upload`,
      filePath: filePath,
      name: 'image',
      formData: {
        openid: openid
      },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            const data = JSON.parse(res.data)
            resolve(data)
          } catch (e) {
            reject({ message: '数据解析失败' })
          }
        } else {
          let errMsg = '上传失败'
          try {
            const data = JSON.parse(res.data)
            errMsg = data.detail || errMsg
          } catch (e) {}
          reject({ statusCode: res.statusCode, message: errMsg })
        }
      },
      fail(err) {
        reject({ statusCode: -1, message: '上传失败，请检查网络' })
      }
    })
  })
}

/**
 * 获取衣橱列表
 * @param {string} openid 用户标识
 * @returns {Promise} 衣橱数据
 */
function getWardrobe(openid) {
  return request({
    url: `/api/wardrobe?openid=${encodeURIComponent(openid)}`,
    method: 'GET'
  })
}

/**
 * AI 搭配推荐
 * @param {string} openid 用户标识
 * @param {Array} itemIds 指定衣物 ID 列表（可选）
 * @returns {Promise} 搭配方案
 */
function getRecommend(openid, itemIds) {
  const data = { openid }
  if (itemIds && itemIds.length > 0) {
    data.item_ids = itemIds
  }
  return request({
    url: '/api/recommend',
    method: 'POST',
    data: data
  })
}

/**
 * 健康检查
 */
function healthCheck() {
  return request({
    url: '/api/health',
    method: 'GET'
  })
}

/**
 * 拼接图片完整 URL
 * @param {string} path 相对路径（如 /static/uploads/xxx.jpg）
 * @returns {string} 完整 URL
 */
function getImageUrl(path) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${BASE_URL}${path}`
}

module.exports = {
  BASE_URL,
  uploadClothing,
  getWardrobe,
  getRecommend,
  healthCheck,
  getImageUrl
}
