<template>
  <div id="app">
    <!-- 登录页面时不显示侧边栏 -->
    <div v-if="isLoginPage" class="login-page">
      <router-view />
    </div>
    
    <!-- 主应用布局 -->
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
          <!-- 老师菜单 (只有teacher角色可见) -->
          <template v-if="!authStore.isAdmin">
            <el-menu-item index="/teacher">
              <el-icon><User /></el-icon>
              <span>老师工作台</span>
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
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Calendar, User, Document, DataAnalysis, Setting, Avatar, ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useStudentsStore } from '@/stores/students'
import { useScheduleStore } from '@/stores/schedule'
import { useLearningProgressStore } from '@/stores/learningProgress'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const studentsStore = useStudentsStore()
const scheduleStore = useScheduleStore()
const progressStore = useLearningProgressStore()

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
  '/teacher': '老师工作台'
}

const pageTitle = computed(() => {
  return pageTitles[route.path] || '英语陪练系统'
})

// 方法
const showTodayReviews = () => {
  // TODO: 显示今日需要复习的内容
  console.log('显示今日复习内容')
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

onMounted(() => {
  // 初始化认证状态
  authStore.initializeAuth()
  
  // TODO: 获取今日复习数量
  todayReviewCount.value = 5
})
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
</style>