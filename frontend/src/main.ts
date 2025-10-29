import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { initDatabase } from '@/utils/localDatabase'
import { initTempAuth } from '@/utils/tempAuth'
import packageJson from '../package.json'

// 暴露版本信息到全局，方便在console检查
declare global {
  interface Window {
    APP_VERSION: {
      version: string
      buildTime: string
      checkUpdate: () => void
    }
  }
}

const buildTime = new Date().toISOString()

window.APP_VERSION = {
  version: packageJson.version,
  buildTime: buildTime,
  checkUpdate: function() {
    console.log('╔══════════════════════════════════════╗')
    console.log('║   英语陪练系统 - 版本信息           ║')
    console.log('╚══════════════════════════════════════╝')
    console.log('📌 版本号:', this.version)
    console.log('🕐 构建时间:', this.buildTime)
    console.log('\n💡 使用方法:')
    console.log('   在Console输入: APP_VERSION')
    console.log('   或: APP_VERSION.checkUpdate()')
  }
}

const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

// 初始化临时认证
initTempAuth()

// 初始化数据库
initDatabase().then(() => {
  console.log('数据库初始化完成')
}).catch((error) => {
  console.error('数据库初始化失败:', error)
})

// 打印版本信息
console.log(`%c英语陪练系统 v${packageJson.version}`, 'color: #42b983; font-size: 16px; font-weight: bold;')
console.log(`%c构建时间: ${buildTime}`, 'color: #888;')
console.log('%c💡 在Console输入 APP_VERSION 查看版本详情', 'color: #888;')

app.mount('#app')