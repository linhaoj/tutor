# 英语陪练系统开发记录

## 📖 新 Claude Code 会话快速上手指南

> **给新 Claude Code 会话的提示**：请仔细阅读本节，了解项目当前状态和开发环境。

### 项目概况
- **项目类型**：智能英语单词学习和抗遗忘系统
- **架构**：Vue 3 (前端) + FastAPI (后端) + SQLite (数据库)
- **开发环境**：macOS，本地开发 + 阿里云服务器部署
- **当前状态**：✅ 生产环境稳定运行，持续迭代优化

### 开发环境路径
```bash
# 项目根目录
/Users/laovexl/Downloads/tutor

# 后端目录
/Users/laovexl/Downloads/tutor/backend

# 前端目录
/Users/laovexl/Downloads/tutor/frontend

# 数据库文件
/Users/laovexl/Downloads/tutor/backend/english_tutor.db

# 虚拟环境
/Users/laovexl/Downloads/tutor/backend/venv
```

### 快速启动命令

**启动后端**（如果还没运行）：
```bash
cd /Users/laovexl/Downloads/tutor/backend
source venv/bin/activate
python main.py
# 后端运行在 http://localhost:8000
```

**启动前端**（开发模式）：
```bash
cd /Users/laovexl/Downloads/tutor/frontend
npm run dev
# 前端运行在 http://localhost:5173
```

**构建前端**（生产模式）：
```bash
cd /Users/laovexl/Downloads/tutor/frontend
npm run build-only  # 跳过类型检查，速度更快
```

### 常用工具和命令

**检查后端是否运行**：
```bash
lsof -ti:8000  # 如果有输出，说明8000端口被占用
```

**停止后端**：
```bash
lsof -ti:8000 | xargs kill -9
```

**查看数据库**：
- 使用 DB Browser for SQLite 打开 `backend/english_tutor.db`
- 或使用命令行：`sqlite3 backend/english_tutor.db`

**Git操作**：
```bash
git status              # 查看修改
git add .               # 添加所有修改
git commit -m "描述"    # 提交
git push origin main    # 推送到远程
```

### 关键文件位置

**前端核心文件**：
- 日程管理：`frontend/src/views/Dashboard.vue`
- 学生管理：`frontend/src/views/Students.vue`
- 单词管理：`frontend/src/views/Words.vue`
- 学习流程：`frontend/src/views/SimpleWordStudy.vue`（第一阶段）
- 时区工具：`frontend/src/utils/timezone.ts`
- 状态管理：`frontend/src/stores/*.ts`

**后端核心文件**：
- 主入口：`backend/main.py`
- 数据模型：`backend/app/models.py`
- 认证API：`backend/app/routes/auth.py`
- 学生API：`backend/app/routes/students_api.py`
- 课程API：`backend/app/routes/schedule_api.py`
- 单词API：`backend/app/routes/words_api.py`

### 最近的重要修改（需要注意）

1. **时区处理**（2025-10-22）：
   - 系统现在统一使用**本地时区**判断"今天"
   - 不要使用 `new Date().toISOString().split('T')[0]`（这是UTC）
   - 正确方式见 `frontend/src/stores/schedule.ts:162-166`

2. **性能优化**（2025-10-22）：
   - WordFilter 使用批量查询，避免 N+1 问题
   - 使用 `getAllWordProgress` 而非循环调用 `getWordProgress`

3. **字段命名**：
   - 后端API返回：snake_case (`learn_date`, `word_set_name`)
   - 前端使用时要匹配这个格式

### 常见问题解决

**问题1：Cannot find module**
```bash
cd frontend
npm install  # 重新安装依赖
```

**问题2：端口被占用**
```bash
lsof -ti:8000 | xargs kill -9  # 后端
lsof -ti:5173 | xargs kill -9  # 前端
```

**问题3：数据库锁定**
```bash
# 确保没有其他进程访问数据库
lsof backend/english_tutor.db
```

**问题4：虚拟环境找不到**
```bash
cd backend
python -m venv venv  # 重新创建
source venv/bin/activate
pip install -r requirements.txt
```

### 开发规范

1. **修改前先读取文件**：使用 Read 工具读取文件后再使用 Edit 或 Write
2. **使用批量操作**：多个独立的 API 调用尽量并行执行
3. **保持一致性**：遵循现有的代码风格和命名规范
4. **更新文档**：重要修改后更新本文件的"最新更新记录"

### 服务器部署信息

- **IP**: 47.108.248.168
- **访问地址**: http://47.108.248.168:5173
- **部署方式**: Nginx + PM2
- **部署路径**: `/var/www/tutor`
- **SSH连接**: `ssh root@47.108.248.168`

