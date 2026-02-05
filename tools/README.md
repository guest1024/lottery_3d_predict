# 🔧 工具脚本目录

本目录包含项目的各类工具脚本，按功能分类组织。

## 📂 目录结构

```
tools/
├── crawlers/          # 🕷️ 数据爬虫脚本
├── analysis/          # 📊 分析工具脚本
├── strategies/        # 💡 投注策略脚本
├── training/          # 🎓 模型训练脚本
├── import_data.py     # 数据导入工具
├── generate_mock_data.py       # 模拟数据生成
└── generate_strategy_summary.py # 策略报告生成
```

---

## 🕷️ crawlers/ - 数据爬虫

数据采集相关脚本。

### 文件列表
- `crawl_data.py` - 基础数据爬取
- `crawl_auto.py` - 自动化爬取
- `crawl_all.py` - 批量全量爬取
- `crawl_real_data.py` - 真实数据爬取

### 使用示例
```bash
# 基础爬取
python tools/crawlers/crawl_data.py

# 自动化爬取
python tools/crawlers/crawl_auto.py

# 爬取所有数据
python tools/crawlers/crawl_all.py
```

---

## 📊 analysis/ - 分析工具

数据分析和回测相关脚本。

### 文件列表
- `backtest_model.py` - 模型回测分析
- `roi_backtest.py` - ROI 完整回测
- `roi_backtest_quick.py` - ROI 快速回测
- `predict_analysis.py` - 预测结果分析
- `compare_threshold_strategies.py` - 策略阈值对比
- `visualize_backtest.py` - 回测结果可视化
- `find_golden_opportunities.py` - 黄金投注机会发现

### 使用示例
```bash
# ROI 回测
python tools/analysis/roi_backtest.py

# 快速回测
python tools/analysis/roi_backtest_quick.py

# 策略对比
python tools/analysis/compare_threshold_strategies.py

# 可视化分析
python tools/analysis/visualize_backtest.py
```

---

## 💡 strategies/ - 投注策略

智能投注策略相关脚本。

### 文件列表
- `smart_betting_strategy.py` - 智能投注策略
- `dynamic_betting_strategy.py` - 动态仓位策略
- `daily_opportunity_check.py` - 每日机会评估
- `realtime_opportunity_monitor.py` - 实时机会监控

### 使用示例
```bash
# 每日机会评估
python tools/strategies/daily_opportunity_check.py

# 实时监控
python tools/strategies/realtime_opportunity_monitor.py

# 智能投注分析
python tools/strategies/smart_betting_strategy.py

# 动态仓位计算
python tools/strategies/dynamic_betting_strategy.py
```

---

## 🎓 training/ - 模型训练

深度学习模型训练相关脚本。

### 文件列表
- `train_model.py` - 标准模型训练
- `train_simple.py` - 简化版训练
- `train_and_test.py` - 训练+测试一体化

### 使用示例
```bash
# 训练模型
python tools/training/train_model.py

# 简化训练
python tools/training/train_simple.py

# 训练并测试
python tools/training/train_and_test.py
```

---

## 🛠️ 通用工具

### import_data.py
从外部导入数据到系统。

```bash
python tools/import_data.py --file data.csv
```

### generate_mock_data.py
生成模拟测试数据。

```bash
python tools/generate_mock_data.py --count 1000
```

### generate_strategy_summary.py
生成投注策略总结报告。

```bash
python tools/generate_strategy_summary.py
```

---

## 📝 使用注意事项

1. **路径问题**: 从项目根目录运行脚本时，需要使用 `tools/` 前缀
   ```bash
   # 正确
   python tools/crawlers/crawl_data.py
   
   # 错误（如果在根目录）
   python crawl_data.py
   ```

2. **依赖项**: 确保已安装所有依赖
   ```bash
   pip install -r requirements.txt
   ```

3. **环境变量**: 某些脚本可能需要配置环境变量或数据库连接

4. **权限**: 某些脚本需要相应的文件系统权限

---

## 🔗 相关文档

- [开发者文档](../docs/developer/README.md)
- [运维文档](../docs/operator/README.md)
- [分析师文档](../docs/analyst/README.md)

---

**最后更新**: 2026-02-05
