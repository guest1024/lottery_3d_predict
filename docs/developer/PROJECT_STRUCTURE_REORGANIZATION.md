# 📂 项目结构重组总结

**日期**: 2026-02-05  
**目标**: 优化根目录结构,将测试、示例和工具脚本分类整理

---

## 🎯 重组目标

1. **简化根目录**: 只保留核心启动脚本和配置文件
2. **分类清晰**: 按功能将文件组织到对应目录
3. **易于维护**: 每个目录都有清晰的职责和 README 文档
4. **向后兼容**: 更新所有引用路径,确保功能正常

---

## 📁 新的目录结构

```
lottery_3d_predict/
├── docs/                          # 📚 文档中心（按角色分类）
│   ├── investor/                  # 💰 投资者文档
│   ├── user/                      # 👤 用户文档
│   ├── developer/                 # 👨‍💻 开发者文档
│   ├── operator/                  # 🔧 运维文档
│   └── analyst/                   # 📊 分析师文档
│
├── lottery/                       # Django 应用
│   ├── models.py
│   ├── views.py
│   ├── scheduler.py               # ✅ 已更新导入路径
│   └── templates/
│
├── lottery_web/                   # Django 项目配置
│
├── src/                           # 核心算法
│   ├── models/                    # 深度学习模型
│   ├── features/                  # 特征工程
│   ├── data_loader/               # 数据加载器
│   └── utils/                     # 工具函数
│
├── tools/                         # 🔧 工具脚本集（新增）
│   ├── README.md                  # 工具目录说明
│   ├── __init__.py
│   │
│   ├── crawlers/                  # 🕷️ 数据爬虫
│   │   ├── __init__.py
│   │   ├── crawl_data.py
│   │   ├── crawl_auto.py
│   │   ├── crawl_all.py
│   │   └── crawl_real_data.py    # ✅ 已更新路径引用
│   │
│   ├── analysis/                  # 📊 分析工具
│   │   ├── __init__.py
│   │   ├── backtest_model.py
│   │   ├── roi_backtest.py
│   │   ├── roi_backtest_quick.py
│   │   ├── predict_analysis.py
│   │   ├── compare_threshold_strategies.py
│   │   ├── visualize_backtest.py
│   │   └── find_golden_opportunities.py
│   │
│   ├── strategies/                # 💡 投注策略
│   │   ├── __init__.py
│   │   ├── smart_betting_strategy.py
│   │   ├── dynamic_betting_strategy.py
│   │   ├── daily_opportunity_check.py  # ✅ scheduler 已更新引用
│   │   └── realtime_opportunity_monitor.py
│   │
│   ├── training/                  # 🎓 模型训练
│   │   ├── __init__.py
│   │   ├── train_model.py
│   │   ├── train_simple.py
│   │   └── train_and_test.py
│   │
│   ├── import_data.py             # 数据导入工具
│   ├── generate_mock_data.py      # 模拟数据生成
│   └── generate_strategy_summary.py
│
├── tests/                         # 🧪 测试文件（新增）
│   ├── README.md                  # 测试目录说明
│   ├── __init__.py
│   │
│   ├── examples/                  # 📝 示例代码
│   │   ├── __init__.py
│   │   └── example_daily_usage.py
│   │
│   ├── test_all_apis.py           # API 接口测试
│   ├── test_backtest.py
│   ├── test_crawler_api.py
│   ├── test_demo.py
│   ├── test_fixes.py
│   ├── test_new_predict_api.py    # ✅ 测试通过
│   ├── test_prediction.py
│   ├── test_prediction_v2.py
│   ├── test_simple.py
│   ├── test_web_interface.py
│   └── test_api_quick.sh
│
├── static/                        # 静态文件
├── logs/                          # 日志文件
├── results/                       # 结果数据
├── data/                          # 数据文件
│
├── manage.py                      # Django 管理脚本
├── quick_start.sh                 # 快速启动脚本
├── start_scheduler.sh             # 调度器启动脚本
├── start_web.sh                   # Web 服务启动脚本
├── requirements.txt               # Python 依赖
├── environment.yml                # Conda 环境
└── README.md                      # 项目说明
```

---

## 🔄 文件移动清单

### ✅ 移动到 `tools/crawlers/`
- `crawl_data.py`
- `crawl_auto.py`
- `crawl_all.py`
- `crawl_real_data.py` (已更新内部路径引用)

### ✅ 移动到 `tools/analysis/`
- `backtest_model.py`
- `roi_backtest.py`
- `roi_backtest_quick.py`
- `predict_analysis.py`
- `compare_threshold_strategies.py`
- `visualize_backtest.py`
- `find_golden_opportunities.py`

### ✅ 移动到 `tools/strategies/`
- `smart_betting_strategy.py`
- `dynamic_betting_strategy.py`
- `daily_opportunity_check.py`
- `realtime_opportunity_monitor.py`

