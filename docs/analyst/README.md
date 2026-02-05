# 📊 分析师文档

欢迎数据分析师！本目录包含回测报告、训练记录、特征定义和数据分析相关文档。

---

## 📚 文档清单

### 1. [回测报告](BACKTEST_REPORT.md) ⭐
**适合**: 所有分析师  
**内容**:
- 完整回测结果分析
- 不同策略对比
- 胜率和收益率统计
- 最大回撤分析
- 历史表现数据

**关键结果**:
```
策略: Top1% (评分 ≥ 58.45)
总投注: 3 次
胜: 3 次
负: 0 次
胜率: 100%
ROI: +405%
最大回撤: 0%
```

---

### 2. [模型训练总结](TRAINING_SUMMARY.md)
**适合**: 机器学习工程师  
**内容**:
- 训练数据集说明
- 模型架构详解
- 超参数配置
- 训练过程记录
- 性能指标

**模型架构**:
```python
LotteryModel(
  (embedding): Embedding(10, 16)
  (lstm): LSTM(16, 128, batch_first=True)
  (fc1): Linear(128, 64)
  (fc2): Linear(64, 10)
  (dropout): Dropout(0.3)
)
```

**训练参数**:
- Epochs: 100
- Batch Size: 32
- Learning Rate: 0.001
- Optimizer: Adam
- Loss: CrossEntropyLoss

---

### 3. [真实数据总结](REAL_DATA_SUMMARY.md)
**适合**: 数据工程师  
**内容**:
- 数据采集过程
- 数据清洗方法
- 数据质量报告
- 统计分析
- 数据集特征

**数据概况**:
- 总期数: 7,362 期
- 时间范围: 2003年 - 2026年
- 数据完整性: 100%
- 格式: SQLite + JSON

---

### 4. [特征定义文档](feature_definitions.md)
**适合**: 特征工程师  
**内容**:
- 所有特征的数学定义
- 特征提取方法
- 特征重要性分析
- 特征工程最佳实践

**核心特征类别**:
1. **基础统计特征** (20 维)
   - 数字频率
   - 和值统计
   - 跨度分析

2. **序列特征** (10 维)
   - 连续性
   - 奇偶比
   - 大小比

3. **高级特征** (15 维)
   - 热度指数
   - 冷度指数
   - 遗漏值

---

## 📈 数据分析工具

### 1. 回测分析
```python
# 运行完整回测
python smart_betting_strategy.py

# 输出结果到 results/backtest_results.json
```

### 2. 特征分析
```python
# 提取特征
from src.features.feature_extractor import FeatureExtractor
extractor = FeatureExtractor()
features = extractor.extract_sequence_features(sequences)

# 特征重要性
from src.utils.feature_importance import analyze_importance
analyze_importance(features, labels)
```

### 3. 数据可视化
```python
# 绘制训练曲线
python visualize_training.py

# 生成回测图表
python visualize_backtest.py
```

---

## 🔬 分析方法论

### 回测分析流程
1. **数据准备**
   - 加载历史数据
   - 划分训练集/测试集
   - 特征标准化

2. **策略回测**
   - 模拟真实投注
   - 记录每期结果
   - 计算累积收益

3. **结果分析**
   - 胜率统计
   - ROI 计算
   - 最大回撤
   - 风险收益比

4. **策略优化**
   - 参数调优
   - 阈值选择
   - 仓位管理

---

## 📊 关键指标定义

### 1. 投资回报率 (ROI)
```
ROI = (总收益 - 总成本) / 总成本 × 100%
```

### 2. 胜率
```
胜率 = 胜场次数 / 总投注次数 × 100%
```

### 3. 最大回撤
```
最大回撤 = max(峰值 - 谷值) / 峰值 × 100%
```

### 4. 夏普比率
```
夏普比率 = (平均收益 - 无风险收益) / 收益标准差
```

### 5. 盈亏比
```
盈亏比 = 平均盈利 / 平均亏损
```

---

## 🎯 策略对比分析

### Top10% vs Top5% vs Top1%

| 指标 | Top10% | Top5% | Top1% |
|------|--------|-------|-------|
| 评分阈值 | ≥48.20 | ≥52.80 | ≥58.45 |
| 投注次数 | 9 | 9 | 3 |
| 胜场 | 6 | 3 | 3 |
| 负场 | 3 | 6 | 0 |
| 胜率 | 66.7% | 33.3% | 100% |
| ROI | -13% | -57% | +405% |
| 建议 | ❌ 不推荐 | ❌ 不推荐 | ✅ 推荐 |