部署流程见下方"快速部署指南"。

### 测试账号

**本地/服务器**：
- 管理员：`admin` / `admin123`
- （其他账号可在系统中创建）

### 技术栈速查

- **前端框架**: Vue 3 + TypeScript + Vite
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP客户端**: Axios
- **后端框架**: FastAPI (Python)
- **ORM**: SQLAlchemy
- **数据库**: SQLite
- **认证**: JWT (JSON Web Tokens)

### 下一步工作建议

当前系统已经非常稳定，如果需要继续开发，可以关注：

- [ ] 完善时区支持（创建课程时使用UTC，显示时转换为本地时区）
- [ ] 添加更多的数据统计和可视化
- [ ] 优化移动端显示
- [ ] 添加单元测试
- [ ] 性能监控和日志系统

---

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

## 📚 重要文档

- **[快速部署速查表](DEPLOY_QUICK.md)** ⭐ - 一页纸速查（推荐）
- **[手动部署完整指南](DEPLOY_MANUAL.md)** - 详细的手动部署步骤
- **[数据管理指南](DATA_MANAGEMENT.md)** - 数据备份、恢复和日常维护
- **[部署检查清单](DEPLOYMENT_CHECKLIST.md)** - 部署前检查和注意事项

## 🔧 数据管理工具

### 备份和恢复脚本

项目包含完整的数据管理脚本，确保数据安全：

```bash
# 手动备份数据库
./backend/backup_database.sh [备份名称] [说明]

# 列出所有备份
./backend/list_backups.sh

# 恢复数据库
./backend/restore_database.sh [备份文件]

# 设置自动备份（仅服务器）
sudo ./backend/setup_auto_backup.sh
```

### 快速部署到服务器

**第1步：本地提交代码**
```bash
cd /Users/laovexl/Downloads/tutor
git add .
git commit -m "描述更新内容"
git push origin main
```

**第2步：服务器部署（一行命令）**
```bash
# 连接服务器
ssh root@47.108.248.168

# 复制粘贴以下命令（自动备份+部署+重启）
cd /var/www/tutor/backend && \
./backup_database.sh pre_deploy_$(date +%Y%m%d_%H%M%S) "部署前备份" && \
cd /var/www/tutor && \
pm2 stop all && \
git pull origin main && \
cd frontend && \
npm run build-only && \
cd .. && \
pm2 restart all && \
pm2 status
```

**第3步：验证**
- 访问 http://47.108.248.168:5173
- 测试登录和核心功能

**⚠️ 重要提醒**:
- 每次部署前都会**自动创建数据库备份**
- 备份保留30天
- 如有问题，运行 `./backend/restore_database.sh` 恢复

详细说明请查看：
- [快速部署速查表](DEPLOY_QUICK.md) ⭐ 推荐
- [手动部署完整指南](DEPLOY_MANUAL.md)
- [数据管理指南](DATA_MANAGEMENT.md)

---

## 最新更新记录

### 2025-01-22

#### 业务逻辑修改
- ✅ 修改课时扣减逻辑
  - **单词学习课程**：完成后扣减课时（大课1.0h，小课0.5h）
  - **抗遗忘复习**：完成后不扣减课时
  - 修改文件：`frontend/src/views/AntiForgetReview.vue`
  - 保留文件：`frontend/src/views/PostLearningTest.vue`（单词学习扣课时）

#### 数据管理系统
- ✅ 添加完整的数据备份和恢复系统
  - 创建自动备份脚本（每天凌晨2点）
  - 创建手动备份脚本（支持自定义命名和说明）
  - 创建数据恢复脚本（交互式选择备份）
  - 创建备份列表脚本（查看所有备份）
  - 备份自动保留30天
- ✅ 添加一键部署脚本
  - 自动检查Git状态
  - 自动备份数据库
  - 自动构建和部署
  - 自动验证部署结果
- ✅ 添加完整的数据管理文档
  - 数据管理指南（DATA_MANAGEMENT.md）
  - 部署检查清单（DEPLOYMENT_CHECKLIST.md）
  - 常见问题处理方案
  - 回滚步骤说明

### 2025-10-22
- ✅ 修复时区显示问题：统一使用本地时区判断"今天"
  - 修复 `schedule.ts` 的 `getGroupedSchedules` 使用本地时区而非UTC
  - 修复 `Dashboard.vue` 的 `isToday` 函数使用字符串比较而非Date对象
  - 修复 `formatDate` 函数移除北京时间硬编码，使用本地时区
  - 现在系统会正确显示用户本地时区的"今天"，无论用户在哪个时区
