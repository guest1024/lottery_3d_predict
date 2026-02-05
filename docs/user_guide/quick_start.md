# 快速开始指南

欢迎使用 Lotto3D-Core 3D彩票预测系统！本指南将帮助您快速上手。

## 安装

### 1. 克隆项目

```bash
git clone <repository-url>
cd lottery_3d_predict
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

**系统要求：**
- Python 3.9+
- 8GB+ RAM（推荐）
- GPU（可选，用于加速训练）

---

## 基础使用

### 第一步：抓取历史数据

```bash
python src/cli.py crawl --pages 1000
```

这将从官方网站抓取1000页历史开奖数据（约20,000条记录），保存到 `./data` 目录。

**参数说明：**
- `--pages`: 抓取页数（默认1000）
- `--workers`: 并发线程数（默认10）

**预计耗时：** 5-10分钟

---

### 第二步：查看系统信息

```bash
python src/cli.py info
```

显示：
- Python版本
- PyTorch版本
- 已注册特征列表
- 系统状态

---

### 第三步：提取特征（可选）

测试特征提取功能：

```bash
python src/cli.py extract --numbers 1,2,3
```

这将显示号码 [1,2,3] 的所有特征值，包括：
- 和值：6
- AC值：2
- 跨度：2
- 形态：组六
- 等等...

---

### 第四步：生成可视化报表

```bash
python src/cli.py visualize --periods 100
```

生成以下图表（保存在 `./output` 目录）：
- 和值走势图
- 遗漏值柱状图
- 数字频率分布图

---

## 高级功能

### 训练模型

由于训练代码较为复杂，建议直接使用预训练模型。如需自行训练：

```python
# train.py 示例
from src.data_loader.loader import DataLoader
from src.models.lottery_model import LotteryModel
import torch

# 加载数据
loader = DataLoader()
df = loader.load_from_json()
X_train, y_train, X_test, y_test = loader.prepare_sequences(window_size=30)

# 创建模型
model = LotteryModel(embedding_dim=16, hidden_dim=128, num_layers=2)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# 训练循环
for epoch in range(100):
    # ... 训练代码
    pass

# 保存模型
model.save('./models/best_model.pth')
```

---

### 预测下一期

```bash
python src/cli.py predict --history 30 --top 100 --strategy balanced
```

**参数说明：**
- `--history`: 使用最近N期数据（默认30）
- `--top`: 输出前N注（默认100）
- `--strategy`: 策略类型
  - `conservative`: 保守（胆码少、杀号多）
  - `balanced`: 平衡（推荐）
  - `aggressive`: 激进（胆码多、杀号少）

**输出示例：**

```
置信度: 72.5%
胆码: [1, 3, 5, 7, 9]
杀号: [0, 2]
推荐形态: 组六
推荐和值范围: 12-18
推荐AC值: 2

┌──────┬────────┬────────────┐
│ 排名 │ 号码   │ 理论胜率   │
├──────┼────────┼────────────┤
│ 1    │ 357    │ 2.45%      │
│ 2    │ 359    │ 2.31%      │
│ 3    │ 157    │ 2.18%      │
...
```

---

### 回测评估

```bash
python src/cli.py backtest --periods 50 --baseline
```

**参数说明：**
- `--periods`: 回测期数（默认50）
- `--baseline`: 同时运行Monte Carlo随机基准测试

**输出示例：**

```
回测结果
┌──────────────┬──────────────┐
│ 指标         │ 数值         │
├──────────────┼──────────────┤
│ 总交易次数   │ 50           │
│ 投注次数     │ 42           │
│ 中奖次数     │ 8            │
│ 中奖率       │ 19.05%       │
│ ROI          │ -15.3%       │
│ 最大回撤     │ 22.1%        │
└──────────────┴──────────────┘

✓ 模型显著优于随机基准
ROI提升: 12.5%
```

---

## 常见问题

### Q1: 爬虫抓取失败怎么办？

**A:** 可能原因：
1. 网络连接问题
2. 目标网站反爬虫限制

**解决方法：**
- 减少并发数：`--workers 5`
- 分批抓取：先抓取1-500页，再抓取501-1000页

---

### Q2: 预测结果置信度过低？

**A:** 置信度<50%时系统会建议观望。可能原因：
1. 历史数据不足
2. 模型需要重新训练
3. 近期开奖数据波动较大

**建议：** 仅在置信度>60%时投注。

---

### Q3: 如何添加自定义特征？

**A:** 参见《开发者指南》中的"扩展特征"章节。

简要步骤：
1. 在 `src/features/` 创建新文件
2. 继承 `BaseFeature` 类
3. 使用 `@register_feature` 装饰器

---

### Q4: 系统能保证盈利吗？

**A:** 不能。彩票具有随机性，本系统仅供学习研究使用。请理性购买，量力而行。

---

## 下一步

- 阅读《开发者指南》了解架构设计
- 阅读《模型训练文档》了解算法原理
- 查看源代码了解实现细节

---

## 获取帮助

如有问题，请：
1. 查看项目 README.md
2. 阅读完整文档
3. 提交 Issue

**祝您使用愉快！**
