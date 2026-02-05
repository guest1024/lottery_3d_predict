# 👥 用户文档

欢迎使用 3D 彩票预测系统！本目录包含系统使用、API 接口和快速入门相关文档。

---

## 📚 文档清单

### 1. [快速开始指南](QUICK_START.md) ⭐
**适合**: 所有新用户  
**内容**:
- 系统安装步骤
- 环境配置
- 第一次运行
- 基础操作示例

**快速开始**:
```bash
# 启动 Web 服务
python manage.py runserver

# 访问系统
http://localhost:8000
```

---

### 2. [Web 应用使用手册](WEB_APP_README.md)
**适合**: Web 界面用户  
**内容**:
- Web 界面功能介绍
- 仪表板使用说明
- 预测功能详解
- 历史数据查询
- 投资策略分析页面

**主要页面**:
- 🏠 首页: 系统概览
- 📊 仪表板: 核心数据展示
- 🔮 预测记录: 查看历史预测
- 💰 投资策略: 策略分析和机会评估
- ⏰ 定时任务: 调度器管理

---

### 3. [API 文档](API_DOCUMENTATION.md)
**适合**: 开发者和程序化用户  
**内容**:
- RESTful API 接口说明
- 请求/响应格式
- 认证方式
- 错误码说明
- 使用示例

**主要接口**:
```bash
# 生成预测
POST /api/predict/

# 爬取数据
POST /api/crawl/

# 运行任务
POST /api/run-task/
```

---

### 4. [URL 测试清单](TEST_URLS.md)
**适合**: 测试和验证用户  
**内容**:
- 所有可访问的 URL 列表
- 页面功能说明
- 测试检查清单

**快速测试**:
```bash
curl http://localhost:8000/
curl http://localhost:8000/dashboard/
curl -X POST http://localhost:8000/api/predict/
```

---

## 🚀 快速导航

### 新手用户路径
1. 📖 阅读 [快速开始指南](QUICK_START.md)
2. 🌐 访问 [Web 应用](WEB_APP_README.md)
3. 🎯 查看 [投资策略页面](../investor/INVESTMENT_STRATEGY_REPORT.md)

### 高级用户路径
1. 📘 学习 [API 文档](API_DOCUMENTATION.md)
2. 💻 编写自动化脚本
3. 🔄 集成到自己的系统

---

## 🎯 常用功能

### 1. 查看今日机会
- 访问: `http://localhost:8000/investment/`
- 查看当前评分和投注建议
- 如果评分 ≥ 58.45，考虑投注

### 2. 生成预测
**Web 界面**:
- 访问首页或仪表板
- 点击"生成预测"按钮

**命令行**:
```bash
curl -X POST http://localhost:8000/api/predict/
```

### 3. 更新数据
**Web 界面**:
- 点击"拉取最新数据"按钮

**命令行**:
```bash
python crawl_real_data.py
```

### 4. 查看历史
- 访问: `http://localhost:8000/history/`
- 筛选日期范围
- 查看开奖号码

---

## 📱 支持的客户端

### Web 浏览器
- ✅ Chrome (推荐)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

### 命令行工具
```bash
# 使用 curl
curl -X POST http://localhost:8000/api/predict/

# 使用 httpie
http POST http://localhost:8000/api/predict/

# 使用 Python
import requests
requests.post('http://localhost:8000/api/predict/')
```

---

## 🔐 安全说明

### API 访问
- 某些 API 已禁用 CSRF 验证（用于测试）
- 生产环境建议启用认证
- 使用 HTTPS 加密传输

### 数据隐私
- 所有数据存储在本地 SQLite 数据库
- 不上传到外部服务器
- 建议定期备份数据

---

## ❓ 常见问题

### Q1: 如何启动系统？
```bash
python manage.py runserver
```

### Q2: 忘记了有哪些页面？
查看 [TEST_URLS.md](TEST_URLS.md) 获取完整列表。

### Q3: API 返回 403 错误？
部分 API 已添加 `@csrf_exempt`，如果仍有问题，检查请求方法是否正确（POST/GET）。

### Q4: 如何查看系统日志？
```bash
# Django 日志
python manage.py runserver

# 调度器日志
tail -f logs/scheduler.log
```

### Q5: 数据库在哪里？
- 主数据库: `lottery.db`
- Django 数据库: `db.sqlite3`

---

## 🔗 相关链接

### 其他角色文档
- 💰 [投资者文档](../investor/README.md) - 投资策略和收益分析
- 👨‍💻 [开发者文档](../developer/README.md) - 开发和调试
- 🔧 [运维文档](../operator/README.md) - 部署和定时任务
- 📊 [分析师文档](../analyst/README.md) - 数据分析和回测

### 项目资源
- [项目 README](../../README.md) - 项目概览
- [项目总结](../PROJECT_SUMMARY.md) - 完整项目说明

---

## 📧 技术支持

遇到问题？
1. 查阅本目录下的文档
2. 查看 [开发者文档](../developer/README.md) 中的修复记录
3. 检查系统日志

---

## 🎨 界面预览

### 首页
- 系统概览
- 快速操作按钮
- 最新预测显示

### 仪表板
- 核心统计数据
- 图表可视化
- 趋势分析

### 投资策略
- 当前评分: 55.65 分
- 阈值: 58.45 分
- 建议: 继续观望

---

**最后更新**: 2026-02-05  
**文档版本**: v1.0  
**适用系统版本**: v1.0
