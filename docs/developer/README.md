# 👨‍💻 开发者文档

欢迎开发者！本目录包含系统架构、开发指南、问题修复记录和更新日志。

---

## 📚 文档清单

### 1. [系统架构文档](architecture.md) ⭐
**适合**: 所有开发者  
**内容**:
- 系统整体架构设计
- 模块划分和职责
- 数据流图
- 技术栈说明
- 设计模式

**核心架构**:
```
Frontend (Vue3 + TDesign)
    ↓
Backend (Django + SQLite)
    ↓
Core Logic (PyTorch + NumPy)
    ↓
Data Layer (SQLite + JSON)
```

---

### 2. [所有修复总结](ALL_FIXES_SUMMARY.md)
**适合**: 维护和调试  
**内容**:
- 所有已修复问题汇总
- 修复方案详细说明
- 测试验证结果
- 文件变更清单

**已修复的问题**:
1. ✅ JSONDecodeError (投资策略页面)
2. ✅ TemplateSyntaxError (模板过滤器)
3. ✅ NameError (Path 变量)
4. ✅ CSRF 403 (预测 API)
5. ✅ ValueError (期号格式)
6. ✅ CSRF 403 (爬取 API)

---

### 3. [爬虫 API 修复](FIX_CRAWLER_API.md)
**适合**: 数据采集开发  
**内容**:
- 爬虫 API 问题诊断
- CSRF 问题解决方案
- 去重机制实现
- 测试案例

---

### 4. [预测 API 修复](FIX_PREDICT_API.md)
**适合**: 核心功能开发  
**内容**:
- 预测 API 5 个错误修复
- Path 导入问题
- 期号格式转换
- CSRF 豁免配置
- 完整测试流程

---

### 5. [Web 界面修复](FIX_WEB_INTERFACE.md)
**适合**: 前端开发  
**内容**:
- 投资策略页面修复
- JSON 解析问题
- 模板过滤器问题
- 测试步骤

---

### 6. [更新日志](CHANGELOG.md)
**适合**: 追踪版本变化  
**内容**:
- 按版本组织的更新记录
- 新增功能
- Bug 修复
- 重大变更

---

### 7. [更新记录](UPDATES.md)
**适合**: 日常开发跟踪  
**内容**:
- 最新更新内容
- 功能改进
- 性能优化

---

## 🏗️ 项目结构

```
lottery_3d_predict/
├── lottery/                    # Django 应用
│   ├── models.py              # 数据模型
│   ├── views.py               # 视图函数
│   ├── urls.py                # URL 路由
│   ├── scheduler.py           # 定时任务调度器
│   ├── templates/             # HTML 模板
│   └── management/            # 管理命令
├── lottery_web/               # Django 项目配置
│   ├── settings.py            # 项目设置
│   ├── urls.py                # 根 URL 配置
│   └── wsgi.py                # WSGI 配置
├── src/                       # 核心算法
│   ├── models/                # 深度学习模型
│   ├── features/              # 特征工程
│   └── utils/                 # 工具函数
├── docs/                      # 文档目录
├── static/                    # 静态文件
├── logs/                      # 日志文件
├── results/                   # 结果文件
└── manage.py                  # Django 管理脚本
```

---

## 🔧 开发环境设置

### 1. 安装依赖
```bash
# Python 3.6+
pip install -r requirements.txt

# 关键依赖
# - Django 3.2+
# - PyTorch 1.10+
# - django-apscheduler
# - BeautifulSoup4
# - pandas
```

### 2. 数据库迁移
```bash
python manage.py migrate
```

### 3. 创建超级用户（可选）
```bash
python manage.py createsuperuser
```

### 4. 启动开发服务器
```bash
python manage.py runserver
```

---

## 🛠️ 开发指南

### 添加新功能

#### 1. 创建数据模型
```python
# lottery/models.py
class MyModel(models.Model):
    field1 = models.CharField(max_length=100)
    field2 = models.IntegerField()
    
    class Meta:
        db_table = 'my_model'
```

#### 2. 创建迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 3. 添加视图
```python
# lottery/views.py
def my_view(request):
    # 视图逻辑
    return render(request, 'template.html', context)
```

#### 4. 配置 URL
```python
# lottery/urls.py
path('my-url/', views.my_view, name='my_view'),
```

#### 5. 创建模板
```html
<!-- lottery/templates/lottery/template.html -->
{% extends 'base.html' %}
{% block content %}
  <!-- 内容 -->
{% endblock %}
```

---

### 调试技巧

#### 1. Django Shell
```bash
python manage.py shell

# 测试模型
from lottery.models import LotteryPeriod
LotteryPeriod.objects.count()

# 测试功能
from lottery.scheduler import run_job_now
run_job_now('daily_opportunity_check')
```

#### 2. 日志记录
```python
import logging
logger = logging.getLogger(__name__)

logger.info("信息日志")
logger.error("错误日志")
logger.debug("调试日志")
```

#### 3. 断点调试
```python
import pdb; pdb.set_trace()
```

---

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
python manage.py test

# 运行特定应用测试
python manage.py test lottery

# 详细输出
python manage.py test --verbosity=2
```

### 手动测试
```bash
# 测试 API
python test_all_apis.py

# 测试 Web 界面
python test_web_interface.py
```

---

## 📋 编码规范

### Python 代码
- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 函数和类添加 docstring
- 变量命名使用小写下划线

### Django 约定
- 视图函数以 `_view` 结尾
- URL 名称使用下划线
- 模型字段明确定义
- 使用 Django ORM 而非原生 SQL

### 前端代码
- 遵循 Vue3 Composition API 风格
- 使用 TDesign 组件库
- Tailwind CSS 辅助样式
- TypeScript 类型定义

---

## 🔍 常见开发问题

### Q1: CSRF 验证失败？
**解决**: 对 API 视图添加 `@csrf_exempt` 装饰器
```python
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_http_methods(["POST"])
def my_api_view(request):
    pass
```

### Q2: 模板找不到？
**检查**:
1. 模板路径: `lottery/templates/lottery/xxx.html`
2. `INSTALLED_APPS` 包含 `'lottery'`
3. `APP_DIRS = True`

### Q3: 静态文件加载失败？
**检查**:
```python
# settings.py
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# 开发环境收集静态文件
python manage.py collectstatic
```

### Q4: 数据库锁定错误？
**原因**: SQLite 并发限制  
**解决**: 
- 开发环境可忽略
- 生产环境考虑使用 PostgreSQL/MySQL

### Q5: 导入路径错误？
**检查**: 确保项目根目录在 Python 路径中
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

---

## 🔗 相关资源

### 官方文档
- [Django 文档](https://docs.djangoproject.com/)
- [PyTorch 文档](https://pytorch.org/docs/)
- [Vue3 文档](https://vuejs.org/)
- [TDesign 文档](https://tdesign.tencent.com/)

### 项目文档
- [用户文档](../user/README.md) - 使用指南
- [运维文档](../operator/README.md) - 部署和维护
- [分析师文档](../analyst/README.md) - 数据分析

---

## 🚀 贡献指南

### 提交代码
1. 创建功能分支
2. 编写代码和测试
3. 提交 commit（清晰的 message）
4. 推送到远程仓库
5. 创建 Pull Request

### Commit 规范
```
feat: 新增功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建/工具变动
```

---

## 📧 开发支持

遇到技术问题？
1. 查看 [修复记录](ALL_FIXES_SUMMARY.md)
2. 阅读 [架构文档](architecture.md)
3. 查看代码注释和 docstring

---

**最后更新**: 2026-02-05  
**文档版本**: v1.0  
**维护者**: Development Team
