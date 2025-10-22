# 手动部署指南

## 📋 部署前准备（本地操作）

### 第1步: 提交代码到Git

```bash
cd /Users/laovexl/Downloads/tutor

# 查看修改
git status

# 添加所有更改
git add .

# 提交（写清楚更新了什么）
git commit -m "描述你的更新内容"

# 推送到远程仓库
git push origin main
```

### 第2步: 本地构建测试（可选）

```bash
cd /Users/laovexl/Downloads/tutor/frontend
npm run build-only
```

如果构建成功，说明代码没问题。

---

## 🚀 部署到服务器（服务器操作）

### 第1步: 连接服务器

```bash
ssh root@47.108.248.168
# 输入密码
```

### 第2步: 备份数据库（重要！）

```bash
cd /var/www/tutor/backend

# 创建备份（带说明）
./backup_database.sh pre_deploy_$(date +%Y%m%d_%H%M%S) "部署前备份"

# 确认备份成功
./list_backups.sh
```

**输出示例**:
```
✅ 备份成功!
备份文件: /var/www/tutor/backups/database/pre_deploy_20250122_140530.db
文件大小: 1.2M
```

### 第3步: 停止服务

```bash
cd /var/www/tutor
pm2 stop all
```

**输出示例**:
```
[PM2] Applying action stopProcessId on app [all](ids: [ 0 ])
[PM2] [tutor](0) ✓
```

### 第4步: 更新代码

```bash
cd /var/www/tutor
git pull origin main
```

**输出示例**:
```
Updating 7c13cfb..a1b2c3d
Fast-forward
 frontend/src/views/Dashboard.vue | 10 +++++++---
 backend/app/routes/schedule_api.py | 5 +++++
 2 files changed, 12 insertions(+), 3 deletions(-)
```

### 第5步: 更新依赖（如果有变化）

```bash
# 检查Python依赖
cd /var/www/tutor/backend
source venv/bin/activate
pip install -r requirements.txt

# 检查Node依赖（如果package.json有变化）
cd /var/www/tutor/frontend
# npm install  # 通常不需要，除非package.json有变化
```

### 第6步: 重新构建前端

```bash
cd /var/www/tutor/frontend
npm run build-only
```

**输出示例**:
```
✓ built in 4.60s
```

### 第7步: 重启服务

```bash
cd /var/www/tutor
pm2 restart all
```

**输出示例**:
```
[PM2] Applying action restartProcessId on app [all](ids: [ 0 ])
[PM2] [tutor](0) ✓
```

### 第8步: 检查服务状态

```bash
pm2 status
```

**期望输出**:
```
┌─────┬────────┬─────────┬─────────┬─────────┐
│ id  │ name   │ status  │ restart │ uptime  │
├─────┼────────┼─────────┼─────────┼─────────┤
│ 0   │ tutor  │ online  │ 0       │ 5s      │
└─────┴────────┴─────────┴─────────┴─────────┘
```

**如果状态不是 online，查看日志**:
```bash
pm2 logs --err --lines 50
```

### 第9步: 验证部署

在浏览器中访问: **http://47.108.248.168:5173**

测试以下功能：
- ✅ 能否正常登录
- ✅ 数据是否都在
- ✅ 新功能是否正常

### 第10步: 查看日志（可选）

```bash
# 查看实时日志
tail -f /var/www/tutor/backend/logs/app_$(date +%Y-%m-%d).log

# 或使用PM2查看日志
pm2 logs --lines 50
```

---

## 🔄 快速部署命令（复制粘贴版）

连接服务器后，依次执行以下命令：

```bash
# 1. 进入项目目录并备份
cd /var/www/tutor/backend && ./backup_database.sh pre_deploy_$(date +%Y%m%d_%H%M%S) "部署前备份"

# 2. 停止服务
cd /var/www/tutor && pm2 stop all

# 3. 拉取代码
git pull origin main

# 4. 更新Python依赖（通常不需要，除非requirements.txt有变化）
# cd backend && source venv/bin/activate && pip install -r requirements.txt && deactivate

# 5. 重新构建前端
cd /var/www/tutor/frontend && npm run build-only

# 6. 重启服务
cd /var/www/tutor && pm2 restart all

# 7. 查看状态
pm2 status
```

