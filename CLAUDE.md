# 英语陪练系统开发记录

## 项目概述
这是一个智能英语单词学习和抗遗忘系统，支持学生管理、单词管理、学习进度跟踪和多阶段学习任务。

## 技术栈
- **前端**: Vue 3 + TypeScript + Element Plus + Pinia
- **后端**: FastAPI + Python + SQLAlchemy + SQLite
- **构建工具**: Vite

## 项目结构
```
tutor/
├── backend/                 # Python FastAPI 后端
│   ├── app/
│   │   ├── database.py     # 数据库配置
│   │   ├── models.py       # 数据模型
│   │   └── routes/         # API 路由
│   ├── main.py             # 后端入口
│   └── requirements.txt    # Python 依赖
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── router/         # 路由配置
│   │   └── api/            # API 接口
│   └── package.json        # 前端依赖
└── CLAUDE.md              # 项目开发记录
```

## 已完成功能

### 核心功能模块
1. **日程管理** (`Dashboard.vue`)
   - ✅ 课程安排的增删改查
   - ✅ 按日期分组显示课程
   - ✅ 支持"单词学习"和"抗遗忘"两种课程类型
   - ✅ 数据持久化存储到 localStorage

2. **学生管理** (`Students.vue`)
   - ✅ 学生信息管理
   - ✅ 数据持久化存储

3. **单词管理** (`Words.vue`)
   - ✅ 单词的增删改查
   - ✅ 单词集管理
   - ✅ Excel 文件导入功能
   - ✅ 数据持久化存储

### 学习系统 - 三个学习任务
#### 第一个学习任务：基础学习 (`SimpleWordStudy.vue`)
- ✅ 5个单词为一组的学习模式
- ✅ 单词卡点击切换中英文显示
- ✅ 一排一个单词卡的布局设计
- ✅ 大号"学完了"按钮和预留按钮位置
- ✅ 底部小盒子显示已学单词
- ✅ 完成后自动进入第二个学习任务

#### 第二个学习任务：检查阶段 (`WordCheckTask.vue`)
- ✅ 红绿两个箭头：绿色=过关，红色=不过关
- ✅ 点击"不过关"后单词卡隐藏（适合Zoom共享屏幕教学）
- ✅ 只显示红色篮子，不显示具体单词内容（保持学生新鲜感）
- ✅ 过关状态可重新点击修改（防止误操作）
- ✅ 状态切换：红色单词可以从篮子取回重新检查
- ✅ 5个单词都过关后进入第三个学习任务

#### 第三个学习任务：混组检测 (`MixedGroupTest.vue`)
- ✅ 按组顺序检测之前学过的所有组
- ✅ 第x组到这一步时，需要检测第1、2、...、x组
- ✅ 上方"下一组"按钮，支持快速跳过学得好的组
- ✅ 两种检测状态：掌握了(绿色) / 需要复习(黄色)
- ✅ 多层进度显示：总体进度 + 当前组进度
- ✅ 完成所有组检测后可进入最后一步

### 数据管理 (Pinia Stores)
1. **auth.ts** - 用户认证和权限管理 *新增
2. **words.ts** - 单词和单词集管理（全局共享）
3. **students.ts** - 学生信息管理（按用户隔离）
4. **schedule.ts** - 课程安排管理（按用户隔离）
5. **learning.ts** - 学习会话和统计数据管理
6. **learningProgress.ts** - 学习进度跟踪管理（按用户隔离）

### 路由配置
- `/login` - 登录页面 (Login)
- `/` - 日程管理 (Dashboard) *需要认证
- `/admin` - 系统管理 (Admin) *需要管理员权限
- `/students` - 学生管理 *需要认证
- `/words` - 单词管理 *需要认证
- `/study/:studentId` - 学习准备页面 (StudyHome) *需要认证
- `/simple-study/:studentId` - 第一个学习任务 *需要认证
- `/word-check/:studentId` - 第二个学习任务 *需要认证
- `/mixed-test/:studentId` - 第三个学习任务 *需要认证
- `/post-test/:studentId` - 训后检测 *需要认证
- `/anti-forget/:studentId` - 抗遗忘复习 (AntiForgetReview) *需要认证
- `/stats` - 统计分析 *需要认证

## 学习流程设计

### 完整学习链条
1. **日程管理** → 点击"学习"按钮
2. **学习准备页面** (StudyHome)：
   - 显示九宫格学习进度统计
   - 选择今日学习单词个数 (5/10/15/20/25/30/自定义)
   - 显示可学习单词统计信息
3. **第一个学习任务** → **第二个学习任务** → **第三个学习任务**

### 学习数据持久化
- 所有学习进度都保存到 localStorage
- 支持页面刷新后继续学习
- 跟踪每个学生每个单词集的详细进度

## 当前开发状态

### 最近完成
- ✅ 修复了Excel导入功能的JavaScript错误
- ✅ 实现了课程数据的持久化存储
- ✅ 创建了完整的三阶段学习任务系统
- ✅ 实现了学习进度管理系统
- ✅ 修复了学习准备页面的显示问题
- ✅ 修复了老师工作台数据加载问题 (2025-09-08)
  - 修复了TeacherHome.vue中学生和课程数据显示为0的问题
  - 使用正确的按用户隔离的数据获取方法（getStudentsByUserId, getSchedulesByUserId）
  - 修复了所有TypeScript构建错误
