# 🧪 测试文件目录

本目录包含项目的所有测试文件和示例代码。

## 📂 目录结构

```
tests/
├── examples/                    # 📝 示例代码
│   └── example_daily_usage.py  # 日常使用示例
├── test_all_apis.py            # API 接口测试
├── test_backtest.py            # 回测功能测试
├── test_crawler_api.py         # 爬虫 API 测试
├── test_demo.py                # 基础演示测试
├── test_fixes.py               # 修复验证测试
├── test_new_predict_api.py     # 新预测 API 测试
├── test_prediction.py          # 预测功能测试 v1
├── test_prediction_v2.py       # 预测功能测试 v2
├── test_simple.py              # 简单功能测试
├── test_web_interface.py       # Web 界面测试
└── test_api_quick.sh           # API 快速测试脚本
```

---

## 🎯 测试文件说明

### API 测试

#### test_all_apis.py
全面测试所有 API 接口。

```bash
python tests/test_all_apis.py
```

**测试内容**:
- 预测接口 (`/api/predict/`)
- 爬虫接口 (`/api/crawl/`)
- 状态查询接口

---

#### test_crawler_api.py
测试数据爬取 API 功能。

```bash
python tests/test_crawler_api.py
```

**测试内容**:
- 爬虫启动
- 数据获取
- 错误处理

---

#### test_new_predict_api.py
测试新版预测 API（含完整投注计划）。

```bash
python tests/test_new_predict_api.py
```

**测试内容**:
- 机会评分计算
- 投注计划生成
- 组六/组三组合
- ROI 预期计算

---

#### test_api_quick.sh
快速测试 API 接口的 Shell 脚本。

```bash
./tests/test_api_quick.sh
```

**测试内容**:
- API 连通性
- 基础响应格式
- 快速回归测试

---

### 功能测试

#### test_prediction.py / test_prediction_v2.py
测试核心预测功能。

```bash
# v1 版本
python tests/test_prediction.py

# v2 版本
python tests/test_prediction_v2.py
```

**测试内容**:
- 模型加载
- 数据预处理
- 预测生成
- Top5 数字输出

---

#### test_backtest.py
测试回测功能。

```bash
python tests/test_backtest.py
```

**测试内容**:
- 历史数据回测
- ROI 计算
- 胜率统计

---

#### test_web_interface.py
测试 Web 界面功能。

```bash
python tests/test_web_interface.py
```

**测试内容**:
- 页面加载
- 表单提交
- 数据展示

---

#### test_simple.py
简单的基础功能测试。

```bash
python tests/test_simple.py
```

**测试内容**:
- 数据加载
- 基础计算
- 工具函数

---

#### test_demo.py
演示和验证基础功能。

```bash
python tests/test_demo.py
```

**测试内容**:
- 系统基本功能
- 数据流验证
- 快速演示

---

#### test_fixes.py
验证已修复的 Bug。

```bash
python tests/test_fixes.py
```

**测试内容**:
- 已知问题修复
- 回归测试
- 边界情况

---

## 📝 示例代码

### examples/example_daily_usage.py
日常使用的完整示例。

```bash
python tests/examples/example_daily_usage.py
```

**示例内容**:
- 每日机会评估流程
- 投注建议生成
- 策略执行示例
- 结果分析方法

---

## 🚀 快速运行所有测试

```bash
# 运行所有 Python 测试
for test in tests/test_*.py; do
    echo "Running $test..."
    python "$test"
done

# 运行 Shell 测试
./tests/test_api_quick.sh
```

---

## 📋 测试最佳实践

### 1. 测试前准备
```bash
# 确保依赖已安装
pip install -r requirements.txt

# 启动 Web 服务（如需要）
python manage.py runserver &

# 确保数据库存在
python manage.py migrate
```

### 2. 测试命名规范
- 测试文件: `test_*.py`
- 测试函数: `test_*()` 或 `def test_*()`
- 测试类: `Test*` 或 `*Test`

### 3. 测试类型
- **单元测试**: 测试单个函数或类
- **集成测试**: 测试多个模块协作
- **API 测试**: 测试 HTTP 接口
- **功能测试**: 测试完整业务流程

### 4. 运行特定测试
```bash
# 运行单个测试文件
python tests/test_prediction.py

# 运行带详细输出
python tests/test_prediction.py -v

# 运行特定测试函数（如果使用 pytest）
pytest tests/test_prediction.py::test_model_loading
```

---

## 🐛 调试技巧

### 查看详细输出
```bash
# Python 测试
python -u tests/test_prediction.py

# 使用 pytest 的详细模式
pytest tests/ -v -s
```

### 断点调试
```python
# 在测试代码中添加
import pdb; pdb.set_trace()

# 或使用 ipdb（更友好）
import ipdb; ipdb.set_trace()
```

---

## 📊 测试覆盖率

```bash
# 安装覆盖率工具
pip install coverage pytest-cov

# 运行并生成覆盖率报告
pytest tests/ --cov=lottery --cov-report=html

# 查看报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## 🔗 相关文档

- [开发者文档](../docs/developer/README.md)
- [API 文档](../docs/user/API_DOCUMENTATION.md)
- [测试清单](../docs/user/TEST_URLS.md)

---

## ⚠️ 注意事项

1. **数据依赖**: 某些测试需要真实数据或模型文件
2. **服务依赖**: API 测试需要先启动 Web 服务
3. **执行顺序**: 某些测试有先后依赖关系
4. **清理工作**: 测试后可能需要清理临时文件或数据

---

**最后更新**: 2026-02-05
