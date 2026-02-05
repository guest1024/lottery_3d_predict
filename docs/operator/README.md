# 🔧 运维文档

欢迎运维人员！本目录包含系统部署、定时任务管理、监控和维护相关文档。

---

## 📚 文档清单

### 1. [定时任务调度器指南](SCHEDULER_GUIDE.md) ⭐
**适合**: 所有运维人员  
**内容**:
- APScheduler 完整使用指南
- 定时任务配置详解
- Cron 表达式说明
- 日志管理
- 故障排查

**已配置任务**:
| 任务 | 时间 | 功能 |
|------|------|------|
| 每日机会评估 | 每天 9:00 | 自动评估投资机会 |
| 每周数据爬取 | 每周一 8:00 | 更新开奖数据 |
| 清理过期记录 | 每天 2:00 | 清理7天前记录 |

---

### 2. [调度器快速参考](SCHEDULER_QUICK_REFERENCE.md)
**适合**: 日常运维  
**内容**:
- 常用命令速查
- 一键启动/停止
- 状态检查
- 问题排查清单

**快速命令**:
```bash
# 启动调度器
./start_scheduler.sh --daemon

# 查看状态
./start_scheduler.sh --status

# 停止服务
./start_scheduler.sh --stop

# 查看日志
tail -f logs/scheduler.log
```

---

### 3. [调度器安装完成报告](SCHEDULER_SETUP_COMPLETE.md)
**适合**: 初次部署  
**内容**:
- 安装步骤详解
- 配置文件说明
- 测试验证结果
- 完整功能清单
- 生产环境部署方案

---

## 🚀 快速开始

### 启动系统

#### 1. Django Web 服务
```bash
# 开发环境
python manage.py runserver

# 生产环境 (Gunicorn)
gunicorn lottery_web.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
```

#### 2. 定时任务调度器
```bash
# 后台运行（推荐）
./start_scheduler.sh --daemon

# 前台运行（调试用）
python manage.py start_scheduler

# 测试模式
./start_scheduler.sh --test
```

---

## 🏗️ 部署架构

### 开发环境
```
Django Development Server (localhost:8000)
    ↓
SQLite Database (lottery.db, db.sqlite3)
    ↓
Background Scheduler (start_scheduler.sh)
```

### 生产环境（推荐）
```
Nginx (反向代理) :80/:443
    ↓
Gunicorn (WSGI 服务器) :8000
    ↓
Django Application
    ↓
PostgreSQL/MySQL (数据库)
    ↓
Systemd Service (调度器)
```

---

## 📋 部署清单

### 1. 系统要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+)
- **Python**: 3.6+
- **内存**: 最低 2GB，推荐 4GB+
- **磁盘**: 最低 10GB 可用空间
- **网络**: 需要访问彩票数据源

### 2. 依赖安装
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 和依赖
sudo apt install python3 python3-pip python3-venv -y

# 安装项目依赖
pip3 install -r requirements.txt
```

### 3. 数据库初始化
```bash
# 运行迁移
python manage.py migrate

# 导入初始数据（如有）
python manage.py loaddata initial_data.json
```

### 4. 收集静态文件（生产环境）
```bash
python manage.py collectstatic --noinput
```

---

## 🔧 Systemd 服务配置

### Django Web 服务

创建 `/etc/systemd/system/lottery-web.service`:
```ini
[Unit]
Description=Lottery Web Application
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/lottery_3d_predict
ExecStart=/usr/bin/gunicorn lottery_web.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 调度器服务

创建 `/etc/systemd/system/lottery-scheduler.service`:
```ini
[Unit]
Description=Lottery Scheduler Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/c1/program/lottery_3d_predict
ExecStart=/usr/bin/python3 manage.py start_scheduler
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 启动服务
```bash
# 重新加载配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start lottery-web
sudo systemctl start lottery-scheduler

# 设置开机自启
sudo systemctl enable lottery-web
sudo systemctl enable lottery-scheduler

# 查看状态
sudo systemctl status lottery-web
sudo systemctl status lottery-scheduler
```

---

## 🌐 Nginx 配置

创建 `/etc/nginx/sites-available/lottery`:
```nginx
server {
    listen 80;
    server_name lottery.example.com;

    # 静态文件
    location /static/ {
        alias /path/to/lottery_3d_predict/static/;
        expires 30d;
    }

    location /media/ {
        alias /path/to/lottery_3d_predict/media/;
        expires 30d;
    }

    # Django 应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置:
```bash
sudo ln -s /etc/nginx/sites-available/lottery /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 📊 监控与日志

### 日志位置
```
logs/scheduler.log          # 调度器日志
logs/django.log             # Django 日志（需配置）
/var/log/nginx/access.log   # Nginx 访问日志
/var/log/nginx/error.log    # Nginx 错误日志
```

### 查看日志
```bash
# 实时查看调度器日志
tail -f logs/scheduler.log

# 查看最近错误
grep -i error logs/scheduler.log | tail -20

# 查看 systemd 日志
sudo journalctl -u lottery-scheduler -f
sudo journalctl -u lottery-web -f
```

### 日志轮转

创建 `/etc/logrotate.d/lottery`:
```
/path/to/lottery_3d_predict/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        systemctl reload lottery-scheduler > /dev/null 2>&1 || true
    endscript
}
```

---

## 🔍 健康检查

### 系统状态检查脚本
```bash
#!/bin/bash
# health_check.sh

