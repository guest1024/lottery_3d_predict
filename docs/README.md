# 📚 3D彩票预测系统 - 文档中心

欢迎来到文档中心！本目录包含项目的所有文档，按照用户角色分类组织。

---

## 🎯 按角色导航

### 💰 [投资者文档](investor/README.md)
**适合人群**: 关注投资策略和收益分析的用户

**包含内容**:
- 投资策略报告（Top1%, Top5%, Top10% 对比）
- ROI 详细分析
- 动态投注策略
- 每日机会评估指南

**核心数据**:
- Top1% 策略: ROI +405%, 胜率 100%
- 评分阈值: 58.45 分
- 历史验证: 7,362 期数据

📂 **文档列表**:
- [投资策略报告](investor/INVESTMENT_STRATEGY_REPORT.md)
- [ROI 报告](investor/ROI_REPORT.md)
- [动态投注策略](investor/DYNAMIC_BETTING_REPORT.md)
- [每日评估指南](investor/DAILY_CHECK_README.md)

---

### 👤 [用户文档](user/README.md)
**适合人群**: 系统使用者、新手用户

**包含内容**:
- 快速开始指南
- Web 应用使用手册
- API 接口文档
- URL 测试清单

**主要功能**:
- 首页和仪表板
- 预测生成
- 历史记录查询
- 投资策略分析

📂 **文档列表**:
- [快速开始](user/QUICK_START.md)
- [Web 应用手册](user/WEB_APP_README.md)
- [API 文档](user/API_DOCUMENTATION.md)
- [URL 测试清单](user/TEST_URLS.md)

---

### 👨‍💻 [开发者文档](developer/README.md)
**适合人群**: 开发和维护人员

**包含内容**:
- 系统架构设计
- 开发指南
- Bug 修复记录
- 更新日志

**技术栈**:
- Backend: Django 3.2+ + SQLite
- Frontend: Bootstrap 5
- AI: PyTorch + NumPy
- Scheduler: APScheduler

📂 **文档列表**:
- [系统架构](developer/architecture.md)
- [所有修复总结](developer/ALL_FIXES_SUMMARY.md)
- [爬虫 API 修复](developer/FIX_CRAWLER_API.md)
- [预测 API 修复](developer/FIX_PREDICT_API.md)
- [Web 界面修复](developer/FIX_WEB_INTERFACE.md)
- [更新日志](developer/CHANGELOG.md)
- [更新记录](developer/UPDATES.md)

---

### 🔧 [运维文档](operator/README.md)
**适合人群**: 系统部署和运维人员

**包含内容**:
- 定时任务配置
- 部署指南
- 监控和日志管理
- 故障排查

**定时任务**:
- 每日机会评估 (9:00)
- 每周数据爬取 (周一 8:00)
- 清理过期记录 (2:00)

📂 **文档列表**:
- [定时任务指南](operator/SCHEDULER_GUIDE.md)
- [快速参考](operator/SCHEDULER_QUICK_REFERENCE.md)
- [安装完成报告](operator/SCHEDULER_SETUP_COMPLETE.md)

---

### 📊 [分析师文档](analyst/README.md)
**适合人群**: 数据分析和研究人员

**包含内容**:
- 回测报告
- 训练记录
- 数据分析
- 特征工程

**数据规模**:
- 历史数据: 7,362 期
- 时间范围: 2003-2026
- 回测期数: 200+ 期
- 策略数量: 3 种

📂 **文档列表**:
- [回测报告](analyst/BACKTEST_REPORT.md)
- [训练总结](analyst/TRAINING_SUMMARY.md)
- [真实数据总结](analyst/REAL_DATA_SUMMARY.md)
- [特征定义](analyst/feature_definitions.md)

---

## 📖 项目总结文档

这些文档提供项目的整体概览和完成情况：

- [项目总结](PROJECT_SUMMARY.md) - 项目完整说明
- [项目完成总结](PROJECT_COMPLETE_SUMMARY.md) - 最终交付总结
- [今日总结](TODAY_SUMMARY.md) - 每日工作记录
- [最终清单](FINAL_CHECKLIST.md) - 完成度检查
- [最终交付](FINAL_DELIVERY.md) - 交付文档
- [交付清单](DELIVERY_CHECKLIST.md) - 交付检查清单
- [最终测试报告](FINAL_TEST_REPORT.md) - 测试结果

---

## 🔍 按功能查找文档

### 投资相关
- [投资策略报告](investor/INVESTMENT_STRATEGY_REPORT.md) - 详细策略分析
- [ROI 报告](investor/ROI_REPORT.md) - 收益率计算
- [每日评估](investor/DAILY_CHECK_README.md) - 日常操作

### 系统使用
- [快速开始](user/QUICK_START.md) - 新手入门
- [Web 应用](user/WEB_APP_README.md) - 界面使用
- [API 文档](user/API_DOCUMENTATION.md) - 接口调用

### 开发维护
- [系统架构](developer/architecture.md) - 架构设计
- [修复记录](developer/ALL_FIXES_SUMMARY.md) - 问题解决
- [更新日志](developer/CHANGELOG.md) - 版本历史

### 部署运维
- [定时任务](operator/SCHEDULER_GUIDE.md) - 调度配置
- [快速参考](operator/SCHEDULER_QUICK_REFERENCE.md) - 常用命令

