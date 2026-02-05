# ✅ Django APScheduler 定时任务集成完成

## 🎉 完成概述

已成功将 `django-apscheduler` 集成到 Django 应用中，实现每天自动运行评估的定时任务系统。

---

## 📋 已完成的工作

### 1. ✅ 依赖安装
- 安装 `django-apscheduler` 包（v0.6.2）
- 安装依赖：apscheduler、tzlocal、pytz-deprecation-shim

### 2. ✅ Django 配置
**文件**: `lottery_web/settings.py`

```python
INSTALLED_APPS = [
    # ...
    'django_apscheduler',  # 新增
    'lottery',
]

# APScheduler 配置
APSCHEDULER_DATETIME_FORMAT = "Y-m-d H:i:s"
APSCHEDULER_RUN_NOW_TIMEOUT = 25
SCHEDULER_DEFAULT = True
SCHEDULER_AUTOSTART = True
```

### 3. ✅ 调度器模块
**文件**: `lottery/scheduler.py`

实现了以下功能：
- `daily_opportunity_check()` - 每日机会评估任务
- `weekly_data_crawl()` - 每周数据爬取任务
- `cleanup_old_job_executions()` - 清理过期记录
- `start_scheduler()` - 启动调度器
- `stop_scheduler()` - 停止调度器
- `get_scheduler_status()` - 获取状态
- `run_job_now()` - 立即运行任务

### 4. ✅ Management Command
**文件**: `lottery/management/commands/start_scheduler.py`

命令行工具：
```bash
python manage.py start_scheduler        # 前台运行
python manage.py start_scheduler --test # 测试模式
```

### 5. ✅ 启动脚本
**文件**: `start_scheduler.sh`

```bash
./start_scheduler.sh           # 前台运行
./start_scheduler.sh --daemon  # 后台运行
./start_scheduler.sh --test    # 测试模式
./start_scheduler.sh --stop    # 停止服务
./start_scheduler.sh --status  # 查看状态
```

### 6. ✅ Web 管理界面
**新增页面**: `/scheduler/`

功能：
- 查看调度器运行状态
- 查看已注册任务列表
- 查看最近执行记录
- 手动触发任务运行

**新增 API**: `/api/run-task/`
- POST 请求立即运行指定任务

### 7. ✅ 数据库迁移
已执行迁移，创建表：
- `django_apscheduler_djangojob`
- `django_apscheduler_djangojobexecution`

### 8. ✅ 文档
- `SCHEDULER_GUIDE.md` - 详细使用指南
- `SCHEDULER_SETUP_COMPLETE.md` - 本文档

---

## 📅 已配置的定时任务

| 任务名称 | 任务ID | 执行时间 | 功能说明 |
|---------|--------|---------|---------|
| **每日机会评估** | `daily_opportunity_check` | 每天 9:00 | 评估投资机会，生成投注建议 |
| **每周数据爬取** | `weekly_data_crawl` | 每周一 8:00 | 爬取最新开奖数据 |
| **清理过期记录** | `cleanup_old_job_executions` | 每天 2:00 | 删除7天前的执行记录 |

---

## 🚀 快速开始

### 方式1: 前台运行（开发/测试）
```bash
python manage.py start_scheduler
```

### 方式2: 后台运行（生产环境）
```bash
./start_scheduler.sh --daemon
```

### 方式3: 测试模式（立即运行一次）
```bash
./start_scheduler.sh --test
```

### 查看状态
```bash
./start_scheduler.sh --status
```

### 停止服务
```bash
./start_scheduler.sh --stop
```

---

## 📊 测试结果

### ✅ 测试1: 管理命令测试
```bash
$ python manage.py start_scheduler --test

======================================================================
启动定时任务调度器
======================================================================

✓ 调度器状态: 运行中

已注册的任务 (3 个):

1. 每日机会评估
   ID: daily_opportunity_check
   触发器: cron[hour='9', minute='0']
   下次运行: 2026-02-06 09:00:00+08:00

2. 每周数据爬取
   ID: weekly_data_crawl
   触发器: cron[day_of_week='mon', hour='8', minute='0']
   下次运行: 2026-02-09 08:00:00+08:00

3. 清理过期任务记录
   ID: cleanup_old_job_executions
   触发器: cron[hour='2', minute='0']
   下次运行: 2026-02-06 02:00:00+08:00

======================================================================
🧪 测试模式：立即运行每日评估任务
======================================================================

🎯 每日机会评估
======================================================================
评估时间: 2026-02-05 16:05:08
投注阈值: 58.45分
======================================================================

[1] 加载数据...
✓ 最新一期: 2026-02-04
  开奖号码: [2, 1, 3]

[2] 加载模型并预测...

[3] 计算机会评分...

======================================================================
📊 评分: 55.65分
======================================================================
❌ 继续观望，评分未达到阈值
   评分: 55.65 < 阈值: 58.45
   差距: 2.80分

💡 建议:
   继续等待，下期再评估
   需要评分提升 2.80分

✓ 评估结果已保存到: results/current_opportunity.json
======================================================================

✓ 测试任务执行成功
```

