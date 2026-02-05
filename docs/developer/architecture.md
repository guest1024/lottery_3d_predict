# 系统架构设计文档

## 1. 设计原则

Lotto3D-Core 遵循以下设计原则：

### 1.1 高内聚、低耦合
- 每个模块职责单一明确
- 模块间通过清晰的接口通信
- 减少模块间依赖

### 1.2 可扩展性
- **插件式特征架构**：新增特征无需修改核心代码
- **策略模式**：支持多种投注策略
- **配置化**：关键参数可通过配置文件调整

### 1.3 可测试性
- 单元测试覆盖核心逻辑
- 接口设计支持Mock测试
- 回测框架验证策略有效性

---

## 2. 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer (cli.py)                    │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐          │
│  │ crawl   │ │ predict │ │ backtest │ │visualize│  ...     │
│  └─────────┘ └─────────┘ └──────────┘ └─────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌─────────▼─────────┐  ┌───────▼────────┐
│ Data Loader    │  │ Feature Engineer  │  │ Model Layer    │
│                │  │                   │  │                │
│ • Crawler      │  │ • BaseFeature     │  │ • LotteryModel │
│ • DataLoader   │  │ • Registry        │  │ • LSTM+Attn    │
│                │  │ • Morphology      │  │ • Multi-head   │
└────────────────┘  │ • Statistical     │  └────────────────┘
                    │ • Metaphysical    │
                    └───────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐  ┌─────────▼─────────┐  ┌───────▼────────┐
│ Strategy       │  │ Evaluation        │  │ Visualization  │
│                │  │                   │  │                │
│ • StrategyEng  │  │ • Backtester      │  │ • Plotter      │
│ • Filter       │  │ • Monte Carlo     │  │ • Charts       │
│ • Scoring      │  │ • ROI Calc        │  │                │
└────────────────┘  └───────────────────┘  └────────────────┘
```

---

## 3. 核心模块详解

### 3.1 数据层 (Data Layer)

**职责：** 数据获取、加载、预处理

**主要组件：**

#### Lottery3DCrawler (crawler.py)
- 多线程并发抓取
- 错误重试机制
- 进度显示（Rich Progress）

```python
crawler = Lottery3DCrawler(max_workers=10)
stats = crawler.crawl(start_page=1, end_page=1000)
```

#### DataLoader (loader.py)
- JSON/CSV数据加载
- 数据格式转换
- 时间序列窗口切分

```python
loader = DataLoader()
df = loader.load_from_json()
X_train, y_train, X_test, y_test = loader.prepare_sequences(window_size=30)
```

---

### 3.2 特征工程层 (Feature Engineering Layer)

**职责：** 特征提取、管理、扩展

**核心设计：插件式架构**

#### 架构组件

1. **BaseFeature（抽象基类）**
   - 定义特征接口
   - 提供输入验证

2. **FeatureRegistry（注册表）**
   - 单例模式
   - 自动发现和注册特征

3. **@register_feature（装饰器）**
   - 声明式注册
   - 零侵入扩展

4. **FeatureEngineer（引擎）**
   - 统一调度所有特征
   - 批量处理

#### 扩展新特征示例

```python
from src.features.base import BaseFeature, register_feature

@register_feature
class MyCustomFeature(BaseFeature):
    name = "my_feature"
    description = "我的自定义特征"
    category = "custom"
    
    def extract(self, numbers, history):
        # 实现特征计算逻辑
        value = sum(numbers) ** 2
        return {'squared_sum': value}
```

**优势：**
- ✅ 无需修改 `FeatureEngineer`
- ✅ 自动参与特征提取
- ✅ 支持热插拔

---

### 3.3 模型层 (Model Layer)

**职责：** 深度学习预测

#### LotteryModel 架构

```python
LotteryModel(
    embedding_dim=16,     # 数字嵌入维度
    hidden_dim=128,       # LSTM隐藏层维度
    num_layers=2,         # LSTM层数
    dropout=0.3           # Dropout率
)
```

**网络结构：**

1. **Embedding层**
   - 将0-9数字映射到连续向量空间

2. **Bi-LSTM层**
   - 双向捕捉时间依赖
   - 2层堆叠增强表达能力

3. **Attention层**
   - Self-Attention机制
   - 自动学习重要历史时刻

4. **多任务输出头**
   - **数字预测头**: 10维 Sigmoid（多标签）
   - **形态分类头**: 3维 Softmax（组六/组三/豹子）
   - **和值预测头**: 28维 Softmax（0-27）
   - **AC值预测头**: 3维 Softmax（1-3）

**损失函数：**

$$
L_{total} = \lambda_1 L_{digit} + \lambda_2 L_{shape} + \lambda_3 L_{sum} + \lambda_4 L_{AC}
$$

默认权重：$\lambda = [2.0, 1.0, 1.5, 1.0]$

---

### 3.4 策略层 (Strategy Layer)

**职责：** 根据预测生成投注方案

#### StrategyEngine 流程

```
模型预测
    ↓