### 数据分析
- [回测报告](analyst/BACKTEST_REPORT.md) - 历史验证
- [训练记录](analyst/TRAINING_SUMMARY.md) - 模型训练
- [特征定义](analyst/feature_definitions.md) - 特征说明

---

## 📋 文档目录树

```
docs/
├── README.md                          # 本文档（文档中心导航）
│
├── investor/                          # 💰 投资者文档
│   ├── README.md                      # 投资者文档索引
│   ├── INVESTMENT_STRATEGY_REPORT.md  # 投资策略报告
│   ├── ROI_REPORT.md                  # ROI 分析
│   ├── DYNAMIC_BETTING_REPORT.md      # 动态投注策略
│   └── DAILY_CHECK_README.md          # 每日评估指南
│
├── user/                              # 👤 用户文档
│   ├── README.md                      # 用户文档索引
│   ├── QUICK_START.md                 # 快速开始
│   ├── WEB_APP_README.md              # Web 应用手册
│   ├── API_DOCUMENTATION.md           # API 文档
│   └── TEST_URLS.md                   # URL 测试清单
│
├── developer/                         # 👨‍💻 开发者文档
│   ├── README.md                      # 开发者文档索引
│   ├── architecture.md                # 系统架构
│   ├── ALL_FIXES_SUMMARY.md           # 修复总结
│   ├── FIX_CRAWLER_API.md             # 爬虫修复
│   ├── FIX_PREDICT_API.md             # 预测修复
│   ├── FIX_WEB_INTERFACE.md           # 界面修复
│   ├── CHANGELOG.md                   # 更新日志
│   └── UPDATES.md                     # 更新记录
│
├── operator/                          # 🔧 运维文档
│   ├── README.md                      # 运维文档索引
│   ├── SCHEDULER_GUIDE.md             # 定时任务指南
│   ├── SCHEDULER_QUICK_REFERENCE.md   # 快速参考
│   └── SCHEDULER_SETUP_COMPLETE.md    # 安装报告
│
├── analyst/                           # 📊 分析师文档
│   ├── README.md                      # 分析师文档索引
│   ├── BACKTEST_REPORT.md             # 回测报告
│   ├── TRAINING_SUMMARY.md            # 训练总结
│   ├── REAL_DATA_SUMMARY.md           # 数据总结
│   └── feature_definitions.md         # 特征定义
│
└── [项目总结文档]                      # 项目级文档
    ├── PROJECT_SUMMARY.md
    ├── PROJECT_COMPLETE_SUMMARY.md
    ├── FINAL_DELIVERY.md
    └── ...
```

---

## 🚀 快速入口

### 我是新用户
👉 从这里开始: [快速开始指南](user/QUICK_START.md)

### 我想投资
👉 查看策略: [投资策略报告](investor/INVESTMENT_STRATEGY_REPORT.md)

### 我是开发者
👉 了解架构: [系统架构文档](developer/architecture.md)

### 我要部署
👉 部署指南: [定时任务配置](operator/SCHEDULER_GUIDE.md)

### 我要分析
👉 查看数据: [回测报告](analyst/BACKTEST_REPORT.md)

---

## 📱 文档格式说明

所有文档使用 Markdown 格式编写，可以通过以下方式阅读：

1. **GitHub 网页**: 直接在 GitHub 仓库中查看
2. **本地编辑器**: 使用 VSCode, Typora 等编辑器
3. **Markdown 阅读器**: 使用专用的 Markdown 阅读器
4. **转换为 PDF**: 使用 Pandoc 等工具转换

---

## 🔄 文档更新

### 更新频率
- 投资者文档: 重大策略变更时更新
- 用户文档: 功能更新时同步更新
- 开发者文档: 代码变更时及时更新
- 运维文档: 配置变更时更新
- 分析师文档: 数据分析完成后更新

### 版本管理
所有文档底部标注：
- 最后更新时间
- 文档版本
- 维护者信息

---

## 💡 文档贡献

欢迎改进文档！

### 如何贡献
1. 发现文档错误或需要改进的地方
2. 创建 Issue 或直接提交 PR
3. 遵循现有文档的格式和风格
4. 更新文档底部的版本信息

### 文档规范
- 使用 Markdown 格式
- 添加适当的 emoji 提升可读性
- 包含代码示例和截图
- 保持简洁明了
- 定期更新

---

## 📧 获取帮助

找不到需要的信息？

1. 📖 查看相应角色的 README 索引
2. 🔍 使用 Ctrl+F 搜索关键词
3. 💬 在 GitHub Issues 提问
4. 📧 联系项目维护者

---

## 🔗 外部资源

- [Django 官方文档](https://docs.djangoproject.com/)
- [PyTorch 官方文档](https://pytorch.org/docs/)
- [Bootstrap 官方文档](https://getbootstrap.com/)
- [APScheduler 文档](https://apscheduler.readthedocs.io/)

---

**最后更新**: 2026-02-05  
**文档版本**: v1.0  
**维护状态**: ✅ 积极维护

---

<div align="center">
<b>📚 选择您的角色，开始探索文档！</b>

[💰 投资者](investor/README.md) | [👤 用户](user/README.md) | [👨‍💻 开发者](developer/README.md) | [🔧 运维](operator/README.md) | [📊 分析师](analyst/README.md)

[⬆️ 返回项目首页](../README.md)
</div>
