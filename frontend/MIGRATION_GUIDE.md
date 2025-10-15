# 前端迁移指南 - localStorage → 后端API

## 📋 进度概览

| Store | 状态 | 说明 |
|-------|------|------|
| ✅ auth.ts | 已完成 | JWT认证、用户管理 |
| ✅ students.ts | 已完成 | 学生CRUD、课时扣减 |
| ⏳ words.ts | 待完成 | 单词和单词集管理 |
| ⏳ schedule.ts | 待完成 | 课程安排管理 |
| ⏳ learningProgress.ts | 待完成 | 学习进度管理 |
| ⏹️ learning.ts | 不需要 | 纯前端状态 |
| ⏹️ antiForget.ts | 不需要 | 纯前端状态 |
| ⏹️ ui.ts | 不需要 | UI状态 |

---

## 🔧 改造模式

### 基础模板

```typescript
/**
 * XXX Store - 连接后端API
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/config'

export interface XXX {
  // 后端返回的字段（使用snake_case）
  id: number
  name: string
  created_at: string
}

export const useXXXStore = defineStore('xxx', () => {
  const items = ref<XXX[]>([])
  const loading = ref(false)

  /**
   * 获取列表
   */
  const fetchItems = async () => {
    loading.value = true
    try {
      const response = await api.get('/api/xxx')
      items.value = response.data
    } catch (error) {
      console.error('Fetch error:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建
   */
  const createItem = async (data: any): Promise<{ success: boolean, message: string }> => {
    try {
      const response = await api.post('/api/xxx', data)
      items.value.push(response.data)
      return { success: true, message: '创建成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '创建失败'
      }
    }
  }

  /**
   * 更新
   */
  const updateItem = async (id: number, updates: any): Promise<{ success: boolean, message: string }> => {
    try {
      const response = await api.put(`/api/xxx/${id}`, updates)
      const index = items.value.findIndex(i => i.id === id)
      if (index !== -1) {
        items.value[index] = response.data
      }
      return { success: true, message: '更新成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '更新失败'
      }
    }
  }

  /**
   * 删除
   */
  const deleteItem = async (id: number): Promise<{ success: boolean, message: string }> => {
    try {
      await api.delete(`/api/xxx/${id}`)
      items.value = items.value.filter(i => i.id !== id)
      return { success: true, message: '删除成功' }
    } catch (error: any) {
      return {
        success: false,
        message: error.response?.data?.detail || '删除失败'
      }
    }
  }

  return {
    items,
    loading,
    fetchItems,
    createItem,
    updateItem,
    deleteItem
  }
})
```

---

## 📝 待完成：words.ts

### 后端API接口

```typescript
// GET /api/words/sets - 获取所有单词集
// POST /api/words/sets - 创建单词集
// GET /api/words/sets/{word_set_name}/words - 获取单词集的所有单词
// POST /api/words/sets/{word_set_name}/words - 添加单词
// POST /api/words/sets/{word_set_name}/import-excel - Excel导入
// DELETE /api/words/words/{word_id} - 删除单词
```

### 数据结构

```typescript
export interface WordSet {
  id: number
  name: string
  owner_id: string
  is_global: boolean
  word_count: number
}

export interface Word {
  id: number
  english: string
  chinese: string
  word_set_name: string
}
```

### 改造要点

1. **获取单词集**
   ```typescript
   const fetchWordSets = async () => {
     const response = await api.get('/api/words/sets')
     wordSets.value = response.data
   }
   ```

2. **获取单词**
   ```typescript
   const fetchWords = async (wordSetName: string) => {
     const response = await api.get(`/api/words/sets/${wordSetName}/words`)
     words.value = response.data
   }
   ```

3. **Excel导入**
   ```typescript
   const importExcel = async (wordSetName: string, file: File) => {
     const formData = new FormData()
     formData.append('file', file)
     await api.post(`/api/words/sets/${wordSetName}/import-excel`, formData, {
       headers: { 'Content-Type': 'multipart/form-data' }
     })
   }
   ```

---

## 📝 待完成：schedule.ts

### 后端API接口

```typescript
// GET /api/schedules - 获取所有课程
// POST /api/schedules - 创建课程
// PUT /api/schedules/{schedule_id}/complete - 标记完成
// DELETE /api/schedules/{schedule_id} - 删除课程
```

### 数据结构

```typescript
export interface Schedule {
  id: number
  student_id: number
  student_name: string
  date: string  // ISO格式 YYYY-MM-DD
  time: string
  word_set_name: string
  course_type: string
  duration: number
  class_type: string
  completed: boolean
}
```

### 改造要点

1. **创建课程**
   ```typescript
   const createSchedule = async (data: {
     student_id: number
     date: string
     time: string
     word_set_name: string
     course_type?: string
     duration?: number
     class_type?: string
   }) => {
     const response = await api.post('/api/schedules', data)
     schedules.value.push(response.data)
   }
   ```

