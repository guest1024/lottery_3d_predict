# Lotto3D-Core: 3D彩票预测系统

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 项目简介

Lotto3D-Core 是一个工程级的 Python 3D 彩票预测系统，采用深度学习技术（LSTM + Attention）进行时间序列预测。系统设计遵循"高内聚、低耦合"原则，具备强大的可扩展性。

### 核心特性

- 🎯 **智能预测**：基于 LSTM + Attention 的多任务学习模型
- 🔧 **模块化设计**：插件式特征工程架构，轻松扩展新特征
- 📊 **可视化分析**：丰富的走势图和统计报表
- 🧪 **严格回测**：滚动窗口验证 + Monte Carlo 基准对比
- 💻 **友好CLI**：基于 Rich 的美观命令行界面
- 📚 **完善文档**：用户指南、开发文档、算法说明

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 数据采集

```bash
python src/cli.py crawl --pages 1000
```

### 训练模型

```bash
python src/cli.py train --epochs 100 --batch-size 32
```

### 预测下一期

```bash
python src/cli.py predict --history 30 --top 100
```

### 回测评估

```bash
python src/cli.py backtest --periods 50 --baseline monte-carlo
```

## 项目结构

```
project_root/
├── docs/                     # 文档中心
│   ├── user_guide/           # 用户使用手册
│   ├── developer_guide/      # 开发者文档
│   └── model_training/       # 模型训练文档
├── src/
│   ├── features/             # 特征工程模块（核心扩展点）
│   ├── models/               # 深度学习模型
│   ├── strategies/           # 投注策略
│   ├── visualization/        # 可视化工具
│   ├── evaluation/           # 回测评估
│   ├── data_loader/          # 数据加载
│   ├── utils/                # 通用工具
│   └── cli.py                # CLI 入口
├── tests/                    # 单元测试
├── data/                     # 数据存储
├── logs/                     # 日志文件
├── config/                   # 配置文件
└── requirements.txt
```

## 特征工程

系统支持丰富的特征类型：

### 基础物理属性
- 和值、跨度、AC值
- 奇偶比、大小比、质合比

### 高级形态结构
- 形态编码（组三/组六/豹子）
- 012路分析、和尾

### 统计趋势
- 遗漏值统计
- 滚动均值/标准差/偏度
- 滚动相关系数

### 玄学逻辑数字化
- 五行生克关系
- 位置互换模式
- 振幅分析

## 扩展新特征

系统采用插件式架构，添加新特征只需：

1. 在 `src/features/` 创建新文件
2. 继承 `BaseFeature` 类
3. 实现 `extract()` 方法
4. 使用 `@register_feature` 装饰器

示例：

```python
from src.features.base import BaseFeature, register_feature

@register_feature
class MyCustomFeature(BaseFeature):
    name = "my_feature"
    
    def extract(self, numbers, history):
        # 实现特征提取逻辑
        return feature_dict
```

## 文档

- [用户使用手册](docs/user_guide/)
- [开发者指南](docs/developer_guide/)
- [模型训练文档](docs/model_training/)
- [变更日志](CHANGELOG.md)

## 技术栈

- Python 3.9+
- PyTorch 2.0+
- NumPy, Pandas, Scikit-learn
- Click, Rich (CLI)
- Matplotlib, Plotly (可视化)

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 免责声明

本项目仅供学习和研究使用。彩票具有随机性，请理性购买，量力而行。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题或建议，请通过 Issue 联系。
