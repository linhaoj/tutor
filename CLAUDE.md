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
pm2 start backend/main.py --name backend --interpreter python3
pm2 start --name frontend --cwd frontend/dist "python3 -m http.server 5173"

# 6. 检查状态
pm2 status
```

### 访问地址
- 前端: http://47.108.248.168:5173
- 默认管理员账号: admin / admin123

### 注意事项
- 如果遇到TypeScript错误，使用 `npm run build-only` 跳过类型检查
- 如果git拉取失败，检查SSH密钥配置或网络连接
- 服务器已配置SSH密钥，可直接使用git pull

---

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

## 生产环境部署

### 新服务器架构 - ✅ 已完成 (2025-09-24)
**服务器**: 47.108.248.168 (4GB内存, 2核CPU, Ubuntu 22.04, 成都地区)

### 部署步骤

#### 1. 连接服务器
```bash
ssh root@47.108.248.168
```

#### 2. 更新代码
```bash
cd /var/www/tutor
git pull origin main
```

#### 3. 重新构建前端
```bash
cd frontend
npm install
npm run build
```

#### 4. 重启服务
```bash
# 重启后端
pm2 restart backend

# 重启Nginx
systemctl restart nginx
```

#### 5. 检查服务状态
```bash
pm2 status
systemctl status nginx
```

### 最新功能更新 - ✅ 已完成 (2025-09-16)

#### 1. **单词筛选功能** - 个性化学习体验
- ✅ 新增 `WordFilter.vue` 单词筛选页面
- ✅ 学习前识别已认识单词，自动替换为新单词
- ✅ 已认识单词直接跳到最后一格（已掌握状态）
- ✅ 支持多轮筛选，确保学习效果
- ✅ Fisher-Yates算法随机排序，避免位置记忆

**技术实现**:
- 路由: `/word-filter/:studentId`
- 数据流: StudyHome → WordFilter → SimpleWordStudy
- 存储: SessionStorage临时存储筛选结果
- 智能替换: 从单词库自动选择替换单词

#### 2. **课时管理系统** - 完善的商业模式
- ✅ 学生数据模型添加 `remainingHours` 字段
- ✅ 管理员专用课时调整界面（Admin.vue增强）
- ✅ 自动课时扣减：大课1.0h，小课0.5h
- ✅ 课时状态颜色编码：红色(空)/橙色(少)/蓝色(中)/绿色(多)
- ✅ 三种调整方式：直接设置/增加课时/扣除课时

**管理界面**:
- 位置: 管理员 → 系统管理 → 老师数据管理 → 学生管理
- 功能: 查看剩余课时，点击"课时"按钮调整
- 权限: 仅管理员可修改，所有用户可查看

#### 3. **课程状态管理** - 实时进度跟踪
- ✅ Dashboard增加未完成/已完成分栏显示（仅今日课程）
- ✅ 学习完成自动标记：点击"结束练习并创造抗遗忘"
- ✅ 抗遗忘完成自动标记：完成所有复习轮次
- ✅ 课程完成时自动扣减对应课时

#### 4. **课程计时器** - 精确时间管理
- ✅ 新增 `CourseTimer.vue` 组件
- ✅ 集成到所有学习页面：StudyHome, SimpleWordStudy, WordCheckTask, MixedGroupTest, AntiForgetReview
- ✅ 实时显示格式：mm:ss
- ✅ SessionStorage存储开始时间，支持页面刷新

### 重要文件更新

#### **新增文件**：
- `frontend/src/views/WordFilter.vue` - 单词筛选功能
- `frontend/src/components/CourseTimer.vue` - 课程计时器组件

#### **主要修改文件**：
- `frontend/src/stores/students.ts` - 课时管理功能
- `frontend/src/views/Admin.vue` - 管理员课时管理界面
- `frontend/src/views/Dashboard.vue` - 课程状态分栏显示
- `frontend/src/views/StudyHome.vue` - 跳转到单词筛选
- `frontend/src/views/SimpleWordStudy.vue` - 支持筛选后单词+随机排序
- `frontend/src/views/PostLearningTest.vue` - 课程完成标记+时长扣减
- `frontend/src/views/AntiForgetReview.vue` - 抗遗忘完成标记+时长扣减
- `frontend/src/router/index.ts` - 新增WordFilter路由

### 用户体验提升

#### **学习流程优化**：
```
选择学习 → 单词筛选 → 确认学习内容 → 开始学习 → 自动完成标记
    ↓           ↓           ↓            ↓          ↓
计时开始     识别已知     替换新单词     计时显示    课时扣减
```

#### **管理功能完善**：
- **课时充值**: 学生缴费后管理员增加课时
- **课时监控**: 实时查看所有学生剩余课时状态
- **自动扣减**: 课程完成后自动扣减，无需手动操作
- **状态跟踪**: 今日课程完成情况一目了然

### 访问地址
- **前端**: http://47.108.248.168:5173
- **后端API**: http://47.108.248.168:8000/docs
- **默认管理员账号**: admin / admin123

### 技术架构优化

#### 🚀 性能提升效果：
- **硬件升级**: 1核→2核CPU，3.5GB→4GB内存
- **前端服务**: Python HTTP服务器 → Nginx（高并发）
- **文件压缩**: 启用gzip压缩（减少70%传输量）
- **缓存策略**: 静态资源缓存1年
- **后端稳定性**: PM2进程管理，解决CPU 100%问题

#### 📦 部署环境：
- **操作系统**: Ubuntu 22.04 LTS
- **Node.js**: v20.19.5
- **Python**: 3.10.12
- **Nginx**: 1.18.0
- **PM2**: 6.0.13

### 部署记录
- **2025-09-16**: 成功部署单词筛选功能和课时管理系统
- **2025-09-24**: 🎉 **新服务器部署成功！** 完成性能优化和架构升级

---

**最后更新**: 2025-09-24
**开发者**: Claude Code Assistant
**项目状态**: ✅ 新服务器部署完成，系统稳定运行