<template>
  <div class="student-dashboard">
    <!-- 头部信息 -->
    <div class="dashboard-header">
      <div class="welcome-section">
        <h1>你好，{{ studentName }}！</h1>
        <div class="stats-card">
          <div class="stat-item">
            <div class="stat-label">已学单词</div>
            <div class="stat-value">{{ totalWords }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 复习记录列表 -->
    <div class="reviews-section">
      <h2>复习记录</h2>

      <div v-if="reviews.length === 0" class="empty-state">
        <el-empty description="暂无复习记录" />
      </div>

      <div v-else class="reviews-grid">
        <el-card
          v-for="review in reviews"
          :key="review.id"
          class="review-card"
          shadow="hover"
        >
          <template #header>
            <div class="card-header">
              <span class="review-date">{{ formatDate(review.learnDate) }}</span>
            </div>
          </template>

          <div class="review-info">
            <div class="info-item">
              <span class="info-label">单词库:</span>
              <span class="info-value word-set-name">{{ review.wordSetName }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">单词数:</span>
              <span class="info-value">{{ review.words.length }} 个</span>
            </div>
            <div v-if="review.lastReviewedAt" class="info-item">
              <span class="info-label">最后复习:</span>
              <span class="info-value">{{ formatDateTime(review.lastReviewedAt) }}</span>
            </div>
          </div>

          <div class="review-actions">
            <el-button type="primary" @click="startReview(review.id)">
              <el-icon><Reading /></el-icon>
              开始复习
            </el-button>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Reading } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useStudentReviewsStore } from '@/stores/studentReviews'

const router = useRouter()
const authStore = useAuthStore()
const reviewsStore = useStudentReviewsStore()

const studentName = computed(() => authStore.currentUser?.display_name || '学生')
const studentId = computed(() => authStore.currentUser?.student_id || 0)

// 获取学生的复习记录
const reviews = computed(() => {
  return reviewsStore.getStudentReviews(studentId.value)
})

// 获取已学单词统计
const totalWords = computed(() => {
  const stats = reviewsStore.getStudentWordsStats(studentId.value)
  return stats.totalWords
})

// 格式化日期
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  const month = date.toLocaleString('zh-CN', { month: 'short' })
  const day = date.getDate()
  return `${month} ${day}日`
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 开始复习
const startReview = (reviewId: string) => {
  router.push(`/student-review/${reviewId}`)
}

onMounted(async () => {
  // 加载学生的复习记录
  if (studentId.value > 0) {
    await reviewsStore.fetchStudentReviews(studentId.value)
  }
})
</script>

<style scoped>
.student-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}

.dashboard-header {
  margin-bottom: 40px;
}

.welcome-section h1 {
  font-size: 32px;
  color: #303133;
  margin-bottom: 20px;
}

.stats-card {
  display: flex;
  gap: 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 30px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
}

.stat-item {
  text-align: center;
  color: white;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
}

.reviews-section h2 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 20px;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
}

.reviews-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.review-card {
  transition: all 0.3s ease;
}

.review-card:hover {
  transform: translateY(-4px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.review-date {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.review-info {
  margin: 20px 0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  color: #909399;
  font-size: 14px;
}

.info-value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

.word-set-name {
  color: #409eff;
  font-weight: 600;
  font-size: 15px;
}

.review-actions {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.review-actions .el-button {
  width: 100%;
  font-size: 15px;
  padding: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .student-dashboard {
    padding: 20px 15px;
  }

  .welcome-section h1 {
    font-size: 24px;
  }

  .stats-card {
    flex-direction: column;
    gap: 20px;
  }

  .reviews-grid {
    grid-template-columns: 1fr;
  }
}
</style>
