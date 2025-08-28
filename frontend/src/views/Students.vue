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
    <el-table :data="students" style="width: 100%">
      <el-table-column prop="name" label="姓名" width="150" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="total_words" label="总单词数" width="120" />
      <el-table-column prop="learned_words" label="已学单词" width="120" />
      <el-table-column label="学习进度" width="200">
        <template #default="scope">
          <el-progress 
            :percentage="getProgress(scope.row)" 
            :stroke-width="8"
          />
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

    <!-- 添加/编辑学生对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEditing ? '编辑学生' : '添加学生'"
      width="400px"
    >
      <el-form :model="studentForm" label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="studentForm.name" placeholder="请输入学生姓名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="studentForm.email" placeholder="请输入邮箱（可选）" />
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

const studentsStore = useStudentsStore()
const students = computed(() => studentsStore.students)

const dialogVisible = ref(false)
const saving = ref(false)
const isEditing = ref(false)
const studentForm = ref({ id: 0, name: '', email: '' })

const getProgress = (student: any) => {
  if (student.total_words === 0) return 0
  return Math.round((student.learned_words / student.total_words) * 100)
}

const showAddDialog = () => {
  isEditing.value = false
  studentForm.value = { id: 0, name: '', email: '' }
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
    learned_words: 0
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
</style>