### ✅ 移动到 `tools/training/`
- `train_model.py`
- `train_simple.py`
- `train_and_test.py`

### ✅ 移动到 `tools/`
- `import_data.py`
- `generate_mock_data.py`
- `generate_strategy_summary.py`

### ✅ 移动到 `tests/`
- `test_all_apis.py`
- `test_backtest.py`
- `test_crawler_api.py`
- `test_demo.py`
- `test_fixes.py`
- `test_new_predict_api.py`
- `test_prediction.py`
- `test_prediction_v2.py`
- `test_simple.py`
- `test_web_interface.py`
- `test_api_quick.sh`

### ✅ 移动到 `tests/examples/`
- `example_daily_usage.py`

### ✅ 移动到 `docs/developer/`
- `PREDICT_API_UPGRADE_SUMMARY.md`

---

## 🔧 代码更新

### 1. lottery/scheduler.py
**更新前**:
```python
from daily_opportunity_check import check_today_opportunity
from crawl_real_data import SimpleLottery3DCrawler
```

**更新后**:
```python
from tools.strategies.daily_opportunity_check import check_today_opportunity
from tools.crawlers.crawl_real_data import SimpleLottery3DCrawler
```

### 2. tools/crawlers/crawl_real_data.py
**更新前**:
```python
sys.path.insert(0, str(Path(__file__).parent / 'src'))
```

**更新后**:
```python
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))
```

---

## ✅ 验证测试

### 测试1: 导入路径验证
```bash
# 测试策略模块导入
$ python -c "from tools.strategies.daily_opportunity_check import check_today_opportunity; print('✓ Import successful')"
✓ Import successful

# 测试爬虫模块导入
$ python -c "from tools.crawlers.crawl_real_data import SimpleLottery3DCrawler; print('✓ Import successful')"
✓ Import successful
```

### 测试2: 功能测试
```bash
# 运行测试文件
$ python tests/test_new_predict_api.py
======================================================================
测试新的预测 API 功能
======================================================================
[测试1] 评分函数
✓ 评分计算成功: 46.15 分
...
✓ 所有测试通过
```

### 测试3: 根目录清洁度
```bash
$ ls -1 *.py *.sh
manage.py
quick_start.sh
start_scheduler.sh
start_web.sh
```
✅ 只保留必要的启动脚本

---

## 📚 新增文档

1. **tools/README.md**
   - 工具脚本目录说明
   - 各子目录功能介绍
   - 使用示例和注意事项

2. **tests/README.md**
   - 测试文件目录说明
   - 各测试文件功能介绍
   - 测试最佳实践和运行方法

3. **docs/developer/PROJECT_STRUCTURE_REORGANIZATION.md** (本文件)
   - 重组总结和记录
   - 文件移动清单
   - 代码更新说明

---

## 🎯 使用指南

### 运行工具脚本
```bash
# 从根目录运行
python tools/crawlers/crawl_data.py
python tools/analysis/roi_backtest.py
python tools/strategies/daily_opportunity_check.py
python tools/training/train_model.py
```

### 运行测试
```bash
# 运行单个测试
python tests/test_new_predict_api.py

# 运行所有测试
for test in tests/test_*.py; do python "$test"; done

# 运行 shell 测试
./tests/test_api_quick.sh
```

### 启动服务
```bash
# 启动 Web 服务
./start_web.sh

# 启动调度器
./start_scheduler.sh --daemon
```

---

## 🎉 重组效果

### Before (重组前)
```
根目录: 38 个 Python 文件 + 4 个 Shell 脚本
- ❌ 文件杂乱无章
- ❌ 难以快速找到文件
- ❌ 不清楚哪些是核心文件
```

### After (重组后)
```
根目录: 1 个核心脚本 + 3 个启动脚本
- ✅ 结构清晰简洁
- ✅ 分类明确易找
- ✅ 职责分离明显
- ✅ 文档完善
```

---

## 📝 维护建议

1. **新文件放置原则**:
   - 测试文件 → `tests/`
   - 爬虫脚本 → `tools/crawlers/`
   - 分析工具 → `tools/analysis/`
   - 策略脚本 → `tools/strategies/`
   - 训练脚本 → `tools/training/`
   - 启动脚本 → 根目录（谨慎添加）

2. **导入路径规范**:
   - 使用相对于项目根目录的绝对导入
   - 示例: `from tools.strategies.xxx import yyy`

3. **文档更新**:
   - 新增工具脚本时更新 `tools/README.md`
   - 新增测试文件时更新 `tests/README.md`
   - 重大变更时更新本文档

---

## 🔗 相关文档

- [项目 README](../../README.md)
- [工具脚本说明](../../tools/README.md)
- [测试文件说明](../../tests/README.md)
- [开发者文档](README.md)

---

**重组完成日期**: 2026-02-05  
**重组人员**: AI Assistant  
**验证状态**: ✅ 全部通过
