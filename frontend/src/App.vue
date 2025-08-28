<template>
  <div id="app">
    <el-container class="app-container">
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
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Calendar, User, Document, Reading, DataAnalysis } from '@element-plus/icons-vue'

const route = useRoute()
const todayReviewCount = ref(0)

// 页面标题映射
const pageTitles: Record<string, string> = {
  '/': '日程管理',
  '/students': '学生管理',
  '/words': '单词管理',
  '/learning': '学习中心',
  '/stats': '统计分析'
}

const pageTitle = computed(() => {
  return pageTitles[route.path] || '英语陪练系统'
})

const showTodayReviews = () => {
  // TODO: 显示今日需要复习的内容
  console.log('显示今日复习内容')
}

onMounted(() => {
  // TODO: 获取今日复习数量
  todayReviewCount.value = 5
})
</script>

<style scoped>
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

.main-content {
  background-color: #f5f5f5;
  padding: 20px;
}
</style>