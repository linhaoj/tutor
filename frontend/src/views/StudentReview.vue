<template>
  <div class="student-review">
    <!-- 头部信息 -->
    <div class="review-header">
      <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
      <div class="header-info">
        <h2>{{ reviewInfo.wordSetName }}</h2>
        <span class="review-date">{{ formatDate(reviewInfo.learnDate) }}</span>
      </div>
      <div class="word-count">{{ reviewInfo.words.length }} 个单词</div>
    </div>

    <!-- 单词卡片列表 -->
    <div class="words-container">
      <div
        v-for="(word, index) in reviewInfo.words"
        :key="word.id"
        class="word-card-wrapper"
      >
        <div
          class="word-card"
          :class="{ 'show-chinese': word.showChinese, 'starred': word.is_starred }"
          @click="toggleDisplay(index)"
        >
          <div class="word-content">
            <div class="word-text">
              {{ word.showChinese ? word.chinese : word.english }}
            </div>
            <div class="word-number">#{{ index + 1 }}</div>
          </div>

          <!-- 星星标记按钮 -->
          <div class="star-button" @click.stop="toggleStar(index)">
            <el-icon :size="24" :class="{ 'starred': word.is_starred }">
              <StarFilled v-if="word.is_starred" />
              <Star v-else />
            </el-icon>
          </div>
        </div>

        <!-- 发音按钮 -->
        <div class="word-actions">
          <el-button
            type="primary"
            :icon="Promotion"
            circle
            size="small"
            @click="speakWord(word.english)"
            title="发音"
          />
        </div>
      </div>
    </div>

    <!-- 底部统计 -->
    <div class="review-footer">
      <div class="starred-count">
        <el-icon><StarFilled /></el-icon>
        已标记 {{ starredCount }} 个重点单词
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Star, StarFilled, Promotion } from '@element-plus/icons-vue'
import { useStudentReviewsStore, type ReviewWord } from '@/stores/studentReviews'

const route = useRoute()
const router = useRouter()
const reviewsStore = useStudentReviewsStore()

// 复习信息
interface ReviewInfo {
  id: string
  wordSetName: string
  learnDate: string
  words: (ReviewWord & { showChinese?: boolean })[]
}

const reviewInfo = ref<ReviewInfo>({
  id: '',
  wordSetName: '',
  learnDate: '',
  words: []
})

// 已标记的单词数量
const starredCount = computed(() => {
  return reviewInfo.value.words.filter(w => w.is_starred).length
})

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// 切换单词显示（中英文）
const toggleDisplay = (index: number) => {
  const word = reviewInfo.value.words[index]
  if (word) {
    word.showChinese = !word.showChinese
  }
}

// 切换星标
const toggleStar = async (index: number) => {
  const word = reviewInfo.value.words[index]
  if (word) {
    // 调用API切换星标
    const newState = await reviewsStore.toggleWordStar(reviewInfo.value.id, word.id)

    // 更新本地显示
    word.is_starred = newState

    const message = newState ? '已标记为重点' : '取消重点标记'
    ElMessage.success(message)
  }
}

// 发音功能
const speakWord = (text: string) => {
  try {
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'en-US'
    utterance.rate = 0.8 // 语速
    window.speechSynthesis.speak(utterance)
  } catch (error) {
    console.error('发音失败:', error)
    ElMessage.warning('发音功能不可用')
  }
}

// 返回
const goBack = () => {
  router.back()
}

// 初始化
onMounted(async () => {
  const reviewId = route.params.reviewId as string

  if (!reviewId) {
    ElMessage.error('复习记录不存在')
    router.back()
    return
  }

  // 从服务器获取最新数据
  const review = await reviewsStore.fetchReview(reviewId)

  if (!review) {
    ElMessage.error('复习记录不存在')
    router.back()
    return
  }

  // 加载复习数据
  reviewInfo.value = {
    id: review.id,
    wordSetName: review.word_set_name,
    learnDate: review.learn_date,
    words: review.words.map(w => ({
      ...w,
      showChinese: false
    }))
  }

  ElMessage.success(`开始复习 ${review.words.length} 个单词`)
})
</script>

<style scoped>
.student-review {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  background-color: #fefefe;
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.header-info {
  flex: 1;
  text-align: center;
}

.header-info h2 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 24px;
}

.review-date {
  color: #909399;
  font-size: 14px;
}

