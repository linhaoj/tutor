<template>
  <div class="dashboard-page">
    <div class="page-header">
      <h1>日程管理</h1>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        添加课程
      </el-button>
    </div>

    <!-- 日程按日期分组 -->
    <div class="schedule-groups">
      <div 
        v-for="dateGroup in groupedSchedules" 
        :key="dateGroup.date"
        class="date-group"
      >
        <div 
          class="date-header" 
          @click="toggleDateGroup(dateGroup.date)"
        >
          <el-icon class="expand-icon" :class="{ expanded: dateGroup.expanded }">
            <ArrowRight />
          </el-icon>
          <span class="date-text">{{ formatDate(dateGroup.date) }}</span>
          <span class="course-count">{{ dateGroup.schedules.length }} 门课程</span>
        </div>
        
        <div v-show="dateGroup.expanded" class="schedule-list">
          <div 
            v-for="schedule in dateGroup.schedules" 
            :key="schedule.id"
            class="schedule-item"
          >
            <div class="schedule-time">{{ schedule.time }}</div>
            <div class="schedule-content">
              <div class="schedule-title">{{ schedule.wordSet }}</div>
              <div class="schedule-student">{{ schedule.studentName }}</div>
              <div class="schedule-type">
                <el-tag 
                  :type="schedule.type === 'review' ? 'warning' : 'success'" 
                  size="small"
                >
                  {{ schedule.type === 'review' ? '抗遗忘' : '单词学习' }}
                </el-tag>
              </div>
            </div>
            <div class="schedule-actions">
              <el-button 
                type="success" 
                @click="startStudy(schedule)"
              >
                {{ schedule.type === 'review' ? '复习' : '学习' }}
              </el-button>
              <el-button 
                size="small" 
                type="danger" 
                @click="deleteSchedule(schedule)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="groupedSchedules.length === 0" class="empty-state">
      <el-empty description="暂无课程安排" />
    </div>

    <!-- 添加课程对话框 -->
    <el-dialog 
      v-model="addDialogVisible" 
      title="添加课程"
      width="500px"
    >
      <el-form :model="courseForm" label-width="100px">
        <el-form-item label="选择学生" required>
          <el-select v-model="courseForm.studentId" placeholder="请选择学生" style="width: 100%">
            <el-option 
              v-for="student in students" 
              :key="student.id" 
              :label="student.name" 
              :value="student.id" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择单词集" required>
          <el-select v-model="courseForm.wordSet" placeholder="请选择单词集" style="width: 100%">
            <el-option 
              v-for="set in wordSets" 
              :key="set.name" 
              :label="set.name" 
              :value="set.name" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="课程类型" required>
          <el-radio-group v-model="courseForm.type">
            <el-radio value="learning">单词学习</el-radio>
            <el-radio value="review">抗遗忘</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="上课日期" required>
          <el-date-picker
            v-model="courseForm.date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="上课时间" required>
  <el-select 
    v-model="courseForm.time" 
    placeholder="选择时间"
    filterable
    allow-create
    style="width: 100%"
  >
    <el-option 
      v-for="timeSlot in timeSlots" 
      :key="timeSlot" 
      :label="timeSlot" 
      :value="timeSlot" 
    />
  </el-select>
  <div class="form-help">
    可选择预设时间或输入自定义时间（如：14:15）
  </div>
</el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addCourse" :loading="adding">
          添加课程
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowRight } from '@element-plus/icons-vue'
import { useStudentsStore } from '@/stores/students'
import { useWordsStore } from '@/stores/words'
import { useScheduleStore } from '@/stores/schedule'

const studentsStore = useStudentsStore()
const students = computed(() => studentsStore.students)

const wordsStore = useWordsStore()
const wordSets = computed(() => wordsStore.wordSets)

const scheduleStore = useScheduleStore()

const router = useRouter()

// 使用 schedule store 的数据

// wordSets 现在从 words store 中获取

// 状态
const addDialogVisible = ref(false)
const adding = ref(false)

// 表单
const courseForm = reactive({
  studentId: '',
  wordSet: '',
  type: 'study',
  date: '',
  time: ''
})

// 计算属性 - 按日期分组
const groupedSchedules = computed(() => {
  return scheduleStore.getGroupedSchedules()
})

