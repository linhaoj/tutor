<template>
  <div class="admin-container">
    <div class="admin-header">
      <div class="header-left">
        <h1>系统管理</h1>
        <el-tag type="danger" size="large">管理员</el-tag>
      </div>
      <div class="header-right">
        <span class="welcome-text">欢迎，{{ authStore.currentUser?.displayName }}</span>
        <el-dropdown @command="handleCommand">
          <el-button type="primary">
            <el-icon><Avatar /></el-icon>
            操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="dashboard">进入主页面</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="admin-content">
      <!-- 用户管理区域 -->
      <el-card class="user-management">
        <template #header>
          <div class="card-header">
            <span>用户管理</span>
            <el-button type="primary" @click="showAddUserDialog">
              <el-icon><Plus /></el-icon>
              添加用户
            </el-button>
          </div>
        </template>

        <div class="users-list">
          <el-table :data="users" style="width: 100%">
            <el-table-column prop="displayName" label="姓名" />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="role" label="角色">
              <template #default="scope">
                <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'success'">
                  {{ scope.row.role === 'admin' ? '管理员' : '老师' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="email" label="邮箱" />
            <el-table-column prop="createdAt" label="创建时间">
              <template #default="scope">
                {{ formatDate(scope.row.createdAt) }}
              </template>
            </el-table-column>
            <el-table-column prop="lastLoginAt" label="最后登录">
              <template #default="scope">
                {{ scope.row.lastLoginAt ? formatDate(scope.row.lastLoginAt) : '从未登录' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button
                  size="small"
                  @click="editUser(scope.row)"
                  :disabled="scope.row.id === authStore.currentUser?.id"
                >
                  编辑
                </el-button>
                <el-button
                  size="small"
                  @click="resetPassword(scope.row)"
                  :disabled="scope.row.id === authStore.currentUser?.id"
                >
                  重置密码
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="deleteUser(scope.row)"
                  :disabled="scope.row.id === authStore.currentUser?.id"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>

    <!-- 添加用户对话框 -->
    <el-dialog 
      v-model="addUserDialogVisible" 
      title="添加用户"
      width="500px"
    >
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="userForm.confirmPassword" type="password" placeholder="请确认密码" />
        </el-form-item>
        <el-form-item label="姓名" prop="displayName">
          <el-input v-model="userForm.displayName" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色">
            <el-option label="老师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addUserDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddUser" :loading="submitting">
          添加
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog 
      v-model="editUserDialogVisible" 
      title="编辑用户"
      width="500px"
    >
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="姓名" prop="displayName">
          <el-input v-model="editForm.displayName" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="editForm.role" placeholder="请选择角色">
            <el-option label="老师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editUserDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEditUser" :loading="submitting">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog 
      v-model="resetPasswordDialogVisible" 
      title="重置密码"
      width="400px"
    >
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" placeholder="请输入新密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" placeholder="请确认密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPasswordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitResetPassword" :loading="submitting">
          重置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { Plus, Avatar, ArrowDown } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { User } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 表单引用
const userFormRef = ref<InstanceType<typeof ElForm>>()
const editFormRef = ref<InstanceType<typeof ElForm>>()
const passwordFormRef = ref<InstanceType<typeof ElForm>>()

// 用户列表
const users = ref<User[]>([])

// 对话框状态
const addUserDialogVisible = ref(false)
const editUserDialogVisible = ref(false)
const resetPasswordDialogVisible = ref(false)
const submitting = ref(false)

// 添加用户表单
const userForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  displayName: '',
  role: 'teacher',
  email: ''
})

// 编辑用户表单
const editForm = reactive({
  id: '',
  username: '',
  displayName: '',
  role: 'teacher',
  email: ''
})

// 重置密码表单
const passwordForm = reactive({
  userId: '',
  newPassword: '',
  confirmPassword: ''
})

// 表单验证规则
const userRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== userForm.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  displayName: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const editRules = {
  displayName: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const passwordRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 50, message: '密码长度在 6 到 50 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 方法
const loadUsers = () => {
  users.value = authStore.getAllUsers()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (command === 'dashboard') {
    router.push('/')
  }
}

const showAddUserDialog = () => {
  Object.assign(userForm, {
    username: '',
    password: '',
    confirmPassword: '',
    displayName: '',
    role: 'teacher',
    email: ''
  })
  addUserDialogVisible.value = true
}

const submitAddUser = async () => {
  if (!userFormRef.value) return
  
  try {
    await userFormRef.value.validate()
    submitting.value = true
    
    const result = await authStore.registerUser({
      username: userForm.username,
      password: userForm.password,
      displayName: userForm.displayName,
      role: userForm.role as 'admin' | 'teacher',
      email: userForm.email || undefined
    })
    
    if (result.success) {
      ElMessage.success(result.message)
      addUserDialogVisible.value = false
      loadUsers()
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('Add user validation failed:', error)
  } finally {
    submitting.value = false
  }
}

const editUser = (user: User) => {
  Object.assign(editForm, {
    id: user.id,
    username: user.username,
    displayName: user.displayName,
    role: user.role,
    email: user.email || ''
  })
  editUserDialogVisible.value = true
}

const submitEditUser = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    submitting.value = true
    
    const result = await authStore.updateUser(editForm.id, {
      displayName: editForm.displayName,
      role: editForm.role as 'admin' | 'teacher',
      email: editForm.email || undefined
    })
    
    if (result.success) {
      ElMessage.success(result.message)
      editUserDialogVisible.value = false
      loadUsers()
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('Edit user validation failed:', error)
  } finally {
    submitting.value = false
  }
}

const resetPassword = (user: User) => {
  passwordForm.userId = user.id
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  resetPasswordDialogVisible.value = true
}

const submitResetPassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    submitting.value = true
    
    const result = await authStore.changePassword(
      passwordForm.userId,
      '', // 管理员重置密码不需要旧密码
      passwordForm.newPassword
    )
    
    if (result.success) {
      ElMessage.success(result.message)
      resetPasswordDialogVisible.value = false
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    console.error('Reset password validation failed:', error)
  } finally {
    submitting.value = false
  }
}

const deleteUser = async (user: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.displayName}" (${user.username}) 吗？\n\n删除后该用户的所有数据将被永久清除！`,
      '确认删除用户',
      {
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )
    
    const result = await authStore.deleteUser(user.id)
    if (result.success) {
      ElMessage.success(result.message)
      loadUsers()
    } else {
      ElMessage.error(result.message)
    }
  } catch {
    // 用户取消删除
  }
}

// 生命周期
onMounted(() => {
  // 检查管理员权限
  if (!authStore.isAdmin) {
    ElMessage.error('权限不足，只有管理员可以访问此页面')
    router.push('/')
    return
  }
  
  loadUsers()
})
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.admin-header {
  background: white;
  padding: 20px 40px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-left h1 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.welcome-text {
  color: #606266;
  font-size: 14px;
}

.admin-content {
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
}

.user-management {
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  font-size: 18px;
  font-weight: 600;
}

.users-list {
  margin-top: 20px;
}

/* 表格样式优化 */
:deep(.el-table) {
  border-radius: 8px;
}

:deep(.el-table th) {
  background: #fafafa;
  color: #303133;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .admin-header {
    padding: 15px 20px;
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
  
  .admin-content {
    padding: 20px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
}
</style>