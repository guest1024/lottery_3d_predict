# Django APScheduler 定时任务使用指南

## 📋 概述

已成功集成 `django-apscheduler` 到 Django 应用中，实现自动化的定时任务调度。

### 已配置的定时任务

| 任务名称 | 执行时间 | 功能说明 |
|---------|---------|---------|
| **每日机会评估** | 每天 9:00 | 评估当前投资机会，生成投注建议 |
| **每周数据爬取** | 每周一 8:00 | 爬取最新开奖数据，更新数据库 |
| **清理过期记录** | 每天 2:00 | 删除7天前的任务执行记录 |

---

## 🚀 快速开始

### 1. 启动定时任务调度器

```bash
# 方式1：持续运行模式（推荐用于生产环境）
python manage.py start_scheduler

# 方式2：测试模式（立即运行一次评估任务）
python manage.py start_scheduler --test
```

### 2. 后台运行（Linux/Mac）

```bash
# 使用 nohup 后台运行
nohup python manage.py start_scheduler > logs/scheduler.log 2>&1 &

# 查看日志
tail -f logs/scheduler.log

# 查看进程
ps aux | grep start_scheduler

# 停止调度器
kill <进程ID>
```

### 3. 使用 systemd 服务（推荐）

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
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start lottery-scheduler

# 设置开机自启
sudo systemctl enable lottery-scheduler

# 查看状态
sudo systemctl status lottery-scheduler

# 查看日志
sudo journalctl -u lottery-scheduler -f

# 停止服务
sudo systemctl stop lottery-scheduler
```

---

## 📁 文件结构

```
lottery_3d_predict/
├── lottery/
│   ├── scheduler.py              # 定时任务调度器模块 ⭐
│   ├── management/
│   │   └── commands/
│   │       └── start_scheduler.py  # Django 管理命令 ⭐
│   └── ...
├── lottery_web/
│   └── settings.py               # Django 配置（已添加 apscheduler） ✅
├── manage.py
└── SCHEDULER_GUIDE.md            # 本文档
```

---

## 🔧 配置详情

### settings.py 配置

```python
INSTALLED_APPS = [
    # ...
    'django_apscheduler',  # ✅ 已添加
    'lottery',
]

# APScheduler 配置
APSCHEDULER_DATETIME_FORMAT = "Y-m-d H:i:s"
APSCHEDULER_RUN_NOW_TIMEOUT = 25  # 超时时间（秒）

# 调度器配置
SCHEDULER_DEFAULT = True
SCHEDULER_AUTOSTART = True
```

### scheduler.py 核心函数

#### 1. `daily_opportunity_check()`
- **功能**: 每日机会评估
- **执行时间**: 每天 9:00
- **输出**: 
  - 当前评分
  - 投注建议
  - 如果评分达标，输出投注计划

#### 2. `weekly_data_crawl()`
- **功能**: 每周数据爬取
- **执行时间**: 每周一 8:00
- **输出**: 
  - 新增数据条数
  - 更新数据条数

#### 3. `cleanup_old_job_executions()`
- **功能**: 清理过期任务记录
- **执行时间**: 每天 2:00
- **输出**: 清理7天前的记录

---

## 🎯 使用示例

### 示例1: 测试模式运行

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

### 示例2: 持续运行模式

```bash
$ python manage.py start_scheduler

======================================================================
启动定时任务调度器
======================================================================

✓ 调度器状态: 运行中

已注册的任务 (3 个):
...

======================================================================
✓ 调度器启动成功，按 Ctrl+C 停止
======================================================================

# 调度器持续运行，到指定时间自动执行任务
# 按 Ctrl+C 停止
```

---

## 📊 数据库表

django-apscheduler 会自动创建以下数据库表：

- `django_apscheduler_djangojob` - 任务定义表
- `django_apscheduler_djangojobexecution` - 任务执行记录表

### 查看任务执行记录

```bash
# 进入 Django shell
python manage.py shell

