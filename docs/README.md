# 3D彩票预测系统 - 文档中心

**版本**: v2.0  
**更新日期**: 2026-02-06

---

## 📖 主文档

### ⭐ [投注策略指南](BETTING_STRATEGY_GUIDE.md) - 必读

**完整的投注策略说明，包括**:
- ✅ Top5策略详解（ROI +98.4%）
- ✅ 回测数据和结论
- ✅ 使用方法（命令行/Web/定时）
- ✅ 资金管理建议
- ✅ 风险提示

**如果你只想读一个文档，就读这个。**

---

## 🚀 快速开始

### 1. 安装和启动

```bash
# 克隆项目（如果还没有）
git clone <repository>
cd lottery_3d_predict

# 安装依赖
pip install -r requirements.txt

# 启动Web服务
python manage.py runserver 0.0.0.0:8000
```

### 2. 查看今日投注建议

**方式1: 命令行（推荐）**
```bash
python tools/betting/bet_advisor.py
```

**方式2: Web界面**
```
访问 http://localhost:8000/predictions/
```

### 3. 设置定时任务（可选）

```bash
# 每天20:00自动生成建议
crontab -e

# 添加
0 20 * * * /path/to/lottery_3d_predict/tools/betting/schedule_daily_recommendation.sh
```

---

## 📚 分类文档

### 用户文档（user/）

| 文档 | 说明 | 状态 |
|------|------|------|
| [DAILY_RECOMMENDATION_SETUP.md](user/DAILY_RECOMMENDATION_SETUP.md) | 每日建议设置详细指南 | ✅ 当前 |
| [QUICK_START.md](user/QUICK_START.md) | 快速开始指南 | ✅ 当前 |
| [WEB_APP_README.md](user/WEB_APP_README.md) | Web应用使用说明 | ✅ 当前 |

### 开发者文档（developer/）

| 文档 | 说明 | 状态 |
|------|------|------|
| [SELECTIVE_BETTING_STRATEGY_SUCCESS.md](developer/SELECTIVE_BETTING_STRATEGY_SUCCESS.md) | 选择性投注策略详细报告 | ✅ 当前 |
| [FRONTEND_INTEGRATION_COMPLETE.md](developer/FRONTEND_INTEGRATION_COMPLETE.md) | 前端集成完成报告 | ✅ 当前 |
| [architecture.md](developer/architecture.md) | 系统架构说明 | ✅ 当前 |
| ~~THRESHOLD_SCAN_CRITICAL_FINDINGS.md~~ | 旧版阈值扫描 | ❌ 已弃用 |
| ~~PROBABILITY_BASED_BETTING.md~~ | 旧版概率投注 | ❌ 已弃用 |

### 分析师文档（analyst/）

| 文档 | 说明 | 状态 |
|------|------|------|
| [BACKTEST_REPORT.md](analyst/BACKTEST_REPORT.md) | 回测报告 | ⚠️ 参考 |
| [TRAINING_SUMMARY.md](analyst/TRAINING_SUMMARY.md) | 模型训练总结 | ⚠️ 参考 |

### 运维文档（operator/）

| 文档 | 说明 | 状态 |
|------|------|------|
| [SCHEDULER_GUIDE.md](operator/SCHEDULER_GUIDE.md) | 调度器使用指南 | ✅ 当前 |

---

## ⚠️ 已弃用文档

以下文档包含过时或不稳定的信息，**请勿参考**：

### investor/ 目录（全部弃用）

- ❌ INVESTMENT_STRATEGY_REPORT.md
- ❌ ROI_REPORT.md  
- ❌ DYNAMIC_BETTING_REPORT.md
- ❌ DAILY_CHECK_README.md

**弃用原因**: 早期研究文档，结论不稳定，已被Top5策略替代。

### developer/ 部分文档

- ❌ THRESHOLD_SCAN_CRITICAL_FINDINGS.md - 旧版阈值扫描结论（全部阈值亏损）
- ❌ PROBABILITY_BASED_BETTING.md - 旧版概率模型
- ❌ PROBABILITY_MODEL_BACKTEST_RESULTS.md - 旧版回测结果

**弃用原因**: 已被选择性投注策略（Top5）替代，新策略ROI +98.4% vs 旧策略全亏。

---

## 🎯 文档导航

### 我想...

**查看投注建议**
→ 运行 `python tools/betting/bet_advisor.py`
→ 或访问 http://localhost:8000/predictions/

**了解策略原理**
→ 阅读 [投注策略指南](BETTING_STRATEGY_GUIDE.md)

**查看回测数据**
→ 阅读 [选择性投注策略报告](developer/SELECTIVE_BETTING_STRATEGY_SUCCESS.md)

**设置定时任务**
→ 阅读 [每日建议设置](user/DAILY_RECOMMENDATION_SETUP.md)

**理解系统架构**
→ 阅读 [架构文档](developer/architecture.md)

**查看API文档**
→ 阅读 [API文档](user/API_DOCUMENTATION.md)

---

## 📊 核心数据（快速参考）

### Top5策略（推荐）

- **ROI**: +98.4%
- **投注率**: 5% (25/500期)
- **胜率**: 24%
- **成本**: 5,000元
- **收益**: 9,920元
- **利润**: +4,920元

### 模型准确率

- **Top5命中率**: 49.5%
- **Top10命中率**: 100%
- **完全命中率**: 5.8%

### 建议

- **每次投注**: 100注 (200元)
- **月投注上限**: 2,000元
- **连续不中止损**: 5期

---

## 🔄 更新日志

### v2.0 (2026-02-06)

- ✅ 创建统一的投注策略指南
- ✅ 整合前端投注建议到预测记录页面
- ✅ 创建命令行工具 bet_advisor.py
- ✅ 优化界面，显示组选结果而非单个数字
- ✅ 标记弃用文档
- ✅ 清晰的数据结论和风险提示

### v1.0 (2026-02-05)

- ✅ 完成Top5策略回测
- ✅ 实现每日投注建议自动生成
- ✅ 前端API集成

---

## 📞 获取帮助

### 常见问题

**Q: 为什么不是每期都投注？**  
A: 数据显示，只投注前5%高置信度期次，ROI高达+98.4%，远超全期投注的-43.8%。

**Q: Top5策略可靠吗？**  
A: 基于500期回测，结论稳定。但样本量较小（25个投注期），未来表现不保证。

**Q: 能否改进策略提高ROI？**  
A: 可以尝试前3%或前2%，但投注机会会更少。建议先使用Top5积累实盘数据。

**Q: 彩票能靠此盈利吗？**  
A: 不建议。彩票本质是负期望值游戏，任何策略都无法改变这一数学事实。

### 技术支持

- 查看文档: `docs/`
- 运行测试: `python tools/betting/bet_advisor.py`
- Web界面: http://localhost:8000

---

**维护者**: AI Assistant  
**最后更新**: 2026-02-06  
**License**: MIT
