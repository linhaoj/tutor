import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 导入页面组件
import Dashboard from '@/views/Dashboard.vue'
import Students from '@/views/Students.vue'
import Words from '@/views/Words.vue'
import Learning from '@/views/Learning.vue'
import Stats from '@/views/Stats.vue'
import WordStudy from '@/views/WordStudy.vue'
import SimpleWordStudy from '@/views/SimpleWordStudy.vue'
import WordCheckTask from '@/views/WordCheckTask.vue'
import MixedGroupTest from '@/views/MixedGroupTest.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { title: '日程管理' }
  },
  {
    path: '/students',
    name: 'Students',
    component: Students,
    meta: { title: '学生管理' }
  },
  {
    path: '/words',
    name: 'Words',
    component: Words,
    meta: { title: '单词管理' }
  },
{
  path: '/study/:studentId',
  name: 'StudyHome',
  component: () => import('../views/StudyHome.vue'),
  meta: { title: '学习准备' },
  props: true
},
{
  path: '/study/:studentId/learn',
  name: 'WordStudy',
  component: WordStudy,
  meta: { title: '背单词' },
  props: true
},
  {
    path: '/learning/study/:studentId',
    name: 'WordStudy',
    component: WordStudy,
    meta: { title: '背单词' },
    props: true
  },
  {
    path: '/simple-study/:studentId',
    name: 'SimpleWordStudy',
    component: SimpleWordStudy,
    meta: { title: '简单学习' },
    props: true
  },
  {
    path: '/word-check/:studentId',
    name: 'WordCheckTask',
    component: WordCheckTask,
    meta: { title: '单词检查任务' },
    props: true
  },
  {
    path: '/mixed-test/:studentId',
    name: 'MixedGroupTest',
    component: MixedGroupTest,
    meta: { title: '混组检测' },
    props: true
  },
  {
    path: '/stats',
    name: 'Stats',
    component: Stats,
    meta: { title: '统计分析' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router