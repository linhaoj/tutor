<template>
  <div class="listening-lesson">
    <!-- 课程计时器 -->
    <CourseTimer @time-expired="handleTimeExpired" />

    <!-- 顶部栏 -->
    <div class="lesson-header">
      <div class="header-left">
        <h2>{{ studentName }} · 听力课</h2>
        <el-tag v-if="article?.title" type="info" size="small">{{ article.title }}</el-tag>
      </div>
      <div class="header-right">
        <el-button size="small" plain @click="toggleAllEnglish">
          {{ allEnglishVisible ? '隐藏全英文' : '显示全英文' }}
        </el-button>
        <el-button size="small" plain @click="toggleAllChinese">
          {{ allChineseVisible ? '隐藏全中文' : '显示全中文' }}
        </el-button>
        <el-button
          :icon="notesVisible ? ArrowRight : ArrowLeft"
          @click="notesVisible = !notesVisible"
          size="small"
          type="info"
          plain
        >
          {{ notesVisible ? '收起备忘录' : '展开备忘录' }}
        </el-button>
        <el-button type="danger" @click="handleEndLesson" size="small">结束课程</el-button>
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="lesson-body" :class="{ 'with-notes': notesVisible }">
      <!-- 内容区域 -->
      <div class="article-area">
        <div v-if="loading" class="loading-state">
          <el-icon class="is-loading" :size="40"><Loading /></el-icon>
          <p>加载听力材料中...</p>
        </div>

        <div v-else-if="!article" class="error-state">
          <el-empty description="未找到该课程的听力材料" />
        </div>

        <div v-else class="article-content">
          <div
            v-for="(paragraph, pIdx) in paragraphs"
            :key="pIdx"
            class="paragraph-block"
            :class="{ active: currentParagraphIndex === pIdx }"
          >
            <div class="para-en-row">
              <el-button
                circle
                size="small"
                :icon="VideoPlay"
                class="para-play-btn"
                @click.stop="seekToParagraph(pIdx)"
                title="播放这一句"
              />
              <p
                v-if="englishVisible[pIdx]"
                class="para-en"
                v-html="renderParagraph(paragraph)"
                @mouseup="handleWordSelect($event)"
                @click="onEnglishTextClick($event, pIdx)"
              />
              <p
                v-else
                class="para-en para-hidden"
                @click="toggleEnglish(pIdx)"
              >
                [ 点击显示英文 ]
              </p>
            </div>

            <div class="para-zh-row">
              <div class="para-play-btn-placeholder" />
              <p
                v-if="chineseVisible[pIdx]"
                class="para-zh"
                @click="toggleChinese(pIdx)"
              >
                {{ article.translation?.[pIdx] || '' }}
              </p>
              <p
                v-else
                class="para-zh para-hidden"
                @click="toggleChinese(pIdx)"
              >
                [ 点击显示中文 ]
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 备忘录区域 -->
      <div v-show="notesVisible" class="notes-area">
        <div class="notes-header">
          <span>课堂备忘录</span>
          <div class="notes-font-controls">
            <el-button size="small" text @click="notesFontSize = Math.max(12, notesFontSize - 1)">A-</el-button>
            <span class="font-size-label">{{ notesFontSize }}px</span>
            <el-button size="small" text @click="notesFontSize = Math.min(28, notesFontSize + 1)">A+</el-button>
          </div>
        </div>
        <el-input
          v-model="notes"
          type="textarea"
          :rows="20"
          placeholder="在这里记录课堂笔记..."
          class="notes-textarea"
          resize="none"
          :inputStyle="{ fontSize: notesFontSize + 'px', lineHeight: '1.8' }"
        />
      </div>
    </div>

    <!-- 底部播放控件 -->
    <AudioPlayerBar
      v-if="article"
      ref="playerBar"
      :src="article.audio_url"
      :disable-prev="currentParagraphIndex <= 0"
      :disable-next="currentParagraphIndex >= paragraphs.length - 1"
      @timeupdate="onAudioTimeUpdate"
      @prev="goToPrevSentence"
      @next="goToNextSentence"
    />

    <!-- 单词气泡弹窗 -->
    <div
      v-if="wordPopup.visible"
      class="word-popup"
      :style="{ top: wordPopup.y + 'px', left: wordPopup.x + 'px' }"
    >
      <div class="popup-word">{{ wordPopup.word }}</div>
      <div class="popup-actions">
        <el-button size="small" type="success" @click="lookupWord" :loading="wordPopup.loading">
          词典
        </el-button>
        <el-button
          v-if="isWordAdded"
          size="small"
          type="danger"
          @click="removeFromAntiForget"
        >
          − 删除抗遗忘
        </el-button>
        <el-button
          v-else
          size="small"
          type="primary"
          @click="addToAntiForget"
        >
          + 抗遗忘
        </el-button>
        <el-button size="small" text @click="closePopup">✕</el-button>
      </div>
      <div v-if="wordPopup.meaning" class="popup-meaning">
        <span class="meaning-text">{{ wordPopup.meaning }}</span>
      </div>
    </div>

    <!-- 结课审查弹窗 -->
    <el-dialog
      v-model="reviewDialogVisible"
      title="结束课程 - 审查抗遗忘单词"
      width="560px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <div class="review-content">
        <p style="color: #606266; margin-bottom: 16px">
          以下单词将加入抗遗忘计划。请确认中文意思是否正确，可直接编辑。
        </p>

        <div v-if="antiForgetWords.length === 0" class="empty-anti-forget">
          <el-empty description="本次课程没有添加抗遗忘单词" :image-size="80" />
        </div>

        <div v-else class="anti-forget-list">
          <div
            v-for="(word, idx) in antiForgetWords"
            :key="idx"
            class="anti-forget-item"
          >
            <span class="af-english">{{ word.english }}</span>
            <el-input
              v-model="antiForgetWords[idx].chinese"
              size="small"
              placeholder="中文意思"
              class="af-chinese-input"
            />
            <el-button
              size="small"
              type="danger"
              text
              @click="antiForgetWords.splice(idx, 1)"
            >删除</el-button>
          </div>
        </div>

        <div v-if="antiForgetWords.length > 0" class="anti-forget-time">
          <label>抗遗忘上课时间：</label>
          <el-select v-model="antiForgetTime" placeholder="选择时间" style="width: 140px">
            <el-option
              v-for="slot in timeSlots"
              :key="slot"
              :label="slot"
              :value="slot"
            />
          </el-select>
        </div>
      </div>

      <template #footer>
        <el-button @click="reviewDialogVisible = false" :disabled="endingLesson">
          返回课程
        </el-button>
        <el-button @click="skipAntiForget" :loading="endingLesson">
          {{ antiForgetWords.length === 0 ? '结束课程' : '跳过抗遗忘，直接结束' }}
        </el-button>
        <el-button
          v-if="antiForgetWords.length > 0"
          type="primary"
          @click="confirmEndLesson"
          :loading="endingLesson"
          :disabled="!antiForgetTime"
        >
          创建抗遗忘并结束
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Loading, VideoPlay } from '@element-plus/icons-vue'
import { useListeningStore } from '@/stores/listening'
import { useStudentsStore } from '@/stores/students'
import { useScheduleStore } from '@/stores/schedule'
import { useUIStore } from '@/stores/ui'
import CourseTimer from '@/components/CourseTimer.vue'
import AudioPlayerBar from '@/components/AudioPlayerBar.vue'