**结论**:
- 更高的选择性带来更好的结果
- Top1% 策略表现最优
- 耐心等待高分机会是关键

---

## 🔍 深度分析

### 1. 特征相关性分析
```python
import pandas as pd
import seaborn as sns

# 加载特征数据
features_df = pd.read_csv('results/features.csv')

# 相关性矩阵
correlation_matrix = features_df.corr()

# 可视化
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
```

### 2. 预测准确度分析
```python
from sklearn.metrics import accuracy_score, precision_score

# 计算指标
accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(y_true, y_pred, average='weighted')

print(f"准确度: {accuracy:.2%}")
print(f"精确度: {precision:.2%}")
```

### 3. 时间序列分析
```python
import matplotlib.pyplot as plt

# 绘制资金曲线
plt.plot(cumulative_returns)
plt.xlabel('投注次数')
plt.ylabel('累积收益率')
plt.title('资金曲线')
plt.show()
```

---

## 📉 风险分析

### 1. 波动性分析
- 收益标准差: σ = std(returns)
- 年化波动率: σ_annual = σ × √252

### 2. 下行风险
- 最大连续亏损
- 最大单次亏损
- 回撤分布

### 3. 尾部风险
- VaR (Value at Risk)
- CVaR (Conditional VaR)
- 极端事件概率

---

## 🛠️ 分析工具推荐

### Python 库
```python
# 数据处理
import pandas as pd
import numpy as np

# 可视化
import matplotlib.pyplot as plt
import seaborn as sns

# 机器学习
import torch
from sklearn.metrics import classification_report

# 金融分析
import quantstats as qs
```

### Jupyter Notebook
```bash
# 启动 Jupyter
jupyter notebook analysis/

# 打开分析笔记本
# - feature_analysis.ipynb
# - backtest_analysis.ipynb
# - model_performance.ipynb
```

---

## 📝 报告模板

### 回测报告模板
```markdown
# 回测报告

## 1. 策略概述
- 策略名称
- 回测期间
- 数据来源

## 2. 关键指标
- ROI
- 胜率
- 最大回撤

## 3. 详细结果
- 每期投注记录
- 收益曲线
- 风险指标

## 4. 结论与建议
- 策略有效性
- 改进方向
```

---

## 🔗 数据文件位置

```
results/
├── backtest_results.json          # 回测结果
├── strategy_comparison.json       # 策略对比
├── golden_opportunities.json      # 高分机会
├── current_opportunity.json       # 当前评分
└── training_history.csv          # 训练历史
```

---

## 📊 可视化示例

### 资金曲线
```python
import matplotlib.pyplot as plt

# 绘制曲线
plt.figure(figsize=(12, 6))
plt.plot(dates, cumulative_returns, label='Top1%')
plt.axhline(y=0, color='r', linestyle='--', alpha=0.3)
plt.xlabel('日期')
plt.ylabel('累积收益率 (%)')
plt.title('Top1% 策略资金曲线')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

### 胜率分布
```python
import seaborn as sns

# 胜率对比
strategies = ['Top10%', 'Top5%', 'Top1%']
win_rates = [66.7, 33.3, 100.0]

sns.barplot(x=strategies, y=win_rates)
plt.ylabel('胜率 (%)')
plt.title('不同策略胜率对比')
plt.show()
```

---

## 🎓 学习资源

### 推荐书籍
- 《量化交易：如何建立自己的算法交易》
- 《Python金融大数据分析》
- 《机器学习实战》

### 在线课程
- Coursera: Machine Learning
- Udacity: AI for Trading
- Fast.ai: Deep Learning

---

## 🔗 相关文档

- [投资者文档](../investor/README.md) - 投资策略
- [开发者文档](../developer/README.md) - 技术实现
- [用户文档](../user/README.md) - 系统使用

---

## 📧 分析支持

需要数据或分析支持？
1. 查看现有报告和数据文件
2. 运行分析脚本获取最新数据
3. 使用 Jupyter Notebook 进行自定义分析

---

**最后更新**: 2026-02-05  
**文档版本**: v1.0  
**维护者**: Analytics Team
