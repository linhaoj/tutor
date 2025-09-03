// PM2进程管理配置文件
module.exports = {
  apps: [
    {
      name: 'tutor-backend',
      script: 'main.py',
      cwd: '/var/www/tutor/backend',
      interpreter: 'python3',
      interpreter_args: '',
      args: '--host 0.0.0.0 --port 8000',
      instances: 1,
      exec_mode: 'fork',
      
      // 环境变量
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/var/www/tutor/backend'
      },
      
      // 重启策略
      autorestart: true,
      watch: false,  // 生产环境建议关闭
      max_memory_restart: '500M',
      
      // 日志配置
      log_file: '/var/log/pm2/tutor-backend.log',
      out_file: '/var/log/pm2/tutor-backend-out.log',
      error_file: '/var/log/pm2/tutor-backend-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      
      // 其他配置
      min_uptime: '10s',
      max_restarts: 10,
      restart_delay: 4000
    }
  ]
};