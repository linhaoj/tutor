# 部署检查清单

## 📋 部署前检查

在部署到生产服务器之前，请确认以下事项：

### ✅ 代码检查
- [ ] 所有功能在本地测试通过
- [ ] 没有 console.log 调试代码（或已清理）
- [ ] 代码已提交到 Git
- [ ] Git 状态干净（无未提交的更改）

### ✅ 数据库检查
- [ ] 数据库迁移脚本已准备（如有）
- [ ] 了解数据结构的变化
- [ ] 准备好回滚方案

### ✅ 备份检查
- [ ] **重要！** 已在服务器上创建数据库备份
- [ ] 备份文件已验证完整性
- [ ] 知道如何恢复备份

---

## 🚀 快速部署步骤

### 方式1: 一键部署（推荐）

```bash
# 在项目根目录执行
cd /Users/laovexl/Downloads/tutor
./deploy_to_server.sh
```

脚本会自动执行：
1. 检查Git状态
2. 提交并推送代码
3. 构建前端
4. 备份服务器数据库
5. 停止服务
6. 更新代码
7. 重新构建
8. 重启服务
9. 验证部署

### 方式2: 手动部署（详细控制）

#### 步骤1: 本地准备
```bash
# 1.1 确保代码已提交
cd /Users/laovexl/Downloads/tutor
git status
git add .
git commit -m "描述更新内容"
git push origin main

# 1.2 本地构建测试
cd frontend
npm run build-only
cd ..
```

#### 步骤2: 服务器备份
```bash
# 2.1 连接服务器
ssh root@47.108.248.168

# 2.2 创建备份（重要！）
cd /var/www/tutor/backend
./backup_database.sh pre_deploy_$(date +%Y%m%d) "部署前备份"

# 2.3 确认备份成功
./list_backups.sh
```

#### 步骤3: 部署代码
```bash
# 3.1 停止服务
cd /var/www/tutor
pm2 stop all

# 3.2 拉取最新代码
git pull origin main

# 3.3 检查是否有Python依赖变化
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 3.4 重新构建前端
cd ../frontend
npm run build-only
```

#### 步骤4: 重启服务
```bash
# 4.1 重启所有服务
cd /var/www/tutor
pm2 restart all

# 4.2 检查服务状态
pm2 status

# 4.3 查看日志（确保没有错误）
pm2 logs --lines 50
```

#### 步骤5: 验证部署
```bash
# 5.1 访问网站
# 在浏览器中打开: http://47.108.248.168:5173

# 5.2 测试关键功能
# - 登录
# - 创建/查看学生
# - 创建/查看课程
# - 开始学习流程

# 5.3 查看后端日志
tail -f /var/www/tutor/backend/logs/app_$(date +%Y-%m-%d).log
```

---

## 🔄 部署后验证

### 必须测试的功能

- [ ] **登录功能** - 管理员和教师账号都能正常登录
- [ ] **日程管理** - 能正常创建和查看课程
- [ ] **学生管理** - 能正常添加和编辑学生
- [ ] **单词管理** - 能正常导入和查看单词
- [ ] **学习流程** - 能正常进入学习页面
- [ ] **数据显示** - 所有数据显示正常（无undefined/null）

### 检查要点

```bash
# 1. 检查服务状态
ssh root@47.108.248.168
pm2 status

# 应该显示:
# ┌─────┬────────┬─────────┬─────────┬─────────┐
# │ id  │ name   │ status  │ restart │ uptime  │
# ├─────┼────────┼─────────┼─────────┼─────────┤
# │ 0   │ tutor  │ online  │ 0       │ 5m      │
# └─────┴────────┴─────────┴─────────┴─────────┘

# 2. 检查端口占用
lsof -i:8000  # 后端
lsof -i:5173  # 前端（Nginx）

# 3. 检查最新日志
tail -f /var/www/tutor/backend/logs/app_$(date +%Y-%m-%d).log

# 4. 测试API是否正常
curl http://localhost:8000/api/auth/me  # 应该返回401（未登录）
```

---

## 🚨 回滚步骤

如果部署后发现问题，立即回滚：

### 紧急回滚

```bash
# 1. 连接服务器
ssh root@47.108.248.168

# 2. 停止服务
cd /var/www/tutor
pm2 stop all

# 3. 恢复数据库
cd backend
./restore_database.sh  # 选择最近的备份

# 4. 回退代码（如果需要）
git log --oneline -5  # 查看最近的提交
git reset --hard <上一个提交的hash>

# 5. 重启服务
pm2 restart all

# 6. 验证
pm2 status
```

### 完全回滚到上一个版本

```bash
# 1. 恢复数据库到部署前
./restore_database.sh pre_deploy_YYYYMMDD.db

# 2. 回退Git代码
git log --oneline -10
git reset --hard <上一个稳定版本的hash>

# 3. 重新构建
cd frontend
npm run build-only

# 4. 重启
cd /var/www/tutor
pm2 restart all
```

---

## 📊 常见问题处理

### 问题1: 前端白屏或报错

**症状**: 访问网站显示白屏或控制台有JavaScript错误

**原因**: 前端构建失败或文件损坏

**解决**:
```bash
ssh root@47.108.248.168
cd /var/www/tutor/frontend

# 清理旧构建
rm -rf dist

# 重新构建
npm run build-only

# 检查Nginx配置
nginx -t

# 重启Nginx
systemctl restart nginx
```

### 问题2: 后端API无响应

**症状**: 前端加载了，但是没有数据或一直转圈

**原因**: 后端服务没启动或崩溃了

**解决**:
```bash
ssh root@47.108.248.168

# 检查后端进程
ps aux | grep python

# 检查PM2状态
pm2 status

# 如果服务停止了，重启
pm2 restart all

# 查看错误日志
pm2 logs --err --lines 100
tail -f /var/www/tutor/backend/logs/app_*.log
```

### 问题3: 数据库锁定

**症状**: 后端日志显示 "database is locked"

**原因**: 有其他进程正在访问数据库

**解决**:
```bash
# 1. 查找占用数据库的进程
lsof /var/www/tutor/backend/english_tutor.db

# 2. 停止所有服务
pm2 stop all

# 3. 等待几秒
sleep 5

# 4. 重启服务
pm2 restart all
```

### 问题4: 端口被占用

**症状**: 服务启动失败，提示端口已被占用

**解决**:
```bash
# 查看端口占用
lsof -i:8000  # 后端端口

# 如果有其他进程占用，杀掉它
lsof -ti:8000 | xargs kill -9

# 重启服务
pm2 restart all
```

---

## 📝 部署日志模板

每次部署后，建议记录以下信息：

```
部署日期: 2025-XX-XX
部署时间: XX:XX
操作人员: [你的名字]
部署分支: main
提交hash: [git log -1 --format=%H]
提交说明: [更新了什么功能]

部署前检查:
- [✅] 本地测试通过
- [✅] 数据库已备份
- [✅] 代码已提交

部署步骤:
- [✅] 拉取代码
- [✅] 构建前端
- [✅] 重启服务
- [✅] 验证功能

验证结果:
- [✅] 网站可访问
- [✅] 登录功能正常
- [✅] 核心功能正常

备注:
[有什么特殊情况或需要注意的事项]
```

---

## 🔐 安全提醒

1. **永远不要**在没有备份的情况下部署
2. **永远不要**直接在生产环境修改数据库
3. **永远不要**删除备份文件（除非确认不再需要）
4. **永远记得**部署前先在本地测试
5. **永远记得**部署后验证功能

---

**最后更新**: 2025-01-22
**文档版本**: 1.0
