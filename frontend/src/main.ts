import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { initDatabase } from '@/utils/localDatabase'
import { initTempAuth } from '@/utils/tempAuth'

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

app.mount('#app')