echo "=== 系统健康检查 ==="

# 检查 Web 服务
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ Web 服务正常"
else
    echo "✗ Web 服务异常"
fi

# 检查调度器
if pgrep -f "start_scheduler" > /dev/null; then
    echo "✓ 调度器运行中"
else
    echo "✗ 调度器未运行"
fi

# 检查数据库
if [ -f "lottery.db" ]; then
    echo "✓ 数据库文件存在"
else
    echo "✗ 数据库文件缺失"
fi

# 检查磁盘空间
DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -lt 80 ]; then
    echo "✓ 磁盘空间充足 ($DISK_USAGE%)"
else
    echo "⚠ 磁盘空间不足 ($DISK_USAGE%)"
fi
```

---

## 🛠️ 维护任务

### 日常维护（每天）
```bash
# 1. 查看系统状态
./start_scheduler.sh --status
systemctl status lottery-web

# 2. 查看日志
tail -50 logs/scheduler.log

# 3. 检查磁盘空间
df -h
```

### 周期维护（每周）
```bash
# 1. 备份数据库
cp lottery.db backups/lottery_$(date +%Y%m%d).db
cp db.sqlite3 backups/db_$(date +%Y%m%d).sqlite3

# 2. 清理旧日志
find logs/ -name "*.log.*" -mtime +30 -delete

# 3. 检查系统更新
sudo apt update && sudo apt list --upgradable
```

### 月度维护（每月）
```bash
# 1. 完整备份
tar -czf backups/full_backup_$(date +%Y%m%d).tar.gz \
    lottery.db db.sqlite3 logs/ results/

# 2. 数据库优化
python manage.py dbshell
# SQLite: VACUUM;

# 3. 性能分析
python manage.py check --deploy
```

---

## ⚠️ 故障排查

### 问题1: Web 服务无法访问
**排查步骤**:
```bash
# 1. 检查进程
ps aux | grep gunicorn

# 2. 检查端口
netstat -tlnp | grep 8000

# 3. 查看错误日志
sudo journalctl -u lottery-web -n 50

# 4. 测试本地访问
curl http://localhost:8000/
```

### 问题2: 调度器任务未执行
**排查步骤**:
```bash
# 1. 确认调度器运行
./start_scheduler.sh --status

# 2. 查看日志
tail -50 logs/scheduler.log

# 3. 检查任务配置
python manage.py shell
from lottery.scheduler import get_scheduler_status
print(get_scheduler_status())

# 4. 手动测试任务
./start_scheduler.sh --test
```

### 问题3: 数据库锁定
**解决方案**:
```bash
# 重启服务释放锁
sudo systemctl restart lottery-web
sudo systemctl restart lottery-scheduler

# 考虑迁移到 PostgreSQL
```

### 问题4: 内存不足
**解决方案**:
```bash
# 查看内存使用
free -h
ps aux --sort=-%mem | head

# 减少 Gunicorn workers
# 修改 ExecStart: --workers 2

# 添加 swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 🔐 安全建议

### 1. 防火墙配置
```bash
# 只开放必要端口
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 2. SSL/TLS 配置
```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d lottery.example.com
```

### 3. 数据库安全
- 定期备份
- 限制访问权限
- 加密敏感数据

### 4. 应用安全
- 使用强 SECRET_KEY
- 启用 CSRF 保护
- 限制 DEBUG = False

---

## 📈 性能优化

### 1. 数据库优化
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

### 2. 缓存配置
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 3. 静态文件优化
- 启用 Gzip 压缩
- 设置缓存头
- 使用 CDN

---

## 🔗 相关资源

- [用户文档](../user/README.md) - 系统使用
- [开发者文档](../developer/README.md) - 开发指南
- [投资者文档](../investor/README.md) - 投资策略

---

## 📧 运维支持

紧急问题联系：
- 查看运维日志
- 检查系统状态
- 必要时重启服务

---

**最后更新**: 2026-02-05  
**文档版本**: v1.0  
**维护者**: Operations Team
