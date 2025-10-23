<template>
  <div id="app">
    <!-- 版本信息 -->
    <VersionInfo />

    <!-- 登录页面时不显示侧边栏 -->
    <div v-if="isLoginPage" class="login-page">
      <router-view />
    </div>

    <!-- 课程模式（全屏，无导航栏） -->
    <div v-else-if="uiStore.isInCourseMode" class="course-mode">
      <!-- 左上角返回按钮 -->
      <div class="course-return-button">
        <el-button
          type="primary"
          :icon="ArrowLeft"
          @click="returnFromCourse"
          size="large"
          round
        >
          返回
        </el-button>
      </div>
      <router-view :key="$route.fullPath" />
    </div>

    <!-- 学生端布局（无侧边栏） -->
    <el-container v-else-if="authStore.isStudent" class="student-container">
      <el-header class="header">
        <div class="header-content">
          <h3>{{ pageTitle }}</h3>
          <div class="header-actions">
            <!-- 用户信息和操作 -->
            <div class="user-info">
              <el-dropdown @command="handleUserCommand">
                <el-button type="text" class="user-button">
                  <el-icon><Avatar /></el-icon>
                  {{ authStore.currentUser?.displayName }}
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="logout" divided>
                      退出登录
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view :key="$route.fullPath" />
      </el-main>
    </el-container>

    <!-- 主应用布局（教师和管理员） -->
    <el-container v-else class="app-container">
      <!-- 侧边导航 -->
      <el-aside width="250px" class="sidebar">
        <div class="logo">
          <h2>英语陪练系统</h2>
        </div>
        
        <el-menu
          :default-active="$route.path"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <!-- 教师菜单 (只有teacher角色可见) -->
          <template v-if="!authStore.isAdmin">
            <el-menu-item index="/teacher">
              <el-icon><User /></el-icon>
              <span>教师工作台</span>
            </el-menu-item>

            <el-menu-item index="/">
              <el-icon><Calendar /></el-icon>
              <span>日程管理</span>
            </el-menu-item>
            
            <el-menu-item index="/students">
              <el-icon><User /></el-icon>
              <span>学生管理</span>
            </el-menu-item>
            
            <el-menu-item index="/words">
              <el-icon><Document /></el-icon>
              <span>单词管理</span>
            </el-menu-item>
            
            <el-menu-item index="/stats">
              <el-icon><DataAnalysis /></el-icon>
              <span>统计分析</span>
            </el-menu-item>
          </template>
          
          <!-- 管理员菜单 -->
          <template v-if="authStore.isAdmin">
            <el-menu-item index="/admin">
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </el-menu-item>
          </template>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <el-header class="header">
          <div class="header-content">
            <h3>{{ pageTitle }}</h3>
            <div class="header-actions">
              <el-badge :value="todayReviewCount" class="review-badge">
                <el-button type="primary" size="small" @click="showTodayReviews">
                  今日复习
                </el-button>
              </el-badge>
              
              <!-- 用户信息和操作 -->
              <div class="user-info">
                <el-dropdown @command="handleUserCommand">
                  <el-button type="text" class="user-button">
                    <el-icon><Avatar /></el-icon>
                    {{ authStore.currentUser?.displayName }}
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item v-if="authStore.isAdmin" command="admin">
                        系统管理
                      </el-dropdown-item>
                      <el-dropdown-item command="logout" divided>
                        退出登录
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>
        </el-header>
        
        <el-main class="main-content">
          <router-view :key="$route.fullPath" />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Calendar, User, Document, DataAnalysis, Setting, Avatar, ArrowDown, ArrowLeft } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useStudentsStore } from '@/stores/students'
import { useScheduleStore } from '@/stores/schedule'
import { useLearningProgressStore } from '@/stores/learningProgress'
import { useUIStore } from '@/stores/ui'
import VersionInfo from '@/components/VersionInfo.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const studentsStore = useStudentsStore()
const scheduleStore = useScheduleStore()
const progressStore = useLearningProgressStore()
const uiStore = useUIStore()

const todayReviewCount = ref(0)

// 计算属性
const isLoginPage = computed(() => route.path === '/login')

// 页面标题映射
const pageTitles: Record<string, string> = {
  '/': '日程管理',
  '/students': '学生管理',
  '/words': '单词管理',
  '/learning': '学习中心',
  '/stats': '统计分析',
  '/admin': '系统管理',
  '/teacher': '教师工作台',
  '/student': ''
}

const pageTitle = computed(() => {
  // 学生端：不显示任何标题
  if (authStore.isStudent) {
    return ''
  }
  return pageTitles[route.path] || '英语陪练系统'
})

// 方法
const showTodayReviews = () => {
  // TODO: 显示今日需要复习的内容
  console.log('显示今日复习内容')
}

const returnFromCourse = () => {
  const returnPath = uiStore.courseReturnPath
  uiStore.temporaryExitCourseMode() // 临时退出，保留计时
  router.push(returnPath)
}

const handleUserCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (command === 'admin') {
    router.push('/admin')
  }
}

// 用户切换时重新加载数据
watch(() => authStore.currentUser, (newUser, oldUser) => {
  if (newUser && oldUser && newUser.id !== oldUser.id) {
    // 用户切换，重新加载所有Store的用户数据
    studentsStore.reloadUserData()
    scheduleStore.reloadUserData()
    progressStore.reloadUserData()
  }
}, { immediate: false })

// 监听路由变化，自动退出课程模式
watch(() => route.path, (newPath) => {
  // 定义学习相关的路径模式
  const learningPaths = [
    '/study/',
    '/simple-study/',
    '/word-check/',
    '/mixed-test/',
    '/post-test/',
    '/anti-forget/',
    '/word-filter/'
  ]

  // 检查当前路径是否为学习相关页面
  const isLearningPage = learningPaths.some(pattern => newPath.includes(pattern))

  // 如果当前在课程模式但不在学习页面，则临时退出课程模式
  if (uiStore.isInCourseMode && !isLearningPage) {
    console.log('路由变化检测到非学习页面，临时退出课程模式:', newPath)
    uiStore.temporaryExitCourseMode()
  }
}, { immediate: false })

onMounted(() => {
  // 初始化认证状态
  authStore.initializeAuth()

  // TODO: 获取今日复习数量
  todayReviewCount.value = 5

  // 添加调试信息
  console.log('App mounted - 当前路由:', route.path)
  console.log('App mounted - 当前用户:', authStore.currentUser)
})

// 监听路由变化进行调试
watch(() => route.path, (newPath, oldPath) => {
  console.log('路由变化:', { from: oldPath, to: newPath })
}, { immediate: false })
</script>

<style scoped>
.login-page {
  width: 100%;
  height: 100vh;
}

.app-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
}

.logo {
  padding: 20px;
  text-align: center;
  color: #bfcbd9;
  border-bottom: 1px solid #434a50;
}

.logo h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-content h3 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.review-badge {
  margin-right: 10px;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-button {
  font-size: 14px;
  color: #606266;
  padding: 8px 12px;
}

.user-button:hover {
  background-color: #f5f7fa;
}

.main-content {
  background-color: #f5f5f5;
  padding: 20px;
}

/* 课程模式样式 */
.course-mode {
  width: 100%;
  height: 100vh;
  background-color: #f5f5f5;
  position: relative;
}

.course-return-button {
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 1000;
}

/* 学生端布局样式 */
.student-container {
  height: 100vh;
  flex-direction: column;
}

.student-container .header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}

.student-container .main-content {
  background-color: #f5f5f5;
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}
</style>