# 查看最近10次任务执行记录
from django_apscheduler.models import DjangoJobExecution
for exec in DjangoJobExecution.objects.order_by('-run_time')[:10]:
    print(f"{exec.run_time} | {exec.job.id} | {exec.status}")
```

---

## 🔍 调试与日志

### 1. 查看 Django 日志

编辑 `settings.py` 添加日志配置：

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/scheduler.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'lottery.scheduler': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apscheduler': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

创建日志目录：

```bash
mkdir -p logs
```

### 2. 手动触发任务（调试用）

```python
# Python shell
python manage.py shell

from lottery.scheduler import run_job_now

# 立即运行每日评估
run_job_now('daily_opportunity_check')

# 立即运行数据爬取
run_job_now('weekly_data_crawl')
```

---

## ⚙️ 自定义定时任务

### 添加新任务

编辑 `lottery/scheduler.py`:

```python
def my_custom_task():
    """自定义任务"""
    try:
        logger.info("开始执行自定义任务")
        # 你的任务逻辑
        logger.info("自定义任务完成")
    except Exception as e:
        logger.error(f"自定义任务失败: {e}", exc_info=True)

def start_scheduler():
    # ... 现有代码 ...
    
    # 添加新任务：每小时运行
    scheduler.add_job(
        my_custom_task,
        trigger=CronTrigger(minute=0),  # 每小时的第0分钟
        id="my_custom_task",
        max_instances=1,
        replace_existing=True,
        name="我的自定义任务",
    )
```

### Cron 触发器示例

```python
from apscheduler.triggers.cron import CronTrigger

# 每天 9:00
CronTrigger(hour=9, minute=0)

# 每周一 8:00
CronTrigger(day_of_week='mon', hour=8, minute=0)

# 每月1号 0:00
CronTrigger(day=1, hour=0, minute=0)

# 每小时
CronTrigger(minute=0)

# 每30分钟
CronTrigger(minute='*/30')

# 工作日 9:00-18:00 每小时
CronTrigger(day_of_week='mon-fri', hour='9-18', minute=0)
```

---

## ❓ 常见问题

### Q1: 调度器启动后任务不执行？

**检查**:
1. 确认调度器正在运行
2. 检查任务的 `next_run_time`
3. 查看日志中是否有错误

### Q2: 如何修改任务执行时间？

编辑 `lottery/scheduler.py` 中的 `CronTrigger` 参数，然后重启调度器。

### Q3: 任务执行失败怎么办？

1. 查看日志文件 `logs/scheduler.log`
2. 在 Django shell 中手动运行任务测试
3. 检查任务函数中的异常处理

### Q4: 如何停止调度器？

- 前台运行：按 `Ctrl+C`
- 后台运行：`kill <进程ID>`
- systemd 服务：`sudo systemctl stop lottery-scheduler`

---

## 🎉 总结

### ✅ 已完成

1. ✅ 安装 `django-apscheduler` 包
2. ✅ 配置 Django settings
3. ✅ 创建 `lottery/scheduler.py` 调度器模块
4. ✅ 创建 `manage.py start_scheduler` 命令
5. ✅ 运行数据库迁移
6. ✅ 测试定时任务功能

### 📝 任务调度

| 任务 | 时间 | 状态 |
|-----|------|------|
| 每日机会评估 | 每天 9:00 | ✅ 已配置 |
| 每周数据爬取 | 每周一 8:00 | ✅ 已配置 |
| 清理过期记录 | 每天 2:00 | ✅ 已配置 |

### 🚀 下一步

```bash
# 启动调度器（后台运行）
nohup python manage.py start_scheduler > logs/scheduler.log 2>&1 &

# 或者配置 systemd 服务实现开机自启
```

---

**版本**: v1.0  
**创建时间**: 2026-02-05  
**维护者**: AI Assistant
