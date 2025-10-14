# 英语陪练系统开发记录

## 🚀 快速部署指南（SSH方式）

### 本地操作（提交代码）
```bash
# 1. 提交本地更改
cd /Users/laovexl/Downloads/tutor
git add .
git commit -m "描述更新内容"
git push origin main
```

### 服务器操作（部署更新）
```bash
# 1. 连接服务器
ssh root@47.108.248.168

# 2. 停止服务
pm2 stop all

# 3. 更新代码
cd /var/www/tutor
git pull origin main

# 4. 重新构建前端
cd frontend
npm run build-only

# 5. 重启服务
cd /var/www/tutor
pm2 restart all

# 6. 检查状态
pm2 status
```

### 访问地址
- **生产环境**: http://47.108.248.168:5173
- **本地开发**: http://localhost:5173
- **默认管理员账号**: admin / admin123

### 注意事项
- 使用 `npm run build-only` 跳过类型检查，加快构建速度
- 如果git拉取失败，检查SSH密钥配置或网络连接
- 服务器已配置SSH密钥，可直接git pull

---

## 项目概述

智能英语单词学习和抗遗忘系统，支持多用户管理、学生管理、单词管理、学习进度跟踪和多阶段学习任务。

## 技术栈

- **前端**: Vue 3 + TypeScript + Element Plus + Pinia
- **后端**: FastAPI + Python + SQLAlchemy + SQLite
- **构建工具**: Vite
- **部署**: Nginx + PM2

## 核心功能

### 1. 用户系统
- ✅ 多用户登录（管理员/教师）
- ✅ 角色权限管理
- ✅ 数据按用户隔离
- ✅ 密码重置功能

### 2. 学生管理
- ✅ 学生信息增删改查
- ✅ 课时管理系统
- ✅ 自动课时扣减（大课1.0h，小课0.5h）
- ✅ 课时状态可视化

### 3. 单词管理
- ✅ 单词集管理
- ✅ Excel批量导入
- ✅ 单词增删改查
- ✅ 全局共享单词库

### 4. 课程管理
- ✅ 日程安排
- ✅ 课程状态跟踪（未完成/已完成）
- ✅ 课程类型：单词学习/抗遗忘复习
- ✅ 课程计时器

### 5. 学习系统（三阶段）

#### 第一阶段：基础学习 (`SimpleWordStudy.vue`)
- 5个单词为一组
- 单词卡点击切换中英文显示
- Fisher-Yates随机排序
- 底部显示已学单词

#### 第二阶段：检查阶段 (`WordCheckTask.vue`)
- 红绿箭头标记：绿色=过关，红色=不过关
- 不过关单词隐藏（适合Zoom共享屏幕）
- 支持重新检查

#### 第三阶段：混组检测 (`MixedGroupTest.vue`)
- 累积检测所有已学单词组
- 两种状态：掌握了/需要复习
- 支持跳过已掌握的组

### 6. 训后检测 (`PostLearningTest.vue`)
- 全部单词最终检测
- 通过/不通过标记
- 自动更新学习进度
- 生成三个PDF报告：
  - **中英对照版**：完整学习材料
  - **纯英文版**：中译英练习（右侧留白）
  - **纯中文版**：英译中练习（左侧留白）

### 7. 抗遗忘复习 (`AntiForgetReview.vue`)
- 10次抗遗忘时间表：第1、2、3、5、7、9、12、14、17、21天
- 单词卡点击切换中英文显示
- 五角星标记系统
- 发音按钮（TTS）
- 自动创建抗遗忘日程

### 8. 单词筛选 (`WordFilter.vue`)
- 学习前识别已认识单词
- 自动替换为新单词
- 已认识单词直接标记为已掌握

## 数据管理 (Pinia Stores)

1. **auth.ts** - 用户认证和权限管理
2. **words.ts** - 单词和单词集管理（全局共享）
3. **students.ts** - 学生信息管理（按用户隔离）
4. **schedule.ts** - 课程安排管理（按用户隔离）
5. **learningProgress.ts** - 学习进度跟踪（按用户隔离）
6. **antiForget.ts** - 抗遗忘会话管理
7. **antiForgetSession.ts** - 抗遗忘临时会话
8. **ui.ts** - UI状态管理（课程计时器等）

## 学习流程

```
1. 日程管理 → 点击"学习"
   ↓
2. 学习准备页面
   - 九宫格进度统计
   - 选择学习单词数（5/10/15/20/25/30/自定义）
   ↓
3. 单词筛选（可选）
   - 识别已认识单词
   - 替换为新单词
   ↓
4. 第一阶段：基础学习（5个一组）
   ↓
5. 第二阶段：检查阶段（红绿标记）
   ↓
6. 第三阶段：混组检测（累积所有组）
   ↓
7. 训后检测
   - 最终检测
   - 生成3个PDF报告
   ↓
8. 创建抗遗忘日程
   - 自动创建10次复习课程
   - 设置复习时间
   ↓
9. 抗遗忘复习（10次）
   - 按时间表复习
   - 五角星标记重点
```

