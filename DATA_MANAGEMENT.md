# 数据管理指南

## 📖 概述

本文档介绍如何管理英语陪练系统的数据，包括备份、恢复和日常维护。

---

## 🗂️ 数据存储位置

### 生产环境（服务器）
- **数据库文件**: `/var/www/tutor/backend/english_tutor.db`
- **备份目录**: `/var/www/tutor/backups/database/`
- **日志目录**: `/var/www/tutor/backups/logs/`

### 本地开发环境
- **数据库文件**: `/Users/laovexl/Downloads/tutor/backend/english_tutor.db`
- **备份目录**: `/Users/laovexl/Downloads/tutor/backend/backups/database/`

---

## 💾 数据备份

### 1. 手动备份（推荐在更新前使用）

```bash
# 连接服务器
ssh root@47.108.248.168

# 进入后端目录
cd /var/www/tutor/backend

# 创建备份（带说明）
./backup_database.sh pre_update_20250122 "更新前备份"

# 或者简单备份（自动命名）
./backup_database.sh
```

**输出示例**:
```
📦 开始备份数据库...
源文件: /var/www/tutor/backend/english_tutor.db
目标文件: /var/www/tutor/backups/database/pre_update_20250122.db
✅ 备份成功!
备份文件: /var/www/tutor/backups/database/pre_update_20250122.db
文件大小: 1.2M
```

### 2. 自动备份（每天凌晨2点）

服务器已配置自动备份，无需手动操作。

**设置自动备份**（首次部署时）:
```bash
ssh root@47.108.248.168
cd /var/www/tutor/backend
sudo ./setup_auto_backup.sh
```

**查看自动备份日志**:
```bash
tail -f /var/www/tutor/backups/logs/auto_backup.log
```

### 3. 查看所有备份

```bash
cd /var/www/tutor/backend
./list_backups.sh
```

**输出示例**:
```
📋 数据库备份列表
================================

备份目录: /var/www/tutor/backups/database
备份总数: 15
占用空间: 18M

--------------------------------

备份 #1
  文件名: backup_20250122_140530.db
  大小:   1.2M
  时间:   2025-01-22 14:05:30 (0天前)
  说明:   自动备份

备份 #2
  文件名: pre_update_20250122.db
  大小:   1.2M
  时间:   2025-01-22 10:00:00 (0天前)
  说明:   更新前备份
```

---

## 🔄 数据恢复

### 场景1: 从列表中选择备份恢复

```bash
ssh root@47.108.248.168
cd /var/www/tutor/backend

# 运行恢复脚本（会显示备份列表）
./restore_database.sh
```

**交互式选择**:
```
🔄 数据库恢复工具
================================
📋 可用的备份文件:

 1) backup_20250122_140530.db
    时间: 2025-01-22 14:05:30  大小: 1.2M

 2) pre_update_20250122.db
    时间: 2025-01-22 10:00:00  大小: 1.2M

请输入要恢复的备份编号 (1-2)，或按 Ctrl+C 取消: 2

⚠️  警告: 此操作将覆盖当前数据库！
是否继续? (yes/no): yes

📦 创建紧急备份...
✅ 紧急备份已保存: /var/www/tutor/backups/database/emergency_backup_20250122_141000.db

🛑 停止后端服务...
✅ 后端服务已停止

🔄 开始恢复数据库...
✅ 数据库恢复成功!

🔍 验证数据库完整性...
✅ 数据库完整性检查通过

✨ 恢复完成!

⚠️  请手动重启后端服务:
   cd /var/www/tutor/backend && pm2 restart all
```

### 场景2: 指定备份文件恢复

```bash
# 恢复指定的备份文件
./restore_database.sh pre_update_20250122.db

# 或使用完整路径
./restore_database.sh /var/www/tutor/backups/database/backup_20250122_140530.db
```

### 场景3: 紧急恢复（恢复过程出错）

如果恢复过程中出现问题，系统会自动创建紧急备份。你可以从紧急备份恢复：

```bash
./restore_database.sh emergency_backup_20250122_141000.db
```

---

## 🚨 常见故障处理

### 问题1: 数据丢失或损坏

**症状**: 打开系统后数据不见了，或者系统报错

**解决方案**:
```bash
# 1. 连接服务器
ssh root@47.108.248.168

# 2. 停止服务
cd /var/www/tutor/backend
pm2 stop all

# 3. 查看可用备份
./list_backups.sh

# 4. 选择最近的备份恢复
./restore_database.sh

# 5. 重启服务
pm2 restart all

# 6. 验证数据
# 在浏览器中访问 http://47.108.248.168:5173
# 检查数据是否恢复正常
```

