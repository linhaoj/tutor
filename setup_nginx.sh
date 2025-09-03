#!/bin/bash

# Nginx配置脚本

PROJECT_PATH="/var/www/tutor"
DOMAIN=${1:-"localhost"}
BACKEND_PORT=8000

echo "=== 配置Nginx反向代理 ==="
echo "域名: $DOMAIN"
echo ""

# 检查Nginx是否安装
if ! command -v nginx &> /dev/null; then
    echo "安装Nginx..."
    apt update && apt install -y nginx
fi

# 创建Nginx配置文件
echo "创建Nginx配置..."
cat > /etc/nginx/sites-available/tutor << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # 前端静态文件
    location / {
        root $PROJECT_PATH/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        index index.html;
        
        # 缓存配置
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:$BACKEND_PORT/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 支持WebSocket（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 上传文件大小限制
    client_max_body_size 10M;
    
    # 日志配置
    access_log /var/log/nginx/tutor_access.log;
    error_log /var/log/nginx/tutor_error.log;
}
EOF

# 启用站点
echo "启用Nginx站点配置..."
ln -sf /etc/nginx/sites-available/tutor /etc/nginx/sites-enabled/

# 删除默认站点（如果存在）
rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
echo "测试Nginx配置..."
nginx -t

if [ $? -eq 0 ]; then
    # 重启Nginx
    echo "重启Nginx服务..."
    systemctl restart nginx
    systemctl enable nginx
    
    echo ""
    echo "=== Nginx配置完成 ==="
    echo ""
    echo "网站访问地址: http://$DOMAIN"
    echo "API访问地址: http://$DOMAIN/api/"
    echo ""
    echo "如需HTTPS，请安装SSL证书："
    echo "sudo apt install certbot python3-certbot-nginx"
    echo "sudo certbot --nginx -d $DOMAIN"
else
    echo "Nginx配置测试失败，请检查配置文件"
    exit 1
fi