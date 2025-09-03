# 英语陪练系统 - 阿里云服务器部署指南

## 概述

本指南帮助你将英语陪练系统部署到阿里云服务器上。系统采用前后端分离架构：
- **前端**: Vue 3 + Vite（构建后通过Nginx提供静态文件）
- **后端**: FastAPI + Python（通过PM2管理进程）
- **数据库**: SQLite（本地文件数据库）
- **反向代理**: Nginx

## 系统要求

### 服务器配置推荐
- **CPU**: 2核心以上
- **内存**: 2GB以上
- **存储**: 20GB以上
- **带宽**: 1Mbps以上
- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+

### 必需软件
- Python 3.8+
- Node.js 20+
- Nginx
- Git
- PM2（Node.js进程管理器）

## 快速部署

### 第一步：连接服务器

```bash
# 使用SSH连接到你的阿里云服务器
ssh root@your-server-ip
```

### 第二步：检查和安装依赖

```bash
# 下载项目文件后，运行环境检查
chmod +x check_server_env.sh
./check_server_env.sh

# 如果缺少依赖，运行安装脚本（Ubuntu/Debian）
chmod +x install_dependencies.sh
sudo ./install_dependencies.sh
```

### 第三步：上传项目代码

方式1：使用Git（推荐）
```bash
cd /var/www
git clone your-repository-url tutor
cd tutor
```

方式2：手动上传
```bash
# 使用scp或其他工具上传项目文件到 /var/www/tutor
```

### 第四步：执行部署

```bash
# 给脚本执行权限
chmod +x *.sh

# 运行主部署脚本
sudo ./deploy.sh
```

### 第五步：配置Nginx

```bash
# 配置Nginx反向代理（替换your-domain.com为你的域名或IP）
sudo ./setup_nginx.sh your-domain.com
```

### 第六步：启动服务

```bash
# 启动所有服务
./start_services.sh
```

### 第七步：验证部署

```bash
# 检查服务状态
./monitor.sh
```

访问 `http://your-domain.com` 查看网站是否正常运行。

## 详细部署步骤

### 1. 环境准备

#### 1.1 系统更新
```bash
sudo apt update && sudo apt upgrade -y
```

#### 1.2 安装基础工具
```bash
sudo apt install -y curl wget git vim unzip
```

#### 1.3 安装Python
```bash
sudo apt install -y python3 python3-pip python3-venv python3-dev
```

#### 1.4 安装Node.js 20.x
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt install -y nodejs
```

#### 1.5 安装Nginx
```bash
sudo apt install -y nginx
```

#### 1.6 安装PM2
```bash
sudo npm install -g pm2
```

### 2. 项目部署

#### 2.1 创建项目目录
```bash
sudo mkdir -p /var/www/tutor
cd /var/www/tutor
```

#### 2.2 设置权限
```bash
sudo chown -R $USER:www-data /var/www/tutor
```

#### 2.3 克隆项目
```bash
git clone your-repository-url .
```

#### 2.4 安装后端依赖
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

#### 2.5 初始化数据库
```bash
python3 -c "
from app.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('数据库初始化完成')
"
```

#### 2.6 构建前端
```bash
cd ../frontend
npm install
npm run build
```

### 3. 服务配置

#### 3.1 使用PM2管理后端服务
```bash
# 使用ecosystem.config.js配置文件
pm2 start ecosystem.config.js

# 或直接启动
cd /var/www/tutor/backend
source venv/bin/activate
pm2 start --name "tutor-backend" --interpreter python3 main.py -- --host 0.0.0.0 --port 8000
```

#### 3.2 配置PM2开机自启
```bash
pm2 startup
pm2 save
```

#### 3.3 配置Nginx

创建Nginx配置文件 `/etc/nginx/sites-available/tutor`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名
    
    # 前端静态文件
    location / {
        root /var/www/tutor/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
        
        # 缓存配置
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    client_max_body_size 10M;
    
    access_log /var/log/nginx/tutor_access.log;
    error_log /var/log/nginx/tutor_error.log;
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/tutor /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 4. 防火墙配置

如果使用UFW防火墙：
```bash
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw enable
```

如果使用阿里云安全组，请在控制台开放相应端口。

### 5. SSL证书配置（可选）

#### 5.1 安装Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

#### 5.2 申请证书
```bash
sudo certbot --nginx -d your-domain.com
```

#### 5.3 自动续期
```bash
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

## 维护和监控

### 日常监控
```bash
# 查看服务状态
./monitor.sh

# 查看PM2状态
pm2 status

# 查看日志
pm2 logs tutor-backend
tail -f /var/log/nginx/tutor_error.log
```

### 定期维护
```bash
# 运行维护脚本
sudo ./maintenance.sh
```

### 更新部署
```bash
# 停止服务
pm2 stop tutor-backend

# 更新代码
git pull origin main

# 重新构建前端
cd frontend
npm run build

# 重启后端
cd ../backend
source venv/bin/activate
pip3 install -r requirements.txt
pm2 restart tutor-backend

# 重载Nginx
sudo systemctl reload nginx
```

## 常见问题

### 1. 服务无法启动
- 检查端口是否被占用：`netstat -tlnp | grep 8000`
- 检查Python虚拟环境是否激活
- 查看PM2日志：`pm2 logs tutor-backend`

### 2. 前端页面无法访问
- 检查Nginx配置：`sudo nginx -t`
- 检查前端构建是否成功：`ls -la frontend/dist/`
- 查看Nginx日志：`tail -f /var/log/nginx/tutor_error.log`

### 3. API请求失败
- 确认后端服务正在运行：`pm2 status`
- 检查防火墙设置
- 测试API：`curl http://localhost:8000/docs`

### 4. 数据库问题
- 检查数据库文件权限：`ls -la backend/tutor.db`
- 重新初始化数据库（注意会丢失数据）

### 5. 内存不足
- 调整PM2配置中的`max_memory_restart`
- 考虑升级服务器配置

## 备份策略

### 自动备份
```bash
# 添加到crontab
sudo crontab -e

# 每天凌晨2点执行备份
0 2 * * * /var/www/tutor/maintenance.sh
```

### 手动备份
```bash
# 备份数据库
cp /var/www/tutor/backend/tutor.db /backup/tutor_$(date +%Y%m%d).db

# 备份整个项目（不包含node_modules）
tar -czf /backup/tutor_project_$(date +%Y%m%d).tar.gz \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='*.log' \
  /var/www/tutor
```

## 性能优化

### 1. Nginx优化
```nginx
# 在server块中添加
gzip on;
gzip_vary on;
gzip_min_length 1000;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

### 2. 后端优化
- 考虑使用Gunicorn替代Uvicorn
- 配置数据库连接池
- 添加Redis缓存（如果需要）

### 3. 前端优化
- 启用CDN（可选）
- 配置浏览器缓存
- 压缩静态资源

## 安全建议

1. **定期更新系统和依赖包**
2. **使用强密码和SSH密钥认证**
3. **配置防火墙限制不必要的端口**
4. **启用HTTPS**
5. **定期备份数据**
6. **监控日志文件，及时发现异常**

## 技术支持

如遇到问题，请检查：
1. 系统日志：`/var/log/nginx/`
2. PM2日志：`pm2 logs`
3. 服务状态：运行 `./monitor.sh`

---

**部署完成后，你的英语陪练系统将在 `http://your-domain.com` 上运行**