- ✅ 实现了基于角色的界面权限控制 (2025-09-08)
  - 隐藏了老师界面中的所有编辑/添加/删除按钮
  - Dashboard: 隐藏"添加课程"和"删除"按钮（仅管理员可见）
  - Students: 隐藏"添加学生"按钮和整个操作列（仅管理员可见）  
  - Words: 隐藏"导入Excel"、"添加单词"、"删除单词集"按钮和操作列（仅管理员可见）
  - 老师只能查看数据和执行学习操作，不能修改基础数据
- ✅ 修复了学习页面单词数据加载问题 (2025-09-10)
  - 添加了teacherId参数传递支持跨用户单词数据访问
  - 实现了getWordsBySetForUser方法用于访问教师的单词数据
  - 修复了StudyHome、SimpleWordStudy、WordCheckTask等页面的单词加载
- ✅ 实现了单词打乱功能 (2025-09-10)
  - 在所有学习任务中加入Fisher-Yates洗牌算法
  - 每组5个单词在显示前都会随机打乱顺序
  - 防止学生通过位置记忆单词，提高学习效果
- ✅ 完整实现抗遗忘复习系统 (2025-09-10)
  - 创建了AntiForgetReview.vue复习页面
  - 实现了antiForget.ts数据存储和管理
  - 支持五角星标记系统，标记状态持久化
  - 每个单词集默认需要复习10次
  - 每次复习单词顺序随机打乱，但五角星状态保持
  - 完整的复习进度跟踪和统计

### 技术细节
- 使用 localStorage 进行前端数据持久化
- 所有 Store 都实现了数据的加载和保存
- 学习任务之间通过路由参数传递数据
- 支持多学生、多单词集的并行学习进度跟踪

### 用户认证系统 - ✅ 已完成 (2025-09-04)
1. **多用户登录系统**
   - ✅ 用户名/密码认证
   - ✅ 角色权限管理（管理员/老师）
   - ✅ 数据隔离（按用户ID分组存储）
   - ✅ 路由守卫和权限控制

2. **系统管理功能**
   - ✅ 管理员页面 (`Admin.vue`)
   - ✅ 用户管理（增删改查）
   - ✅ 密码重置功能
   - ✅ 用户数据清理

3. **数据架构优化**
   - ✅ 学生数据按用户隔离 (`students_${userId}`)
   - ✅ 日程数据按用户隔离 (`schedule_${userId}`)
   - ✅ 学习进度按用户隔离 (`learningProgress_${userId}`)
   - ✅ 单词库全局共享（所有用户通用）

4. **默认账号信息**
   - **管理员账号**: `admin` / `admin123`
   - 可通过管理页面创建新的老师账号

## 待开发功能

### 高优先级
1. **最后一个学习任务** - 混组检测完成后的最终环节
2. **抗遗忘模式** - 日程管理中的"抗遗忘"课程类型功能
3. **统计分析页面** - 学习数据的可视化展示
4. **后端API集成** - 将localStorage数据迁移到真实数据库

### 中优先级
1. **学习历史记录** - 详细的学习轨迹追踪
2. **导出功能** - 学习报告和进度导出
3. **数据备份和恢复** - 用户数据的备份机制

### 低优先级
1. **多语言支持**
2. **移动端适配优化**
3. **邮件通知功能**

## 开发注意事项

### 代码规范
- 所有数据修改操作都要调用对应store的保存方法
- 路由跳转时要传递必要的query参数
- 新增页面需要添加到router配置中

### 数据一致性
- Store之间的数据要保持同步
- 学习进度要及时更新和保存
- 页面刷新后数据要正确恢复

### 用户体验
- 所有操作都要有明确的反馈提示
- 防止用户误操作（如删除确认、状态重置等）
- 界面要适合在线教学场景（大按钮、清晰状态）

## 启动命令

### 后端启动
```bash
cd backend
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python main.py
```

### 前端启动
```bash
cd frontend
npm install
npm run dev
```

- 后端：http://localhost:8000
- 前端：http://localhost:5173

## 服务器部署指南

### 手动部署到服务器（推荐）

由于SSH密钥有密码保护，建议使用以下步骤手动更新服务器：

#### 1. 停止现有服务
```bash
ssh admin@39.107.153.217
pm2 stop all
```

#### 2. 更新代码
```bash
cd /var/www/tutor
git pull origin main
# 如果拉取失败，使用强制更新：
# git fetch --all
# git reset --hard origin/main
```

#### 3. 重新构建前端
```bash
cd /var/www/tutor/frontend
npm install
npm run build
```

#### 4. 重启服务
```bash
cd /var/www/tutor
# 启动后端
pm2 start backend/main.py --name backend --interpreter python3
# 启动前端
pm2 start --name frontend --cwd frontend/dist "python3 -m http.server 5173"
```

#### 5. 检查服务状态
```bash
pm2 status
```

### 重要文件更新

如果需要单独更新特定文件，主要的新增和修改文件：

1. **新增认证系统文件**：
   - `frontend/src/stores/auth.ts`
   - `frontend/src/views/Login.vue`
   - `frontend/src/views/Admin.vue`

2. **修改过的现有文件**：
   - `frontend/src/router/index.ts` (添加路由守卫)
   - `frontend/src/App.vue` (添加登录逻辑)
   - `frontend/src/stores/students.ts` (数据隔离)
   - `frontend/src/stores/schedule.ts` (数据隔离)
   - `frontend/src/stores/learningProgress.ts` (数据隔离)

### 访问地址
- 前端: http://39.107.153.217:5173
- 后端: http://39.107.153.217:8000
- **默认管理员账号**: admin / admin123

---

**最后更新**: 2025-09-04
**开发者**: Claude Code Assistant  
**项目状态**: 已实现多用户登录系统，准备部署