## 项目结构

```
tutor/
├── backend/                 # Python FastAPI 后端
│   ├── main.py             # 后端入口
│   └── requirements.txt    # Python 依赖
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   │   ├── Dashboard.vue           # 日程管理
│   │   │   ├── Students.vue            # 学生管理
│   │   │   ├── Words.vue               # 单词管理
│   │   │   ├── Admin.vue               # 系统管理
│   │   │   ├── StudyHome.vue           # 学习准备
│   │   │   ├── WordFilter.vue          # 单词筛选
│   │   │   ├── SimpleWordStudy.vue     # 第一阶段
│   │   │   ├── WordCheckTask.vue       # 第二阶段
│   │   │   ├── MixedGroupTest.vue      # 第三阶段
│   │   │   ├── PostLearningTest.vue    # 训后检测
│   │   │   └── AntiForgetReview.vue    # 抗遗忘复习
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── router/         # 路由配置
│   │   └── components/     # 组件
│   │       └── CourseTimer.vue         # 课程计时器
│   └── package.json        # 前端依赖
└── CLAUDE.md              # 项目开发记录
```

## 路由配置

| 路径 | 组件 | 权限 | 说明 |
|------|------|------|------|
| `/login` | Login | 公开 | 登录页面 |
| `/` | Dashboard | 认证 | 日程管理 |
| `/admin` | Admin | 管理员 | 系统管理 |
| `/students` | Students | 认证 | 学生管理 |
| `/words` | Words | 认证 | 单词管理 |
| `/study/:studentId` | StudyHome | 认证 | 学习准备 |
| `/word-filter/:studentId` | WordFilter | 认证 | 单词筛选 |
| `/simple-study/:studentId` | SimpleWordStudy | 认证 | 基础学习 |
| `/word-check/:studentId` | WordCheckTask | 认证 | 检查阶段 |
| `/mixed-test/:studentId` | MixedGroupTest | 认证 | 混组检测 |
| `/post-test/:studentId` | PostLearningTest | 认证 | 训后检测 |
| `/anti-forget/:studentId` | AntiForgetReview | 认证 | 抗遗忘复习 |

## 启动命令

### 本地开发

**后端启动**：
```bash
cd backend
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python main.py
```

**前端启动**：
```bash
cd frontend
npm install
npm run dev
```

- 后端：http://localhost:8000
- 前端：http://localhost:5173

### 生产构建

```bash
cd frontend
npm run build-only
```

## 部署环境

### 服务器配置
- **IP**: 47.108.248.168
- **系统**: Ubuntu 22.04 LTS
- **CPU**: 2核
- **内存**: 4GB
- **地区**: 成都

### 软件版本
- **Node.js**: v20.19.5
- **Python**: 3.10.12
- **Nginx**: 1.18.0
- **PM2**: 6.0.13

### 性能优化
- Nginx反向代理（高并发支持）
- Gzip压缩（减少70%传输）
- 静态资源缓存（1年）
- PM2进程管理（自动重启）

## 开发注意事项

### 跨用户数据访问
- 教师账号访问管理员创建的课程/学生/单词时，需要传递 `teacherId` 参数
- 使用 `getStudentsByUserId(teacherId)` 获取特定用户的学生
- 使用 `getWordsBySetForUser(teacherId, wordSetName)` 获取特定用户的单词

### 数据持久化
- 所有数据存储在 localStorage
- 数据按用户ID隔离：`students_${userId}`, `schedule_${userId}`, `learningProgress_${userId}`
- 单词库全局共享：`words`, `wordSets`

### 路由参数
- `studentId`: 学生ID
- `wordSet`: 单词集名称
- `teacherId`: 教师ID（用于跨用户访问）
- `totalWords`: 学习单词总数
- `startIndex`: 起始索引

### PDF生成
- 使用 `html2canvas` + `jsPDF`
- 完美支持中文显示
- 三个版本：中英对照/纯英文/纯中文
- 自动包含学生姓名和教师姓名

## 最新更新记录

### 2025-09-29
- ✅ 修复训后检测和抗遗忘的跨用户访问问题
- ✅ PDF完美支持中文显示（html2canvas方案）
- ✅ PDF动态获取学生和教师姓名
- ✅ 同时生成3个PDF：中英对照/纯英文/纯中文
- ✅ 抗遗忘单词卡点击切换中英文显示

### 2025-09-24
- ✅ 新服务器部署完成
- ✅ Nginx + PM2架构优化

### 2025-09-16
- ✅ 单词筛选功能
- ✅ 课时管理系统
- ✅ 课程状态管理
- ✅ 课程计时器

---

**最后更新**: 2025-09-29
**开发者**: Claude Code Assistant
**项目状态**: ✅ 生产环境稳定运行