const api = require('../../utils/api')
const util = require('../../utils/util')

// 颜色名 → CSS 颜色映射
const colorMap = {
  '白色': '#F5F5F5', '黑色': '#333333', '灰色': '#999999',
  '红色': '#FF4D4F', '粉色': '#FF85C0', '浅粉': '#FFB8D4',
  '橙色': '#FF8C00', '黄色': '#FFD700', '绿色': '#52C41A',
  '蓝色': '#1890FF', '深蓝': '#003A8C', '浅蓝': '#91D5FF',
  '紫色': '#722ED1', '棕色': '#8B4513', '米色': '#F5DEB3',
  '卡其': '#C3B091', '藏青': '#003153', '军绿': '#4B5320',
  '酒红': '#722F37', '驼色': '#C19A6B', '杏色': '#FBCEB1'
}

Component({
  properties: {
    item: { type: Object, value: {} },
    selectable: { type: Boolean, value: false },
    selected: { type: Boolean, value: false }
  },

  observers: {
    'item': function(item) {
      if (item && item.id) {
        this.setData({
          imageUrl: api.getImageUrl(item.thumbnail_url || item.image_url),
          emoji: util.getCategoryEmoji(item.category),
          colorDot: colorMap[item.color] || '#CCCCCC'
        })
      }
    }
  },

  data: {
    imageUrl: '',
    emoji: '👔',
    colorDot: '#CCCCCC'
  },

  methods: {
    onTap() {
      this.triggerEvent('tap', { item: this.properties.item })
    }
  }
})
