<template>
  <div class="students-page">
    <div class="page-header">
      <h1>学生管理</h1>
      <el-button v-if="authStore.isAdmin" type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        添加学生
      </el-button>
    </div>

    <!-- 学生列表 -->
    <el-table :data="students" style="width: 100%">
      <el-table-column prop="name" label="姓名" width="150" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="total_words" label="总单词数" width="120" />
      <el-table-column prop="learned_words" label="已学单词" width="120" />
      <el-table-column label="剩余课时" width="120">
        <template #default="scope">
          <span :class="getHoursClass(scope.row.remainingHours)">
            {{ (scope.row.remainingHours || 0).toFixed(1) }}h
          </span>
        </template>
      </el-table-column>
      <el-table-column label="学习进度" width="200">
        <template #default="scope">
          <el-progress 
            :percentage="getProgress(scope.row)" 
            :stroke-width="8"
          />
        </template>
      </el-table-column>
      <el-table-column v-if="authStore.isAdmin" label="操作" width="200">
        <template #default="scope">
          <el-button size="small" @click="editStudent(scope.row)">编辑</el-button>
          <el-button 
            size="small" 
            type="danger" 
            @click="deleteStudent(scope.row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加/编辑学生对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEditing ? '编辑学生' : '添加学生'"
      width="400px"
    >
      <el-form :model="studentForm" label-width="100px">
        <el-form-item label="姓名" required>
          <el-input v-model="studentForm.name" placeholder="请输入学生姓名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="studentForm.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>
        <el-form-item v-if="authStore.isAdmin" label="剩余课时">
          <el-input-number 
            v-model="studentForm.remainingHours" 
            :precision="1"
            :step="0.5"
            :min="0"
            :max="1000"
            placeholder="剩余课程时长（小时）"
            style="width: 100%"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            大课60分钟 = 1.0h，小课30分钟 = 0.5h
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveStudent" :loading="saving">
          {{ isEditing ? '更新' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useStudentsStore } from '../stores/students'
import { useAuthStore } from '../stores/auth'

const studentsStore = useStudentsStore()
const authStore = useAuthStore()
const students = computed(() => {
  const currentUser = authStore.currentUser
  return currentUser ? studentsStore.getStudentsByUserId(currentUser.id) : []
})

const dialogVisible = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const studentForm = ref({ id: 0, name: '', email: '', remainingHours: 0 })

const getProgress = (student: any) => {
  if (student.total_words === 0) return 0
  return Math.round((student.learned_words / student.total_words) * 100)
}

const getHoursClass = (hours: number) => {
  if (!hours || hours <= 0) return 'hours-empty'
  if (hours <= 1) return 'hours-low'
  if (hours <= 5) return 'hours-medium'
  return 'hours-high'
}

const showAddDialog = () => {
  isEditing.value = false
  studentForm.value = { id: 0, name: '', email: '', remainingHours: 0 }
  dialogVisible.value = true
}

const editStudent = (student: any) => {
  isEditing.value = true
  studentForm.value = { ...student }
  dialogVisible.value = true
}

const saveStudent = async () => {
  if (!studentForm.value.name) {
    ElMessage.error('请输入学生姓名')
    return
  }
  
  saving.value = true
  
  try {
    if (isEditing.value) {
  // 更新学生
  studentsStore.updateStudent(studentForm.value.id, studentForm.value)
  ElMessage.success('学生信息更新成功')
} else {
  // 添加学生
  const newStudent = {
    ...studentForm.value,
    id: Date.now(),
    total_words: 0,
    learned_words: 0,
    remainingHours: studentForm.value.remainingHours || 0
  }
  studentsStore.addStudent(newStudent)
  ElMessage.success('学生添加成功')
}
    
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    saving.value = false
  }
}

const deleteStudent = async (student: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除学生 ${student.name} 吗？`, '确认删除', {
      type: 'warning'
    })
    
    studentsStore.deleteStudent(student.id)
ElMessage.success('学生删除成功')
  } catch {
    // 用户取消删除
  }
}

onMounted(() => {
  // TODO: 从API加载学生数据
})
</script>

<style scoped>
.students-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

/* 剩余时长颜色样式 */
.hours-empty {
  color: #f56c6c;
  font-weight: bold;
}

.hours-low {
  color: #e6a23c;
  font-weight: bold;
}

.hours-medium {
  color: #409eff;
  font-weight: bold;
}

.hours-high {
  color: #67c23a;
  font-weight: bold;
}
</style>
