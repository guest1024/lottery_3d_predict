# Prompt: 开发模块化 Python 3D彩票预测系统 (CLI + 特征工程 + 回测框架)

**角色设定：**
请你担任一位拥有 10 年经验的 Python 高级架构师和数据工程专家。

**项目目标：**
构建一个名为 `Lotto3D-Core` 的工程级 Python 项目。该项目旨在通过深度学习模型辅助 3D 彩票预测。代码必须遵循“高内聚、低耦合”原则，具备极强的可扩展性（特别是特征工程模块），并包含完善的文档体系。

---

## 1. 项目目录结构要求 (Directory Structure)
请严格按照以下标准设计项目结构，确保文档和代码分离：

```text
project_root/
├── docs/                     # 文档中心 (必须包含以下三个独立子目录)
│   ├── user_guide/           # 面向最终用户：CLI使用手册、配置说明
│   ├── developer_guide/      # 面向开发者：架构图、接口文档、扩展指南
│   └── model_training/       # 面向算法工程师：特征数学原理、模型超参数实验记录
├── src/
│   ├── features/             # 特征工程模块 (核心扩展点)
│   ├── models/               # 深度学习模型定义
│   ├── strategies/           # 投注策略与过滤逻辑
│   ├── visualization/        # 图表生成工具
│   ├── utils/                # 通用工具
│   └── cli.py                # 命令行入口
├── tests/                    # 单元测试
├── data/                     # 数据存放
├── CHANGELOG.md              # 版本变更记录 (需包含模板)
├── requirements.txt
└── README.md2. 核心功能模块需求


模块 A: CLI 交互工具 (Command Line Interface)
基于 Click 或 Typer 库开发，提供以下指令：

predict --history 30: 加载模型，根据最近 30 期数据，输出下一期的预测结果。

输出内容： 预测号码（组选/直选概率）、推荐的 100 注清单、每注的理论胜率。

交互体验： 使用 Rich 库展示漂亮的彩色表格和进度条。

模块 B: 可扩展特征提取与可视化工具 (Feature Extractor)
这是一个独立的工具类，必须设计为插件式架构 (Plugin/Registry Pattern)，以便未来轻松添加新特征（如“五行”、“相位”等）而无需修改核心代码。

输入： 任意三个数字 (如 1, 2, 3) 或 历史期数。

功能 1 (提取): 输出该号码的所有特征向量 (JSON 格式)，包含 AC值、和值、跨度、遗漏值、形态等。

功能 2 (图表): 生成符合彩民偏好的历史走势图（如：和值走势折线图、遗漏值柱状图）。

技术栈： 使用 Matplotlib 或 Plotly 生成 HTML 或 PNG 报表。

模块 C: 回测与鲁棒性评估工具 (Backtester & ROI Validator)
用于验证模型在历史数据上的表现，必须包含对比基准。

功能 1 (仿真交易): 模拟过去 N 期的每一期投入（如每期 100 注），计算资金曲线。

功能 2 (基准对比):

模型组： 显示模型策略的 ROI、最大回撤、中奖率。

随机组 (Baseline): 引入 Monte Carlo 模拟，计算“完全随机购买 100 注”的期望收益分布。

目的： 只有当模型组 ROI 显著高于随机组的 95% 置信区间时，才判定模型有效。

3. 非功能性要求 (代码质量与规范)
可扩展性设计：

在 src/features/ 下定义一个 BaseFeature 抽象基类 (ABC)。

所有具体的特征（如 SumFeature, AcValueFeature）都必须继承该类并注册。

要求： 演示如何只通过添加一个 .py 文件，就能让系统识别并计算新的特征，而无需修改主流程代码。

文档规范 (/docs):

请为 /docs/model_training/ 目录提供一个示例文档 feature_definitions.md，详细解释 AC 值和遗漏值的数学定义。

请为 CHANGELOG.md 提供一个基于 Keep a Changelog 标准的初始模板。

工程标准：

使用 Python 3.9+。

必须包含 Type Hinting (类型注解)。

使用 Python 的 logging 模块记录日志，而不是 print。

4. 输出要求
请提供以下内容的代码实现或详细伪代码结构：

项目文件结构树。

src/features/base.py (抽象基类) 和 src/features/morphology.py (AC值/形态特征实现) 的代码，展示可扩展性。

src/cli.py 的核心逻辑，展示如何串联各模块。

src/evaluation/backtest.py 的代码，展示如何计算随机基准 (Random Baseline) 并与模型结果对比。