- ✅ UI优化：Dashboard日程管理界面改进
  - 将"未完成"和"已完成"课程从水平排列改为垂直排列
  - 添加可折叠功能：点击标题栏展开/收起课程列表
  - 添加旋转三角箭头图标指示展开状态
  - 未完成课程默认展开，已完成课程默认收起
  - 优化交互体验：标题栏悬停效果和平滑动画
- ✅ 性能优化：单词筛选批量查询
  - 修复WordFilter.vue的N+1查询问题
  - 添加 `getAllWordProgress` 批量查询方法
  - 将2504个API调用优化为1个批量调用
  - 加载时间从4-8分钟缩短到0.5秒以内（>1000x提升）
- ✅ 修复学生端显示问题
  - 修复StudentDashboard.vue字段名不匹配
  - 统一使用snake_case: `learn_date`, `word_set_name`, `last_reviewed_at`

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

## 🔄 多用户系统改造（2025-01-14）

### 改造背景
原系统使用localStorage存储数据，每个浏览器独立，无法跨设备共享。现已改造为真正的多用户系统。

### 架构变化

**改造前**:
```
前端 → localStorage（浏览器本地）
数据隔离：每个设备独立
```

**改造后**:
```
前端 → HTTP API → 后端 → SQLite数据库
数据隔离：按用户ID隔离，支持跨设备访问
```

### 数据库表结构

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `users` | 用户表 | username, password_hash, role |
| `students` | 学生表 | teacher_id, name, remaining_hours |
| `word_sets` | 单词集表 | name, owner_id, is_global |
| `words` | 单词表 | word_set_id, english, chinese |
| `schedules` | 课程安排表 | teacher_id, student_id, date, time |
| `learning_progress` | 学习进度表 | student_id, word_set_name, current_stage |
| `anti_forget_sessions` | 抗遗忘会话表 | student_id, teacher_id, words |

### 后端API文档

#### 🔐 认证API (`/api/auth`)
```bash
# 登录
POST /api/auth/login
Body: { username: "admin", password: "admin123" }
Response: { access_token: "xxx", token_type: "bearer" }

# 获取当前用户信息
GET /api/auth/me
Headers: { Authorization: "Bearer xxx" }

# 注册用户（管理员）
POST /api/auth/register
Headers: { Authorization: "Bearer xxx" }
Body: { username, password, display_name, role }

# 获取所有用户（管理员）
GET /api/auth/users
Headers: { Authorization: "Bearer xxx" }
```

#### 👨‍🎓 学生管理API (`/api/students`)
```bash
# 创建学生
POST /api/students
Headers: { Authorization: "Bearer xxx" }
Body: { name, email, remaining_hours }

# 获取我的学生列表
GET /api/students
Headers: { Authorization: "Bearer xxx" }

# 更新学生信息
PUT /api/students/{student_id}
Headers: { Authorization: "Bearer xxx" }
Body: { name, email, remaining_hours }

# 扣减课时
POST /api/students/{student_id}/deduct-hours
Headers: { Authorization: "Bearer xxx" }
Body: { hours: 1.0 }
```

#### 📚 单词管理API (`/api/words`)
```bash
# 创建单词集
POST /api/words/sets
Headers: { Authorization: "Bearer xxx" }
Body: { name, is_global }

# 获取单词集列表
GET /api/words/sets
Headers: { Authorization: "Bearer xxx" }

# 获取单词集的单词
GET /api/words/sets/{word_set_name}/words
Headers: { Authorization: "Bearer xxx" }

# 添加单词
POST /api/words/sets/{word_set_name}/words
Headers: { Authorization: "Bearer xxx" }
Body: { english, chinese }

# Excel批量导入
POST /api/words/sets/{word_set_name}/import-excel
Headers: { Authorization: "Bearer xxx" }
Form-data: file (Excel文件，必须包含english和chinese列)
```

#### 📅 课程安排API (`/api/schedules`)
```bash
# 创建课程
POST /api/schedules
Headers: { Authorization: "Bearer xxx" }
Body: { student_id, date, time, word_set_name, course_type, duration, class_type }

# 获取我的课程列表
GET /api/schedules
Headers: { Authorization: "Bearer xxx" }

# 标记课程完成
PUT /api/schedules/{schedule_id}/complete
Headers: { Authorization: "Bearer xxx" }
```

#### 📊 学习进度API (`/api/progress`)
```bash
# 创建/更新进度
POST /api/progress
Headers: { Authorization: "Bearer xxx" }
Body: { student_id, word_set_name, word_index, current_stage, total_groups, tasks_completed }

# 获取学生进度
GET /api/progress/student/{student_id}?word_set_name=xxx
Headers: { Authorization: "Bearer xxx" }
```

### 🧪 如何测试多用户功能