// 生成时间选项（6:00-22:00，每30分钟一个）
const timeSlots = computed(() => {
  const slots = []
  for (let hour = 6; hour <= 22; hour++) {
    slots.push(`${hour.toString().padStart(2, '0')}:00`)
    if (hour < 22) { // 22:30 超出范围
      slots.push(`${hour.toString().padStart(2, '0')}:30`)
    }
  }
  return slots
})

// 方法
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr + 'T00:00:00+08:00') // 北京时间
  const today = new Date()
  const beijingToday = new Date(today.toLocaleString('en-US', { timeZone: 'Asia/Shanghai' }))
  const todayStr = beijingToday.toISOString().split('T')[0]
  
  const tomorrow = new Date(beijingToday)
  tomorrow.setDate(tomorrow.getDate() + 1)
  const tomorrowStr = tomorrow.toISOString().split('T')[0]
  
  if (dateStr === todayStr) {
    return `今天 (${dateStr})`
  } else if (dateStr === tomorrowStr) {
    return `明天 (${dateStr})`
  } else {
    return dateStr
  }
}


const toggleDateGroup = (date: string) => {
  scheduleStore.toggleDateGroupExpanded(date)
}

const startStudy = (schedule: any) => {
  if (schedule.type === 'review') {
    console.log('进入抗遗忘模式:', schedule)
    // TODO: 实现抗遗忘模式
    ElMessage.info('抗遗忘模式功能正在开发中...')
  } else if (schedule.type === 'learning') {
    // 跳转到学习准备页面，显示九宫格和选择学习单词数
    router.push({
      name: 'StudyHome',
      params: { studentId: schedule.studentId },
      query: { 
        wordSet: schedule.wordSet
      }
    })
  } else {
    ElMessage.error('未知的课程类型')
  }
}

const showAddDialog = () => {
  Object.assign(courseForm, {
    studentId: '',
    wordSet: '',
    type: 'learning',
    date: '',
    time: ''
  })
  addDialogVisible.value = true
}

const addCourse = async () => {
  if (!courseForm.studentId || !courseForm.wordSet || !courseForm.date || !courseForm.time) {
    ElMessage.error('请填写完整的课程信息')
    return
  }
  
  adding.value = true
  
  try {
    const student = students.value.find(s => s.id === courseForm.studentId)
    const dateStr = new Date(courseForm.date).toISOString().split('T')[0]
    const timeStr = courseForm.time
    
    const newSchedule = {
      time: timeStr,
      date: dateStr,
      wordSet: courseForm.wordSet,
      studentName: student?.name || '',
      studentId: courseForm.studentId,
      type: courseForm.type as 'learning' | 'review'
    }
    
    scheduleStore.addSchedule(newSchedule)
    
    ElMessage.success('课程添加成功')
    addDialogVisible.value = false
  } catch (error) {
    ElMessage.error('添加课程失败')
  } finally {
    adding.value = false
  }
}

const deleteSchedule = async (schedule: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${schedule.studentName} 的课程吗？`, 
      '确认删除', 
      { type: 'warning' }
    )
    
    scheduleStore.deleteSchedule(schedule.id)
    ElMessage.success('课程删除成功')
  } catch {}
}

onMounted(() => {
  // 学生数据已经在store中，不需要额外加载
})
</script>

<style scoped>
.dashboard-page {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

.date-group {
  margin-bottom: 20px;
}

.date-header {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.date-header:hover {
  background: #e6f7ff;
}

.expand-icon {
  margin-right: 10px;
  transition: transform 0.3s ease;
}

.expand-icon.expanded {
  transform: rotate(90deg);
}

.date-text {
  flex: 1;
  font-weight: 600;
  color: #303133;
}

.course-count {
  color: #909399;
  font-size: 14px;
}

.schedule-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.schedule-item {
  display: flex;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-left: 30px;
}

.schedule-time {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-right: 20px;
  min-width: 80px;
}

.schedule-content {
  flex: 1;
}

.schedule-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.schedule-student {
  font-size: 14px;
  color: #e6a23c;
  margin-bottom: 8px;
}

.schedule-type {
  display: flex;
}

.schedule-actions {
  display: flex;
  gap: 10px;
}

.empty-state {
  margin-top: 50px;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>