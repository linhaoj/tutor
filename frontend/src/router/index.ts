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
import PostLearningTest from '@/views/PostLearningTest.vue'
import AntiForgetReview from '@/views/AntiForgetReview.vue'
import WordFilter from '@/views/WordFilter.vue'
import Login from '@/views/Login.vue'
import Admin from '@/views/Admin.vue'
import StudentDashboard from '@/views/StudentDashboard.vue'
import StudentReview from '@/views/StudentReview.vue'

// 导入认证Store用于路由守卫
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: '登录', requiresGuest: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { title: '日程管理', requiresAuth: true, requiresTeacher: true }
  },
  {
    path: '/student',
    name: 'StudentDashboard',
    component: StudentDashboard,
    meta: { title: '学生复习', requiresAuth: true, requiresStudent: true }
  },
  {
    path: '/student-review/:reviewId',
    name: 'StudentReview',
    component: StudentReview,
    meta: { title: '单词复习', requiresAuth: true, requiresStudent: true },
    props: true
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { title: '系统管理', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/teacher',
    name: 'TeacherHome',
    component: () => import('../views/TeacherHome.vue'),
    meta: { title: '教师首页', requiresAuth: true }
  },
  {
    path: '/data-management',
    name: 'DataManagement',
    component: () => import('../views/DataManagement.vue'),
    meta: { title: '数据管理', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/students',
    name: 'Students',
    component: Students,
    meta: { title: '学生管理', requiresAuth: true, requiresTeacher: true }
  },
  {
    path: '/words',
    name: 'Words',
    component: Words,
    meta: { title: '单词管理', requiresAuth: true, requiresTeacher: true }
  },
{
  path: '/study/:studentId',
  name: 'StudyHome',
  component: () => import('../views/StudyHome.vue'),
  meta: { title: '学习准备', requiresAuth: true },
  props: true
},
{
  path: '/study/:studentId/learn',
  name: 'WordStudy',
  component: WordStudy,
  meta: { title: '背单词', requiresAuth: true },
  props: true
},
  {
    path: '/learning/study/:studentId',
    name: 'WordStudy2',
    component: WordStudy,
    meta: { title: '背单词', requiresAuth: true },
    props: true
  },
  {
    path: '/word-filter/:studentId',
    name: 'WordFilter',
    component: WordFilter,
    meta: { title: '单词筛选', requiresAuth: true },
    props: true
  },
  {
    path: '/simple-study/:studentId',
    name: 'SimpleWordStudy',
    component: SimpleWordStudy,
    meta: { title: '简单学习', requiresAuth: true },
    props: true
  },
  {
    path: '/word-check/:studentId',
    name: 'WordCheckTask',
    component: WordCheckTask,
    meta: { title: '单词检查任务', requiresAuth: true },
    props: true
  },
  {
    path: '/mixed-test/:studentId',
    name: 'MixedGroupTest',
    component: MixedGroupTest,
    meta: { title: '混组检测', requiresAuth: true },
    props: true
  },
  {
    path: '/post-test/:studentId',
    name: 'PostLearningTest',
    component: PostLearningTest,
    meta: { title: '训后检测', requiresAuth: true },
    props: true
  },
  {
    path: '/anti-forget/:studentId',
    name: 'AntiForgetReview',
    component: AntiForgetReview,
    meta: { title: '抗遗忘复习', requiresAuth: true },
    props: true
  },
  {
    path: '/stats',
    name: 'Stats',
    component: Stats,
    meta: { title: '统计分析', requiresAuth: true, requiresTeacher: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  
  // 初始化认证状态
  if (!authStore.currentUser) {
    authStore.initializeAuth()
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    // 需要认证但未登录，跳转到登录页
    next('/login')
    return
  }
  
  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    // 需要管理员权限但不是管理员，跳转到对应首页
    if (authStore.currentUser?.role === 'teacher') {
      next('/')  // 教师跳转到日程管理
    } else if (authStore.currentUser?.role === 'student') {
      next('/student')
    } else {
      next('/login')
    }
    return
  }

  // 检查是否需要教师权限
  if (to.meta.requiresTeacher && !authStore.currentUser) {
    next('/login')
    return
  }

  if (to.meta.requiresTeacher && (authStore.isAdmin || authStore.isStudent)) {
    // 需要教师权限但是管理员或学生，跳转到对应首页
    if (authStore.isAdmin) {
      next('/admin')
    } else {
      next('/student')
    }
    return
  }

  // 检查是否需要学生权限
  if (to.meta.requiresStudent && !authStore.isStudent) {
    // 需要学生权限但不是学生，跳转到对应首页
    if (authStore.isAdmin) {
      next('/admin')
    } else if (authStore.currentUser?.role === 'teacher') {
      next('/')
    } else {
      next('/login')
    }
    return
  }

  // 检查是否需要访客身份（如登录页）
  if (to.meta.requiresGuest && authStore.isLoggedIn) {
    // 已登录用户访问登录页，跳转到对应首页
    if (authStore.isAdmin) {
      next('/admin')
    } else if (authStore.isStudent) {
      next('/student')
    } else {
      // 教师跳转到日程管理（Dashboard）而不是TeacherHome
      next('/')
    }
    return
  }
  
  next()
})

export default router