Step A: 定胆（选择高概率数字）
    ↓
Step B: 杀号（剔除低概率数字）
    ↓
Step C: 生成组合（笛卡尔积）
    ↓
Step D: 过滤
    • 和值过滤（保留top-K和值范围）
    • AC值过滤（符合预测AC值）
    • 形态过滤（可选）
    ↓
Step E: 评分排序
    • 联合概率：P(d0) × P(d1) × P(d2)
    • 降序排列
    ↓
Step F: 截取Top N注
    ↓
输出推荐方案
```

**策略类型：**

| 策略 | 胆码数 | 杀号数 | 适用场景 |
|------|--------|--------|----------|
| Conservative | 3 | 4 | 低风险、小额投注 |
| Balanced | 5 | 2 | 均衡风险收益 |
| Aggressive | 6 | 1 | 高风险、追求覆盖 |

---

### 3.5 评估层 (Evaluation Layer)

**职责：** 回测、性能评估、基准对比

#### Backtester 核心功能

1. **Walk-Forward Validation**
   - 滚动窗口训练
   - 避免未来函数
   - 真实模拟交易

2. **Monte Carlo基准**
   - 1000次随机模拟
   - 计算95%置信区间
   - 统计显著性检验

3. **性能指标**
   - ROI（投资回报率）
   - 最大回撤
   - 夏普比率
   - 中奖率

---

### 3.6 可视化层 (Visualization Layer)

**职责：** 生成图表和报表

**支持的图表：**
- 和值走势图（折线图）
- 遗漏值柱状图
- 数字频率分布
- 资金曲线图
- AC值分布（待实现）

---

## 4. 数据流示例

### 4.1 预测流程

```
用户输入: --history 30 --top 100
    ↓
DataLoader加载最近30期数据
    ↓
转换为Tensor: (1, 30, 3)
    ↓
LotteryModel.predict()
    ↓
输出4个概率分布
    ↓
StrategyEngine.generate_recommendations()
    ↓
过滤、评分、排序
    ↓
返回Top 100注
    ↓
CLI美化显示（Rich Table）
```

### 4.2 回测流程

```
用户输入: --periods 50
    ↓
加载测试数据（50+30期）
    ↓
For each period in 50:
    ├─ 获取历史窗口(30期)
    ├─ 模型预测
    ├─ 生成推荐
    ├─ 模拟投注
    ├─ 检查中奖
    └─ 更新资金曲线
    ↓
计算统计指标
    ↓
（可选）Monte Carlo基准
    ↓
对比分析
    ↓
生成报告
```

---

## 5. 技术选型

| 模块 | 技术栈 | 理由 |
|------|--------|------|
| 深度学习 | PyTorch | 灵活、动态图、生态完善 |
| CLI | Click + Rich | 现代化、美观、易用 |
| 数据处理 | Pandas + NumPy | 事实标准 |
| 可视化 | Matplotlib | 稳定、可控 |
| 爬虫 | Requests + BeautifulSoup | 轻量、高效 |
| 类型检查 | Type Hints + MyPy | 提升代码质量 |

---

## 6. 性能优化

### 6.1 已实现的优化

1. **并发爬虫**：ThreadPoolExecutor多线程
2. **批量特征提取**：向量化计算
3. **模型推理优化**：torch.no_grad()

### 6.2 未来可优化点

1. **特征缓存**：避免重复计算
2. **模型量化**：减少内存占用
3. **GPU加速**：CUDA并行计算
4. **分布式训练**：多卡训练

---

## 7. 安全性考虑

1. **输入验证**：CLI参数校验
2. **异常处理**：完善的错误捕获
3. **日志记录**：追踪系统运行状态
4. **数据备份**：定期保存模型和数据

---

## 8. 未来扩展方向

### 8.1 功能扩展
- [ ] Web界面（Flask/FastAPI）
- [ ] 实时监控面板
- [ ] 邮件/微信通知
- [ ] 多模型集成（Ensemble）

### 8.2 算法扩展
- [ ] Transformer模型
- [ ] 强化学习策略
- [ ] 贝叶斯优化超参数
- [ ] AutoML自动特征工程

---

## 9. 贡献指南

欢迎贡献代码！请遵循：

1. **代码风格**：Black + Flake8
2. **类型注解**：所有函数必须有类型提示
3. **文档字符串**：Google Style
4. **测试覆盖**：新功能必须包含测试

---

**版本：** v1.0  
**更新日期：** 2024-01-01  
**维护者：** Lotto3D-Core Team