const route = useRoute()
const router = useRouter()
const listeningStore = useListeningStore()
const studentsStore = useStudentsStore()
const scheduleStore = useScheduleStore()
const uiStore = useUIStore()

// 响应式数据
const studentName = ref('')
const article = ref<any>(null)
const loading = ref(true)
const notesVisible = ref(false)
const notes = ref('')
const reviewDialogVisible = ref(false)
const endingLesson = ref(false)
const antiForgetTime = ref('')
const notesFontSize = ref(14)
const currentParagraphIndex = ref(-1)
const playerBar = ref<InstanceType<typeof AudioPlayerBar>>()

const antiForgetWords = ref<Array<{ english: string; chinese: string }>>([])

const wordPopup = reactive({
  visible: false,
  word: '',
  meaning: '',
  loading: false,
  x: 0,
  y: 0,
})

// 计算段落：按单个换行分段（听力课的换行本身决定分段和时间戳切分，不是双换行/空行）
const paragraphs = computed(() => {
  if (!article.value?.article_content) return []
  return article.value.article_content
    .split(/\n/)
    .map((p: string) => p.trim())
    .filter((p: string) => p.length > 0)
})

// 每句英文/中文的显示状态，默认全部显示；文章加载后按段落数初始化
const englishVisible = ref<boolean[]>([])
const chineseVisible = ref<boolean[]>([])