#### 方式1: 使用localhost测试（推荐）

**1. 启动后端**
```bash
cd backend
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

**2. 使用API测试工具**

可以使用以下任一工具：
- **Postman** (图形界面，推荐新手)
- **curl** (命令行)
- **HTTPie** (命令行，更友好)

**测试步骤示例（使用curl）**：

```bash
# 1. 登录获取token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# 返回: {"access_token":"eyJ...","token_type":"bearer"}
# 复制 access_token 的值

# 2. 使用token访问API（替换YOUR_TOKEN为上面获取的token）
TOKEN="YOUR_TOKEN"

# 3. 获取当前用户信息
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 4. 创建学生
curl -X POST http://localhost:8000/api/students \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"张三","email":"zhangsan@example.com","remaining_hours":10}'

# 5. 获取学生列表
curl http://localhost:8000/api/students \
  -H "Authorization: Bearer $TOKEN"
```

**3. 测试多用户数据隔离**

```bash
# 创建第二个教师账号（使用admin登录后）
curl -X POST http://localhost:8000/api/auth/register \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username":"teacher1",
    "password":"password123",
    "display_name":"教师1",
    "role":"teacher"
  }'

# 用teacher1登录，获取新token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=teacher1&password=password123"

# 用teacher1的token创建学生
# 然后用admin的token查看学生列表，应该看不到teacher1创建的学生
```

#### 方式2: 浏览器多设备测试

**在localhost测试多用户**：

1. **Chrome正常模式** - 登录admin账号
2. **Chrome隐身模式** - 登录teacher1账号
3. **Firefox** - 登录teacher2账号

这样可以在同一台电脑上模拟多个用户同时使用。

**验证数据隔离**：
- admin创建的学生，teacher1看不到
- teacher1创建的课程，teacher2看不到
- 但所有用户共享单词库（is_global=true的单词集）

#### 方式3: 真实多设备测试

**前提**：后端部署到服务器（47.108.248.168）

1. **电脑A** - http://47.108.248.168:5173 - 登录admin
2. **电脑B** - http://47.108.248.168:5173 - 登录teacher1
3. **手机** - http://47.108.248.168:5173 - 登录teacher2

### 🔍 验证清单

测试以下场景确保多用户系统正常：

- [ ] 用户A创建学生，用户B看不到
- [ ] 用户A创建课程，用户B看不到
- [ ] 用户A和B都能看到全局单词库
- [ ] 用户A在设备1登录，在设备2也能看到数据
- [ ] 退出登录后，token失效，无法访问API
- [ ] 管理员可以看到所有用户列表
- [ ] 普通教师无法创建其他用户

### 📝 测试API工具推荐

**Postman（最推荐）**:
1. 下载：https://www.postman.com/downloads/
2. 创建Collection
3. 设置环境变量：`base_url = http://localhost:8000`
4. 设置授权：Bearer Token
5. 一键发送请求，查看响应

**HTTPie（命令行友好）**:
```bash
# 安装
pip install httpie

# 使用
http POST localhost:8000/api/auth/login username=admin password=admin123
http GET localhost:8000/api/auth/me Authorization:"Bearer YOUR_TOKEN"
```

### 🚨 常见问题

**Q: localhost可以测试多用户吗？**
A: 可以！使用不同浏览器或隐身模式登录不同账号即可。

**Q: 如何重置数据库？**
A: 删除 `backend/english_tutor.db` 文件，重启后端，会自动创建新数据库。

**Q: 忘记admin密码怎么办？**
A: 删除数据库文件重启，会重新创建默认admin账号（admin/admin123）。

**Q: API返回401错误？**
A: token过期或无效，重新登录获取新token。

**Q: 如何查看数据库内容？**
A: 使用SQLite浏览器工具打开 `backend/english_tutor.db`：
- DB Browser for SQLite: https://sqlitebrowser.org/

---

## 📚 下一步工作（前端改造）

### 待完成任务

**阶段8**: 修改前端store连接后端API
- [ ] auth.ts - 改用JWT登录
- [ ] students.ts - 改用REST API
- [ ] words.ts - 改用REST API
- [ ] schedule.ts - 改用REST API
- [ ] learningProgress.ts - 改用REST API
- [ ] 添加axios拦截器处理token

**阶段9**: 本地测试
- [ ] 测试登录/登出
- [ ] 测试多用户数据隔离
- [ ] 测试所有CRUD操作

**阶段10**: 服务器部署
- [ ] 部署后端API到服务器
- [ ] 配置Nginx反向代理
- [ ] 测试生产环境

---

**最后更新**: 2025-01-14
**开发者**: Claude Code Assistant
**项目状态**: 🚧 后端API已完成，前端改造进行中