<template>
  <div class="data-management">
    <div class="page-header">
      <h1>数据管理</h1>
    </div>

    <div class="content">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="action-card">
            <template #header>
              <span>数据备份</span>
            </template>
            <div class="action-content">
              <p>将所有数据导出到JSON文件，用于备份和迁移</p>
              <el-button type="primary" @click="exportData" :loading="exporting">
                <el-icon><Download /></el-icon>
                导出数据
              </el-button>
            </div>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card class="action-card">
            <template #header>
              <span>数据恢复</span>
            </template>
            <div class="action-content">
              <p>从JSON文件恢复数据（会覆盖现有数据）</p>
              <el-upload
                :auto-upload="false"
                :on-change="handleFileSelect"
                :show-file-list="false"
                accept=".json"
              >
                <el-button type="success" :loading="importing">
                  <el-icon><Upload /></el-icon>
                  选择文件导入
                </el-button>
              </el-upload>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card class="stats-card">
            <template #header>
              <span>数据统计</span>
            </template>
            <div class="stats-content">
              <el-row :gutter="20">
                <el-col :span="6">
                  <div class="stat-item">
                    <div class="stat-value">{{ stats.users }}</div>
                    <div class="stat-label">用户数量</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-item">
                    <div class="stat-value">{{ stats.students }}</div>
                    <div class="stat-label">学生总数</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-item">
                    <div class="stat-value">{{ stats.words }}</div>
                    <div class="stat-label">单词总数</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-item">
                    <div class="stat-value">{{ stats.schedules }}</div>
                    <div class="stat-label">课程总数</div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card class="danger-card">
            <template #header>
              <span>危险操作</span>
            </template>
            <div class="danger-content">
              <p class="warning-text">以下操作不可恢复，请谨慎使用！</p>
              <el-button type="danger" @click="confirmClearData">
                <el-icon><Delete /></el-icon>
                清空所有数据
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type UploadFile } from 'element-plus'
import { Download, Upload, Delete } from '@element-plus/icons-vue'
import tutorDB from '@/utils/localDatabase'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const exporting = ref(false)
const importing = ref(false)

const stats = ref({
  users: 0,
  students: 0,
  words: 0,
  schedules: 0
})

// 导出数据
const exportData = async () => {
  try {
    exporting.value = true
    await tutorDB.backupToFile()
    ElMessage.success('数据导出成功！')
  } catch (error) {
    console.error('数据导出失败:', error)
    ElMessage.error('数据导出失败')
  } finally {
    exporting.value = false
  }
}

// 处理文件选择
const handleFileSelect = async (file: UploadFile) => {
  if (!file.raw) return

  try {
    await ElMessageBox.confirm(
      '导入数据会覆盖现有的所有数据，确定要继续吗？',
      '确认导入',
      {
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )

    importing.value = true
    await tutorDB.restoreFromFile(file.raw)
    ElMessage.success('数据导入成功！页面将刷新以应用新数据。')
    
    // 刷新页面以重新加载数据
    setTimeout(() => {
      window.location.reload()
    }, 1500)
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('数据导入失败:', error)
      ElMessage.error('数据导入失败：' + (error.message || '未知错误'))
    }
  } finally {
    importing.value = false
  }
}

// 清空所有数据
const confirmClearData = async () => {
  try {
    await ElMessageBox.confirm(
      '这将删除所有用户、学生、单词、课程等数据，此操作无法恢复！\n\n请输入 "CLEAR" 确认删除：',
      '危险操作确认',
      {
        type: 'error',
        showInput: true,
        inputValidator: (value: string) => {
          return value === 'CLEAR' ? true : '请输入 CLEAR 确认删除'
        }
      }
    )

    // 清空所有localStorage数据
    const keys = Object.keys(localStorage)
    keys.forEach(key => {
      if (key.startsWith('backup_') || key.includes('students_') || 
          key.includes('schedule_') || key.includes('words') || 
          key.includes('users') || key.includes('learning')) {
        localStorage.removeItem(key)
      }
    })

    // 清空IndexedDB
    try {
      indexedDB.deleteDatabase('TutorDatabase')
    } catch (error) {
      console.error('清空IndexedDB失败:', error)
    }

    ElMessage.success('所有数据已清空！页面将刷新。')
    
    // 刷新页面
    setTimeout(() => {
      window.location.reload()
    }, 1500)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空数据失败:', error)
    }
  }
}

// 加载统计数据
const loadStats = async () => {
  try {
    // 统计用户数量
    const users = await authStore.getAllUsers()
    stats.value.users = users.length

    // 统计其他数据（这里简化处理，实际中应该从各个store获取）
    const localStorageKeys = Object.keys(localStorage)
    
    stats.value.students = localStorageKeys
      .filter(key => key.startsWith('backup_students_'))
      .reduce((total, key) => {
        try {
          const data = JSON.parse(localStorage.getItem(key) || '[]')
          return total + (Array.isArray(data) ? data.length : 0)
        } catch {
          return total
        }
      }, 0)

    stats.value.schedules = localStorageKeys
      .filter(key => key.startsWith('backup_schedules_'))
      .reduce((total, key) => {
        try {
          const data = JSON.parse(localStorage.getItem(key) || '[]')
          return total + (Array.isArray(data) ? data.length : 0)
        } catch {
          return total
        }
      }, 0)

    // 单词数统计
    try {
      const wordsData = localStorage.getItem('backup_words_userList')
      if (wordsData) {
        const words = JSON.parse(wordsData)
        stats.value.words = Array.isArray(words) ? words.length : 0
      }
    } catch {
      stats.value.words = 0
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.data-management {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.page-header {
  background: white;
  padding: 20px 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.content {
  max-width: 1200px;
  margin: 0 auto;
}

.action-card {
  height: 200px;
}

.action-content {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
}

.action-content p {
  color: #606266;
  margin: 0 0 20px 0;
  line-height: 1.5;
}

.stats-card {
  margin-bottom: 20px;
}

.stats-content {
  padding: 20px 0;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.danger-card {
  border: 1px solid #f56c6c;
}

.danger-card :deep(.el-card__header) {
  background: #fef0f0;
  color: #f56c6c;
}

.danger-content {
  padding: 20px 0;
}

.warning-text {
  color: #f56c6c;
  margin: 0 0 20px 0;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .data-management {
    padding: 10px;
  }
  
  .page-header {
    padding: 15px 20px;
  }
  
  .page-header h1 {
    font-size: 20px;
  }
  
  .action-card {
    margin-bottom: 15px;
  }
  
  .stat-item {
    margin-bottom: 15px;
  }
}
</style>