2. **标记完成**
   ```typescript
   const completeSchedule = async (id: number) => {
     await api.put(`/api/schedules/${id}/complete`)
     const index = schedules.value.findIndex(s => s.id === id)
     if (index !== -1) {
       schedules.value[index].completed = true
     }
   }
   ```

---

## 📝 待完成：learningProgress.ts

### 后端API接口

```typescript
// POST /api/progress - 创建/更新进度
// GET /api/progress/student/{student_id} - 获取学生进度
```

### 数据结构

```typescript
export interface LearningProgress {
  id: number
  student_id: number
  word_set_name: string
  word_index: number
  current_stage: number
  total_groups: number
  tasks_completed: Record<string, any>
}
```

### 改造要点

1. **保存进度**
   ```typescript
   const saveProgress = async (data: {
     student_id: number
     word_set_name: string
     word_index: number
     current_stage: number
     total_groups: number
     tasks_completed: Record<string, any>
   }) => {
     await api.post('/api/progress', data)
   }
   ```

2. **获取进度**
   ```typescript
   const fetchProgress = async (studentId: number, wordSetName?: string) => {
     const params = wordSetName ? { word_set_name: wordSetName } : {}
     const response = await api.get(`/api/progress/student/${studentId}`, { params })
     return response.data
   }
   ```

---

## 🔑 关键注意事项

### 1. 字段命名差异

**后端（Python/snake_case）**：
```json
{
  "id": 1,
  "display_name": "张三",
  "created_at": "2025-01-01T00:00:00"
}
```

**前端（TypeScript interface）**：
```typescript
interface User {
  id: number
  display_name: string  // 保持snake_case
  created_at: string
}
```

**不要转换为camelCase**，保持与后端一致！

---

### 2. 日期格式

**后端返回**：ISO 8601格式字符串
```
"2025-01-14T10:30:00"
```

**前端使用**：
```typescript
// 显示
const date = new Date(user.created_at).toLocaleDateString()

// 提交
const dateStr = new Date().toISOString().split('T')[0]  // "2025-01-14"
```

---

### 3. 错误处理

**所有API调用都会被拦截器处理**：
- 401 → 自动跳转登录
- 400/404 → 显示错误提示
- 500 → 显示服务器错误

**额外处理**：
```typescript
try {
  const response = await api.post('/api/xxx', data)
  return { success: true, message: '成功' }
} catch (error: any) {
  // 拦截器已经显示了错误提示
  return {
    success: false,
    message: error.response?.data?.detail || '操作失败'
  }
}
```

---

### 4. Loading状态

**推荐模式**：
```typescript
const loading = ref(false)

const fetchData = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/xxx')
    items.value = response.data
  } catch (error) {
    console.error('Error:', error)
  } finally {
    loading.value = false  // 确保总是重置
  }
}
```

---

### 5. 本地缓存策略

**不再使用localStorage存储业务数据**：
- ✅ 只缓存 `auth_token` 和 `current_user`
- ❌ 删除所有 `students_xxx`, `schedule_xxx` 等缓存
- ✅ 每次刷新页面都从API获取最新数据

---

## 🧪 测试清单

### Store改造完成后测试

- [ ] **登录测试**
  - [ ] 正确的用户名密码 → 成功登录
  - [ ] 错误的密码 → 提示密码错误
  - [ ] 不存在的用户 → 提示用户不存在
  - [ ] Token自动保存到localStorage

- [ ] **CRUD测试**（每个store）
  - [ ] 创建 → 数据保存到数据库
  - [ ] 读取 → 显示正确数据
  - [ ] 更新 → 修改生效
  - [ ] 删除 → 数据移除

- [ ] **权限测试**
  - [ ] 未登录 → 跳转到登录页
  - [ ] Token过期 → 自动跳转登录
  - [ ] 普通教师 → 只能看到自己的数据
  - [ ] 管理员 → 可以管理用户

- [ ] **多用户隔离测试**
  - [ ] 教师A创建的学生，教师B看不到
  - [ ] 不同浏览器/设备 → 数据独立

---

## 🚀 启动步骤

### 1. 安装依赖（如果还没有）

```bash
cd frontend
npm install
```

### 2. 启动后端

```bash
cd backend
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
python main.py
```

后端运行在 `http://localhost:8000`

### 3. 启动前端

```bash
cd frontend
npm run dev
```

前端运行在 `http://localhost:5173`

### 4. 默认管理员账号

- 用户名：`admin`
- 密码：`admin123`

---

## 📖 参考文档

- 后端API文档：`backend/CLAUDE.md` - 多用户系统API章节
- 数据安全文档：`backend/DATA_SAFETY.md`
- 前端API配置：`frontend/src/api/config.ts`

---

**下次启动时从这里继续**：
1. 打开 `frontend/src/stores/words.ts`
2. 按照上面的模板改造
3. 重复 schedule.ts 和 learningProgress.ts

Good luck! 🎉