### ✅ 测试2: 后台运行测试
```bash
$ ./start_scheduler.sh --daemon

=======================================================================
启动定时任务调度器 (后台模式)
=======================================================================
✓ 调度器已启动
  进程ID: 3482505
  日志文件: /c1/program/lottery_3d_predict/logs/scheduler.log

查看日志: tail -f /c1/program/lottery_3d_predict/logs/scheduler.log
停止服务: ./start_scheduler.sh --stop
查看状态: ./start_scheduler.sh --status
=======================================================================
```

### ✅ 测试3: 状态查询测试
```bash
$ ./start_scheduler.sh --status

=======================================================================
调度器状态
=======================================================================
状态: ✓ 运行中
进程ID: 3482505
日志文件: /c1/program/lottery_3d_predict/logs/scheduler.log
=======================================================================
```

### ✅ 测试4: 停止服务测试
```bash
$ ./start_scheduler.sh --stop

正在停止调度器...
发现运行中的调度器进程 (PID: 3482505)
✓ 调度器已停止
```

---

## 📁 新增文件清单

```
lottery_3d_predict/
├── lottery/
│   ├── scheduler.py                          # ⭐ 调度器核心模块
│   ├── management/
│   │   ├── __init__.py                       # ✅ 新增
│   │   └── commands/
│   │       ├── __init__.py                   # ✅ 新增
│   │       └── start_scheduler.py            # ⭐ 管理命令
│   ├── templates/lottery/
│   │   └── scheduler_status.html             # ⭐ Web 管理界面
│   ├── urls.py                               # ✅ 已修改（添加路由）
│   └── views.py                              # ✅ 已修改（添加视图）
├── lottery_web/
│   └── settings.py                           # ✅ 已修改（添加配置）
├── logs/                                     # ✅ 新增目录
│   ├── scheduler.log                         # 日志文件
│   └── scheduler.pid                         # PID文件
├── start_scheduler.sh                        # ⭐ 启动脚本
├── SCHEDULER_GUIDE.md                        # ⭐ 使用指南
└── SCHEDULER_SETUP_COMPLETE.md               # ⭐ 本文档
```

---

## 🌐 Web 界面访问

### 调度器管理页面
```
http://localhost:8000/scheduler/
```

功能：
1. ✅ 查看调度器运行状态（运行中/已停止）
2. ✅ 显示已注册任务数量
3. ✅ 列出所有定时任务（任务ID、名称、触发器、下次运行时间）
4. ✅ 手动触发任务运行（"立即运行"按钮）
5. ✅ 查看最近20条执行记录（状态、时间、耗时、异常信息）
6. ✅ 使用说明和命令参考

### 导航栏新增
所有页面的导航栏已添加"定时任务"链接，方便快速访问。

---

## 🔧 自定义定时任务

### 添加新任务

编辑 `lottery/scheduler.py`，添加任务函数：

```python
def my_custom_task():
    """自定义任务"""
    try:
        logger.info("开始执行自定义任务")
        # 你的任务逻辑
        logger.info("自定义任务完成")
    except Exception as e:
        logger.error(f"自定义任务失败: {e}", exc_info=True)
```

在 `start_scheduler()` 函数中注册：

```python
scheduler.add_job(
    my_custom_task,
    trigger=CronTrigger(hour=12, minute=0),  # 每天12:00
    id="my_custom_task",
    max_instances=1,
    replace_existing=True,
    name="我的自定义任务",
)
```

### Cron 触发器示例

```python
# 每天特定时间
CronTrigger(hour=9, minute=30)           # 每天 9:30

# 每周特定时间
CronTrigger(day_of_week='mon', hour=8)   # 每周一 8:00
CronTrigger(day_of_week='0-4', hour=9)   # 周一至周五 9:00

# 每月特定时间
CronTrigger(day=1, hour=0, minute=0)     # 每月1号 0:00

# 间隔时间
CronTrigger(minute='*/30')               # 每30分钟
CronTrigger(hour='*/2')                  # 每2小时
```