.word-count {
  font-size: 16px;
  color: #409eff;
  font-weight: 600;
}

.words-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 30px;
}

.word-card-wrapper {
  display: flex;
  align-items: center;
  gap: 15px;
}

.word-card {
  flex: 1;
  background: linear-gradient(135deg, #81c784 0%, #66bb6a 100%);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 100px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border: 2px solid rgba(129, 199, 132, 0.3);
  box-shadow: 0 4px 12px rgba(129, 199, 132, 0.2);
  position: relative;
}

.word-card:hover {
  background: linear-gradient(135deg, #66bb6a 0%, #4caf50 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.3);
}

.word-card.show-chinese {
  background: linear-gradient(135deg, #64b5f6 0%, #42a5f5 100%);
  border-color: rgba(100, 181, 246, 0.3);
}

.word-card.starred {
  box-shadow: 0 4px 16px rgba(255, 193, 7, 0.4);
  border-color: rgba(255, 193, 7, 0.5);
}

.word-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 40px;
}

.word-text {
  font-size: 24px;
  font-weight: 600;
  color: #1b5e20;
  text-align: left;
  line-height: 1.4;
  word-break: break-word;
  flex: 1;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.7);
}

.show-chinese .word-text {
  color: #0d47a1;
}

.word-number {
  font-size: 14px;
  color: #2e7d32;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.7);
}

.star-button {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: #ffc107;
  transition: all 0.2s ease;
  z-index: 10;
}

.star-button:hover {
  transform: translateY(-50%) scale(1.2);
}

.star-button .el-icon {
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.star-button .el-icon.starred {
  color: #ffc107;
  animation: star-pulse 0.3s ease-in-out;
}

@keyframes star-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.3); }
}

.word-actions {
  display: flex;
  gap: 10px;
}

.review-footer {
  position: sticky;
  bottom: 0;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.starred-count {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  color: #303133;
  font-weight: 500;
}

.starred-count .el-icon {
  color: #ffc107;
  font-size: 20px;
}

/* 响应式设计 - 平板 */
@media (max-width: 768px) {
  .student-review {
    padding: 15px;
  }

  .review-header {
    flex-direction: column;
    gap: 15px;
  }

  .header-info h2 {
    font-size: 20px;
  }

  .word-card-wrapper {
    flex-direction: column;
    gap: 10px;
  }

  .word-text {
    font-size: 20px;
  }

  .word-actions {
    width: 100%;
    justify-content: center;
  }
}

/* 响应式设计 - 手机 */
@media (max-width: 480px) {
  .student-review {
    padding: 10px;
  }

  /* 头部优化 */
  .review-header {
    padding: 15px;
    margin-bottom: 20px;
  }

  .header-info h2 {
    font-size: 18px;
    margin-bottom: 6px;
  }

  .review-date {
    font-size: 13px;
  }

  .word-count {
    font-size: 15px;
  }

  /* 单词列表优化 */
  .words-container {
    gap: 15px;
    margin-bottom: 20px;
  }

  .word-card-wrapper {
    gap: 12px;
  }

  /* 单词卡片优化 - 增大便于点击和阅读 */
  .word-card {
    min-height: 120px;
    padding: 20px;
    border-radius: 12px;
  }

  .word-text {
    font-size: 22px; /* 增大字体便于手机阅读 */
    font-weight: 700;
  }

  .word-number {
    font-size: 13px;
  }

  /* 星标按钮优化 - 增大点击区域 */
  .star-button {
    right: 15px;
  }

  .star-button .el-icon {
    font-size: 28px; /* 增大星标图标 */
  }

  /* 发音按钮优化 - 增大便于点击 */
  .word-actions {
    justify-content: center;
  }

  .word-actions .el-button {
    width: 56px !important;
    height: 56px !important;
    font-size: 24px;
  }

  /* 底部统计 */
  .review-footer {
    padding: 15px;
  }

  .starred-count {
    font-size: 15px;
  }

  .starred-count .el-icon {
    font-size: 18px;
  }
}

/* 超小屏幕优化 */
@media (max-width: 375px) {
  .header-info h2 {
    font-size: 16px;
  }

  .word-card {
    min-height: 100px;
    padding: 18px;
  }

  .word-text {
    font-size: 20px;
  }

  .star-button .el-icon {
    font-size: 24px;
  }

  .word-actions .el-button {
    width: 50px !important;
    height: 50px !important;
    font-size: 20px;
  }
}
</style>