### 问题2: 更新后数据出现异常

**症状**: 更新系统后，某些功能不正常或数据显示错误

**解决方案**:
```bash
# 1. 恢复到更新前的备份
ssh root@47.108.248.168
cd /var/www/tutor/backend
./restore_database.sh pre_update_YYYYMMDD.db

# 2. 重启服务
pm2 restart all

# 3. 如果问题解决，说明是更新导致的数据兼容性问题
# 4. 联系开发人员修复兼容性问题
```

### 问题3: 备份文件损坏

**症状**: 恢复时提示数据库完整性检查失败

**解决方案**:
```bash
# 1. 尝试使用更早的备份
./list_backups.sh  # 查看所有备份
./restore_database.sh  # 选择更早的备份

# 2. 如果所有备份都损坏，检查硬盘空间
df -h

# 3. 如果硬盘空间不足，清理日志文件
cd /var/www/tutor/backend/logs
rm -f app_*.log  # 删除旧日志（谨慎操作！）

# 4. 最坏情况：从头开始
# 注意：这会丢失所有数据！
rm english_tutor.db
pm2 restart all  # 后端会自动创建新数据库
```

---

## 📅 日常维护建议

### 每周检查

```bash
# 1. 登录服务器
ssh root@47.108.248.168

# 2. 查看备份状态
cd /var/www/tutor/backend
./list_backups.sh

# 3. 检查磁盘空间
df -h

# 4. 查看后端日志（检查是否有错误）
tail -n 50 logs/app_$(date +%Y-%m-%d).log
```

### 每月维护

```bash
# 1. 下载重要备份到本地
scp root@47.108.248.168:/var/www/tutor/backups/database/backup_YYYYMMDD.db ~/backups/

# 2. 清理超过30天的日志
cd /var/www/tutor/backend/logs
find . -name "*.log" -mtime +30 -delete

# 3. 检查数据库大小
du -h /var/www/tutor/backend/english_tutor.db
```

---

## 🔐 安全建议

### 1. 定期下载备份到本地

```bash
# 在本地Mac上执行
mkdir -p ~/tutor_backups
scp root@47.108.248.168:/var/www/tutor/backups/database/backup_*.db ~/tutor_backups/
```

### 2. 重要操作前必须备份

**以下操作前必须先备份**:
- ✅ 更新系统代码
- ✅ 修改数据库结构
- ✅ 批量导入/删除数据
- ✅ 升级Python依赖
- ✅ 修改配置文件

**备份命令**:
```bash
./backup_database.sh pre_$(date +%Y%m%d) "操作说明"
```

### 3. 备份文件命名规范

推荐使用以下命名格式：
- `pre_update_YYYYMMDD` - 更新前备份
- `pre_import_YYYYMMDD` - 导入数据前备份
- `weekly_YYYYMMDD` - 每周备份
- `emergency_YYYYMMDD_HHMMSS` - 紧急备份（自动创建）

---

## 📊 备份策略

### 自动备份
- **频率**: 每天凌晨 2:00
- **保留期**: 30天
- **存储位置**: `/var/www/tutor/backups/database/`

### 手动备份
- **更新前**: 必须手动备份
- **重要操作前**: 建议手动备份
- **命名**: 使用有意义的名称和说明

### 本地备份
- **频率**: 每周下载一次到本地
- **保留期**: 永久保留重要备份
- **存储位置**: `~/tutor_backups/`

---

## 🛠️ 脚本使用速查

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| `backup_database.sh` | 手动备份数据库 | `./backup_database.sh [名称] [说明]` |
| `restore_database.sh` | 恢复数据库 | `./restore_database.sh [备份文件]` |
| `list_backups.sh` | 列出所有备份 | `./list_backups.sh` |
| `setup_auto_backup.sh` | 设置自动备份 | `sudo ./setup_auto_backup.sh` |

---

## 📞 紧急联系

如果遇到无法解决的数据问题：

1. **不要慌张** - 系统有自动备份
2. **停止操作** - 避免进一步损坏数据
3. **查看备份** - 运行 `./list_backups.sh`
4. **尝试恢复** - 从最近的备份恢复
5. **记录错误** - 保存错误日志和截图
6. **寻求帮助** - 联系技术支持

---

**最后更新**: 2025-01-22
**文档版本**: 1.0
