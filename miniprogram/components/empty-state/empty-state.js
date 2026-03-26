Component({
  properties: {
    icon: { type: String, value: '👗' },
    title: { type: String, value: '这里空空如也' },
    desc: { type: String, value: '' },
    btnText: { type: String, value: '' }
  },
  methods: {
    onBtnTap() {
      this.triggerEvent('action')
    }
  }
})