---

## 🔍 调试与日志

### 查看日志
```bash
# 实时查看日志
tail -f logs/scheduler.log

# 查看最近日志
tail -50 logs/scheduler.log

# 搜索错误
grep -i error logs/scheduler.log
```

### Django Shell 调试
```bash
python manage.py shell

# 手动运行任务
from lottery.scheduler import run_job_now
run_job_now('daily_opportunity_check')

# 查看任务执行记录
from django_apscheduler.models import DjangoJobExecution
for exec in DjangoJobExecution.objects.order_by('-run_time')[:5]:
    print(f"{exec.run_time} | {exec.job.id} | {exec.status}")
```

---

## 🎯 生产环境部署

### 方式1: Systemd 服务（推荐）

创建服务文件 `/etc/systemd/system/lottery-scheduler.service`:

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

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start lottery-scheduler
sudo systemctl enable lottery-scheduler  # 开机自启
sudo systemctl status lottery-scheduler
```

### 方式2: Supervisor

创建配置文件 `/etc/supervisor/conf.d/lottery-scheduler.conf`:

```ini
[program:lottery-scheduler]
command=/usr/bin/python3 manage.py start_scheduler
directory=/c1/program/lottery_3d_predict
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/c1/program/lottery_3d_predict/logs/scheduler.log
```

启动服务：
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start lottery-scheduler
```

### 方式3: Docker（可选）

```dockerfile
# Dockerfile
FROM python:3.6
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "manage.py", "start_scheduler"]
```

```bash
docker build -t lottery-scheduler .
docker run -d --name scheduler lottery-scheduler
```

---

## 📝 注意事项

### 1. 时区设置
确保 `settings.py` 中的时区正确：
```python
TIME_ZONE = 'Asia/Shanghai'
USE_TZ = True
```

### 2. 任务互斥
每个任务设置了 `max_instances=1`，防止任务重叠执行。

### 3. 错误处理
所有任务都有 try-except 包装，失败不会影响调度器运行。

### 4. 日志管理
定期清理日志文件以防止占用过多空间：
```bash
# 定期清理（可添加到cron）
find logs/ -name "*.log" -mtime +30 -delete
```

### 5. 性能考虑
- 避免在任务中执行耗时操作
- 长时间任务考虑使用 Celery 替代

---

## ❓ 常见问题

### Q1: 调度器未启动怎么办？
**A**: 检查进程是否存在，查看日志文件排查错误。

### Q2: 任务没有按时执行？
**A**: 确认调度器正在运行，检查系统时间是否正确。

### Q3: 如何修改任务执行时间？
**A**: 编辑 `lottery/scheduler.py` 中的 `CronTrigger` 参数，重启调度器。

### Q4: 数据库迁移失败？
**A**: 确保 `django_apscheduler` 已添加到 `INSTALLED_APPS`，然后运行：
```bash
python manage.py migrate
```

### Q5: Web界面显示"未运行"但进程存在？
**A**: 可能是调度器初始化失败，查看日志文件了解详情。

---

## 🎉 总结

### ✅ 完成清单

- [x] 安装 django-apscheduler
- [x] 配置 Django settings
- [x] 创建调度器模块
- [x] 实现管理命令
- [x] 创建启动脚本
- [x] 开发 Web 管理界面
- [x] 运行数据库迁移
- [x] 测试所有功能
- [x] 编写完整文档

### 📊 功能统计

| 功能类型 | 数量 |
|---------|------|
| 定时任务 | 3 个 |
| 管理命令 | 1 个 |
| API 接口 | 1 个 |
| Web 页面 | 1 个 |
| Shell 脚本 | 1 个 |
| 文档文件 | 2 个 |

### 🚀 后续建议

1. **监控告警**: 集成监控系统，任务失败时发送通知
2. **日志分析**: 使用 ELK 或 Grafana 分析日志
3. **性能优化**: 对耗时任务进行性能分析和优化
4. **备份策略**: 定期备份任务执行记录和评估结果
5. **扩展功能**: 根据需求添加更多定时任务

---

## 📚 相关文档

- [SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md) - 详细使用指南
- [Django APScheduler 官方文档](https://github.com/jcass77/django-apscheduler)
- [APScheduler 官方文档](https://apscheduler.readthedocs.io/)

---

**完成时间**: 2026-02-05  
**版本**: v1.0  
**状态**: ✅ 完全可用  
**维护者**: AI Assistant

🎉 **恭喜！定时任务系统已成功集成并可投入使用！**