// 顶部"隐藏/显示全英文"、"隐藏/显示全中文"按钮的状态：只要还有一句被隐藏就算"未全部显示"
const allEnglishVisible = computed(() => englishVisible.value.length > 0 && englishVisible.value.every(v => v))
const allChineseVisible = computed(() => chineseVisible.value.length > 0 && chineseVisible.value.every(v => v))

const initVisibilityState = () => {
  englishVisible.value = paragraphs.value.map(() => true)
  chineseVisible.value = paragraphs.value.map(() => true)
}

const toggleEnglish = (pIdx: number) => {
  englishVisible.value[pIdx] = !englishVisible.value[pIdx]
}

const toggleChinese = (pIdx: number) => {
  chineseVisible.value[pIdx] = !chineseVisible.value[pIdx]
}

const toggleAllEnglish = () => {
  const next = !allEnglishVisible.value
  englishVisible.value = englishVisible.value.map(() => next)
}

const toggleAllChinese = () => {
  const next = !allChineseVisible.value
  chineseVisible.value = chineseVisible.value.map(() => next)
}

// 已添加抗遗忘的单词（蓝色高亮）
const addedWords = computed(() => {
  return new Set(antiForgetWords.value.map(w => w.english.toLowerCase()))
})

const isWordAdded = computed(() => {
  if (!wordPopup.word) return false
  return addedWords.value.has(wordPopup.word.toLowerCase())
})

const timeSlots = computed(() => {
  const slots = []
  for (let h = 6; h <= 22; h++) {
    slots.push(`${String(h).padStart(2, '0')}:00`)
    if (h < 22) slots.push(`${String(h).padStart(2, '0')}:30`)
  }
  return slots
})

