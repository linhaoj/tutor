<template>
  <div class="students-page">
    <div class="page-header">
      <h1>学生管理</h1>
      <el-button v-if="authStore.isAdmin" type="primary" @click="showAddDialog">
        <el-icon><Plus /></el-icon>
        创建学生账号
      </el-button>
    </div>

    <!-- 学生列表 -->
    <el-table :data="students" style="width: 100%">
      <el-table-column prop="name" label="姓名" width="150" />
      <el-table-column label="账号状态" width="120">
        <template #default="scope">
          <el-tag v-if="scope.row.hasAccount" type="success">已创建</el-tag>
          <el-tag v-else type="info">未创建</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="剩余课时" width="120">
        <template #default="scope">
          <span :class="getHoursClass(scope.row.remainingHours)">
            {{ (scope.row.remainingHours || 0).toFixed(1) }}h
          </span>
        </template>
      </el-table-column>
      <el-table-column v-if="authStore.isAdmin" label="操作" width="250">
        <template #default="scope">
          <el-button size="small" @click="editStudent(scope.row)">编辑</el-button>
          <el-button
            v-if="scope.row.hasAccount"
            size="small"
            type="warning"
            @click="resetPassword(scope.row)"
          >
            重置密码
          </el-button>
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

    <!-- 创建/编辑学生账号对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑学生信息' : '创建学生账号'"
      width="450px"
    >
      <el-form :model="studentForm" label-width="100px">
        <el-form-item label="姓名" required>
          <el-input v-model="studentForm.name" placeholder="请输入学生姓名" />
        </el-form-item>

        <el-form-item label="用户名" required>
          <el-input
            v-model="studentForm.username"
            placeholder="请输入登录用户名"
            :disabled="isEditing && studentForm.hasAccount"
          />
          <div v-if="isEditing && studentForm.hasAccount" style="font-size: 12px; color: #909399; margin-top: 5px;">
            账号已创建，不可修改用户名
          </div>
        </el-form-item>

        <el-form-item v-if="!isEditing || !studentForm.hasAccount" label="密码" required>
          <el-input
            v-model="studentForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
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
          {{ isEditing ? '更新' : '创建' }}
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
const studentForm = ref({
  id: 0,
  name: '',
  username: '',
  password: '',
  email: '',
  remainingHours: 0,
  hasAccount: false,
  userId: ''
})

const getHoursClass = (hours: number) => {
  if (!hours || hours <= 0) return 'hours-empty'
  if (hours <= 1) return 'hours-low'
  if (hours <= 5) return 'hours-medium'
  return 'hours-high'
}

const showAddDialog = () => {
  isEditing.value = false
  studentForm.value = {
    id: 0,
    name: '',
    username: '',
    password: '',
    email: '',
    remainingHours: 0,
    hasAccount: false,
    userId: ''
  }
  dialogVisible.value = true
}

const editStudent = (student: any) => {
  isEditing.value = true
  studentForm.value = { ...student, password: '' }
  dialogVisible.value = true
}

const saveStudent = async () => {
  if (!studentForm.value.name) {
    ElMessage.error('请输入学生姓名')
    return
  }

  if (!studentForm.value.username) {
    ElMessage.error('请输入用户名')
    return
  }

  if (!isEditing.value && !studentForm.value.password) {
    ElMessage.error('请输入密码')
    return
  }

  saving.value = true

  try {
    if (isEditing.value) {
      // 更新学生信息
      studentsStore.updateStudent(studentForm.value.id, {
        name: studentForm.value.name,
        email: studentForm.value.email,
        remainingHours: studentForm.value.remainingHours
      })
      ElMessage.success('学生信息更新成功')
    } else {
      // 创建新学生账号
      // 1. 先在auth store中创建用户账号
      const studentId = Date.now()
      const result = await authStore.registerUser({
        username: studentForm.value.username,
        password: studentForm.value.password,
        displayName: studentForm.value.name,
        role: 'student',
        email: studentForm.value.email,
        studentId: studentId
      })

      if (!result.success) {
        ElMessage.error(result.message)
        saving.value = false
        return
      }

      // 2. 在students store中创建学生记录
      const newStudent = {
        id: studentId,
        name: studentForm.value.name,
        username: studentForm.value.username,
        email: studentForm.value.email,
        total_words: 0,
        learned_words: 0,
        remainingHours: studentForm.value.remainingHours || 0,
        hasAccount: true,
        userId: `user-${studentId}` // 关联User ID
      }

      studentsStore.addStudent(newStudent)
      ElMessage.success('学生账号创建成功！学生可使用账号密码登录')
    }

    dialogVisible.value = false
  } catch (error) {
    console.error('保存学生失败:', error)
    ElMessage.error('操作失败')
  } finally {
    saving.value = false
  }
}

const resetPassword = async (student: any) => {
  try {
    const { value: newPassword } = await ElMessageBox.prompt(
      `为学生 ${student.name} 设置新密码`,
      '重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPlaceholder: '请输入新密码',
        inputType: 'password'
      }
    )

    if (!newPassword) {
      ElMessage.warning('密码不能为空')
      return
    }

    // 通过username找到用户并重置密码
    const users = await authStore.getAllUsers()
    const user = users.find((u: any) => u.username === student.username)

    if (user) {
      const result = await authStore.changePassword(user.id, '', newPassword)
      if (result.success) {
        ElMessage.success('密码重置成功')
      } else {
        ElMessage.error(result.message)
      }
    } else {
      ElMessage.error('未找到对应的用户账号')
    }
  } catch {
    // 用户取消操作
  }
}

const deleteStudent = async (student: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除学生 ${student.name} 吗？这将同时删除其账号和所有学习数据。`,
      '确认删除',
      {
        type: 'warning',
        confirmButtonText: '确定删除',
        cancelButtonText: '取消'
      }
    )

    // 1. 如果有账号，先删除用户账号
    if (student.hasAccount && student.userId) {
      const users = await authStore.getAllUsers()
      const user = users.find((u: any) => u.studentId === student.id)
      if (user) {
        await authStore.deleteUser(user.id)
      }
    }

    // 2. 删除学生记录
    const currentUser = authStore.currentUser
    if (currentUser) {
      studentsStore.deleteStudentForUser(currentUser.id, student.id)
    }

    ElMessage.success('学生删除成功')
  } catch {
    // 用户取消删除
  }
}

onMounted(() => {
  // 初始化加载
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
