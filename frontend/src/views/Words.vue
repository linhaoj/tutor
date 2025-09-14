<template>
  <div class="words-page">
    <div class="page-header">
      <h1>单词管理</h1>
      <div v-if="authStore.isAdmin" class="header-actions">
        <el-button type="success" @click="showImportDialog">
          <el-icon><Upload /></el-icon>
          导入Excel
        </el-button>
        <el-button type="primary" @click="showAddDialog">
          <el-icon><Plus /></el-icon>
          添加单词
        </el-button>
      </div>
    </div>

    <!-- 单词集筛选 -->
    <div class="filters">
      <el-select 
        v-model="selectedWordSet" 
        placeholder="选择单词集" 
        clearable
        @change="loadWords"
        style="width: 300px"
      >
        <el-option label="全部单词集" value="" />
        <el-option 
          v-for="set in wordSets" 
          :key="set.name" 
          :label="set.name" 
          :value="set.name" 
        />
      </el-select>
      <span class="word-count">共 {{ filteredWords.length }} 个单词</span>
      
      <!-- 删除单词集按钮 -->
      <el-button 
        v-if="selectedWordSet && authStore.isAdmin" 
        type="danger" 
        size="small"
        @click="deleteWordSet"
      >
        <el-icon><Delete /></el-icon>
        删除单词集
      </el-button>
    </div>

    <!-- 单词列表 -->
    <el-table :data="paginatedWords" style="width: 100%" stripe>
      <el-table-column prop="english" label="英文" width="200" />
      <el-table-column prop="chinese" label="中文" />
      <el-table-column prop="word_set" label="单词集">
        <template #default="scope">
          <el-tag size="small" type="info">{{ scope.row.word_set || '未分类' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column v-if="authStore.isAdmin" label="操作" width="150">
        <template #default="scope">
          <el-button size="small" @click="editWord(scope.row)">编辑</el-button>
          <el-button 
            size="small" 
            type="danger" 
            @click="deleteWord(scope.row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100]"
        :total="filteredWords.length"
        layout="total, sizes, prev, pager, next, jumper"
      />
    </div>

    <!-- 添加/编辑单词对话框 -->
    <el-dialog 
      v-model="wordDialogVisible" 
      :title="isEditingWord ? '编辑单词' : '添加单词'"
      width="500px"
    >
      <el-form :model="wordForm" label-width="100px">
        <el-form-item label="英文单词" required>
          <el-input v-model="wordForm.english" placeholder="请输入英文单词" />
        </el-form-item>
        <el-form-item label="中文释义" required>
          <el-input 
            v-model="wordForm.chinese" 
            type="textarea" 
            :rows="3"
            placeholder="请输入中文释义"
          />
        </el-form-item>
        <el-form-item label="单词集">
          <el-select 
            v-model="wordForm.word_set" 
            placeholder="选择或输入新的单词集"
            filterable
            allow-create
            style="width: 100%"
          >
            <el-option 
              v-for="set in wordSets" 
              :key="set.name" 
              :label="set.name" 
              :value="set.name" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="wordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveWord" :loading="savingWord">
          {{ isEditingWord ? '更新' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Excel导入对话框 -->
    <el-dialog 
      v-model="importDialogVisible" 
      title="导入Excel单词"
      width="800px"
    >
      <div class="import-content">
        <el-alert
          title="导入说明"
          description="Excel文件第一列必须是英文，第二列必须是中文。支持多个Sheet，每个Sheet会被识别为一个单词集。"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        />
        
        <el-form label-width="100px">
          <el-form-item label="选择文件" required>
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :limit="1"
              accept=".xlsx,.xls"
              :on-change="handleFileChange"
              :file-list="fileList"
              :before-remove="handleFileRemove"
            >
              <el-button type="primary">
                <el-icon><Upload /></el-icon>
                选择Excel文件
              </el-button>
              <template #tip>
                <div class="el-upload__tip">
                  只能上传xlsx/xls文件，且不超过10MB
                </div>
              </template>
            </el-upload>
          </el-form-item>
          
          <!-- 显示解析结果 -->
          <div v-if="excelSheets.length > 0" class="sheets-preview">
            <h4>检测到的Sheet：</h4>
            <div class="sheets-list">
              <el-card 
                v-for="(sheet, index) in excelSheets" 
                :key="index"
                style="margin-bottom: 15px"
              >
                <div class="sheet-header">
                  <div class="sheet-info">
                    <h5>{{ sheet.name }}</h5>
                    <span class="word-count-badge">{{ sheet.wordCount }} 个单词</span>
                  </div>
                  <div class="sheet-actions">
                    <el-input 
                      v-model="sheet.customName" 
                      placeholder="自定义单词集名称"
                      style="width: 250px; margin-right: 10px"
                    />
                    <el-checkbox v-model="sheet.selected">导入</el-checkbox>
                  </div>
                </div>
                
                <!-- 预览前几个单词 -->
                <div class="word-preview">
                  <div 
                    v-for="(word, wordIndex) in sheet.preview" 
                    :key="wordIndex"
                    class="preview-word"
                  >
                    <span class="english">{{ word.english }}</span>
                    <span class="chinese">{{ word.chinese }}</span>
                  </div>
                  <div v-if="sheet.wordCount > 3" class="more-words">
                    还有 {{ sheet.wordCount - 3 }} 个单词...
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </el-form>
      </div>
      
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="importWords" 
          :loading="importing"
          :disabled="!hasSelectedSheets"
        >
          开始导入 ({{ selectedSheetsCount }} 个Sheet)
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Delete } from '@element-plus/icons-vue'
import * as XLSX from 'xlsx'

// 接口定义
interface ExcelSheet {
  name: string
  customName: string
  selected: boolean
  wordCount: number
  preview: Array<{ english: string; chinese: string }>
  data: Array<{ english: string; chinese: string }>
}

import { useWordsStore } from '../stores/words'
import { useAuthStore } from '../stores/auth'

const wordsStore = useWordsStore()
const authStore = useAuthStore()
const words = computed(() => wordsStore.words)
const wordSets = computed(() => {
  // 使用按用户隔离的单词集数据
  const currentUser = authStore.currentUser
  return currentUser ? wordsStore.getWordSetsByUserId(currentUser.id) : []
})

// 状态
const selectedWordSet = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const wordDialogVisible = ref(false)
const importDialogVisible = ref(false)
const isEditingWord = ref(false)
const savingWord = ref(false)
const importing = ref(false)

// Excel相关状态
const excelSheets = ref<ExcelSheet[]>([])
const fileList = ref([])
const selectedFile = ref<File | null>(null)

// 表单数据
const wordForm = reactive({
  id: 0,
  english: '',
  chinese: '',
  word_set: ''
})

// 导入表单数据
const importForm = reactive({
  word_set: ''
})

// 计算属性
const filteredWords = computed(() => {
  if (!selectedWordSet.value) return words.value
  return words.value.filter(word => word.word_set === selectedWordSet.value)
})

const paginatedWords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredWords.value.slice(start, end)
})

const hasSelectedSheets = computed(() => {
  return excelSheets.value.some(sheet => sheet.selected)
})

const selectedSheetsCount = computed(() => {
  return excelSheets.value.filter(sheet => sheet.selected).length
})

// 方法
const loadWords = () => {
  currentPage.value = 1
}

const showAddDialog = () => {
  isEditingWord.value = false
  Object.assign(wordForm, { id: 0, english: '', chinese: '', word_set: '' })
  wordDialogVisible.value = true
}

const editWord = (word: any) => {
  isEditingWord.value = true
  Object.assign(wordForm, word)
  wordDialogVisible.value = true
}

const saveWord = async () => {
  if (savingWord.value) return
  
  savingWord.value = true
  
  try {
    if (isEditingWord.value) {
      wordsStore.updateWord(wordForm.id, wordForm)
      ElMessage.success('单词更新成功')
    } else {
      const newWord = { ...wordForm, id: Date.now() }
      wordsStore.addWord(newWord)
      ElMessage.success('单词添加成功')
    }
    
    wordDialogVisible.value = false
  } catch (error) {
    ElMessage.error('保存失败')
    console.error('保存错误:', error)
  } finally {
    savingWord.value = false
  }
}

const deleteWord = async (word: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除单词 "${word.english}" 吗？`, '确认删除', {
      type: 'warning'
    })
    
    wordsStore.deleteWord(word.id)
    ElMessage.success('单词删除成功')
  } catch {
    // 用户取消删除
  }
}

const deleteWordSet = async () => {
  if (!selectedWordSet.value) return
  
  const wordsInSet = words.value.filter(w => w.word_set === selectedWordSet.value)
  
  try {
    await ElMessageBox.confirm(
      `确定要删除单词集 "${selectedWordSet.value}" 吗？这将删除该单词集下的所有 ${wordsInSet.length} 个单词。`, 
      '确认删除单词集', 
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )
    
    wordsStore.deleteWordSet(selectedWordSet.value)
    
    // 重置筛选
    selectedWordSet.value = ''
    
    ElMessage.success(`单词集已删除`)
  } catch {
    // 用户取消删除
  }
}

const showImportDialog = () => {
  fileList.value = []
  selectedFile.value = null
  excelSheets.value = []
  importDialogVisible.value = true
}

const handleFileChange = async (file: any) => {
  selectedFile.value = file.raw
  
  try {
    const arrayBuffer = await file.raw.arrayBuffer()
    const workbook = XLSX.read(arrayBuffer)
    
    excelSheets.value = []
    
    // 解析每个Sheet
    workbook.SheetNames.forEach(sheetName => {
      const worksheet = workbook.Sheets[sheetName]
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 })
      
      // 过滤空行并提取单词数据
      const wordData: Array<{ english: string; chinese: string }> = []
      
      for (let i = 0; i < jsonData.length; i++) {
        const row = jsonData[i] as any[]
        if (row && row.length >= 2 && row[0] && row[1]) {
          const english = String(row[0]).trim()
          const chinese = String(row[1]).trim()
          
          if (english && chinese) {
            wordData.push({ english, chinese })
          }
        }
      }
      
      if (wordData.length > 0) {
        excelSheets.value.push({
          name: sheetName,
          customName: sheetName,
          selected: true,
          wordCount: wordData.length,
          preview: wordData.slice(0, 3),
          data: wordData
        })
      }
    })
    
    if (excelSheets.value.length === 0) {
      ElMessage.error('Excel文件中没有找到有效的单词数据')
    } else {
      ElMessage.success(`成功解析 ${excelSheets.value.length} 个Sheet`)
    }
    
  } catch (error) {
    ElMessage.error('解析Excel文件失败，请检查文件格式')
    console.error('Excel解析错误:', error)
  }
}

const handleFileRemove = () => {
  selectedFile.value = null
  excelSheets.value = []
}

const importWords = async () => {
  if (!selectedFile.value) {
    ElMessage.error('请选择文件')
    return
  }
  
  importing.value = true
  
  try {
    const selectedSheets = excelSheets.value.filter(sheet => sheet.selected)
    
    if (selectedSheets.length === 0) {
      ElMessage.error('请至少选择一个Sheet导入')
      return
    }
    
    const allImportedWords: any[] = []
    
    for (const sheet of selectedSheets) {
      const wordSetName = sheet.customName || sheet.name
      
      // 将sheet数据转换为Word格式
      const sheetWords = sheet.data.map(wordData => ({
        id: Date.now() + Math.random(),
        english: wordData.english,
        chinese: wordData.chinese,
        word_set: wordSetName
      }))
      
      allImportedWords.push(...sheetWords)
    }
    
    // 使用store导入所有单词
    wordsStore.importWords(allImportedWords)
    
    ElMessage.success(`成功导入 ${allImportedWords.length} 个单词，来自 ${selectedSheets.length} 个Sheet`)
    importDialogVisible.value = false
    
  } catch (error) {
    ElMessage.error('导入失败')
    console.error('导入错误:', error)
  } finally {
    importing.value = false
  }
}

onMounted(() => {
  // TODO: 加载数据
})
</script>

<style scoped>
.words-page {
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

.header-actions {
  display: flex;
  gap: 12px;
}

.filters {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.word-count {
  color: #606266;
  font-size: 14px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* Excel导入相关样式 */
.sheets-preview {
  margin-top: 20px;
}

.sheets-preview h4 {
  margin: 0 0 15px 0;
  color: #303133;
}

.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.sheet-info h5 {
  margin: 0 0 5px 0;
  color: #303133;
}

.word-count-badge {
  background: #e6f7ff;
  color: #1890ff;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.sheet-actions {
  display: flex;
  align-items: center;
}

.word-preview {
  background: #f9f9f9;
  padding: 10px;
  border-radius: 4px;
}

.preview-word {
  display: flex;
  gap: 20px;
  margin-bottom: 5px;
}

.preview-word .english {
  font-weight: 600;
  color: #303133;
  min-width: 120px;
}

.preview-word .chinese {
  color: #606266;
}

.more-words {
  color: #909399;
  font-size: 12px;
  margin-top: 10px;
}
</style>
