<template>
  <div class="students-page">
    <div class="page-header">
      <h1>学生管理</h1>
      <el-button type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        添加学生
      </el-button>
    </div>

    <!-- 学生列表 -->
    <el-table :data="studentsStore.students" style="width: 100%" v-loading="studentsStore.loading">
      <el-table-column prop="name" label="姓名" width="150" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="剩余课时" width="120">
        <template #default="scope">
          <span :class="getHoursClass(scope.row.remaining_hours)">
            {{ scope.row.remaining_hours.toFixed(1) }}h
          </span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
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

    <!-- 创建/编辑学生对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑学生信息' : '添加学生'"
      width="450px"
    >
      <el-form :model="studentForm" label-width="100px">
        <el-form-item label="姓名" required>
          <el-input v-model="studentForm.name" placeholder="请输入学生姓名" />
        </el-form-item>

        <el-form-item label="邮箱">
          <el-input v-model="studentForm.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>

        <el-form-item label="剩余课时">
          <el-input-number
            v-model="studentForm.remaining_hours"
            :precision="1"
            :step="0.5"
            :min="0"
            :max="1000"
            :disabled="!authStore.isAdmin"
            placeholder="剩余课程时长（小时）"
            style="width: 100%"
          />
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            <template v-if="authStore.isAdmin">
              大课60分钟 = 1.0h，小课30分钟 = 0.5h
            </template>
            <template v-else>
              <span style="color: #f56c6c;">⚠️ 只有管理员可以修改课时</span>
            </template>
          </div>
        </el-form-item>

        <!-- 管理员可以为其他教师创建学生 -->
        <el-form-item v-if="authStore.isAdmin && !isEditing" label="所属教师">
          <el-select v-model="studentForm.teacher_id" placeholder="选择教师" style="width: 100%">
            <el-option
              v-for="teacher in teachers"
              :key="teacher.id"
              :label="teacher.display_name"
              :value="teacher.id"
            />
          </el-select>
          <div style="font-size: 12px; color: #909399; margin-top: 5px;">
            留空则为当前登录用户创建学生
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveStudent" :loading="saving">
          {{ isEditing ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useStudentsStore } from '../stores/students'
import { useAuthStore } from '../stores/auth'

const studentsStore = useStudentsStore()
const authStore = useAuthStore()

const dialogVisible = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const teachers = ref<any[]>([])

const studentForm = ref({
  id: 0,
  name: '',
  email: '',
  remaining_hours: 0,
  teacher_id: ''
})

const getHoursClass = (hours: number) => {
  if (!hours || hours <= 0) return 'hours-empty'
  if (hours <= 1) return 'hours-low'
  if (hours <= 5) return 'hours-medium'
  return 'hours-high'
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const showAddDialog = async () => {
  isEditing.value = false
  studentForm.value = {
    id: 0,
    name: '',
    email: '',
    remaining_hours: 0,
    teacher_id: ''
  }

  // 如果是管理员，加载教师列表
  if (authStore.isAdmin) {
    const users = await authStore.getAllUsers()
    teachers.value = users.filter((u: any) => u.role === 'teacher')
  }

  dialogVisible.value = true
}

const editStudent = (student: any) => {
  isEditing.value = true
  studentForm.value = {
    id: student.id,
    name: student.name,
    email: student.email || '',
    remaining_hours: student.remaining_hours,
    teacher_id: student.teacher_id
  }
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
      // 更新学生信息
      const result = await studentsStore.updateStudent(studentForm.value.id, {
        name: studentForm.value.name,
        email: studentForm.value.email || undefined,
        remaining_hours: studentForm.value.remaining_hours
      })

      if (result.success) {
        ElMessage.success('学生信息更新成功')
        dialogVisible.value = false
      } else {
        ElMessage.error(result.message)
      }
    } else {
      // 创建新学生
      const result = await studentsStore.addStudent({
        name: studentForm.value.name,
        email: studentForm.value.email || undefined,
        remaining_hours: studentForm.value.remaining_hours,
        teacher_id: studentForm.value.teacher_id || undefined
      })

      if (result.success) {
        ElMessage.success('学生添加成功')
        dialogVisible.value = false
      } else {
        ElMessage.error(result.message)
      }
    }
  } catch (error) {
    console.error('保存学生失败:', error)
    ElMessage.error('操作失败')
  } finally {
    saving.value = false
  }
}

const deleteStudent = async (student: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除学生 ${student.name} 吗？这将删除该学生的所有学习数据。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )

    const result = await studentsStore.deleteStudent(student.id)
    if (result.success) {
      ElMessage.success('学生删除成功')
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消删除
  }
}

onMounted(async () => {
  // 加载学生列表
  await studentsStore.fetchStudents()
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
