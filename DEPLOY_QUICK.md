# 快速部署速查表 ⚡

## 本地操作（5分钟）

```bash
# 1. 提交代码
cd /Users/laovexl/Downloads/tutor
git add .
git commit -m "描述更新内容"
git push origin main
```

## 服务器操作（10分钟）

```bash
# 1. 连接服务器
ssh root@47.108.248.168

# 2. 一键部署（复制整段）
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

## 验证

- 访问: http://47.108.248.168:5173
- 测试: 登录 + 查看数据 + 测试新功能

## 如果出问题

```bash
# 恢复数据库
cd /var/www/tutor/backend
./restore_database.sh  # 选择最近的备份
pm2 restart all
```

---

**完整文档**: [DEPLOY_MANUAL.md](DEPLOY_MANUAL.md)