// 渲染段落：已添加抗遗忘单词标蓝
const renderParagraph = (text: string): string => {
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  html = html.replace(/\b([a-zA-Z']+)\b/g, (match) => {
    const lower = match.toLowerCase()
    if (addedWords.value.has(lower)) {
      return `<span class="word-token af-word" data-word="${match}">${match}</span>`
    } else {
      return `<span class="word-token" data-word="${match}">${match}</span>`
    }
  })

  return html
}

// 点击英文段落文字：如果点在具体单词上（用于查词），不切换隐藏；
// 点在单词之间的空白/标点区域，才切换这句英文的隐藏/显示
const onEnglishTextClick = (event: MouseEvent, pIdx: number) => {
  const target = event.target as HTMLElement
  if (target.closest('[data-word]')) return
  toggleEnglish(pIdx)
}

// 跳转音频到指定段落的时间戳播放（供"上一句/下一句"按钮调用）
const seekToParagraph = (pIdx: number) => {
  const ts = article.value?.paragraph_timestamps?.[pIdx]
  if (!ts || !playerBar.value) return
  currentParagraphIndex.value = pIdx
  playerBar.value.seekTo(ts.start)
}

const goToPrevSentence = () => {
  if (currentParagraphIndex.value <= 0) return
  seekToParagraph(currentParagraphIndex.value - 1)
}

const goToNextSentence = () => {
  if (currentParagraphIndex.value >= paragraphs.value.length - 1) return
  seekToParagraph(currentParagraphIndex.value + 1)
}

// 播放进度更新：找到当前播放位置对应的段落，驱动高亮
const onAudioTimeUpdate = (currentTime: number) => {
  const timestamps = article.value?.paragraph_timestamps
  if (!timestamps) return

  let matchedIdx = -1
  for (const ts of timestamps) {
    if (currentTime >= ts.start && currentTime < ts.end) {
      matchedIdx = ts.index
      break
    }
  }
  // 落在两段之间的空隙时，保持上一段高亮，不清空
  if (matchedIdx !== -1) {
    currentParagraphIndex.value = matchedIdx
  }
}

// 双击/选择单词处理
const handleWordSelect = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  const wordEl = target.closest('[data-word]') as HTMLElement
  if (!wordEl) {
    closePopup()
    return
  }

  const word = wordEl.dataset.word || ''
  if (!word || !/^[a-zA-Z']+$/.test(word)) return

  const rect = wordEl.getBoundingClientRect()
  const containerRect = document.querySelector('.listening-lesson')?.getBoundingClientRect()

  wordPopup.word = word
  wordPopup.meaning = ''
  wordPopup.loading = false
  wordPopup.visible = true
  wordPopup.x = rect.left - (containerRect?.left || 0) + rect.width / 2
  wordPopup.y = rect.bottom - (containerRect?.top || 0) + 8
}

const lookupWord = async () => {
  if (!wordPopup.word || !article.value) return
  wordPopup.loading = true
  try {
    const result = await listeningStore.lookupWord(
      wordPopup.word,
      article.value.article_content
    )
    wordPopup.meaning = result.chinese_meaning
  } catch {
    ElMessage.error('查词失败，请重试')
  } finally {
    wordPopup.loading = false
  }
}

const addToAntiForget = () => {
  const word = wordPopup.word
  if (!word) return

  if (antiForgetWords.value.some(w => w.english.toLowerCase() === word.toLowerCase())) {
    ElMessage.warning(`"${word}" 已在抗遗忘列表中`)
    closePopup()
    return
  }

  const newItem = { english: word, chinese: wordPopup.meaning || '' }
  antiForgetWords.value.push(newItem)
  ElMessage.success(`"${word}" 已添加到抗遗忘列表`)
  closePopup()

  if (!newItem.chinese && article.value) {
    listeningStore.lookupWord(word, article.value.article_content).then(result => {
      newItem.chinese = result.chinese_meaning
    }).catch(() => {
      // 查失败静默处理，让老师手动填
    })
  }
}

const removeFromAntiForget = () => {
  const word = wordPopup.word
  if (!word) return

  const idx = antiForgetWords.value.findIndex(w => w.english.toLowerCase() === word.toLowerCase())
  if (idx === -1) return

  antiForgetWords.value.splice(idx, 1)
  ElMessage.success(`"${word}" 已从抗遗忘列表移除`)
  closePopup()
}

const closePopup = () => {
  wordPopup.visible = false
  wordPopup.word = ''
  wordPopup.meaning = ''
}

const handleDocumentClick = (e: MouseEvent) => {
  const popup = document.querySelector('.word-popup')
  if (popup && !popup.contains(e.target as Node)) {
    const wordEl = (e.target as HTMLElement).closest('[data-word]')
    if (!wordEl) closePopup()
  }
}

const handleEndLesson = async () => {
  reviewDialogVisible.value = true

  const missing = antiForgetWords.value.filter(w => !w.chinese || w.chinese === '（待填写）')
  if (missing.length > 0 && article.value) {
    for (const item of missing) {
      try {
        const result = await listeningStore.lookupWord(item.english, article.value.article_content)
        item.chinese = result.chinese_meaning
      } catch {
        // 查失败就留空让老师填
      }
    }
  }
}

const handleTimeExpired = () => {
  ElMessage.warning('课程时间已到，请结束课程')
  reviewDialogVisible.value = true
}

const skipAntiForget = async () => {
  endingLesson.value = true
  try {
    await downloadNotesPDF()
    await completeCourse()
    uiStore.endCourse()
    router.push('/')
  } finally {
    endingLesson.value = false
  }
}

const confirmEndLesson = async () => {
  if (!antiForgetTime.value) {
    ElMessage.warning('请选择抗遗忘上课时间')
    return
  }
  endingLesson.value = true
  try {
    await downloadNotesPDF()
    await completeCourse()

    const studentId = parseInt(route.params.studentId as string)
    const words = antiForgetWords.value.map((w, idx) => ({
      id: idx,
      english: w.english,
      chinese: w.chinese,
      originalIndex: idx
    }))

    sessionStorage.setItem('filteredWords', JSON.stringify(words))

    const tempWordSet = `listening-af-${Date.now()}`
    const teacherId = String(authStoreTeacherId())

    uiStore.endCourse()

    router.push({
      name: 'SimpleWordStudy',
      params: { studentId },
      query: {
        wordSet: tempWordSet,
        wordsCount: Math.min(words.length, 5),
        startIndex: 0,
        groupNumber: 1,
        totalWords: words.length,
        teacherId,
        filtered: 'true',
        skipProgress: 'true',
        antiForgetTime: antiForgetTime.value
      }
    })
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '进入抗遗忘学习失败')
  } finally {
    endingLesson.value = false
  }
}

const authStoreTeacherId = () => {
  const raw = localStorage.getItem('current_user')
  if (!raw) return ''
  try {
    return JSON.parse(raw).id || ''
  } catch {
    return ''
  }
}

const completeCourse = async () => {
  try {
    const scheduleIdStr = sessionStorage.getItem('currentScheduleId')
    if (!scheduleIdStr) return
    await scheduleStore.completeSchedule(parseInt(scheduleIdStr))
  } catch (e) {
    console.error('标记课程完成失败:', e)
  }
}

// 下载备忘录 PDF：包含听力原文+中文翻译、课堂笔记、抗遗忘单词表
const downloadNotesPDF = async () => {
  const hasNotes = notes.value.trim().length > 0
  const hasArticle = !!article.value?.article_content
  const hasWords = antiForgetWords.value.length > 0
  if (!hasNotes && !hasArticle && !hasWords) return

  try {
    const [jsPDFModule, html2canvasModule] = await Promise.all([
      import('jspdf'),
      import('html2canvas')
    ])
    const jsPDF = jsPDFModule.jsPDF || jsPDFModule.default
    const html2canvas = html2canvasModule.default

    const dateStr = new Date().toLocaleDateString('zh-CN')
    const escapeHtml = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

    const articleParasHtml = paragraphs.value
      .map((p: string, idx: number) => {
        const translation = article.value?.translation?.[idx] || ''
        return `
          <div style="margin-bottom: 14px;">
            <p style="margin: 0 0 4px 0; line-height: 1.7;">${escapeHtml(p)}</p>
            ${translation ? `<p style="margin: 0; line-height: 1.7; color: #67c23a;">${escapeHtml(translation)}</p>` : ''}
          </div>
        `
      }).join('')

    const wordsHtml = antiForgetWords.value.map(w => `
      <div style="display: flex; padding: 6px 0; border-bottom: 1px solid #eee;">
        <span style="width: 140px; font-weight: bold;">${escapeHtml(w.english)}</span>
        <span>${escapeHtml(w.chinese || '')}</span>
      </div>
    `).join('')

    const tempDiv = document.createElement('div')
    tempDiv.style.cssText = `
      position: absolute; left: -9999px; top: 0;
      width: 800px; padding: 40px;
      font-family: 'PingFang SC', 'Microsoft YaHei', 'Heiti SC', Arial, sans-serif;
      background: white; color: #333; font-size: 15px;
    `
    tempDiv.innerHTML = `
      <h2 style="margin: 0 0 4px 0; color: #303133;">课堂备忘录</h2>
      <p style="color: #909399; margin: 0 0 24px 0; font-size: 13px;">
        学生：${escapeHtml(studentName.value)} | ${article.value?.title ? '材料：' + escapeHtml(article.value.title) + ' | ' : ''}日期：${dateStr}
      </p>

      ${hasArticle ? `
        <h3 style="color: #303133; border-bottom: 2px solid #409eff; padding-bottom: 6px;">听力原文</h3>
        <div style="margin-bottom: 24px;">${articleParasHtml}</div>
      ` : ''}

      ${hasNotes ? `
        <h3 style="color: #303133; border-bottom: 2px solid #409eff; padding-bottom: 6px;">课堂笔记</h3>
        <div style="white-space: pre-wrap; line-height: 1.8; margin-bottom: 24px;">${escapeHtml(notes.value)}</div>
      ` : ''}

      ${hasWords ? `
        <h3 style="color: #303133; border-bottom: 2px solid #409eff; padding-bottom: 6px;">抗遗忘单词</h3>
        <div style="margin-top: 8px;">${wordsHtml}</div>
      ` : ''}
    `
    document.body.appendChild(tempDiv)

    if (document.fonts && document.fonts.ready) {
      await document.fonts.ready
    }
    await new Promise(r => setTimeout(r, 200))
    const canvas = await html2canvas(tempDiv, {
      scale: 2, useCORS: true, backgroundColor: '#ffffff', logging: false,
      letterRendering: true
    })
    document.body.removeChild(tempDiv)

    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    const imgWidth = 210
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    const pageHeight = 297

    const imgData = canvas.toDataURL('image/png')
    let heightLeft = imgHeight
    let position = 0

    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= pageHeight

    while (heightLeft > 0) {
      position = heightLeft - imgHeight
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
    }

    const fileDateStr = new Date().toISOString().split('T')[0]
    pdf.save(`课堂备忘录_${studentName.value}_${fileDateStr}.pdf`)
  } catch (e) {
    console.error('PDF 生成失败:', e)
  }
}

onMounted(async () => {
  if (!uiStore.isInCourseMode) {
    uiStore.enterCourseMode('/')
  }

  const studentId = parseInt(route.params.studentId as string)
  const scheduleId = parseInt(route.query.scheduleId as string || sessionStorage.getItem('currentScheduleId') || '0')

  await studentsStore.fetchStudents()
  const student = studentsStore.students.find(s => s.id === studentId)
  if (student) studentName.value = student.name

  try {
    article.value = await listeningStore.getArticleBySchedule(scheduleId)
    if (!article.value) {
      ElMessage.error('未找到该课程的听力材料')
    } else {
      initVisibilityState()
    }
  } catch {
    ElMessage.error('未找到该课程的听力材料')
  } finally {
    loading.value = false
  }

  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<style scoped>
.listening-lesson {
  position: relative;
  min-height: 100vh;
  background: #f7f8f6;
  display: flex;
  flex-direction: column;
  padding-bottom: 60px; /* 留出底部播放条空间 */
}

.lesson-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.header-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.lesson-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 0;
}

.lesson-body.with-notes .article-area {
  flex: 1;
  border-right: 1px solid #e4e7ed;
}

.article-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  max-width: 900px;
  margin: 0 auto;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: #909399;
  gap: 16px;
}

.paragraph-block {
  margin-bottom: 32px;
  padding: 12px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.paragraph-block:hover {
  background: #f0f4ff;
}

.paragraph-block.active {
  background: #e8f2ff;
  box-shadow: inset 3px 0 0 #409eff;
}

.para-en-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.para-zh-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.para-play-btn {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  margin-top: 2px;
}

.para-play-btn-placeholder {
  flex-shrink: 0;
  width: 24px;
}

.para-en {
  flex: 1;
  font-size: 17px;
  line-height: 1.9;
  color: #303133;
  margin: 0 0 14px 0;
  word-wrap: break-word;
}

.para-zh {
  flex: 1;
  font-size: 15px;
  line-height: 1.8;
  color: #67c23a;
  margin: 0;
  cursor: pointer;
}

.para-hidden {
  color: #c0c4cc;
  font-style: italic;
  cursor: pointer;
  user-select: none;
}

.para-en :deep(.word-token) {
  cursor: pointer;
  border-radius: 2px;
  transition: background 0.15s;
}

.para-en :deep(.word-token:hover) {
  background: #e8f4ff;
}

.para-en :deep(.af-word) {
  background: #d4edff;
  font-weight: 600;
  padding: 0 1px;
  border-bottom: 2px solid #409eff;
}

.notes-area {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #fffef5;
  border-left: 1px solid #e4e7ed;
}

.notes-header {
  padding: 8px 12px;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
  border-bottom: 1px solid #e4e7ed;
  background: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notes-font-controls {
  display: flex;
  align-items: center;
  gap: 2px;
}

.font-size-label {
  font-size: 12px;
  color: #909399;
  min-width: 32px;
  text-align: center;
}

.notes-textarea {
  flex: 1;
}

.notes-textarea :deep(.el-textarea__inner) {
  height: 100%;
  border: none;
  border-radius: 0;
  background: #fffef5;
  font-size: 14px;
  line-height: 1.8;
  resize: none;
  padding: 16px;
}

.word-popup {
  position: absolute;
  z-index: 1000;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: 10px 12px;
  min-width: 180px;
  transform: translateX(-50%);
}

.popup-word {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
  text-align: center;
}

.popup-actions {
  display: flex;
  gap: 6px;
  justify-content: center;
  align-items: center;
}

.popup-meaning {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
  font-size: 14px;
  color: #409eff;
  text-align: center;
}

.anti-forget-list {
  max-height: 280px;
  overflow-y: auto;
}

.anti-forget-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.af-english {
  font-weight: 600;
  color: #303133;
  min-width: 120px;
  font-size: 15px;
}

.af-chinese-input {
  flex: 1;
}

.anti-forget-time {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.anti-forget-time label {
  font-size: 14px;
  color: #606266;
}

.empty-anti-forget {
  padding: 20px 0;
}
</style>
