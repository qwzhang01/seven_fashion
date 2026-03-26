/**
 * 通用工具函数
 */

/**
 * 格式化日期
 */
function formatDate(date) {
  if (typeof date === 'string') date = new Date(date)
  const y = date.getFullYear()
  const m = (date.getMonth() + 1).toString().padStart(2, '0')
  const d = date.getDate().toString().padStart(2, '0')
  return `${y}-${m}-${d}`
}

/**
 * 显示加载提示
 */
function showLoading(title = '加载中...') {
  wx.showLoading({ title, mask: true })
}

/**
 * 隐藏加载提示
 */
function hideLoading() {
  wx.hideLoading()
}

/**
 * 显示成功提示
 */
function showSuccess(title) {
  wx.showToast({ title, icon: 'success', duration: 1500 })
}

/**
 * 显示错误提示
 */
function showError(title) {
  wx.showToast({ title, icon: 'none', duration: 2000 })
}

/**
 * 衣物品类对应的 emoji
 */
const categoryEmoji = {
  '上衣': '👕',
  '裤装': '👖',
  '裙装': '👗',
  '外套': '🧥',
  '鞋': '👟',
  '包': '👜',
  '配饰': '💍'
}

/**
 * 获取品类 emoji
 */
function getCategoryEmoji(category) {
  return categoryEmoji[category] || '👔'
}

/**
 * 品类颜色映射（用于标签背景色）
 */
const categoryColors = {
  '上衣': '#FF6B6B',
  '裤装': '#4ECDC4',
  '裙装': '#FF8E8E',
  '外套': '#45B7D1',
  '鞋': '#96CEB4',
  '包': '#DDA0DD',
  '配饰': '#FFE66D'
}

function getCategoryColor(category) {
  return categoryColors[category] || '#999999'
}

module.exports = {
  formatDate,
  showLoading,
  hideLoading,
  showSuccess,
  showError,
  getCategoryEmoji,
  getCategoryColor
}
