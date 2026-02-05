# 🚀 定时任务调度器 - 快速参考

## 一分钟快速上手

### 启动调度器
```bash
# 后台运行（生产环境）
./start_scheduler.sh --daemon

# 前台运行（开发测试）
python manage.py start_scheduler

# 测试模式（立即运行一次评估）
./start_scheduler.sh --test
```

### 管理调度器
```bash
# 查看状态
./start_scheduler.sh --status

# 停止服务
./start_scheduler.sh --stop

# 查看日志
tail -f logs/scheduler.log
```

### Web 管理界面
```
http://localhost:8000/scheduler/
```

---

## 📅 定时任务清单

| 任务 | 时间 | 功能 |
|------|------|------|
| 每日机会评估 | 每天 9:00 | 评估投资机会 |
| 每周数据爬取 | 每周一 8:00 | 更新开奖数据 |
| 清理过期记录 | 每天 2:00 | 清理7天前记录 |

---

## 🔧 常用命令

### 手动运行任务
```python
python manage.py shell

from lottery.scheduler import run_job_now
run_job_now('daily_opportunity_check')  # 每日评估
run_job_now('weekly_data_crawl')        # 数据爬取
```

### 查看执行记录
```python
from django_apscheduler.models import DjangoJobExecution
for exec in DjangoJobExecution.objects.order_by('-run_time')[:10]:
    print(f"{exec.run_time} | {exec.job.id} | {exec.status}")
```

---

## 📁 重要文件

```
lottery/scheduler.py              # 调度器核心
lottery/management/commands/      # 管理命令
  └── start_scheduler.py
lottery/templates/lottery/        # Web界面
  └── scheduler_status.html
start_scheduler.sh                # 启动脚本
logs/scheduler.log                # 运行日志
```

---

## 🎯 生产环境部署

### Systemd 服务（推荐）
```bash
# 创建服务文件
sudo nano /etc/systemd/system/lottery-scheduler.service

# 启动服务
sudo systemctl start lottery-scheduler
sudo systemctl enable lottery-scheduler

# 查看状态
sudo systemctl status lottery-scheduler
```

---

## ❓ 故障排查

### 问题：调度器未运行
```bash
# 1. 检查进程
ps aux | grep start_scheduler

# 2. 查看日志
cat logs/scheduler.log

# 3. 测试启动
./start_scheduler.sh --test
```

### 问题：任务未执行
```bash
# 1. 确认调度器运行
./start_scheduler.sh --status

# 2. 检查任务配置
python manage.py shell
from lottery.scheduler import get_scheduler_status
print(get_scheduler_status())

# 3. 手动运行测试
./start_scheduler.sh --test
```

---

## 📚 完整文档

- **详细指南**: [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md)
- **完成报告**: [SCHEDULER_SETUP_COMPLETE.md](SCHEDULER_SETUP_COMPLETE.md)

---

**提示**: 首次使用请运行 `./start_scheduler.sh --test` 验证功能！