**一行命令版（适合快速部署）**:
```bash
cd /var/www/tutor/backend && ./backup_database.sh pre_deploy_$(date +%Y%m%d_%H%M%S) "部署前备份" && cd /var/www/tutor && pm2 stop all && git pull origin main && cd frontend && npm run build-only && cd .. && pm2 restart all && pm2 status
```

---

## 🚨 如果部署出现问题

### 问题1: 构建失败

**症状**: `npm run build-only` 报错

**解决**:
```bash
# 1. 清理node_modules和缓存
cd /var/www/tutor/frontend
rm -rf node_modules package-lock.json
npm install
npm run build-only

# 2. 如果还是失败，检查磁盘空间
df -h
```

### 问题2: 服务启动失败

**症状**: `pm2 status` 显示 errored 或 stopped

**解决**:
```bash
# 1. 查看错误日志
pm2 logs --err --lines 100

# 2. 常见原因：端口被占用
lsof -ti:8000 | xargs kill -9

# 3. 重启服务
pm2 restart all
```

### 问题3: 数据丢失或损坏

**症状**: 登录后数据不见了

**解决**:
```bash
# 1. 停止服务
pm2 stop all

# 2. 恢复数据库
cd /var/www/tutor/backend
./restore_database.sh  # 选择最近的备份

# 3. 重启服务
pm2 restart all
```

### 问题4: 白屏或前端报错

**症状**: 访问网站显示白屏

**解决**:
```bash
# 1. 检查Nginx配置
nginx -t

# 2. 重启Nginx
systemctl restart nginx

# 3. 清理浏览器缓存
# 在浏览器中按 Cmd+Shift+R 强制刷新
```

---

## 📊 部署检查清单

每次部署前，确认以下事项：

### 部署前
- [ ] 本地测试通过
- [ ] 代码已提交到Git
- [ ] 已推送到远程仓库

### 部署中
- [ ] ✅ **已创建数据库备份**
- [ ] 已停止服务
- [ ] 已拉取最新代码
- [ ] 已重新构建前端
- [ ] 已重启服务

### 部署后
- [ ] 服务状态为 online
- [ ] 网站可以访问
- [ ] 登录功能正常
- [ ] 数据显示正常
- [ ] 核心功能测试通过

---

## 💡 实用技巧

### 技巧1: 使用screen保持会话

如果构建时间长，怕SSH断开：

```bash
# 1. 创建screen会话
screen -S deploy

# 2. 执行部署命令
# ... 你的部署命令 ...

# 3. 如果SSH断开，重新连接后
screen -r deploy  # 恢复会话
```

### 技巧2: 查看实时构建进度

```bash
# 构建时查看详细输出
cd /var/www/tutor/frontend
npm run build-only 2>&1 | tee build.log
```

### 技巧3: 快速检查服务是否正常

```bash
# 检查后端API
curl http://localhost:8000/api/auth/me
# 应该返回401（未登录），说明API正常

# 检查前端
curl -I http://localhost:5173
# 应该返回200，说明Nginx正常
```

### 技巧4: 定期下载备份到本地

在**本地Mac**上执行：

```bash
# 创建本地备份目录
mkdir -p ~/tutor_backups

# 下载最新备份
scp root@47.108.248.168:/var/www/tutor/backups/database/backup_*.db ~/tutor_backups/
```

---

## 📝 部署日志模板

建议每次部署后记录：

```
部署日期: 2025-01-22 14:30
操作人: [你的名字]
更新内容: [修复了什么/添加了什么功能]

备份文件: pre_deploy_20250122_143000.db
Git commit: a1b2c3d

验证结果:
✅ 登录正常
✅ 数据完整
✅ 新功能正常

备注: 无问题
```

---

## 🔐 安全提醒

1. **每次部署前必须备份数据库**
2. **不要在生产环境直接修改数据库**
3. **不要删除备份文件**
4. **部署后必须验证功能**
5. **有问题立即回滚**

---

**最后更新**: 2025-01-22
**文档版本**: 1.0
