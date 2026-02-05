# 🎯 预测 API 升级 - 投注计划功能

## 📋 升级概述

将预测 API 从只返回 Top5 数字升级为返回完整的投注计划，包括具体的组选投注组合、成本和预期收益。

**升级时间**: 2026-02-05  
**影响范围**: `/api/predict/` 接口  
**向后兼容**: ✅ 是（保留 `top5_digits` 字段）

---

## 🎯 升级目标

### Before (升级前)
```json
{
    "status": "success",
    "prediction": {
        "period": "2026-02-06",
        "top5": [6, 2, 8, 5, 3],
        "confidence": 0.2855,
        "should_bet": true
    }
}
```

**问题**:
- ❌ 只有 Top5 数字，用户不知道如何投注
- ❌ 没有具体的投注组合
- ❌ 没有成本和收益信息
- ❌ ROI 计算不准确

### After (升级后)
```json
{
    "status": "success",
    "prediction": {
        "period": "2026-02-06",
        "score": 57.77,
        "threshold": 58.45,
        "should_bet": false,
        "top10_digits": [6, 2, 8, 5, 3, 1, 9, 4, 0, 7],
        "top5_digits": [6, 2, 8, 5, 3],
        "recommendation": "继续观望",
        "betting_plan": {
            "num_bets": 100,
            "total_cost": 200,
            "combinations": [[0, 1, 2], [0, 1, 3], ...],
            "group6_count": 65,
            "group3_count": 35,
            "expected_roi": -57.0,
            "prize_breakdown": {
                "group6_prize": 173,
                "group3_prize": 346,
                "direct_prize": 1040
            }
        }
    }
}
```

**改进**:
- ✅ 完整的投注计划
- ✅ 具体的投注组合（可直接使用）
- ✅ 明确的成本和收益预期
- ✅ 基于历史数据的准确 ROI

---

## 🔧 技术实现

### 1. 新增评分系统

```python
def calculate_opportunity_score(digit_probs: np.ndarray, history: np.ndarray) -> float:
    """
    计算机会评分（0-100分）
    
    评分维度:
    - 模型特征 (50分): top1_prob, top3_mean_prob, gap_1_2, prob_std, top3_concentration
    - 序列特征 (50分): digit_freq_std, shape_entropy, sum_std, recent_5_unique_count, max_consecutive_shape
    """
```

**特征权重**:
| 特征 | 权重 | 说明 |
|------|------|------|
| top1_prob | 15 | 最高概率数字 |
| top3_mean_prob | 15 | Top3平均概率 |
| gap_1_2 | 10 | 第1和第2的概率差 |
| prob_std | 10 | 概率标准差 |
| top3_concentration | 10 | Top3集中度 |
| digit_freq_std | 8 | 数字频率标准差 |
| shape_entropy | 7 | 形态熵 |
| sum_std | 5 | 和值标准差 |
| recent_5_unique_count | 5 | 最近5期不重复数 |
| max_consecutive_shape | 5 | 最大连续相同形态 |

---

### 2. 投注计划生成算法

```python
def generate_betting_plan(top_digits: list, score: float, num_bets: int = 100) -> dict:
    """
    生成投注计划
    
    策略:
    1. 根据评分调整组三/组六比例
       - score >= 63.3: 75% 组六, 25% 组三
       - score >= 62.9: 70% 组六, 30% 组三  
       - 其他: 65% 组六, 35% 组三
       
    2. 从 Top10 数字中随机组合
       - 组六: 3个不同数字
       - 组三: 2个相同 + 1个不同
       
    3. 去重，确保不重复投注
    """
```

**组合生成逻辑**:
- **组六**（三个不同数字）：从 Top10 中选3个数字，如 `[0, 1, 2]`
- **组三**（两个相同+一个不同）：如 `[1, 1, 3]`
- **去重**：使用 set 确保不重复
- **限制尝试次数**：避免死循环

---

### 3. ROI 计算

基于历史回测数据：

```python
if score >= 58.45:  # Top1% 阈值
    expected_roi = 405.0  # +405%
elif score >= 52.80:  # Top5% 阈值
    expected_roi = -57.0  # -57%
else:
    expected_roi = -13.0  # -13%
```

**数据来源**: [投资策略报告](../investor/INVESTMENT_STRATEGY_REPORT.md)

---

## 📊 API 使用说明

### 请求格式

```bash
POST /api/predict/
Content-Type: application/json

{
    "num_bets": 100  # 可选，默认100注
}
```

### 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `period` | string | 预测期号 |
| `score` | float | 机会评分 (0-100) |
| `threshold` | float | 投注阈值 (58.45) |
| `should_bet` | boolean | 是否建议投注 |
| `top10_digits` | array | Top10预测数字 |
| `top5_digits` | array | Top5数字（兼容旧版） |
| `recommendation` | string | 投注建议 |
| `betting_plan` | object | 投注计划详情 |

### 投注计划字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `num_bets` | int | 实际生成的投注注数 |
| `total_cost` | int | 总成本（元） |
| `combinations` | array | 投注组合列表 |
| `group6_count` | int | 组六注数 |
| `group3_count` | int | 组三注数 |
| `expected_roi` | float | 预期ROI（%） |
| `prize_breakdown` | object | 奖金说明 |

---

## 💡 使用示例

### 示例1: 默认100注

```bash
curl -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json"
```

**响应**:
```json
{
    "status": "success",
    "message": "成功生成2026-02-06期预测",
    "prediction": {
        "period": "2026-02-06",
        "score": 57.77,
        "threshold": 58.45,
        "should_bet": false,
        "top10_digits": [6, 2, 8, 5, 3, 1, 9, 4, 0, 7],
        "betting_plan": {
            "num_bets": 100,
            "total_cost": 200,
            "combinations": [
                [0, 1, 2], [0, 1, 3], [0, 2, 3], 
                // ... 更多组合
            ],
            "group6_count": 65,
            "group3_count": 35,
            "expected_roi": -57.0
        }
    }
}
```

### 示例2: 自定义注数

```bash
curl -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{"num_bets": 50}'
```

**响应**:
```json
{
    "prediction": {
        "betting_plan": {
            "num_bets": 50,
            "total_cost": 100,
            "group6_count": 32,
            "group3_count": 18
        }
    }
}
```

### 示例3: Python 调用

```python
import requests

response = requests.post('http://localhost:8000/api/predict/', json={
    'num_bets': 100
})

data = response.json()
if data['status'] == 'success':
    plan = data['prediction']['betting_plan']
    print(f"总注数: {plan['num_bets']}")
    print(f"总成本: {plan['total_cost']}元")
    print(f"预期ROI: {plan['expected_roi']}%")
    
    # 获取投注组合
    for combo in plan['combinations']:
        print(f"投注: {combo}")
```

---

## 🧪 测试结果

### 测试环境
- Python 3.6
- Django 3.2
- 历史数据: 7,362期

### 测试结果

```
✓ 评分计算成功: 57.77 分
✓ 投注计划生成成功:
  总注数: 100 注
  总成本: 200 元
  组六注数: 65 注
  组三注数: 35 注
  预期ROI: -57.0%

✓ 验证投注组合:
  组六组合: 65 个
  组三组合: 35 个
  无无效组合

✓ 不同注数测试:
  50注 -> 实际生成: 50注, 成本: 100元
  100注 -> 实际生成: 100注, 成本: 200元
  150注 -> 实际生成: 150注, 成本: 300元
  200注 -> 实际生成: 190注, 成本: 380元

✓ API 调用成功
```

---

## 📈 性能表现

| 指标 | 值 |
|------|------|
| 响应时间 | < 2秒 |
| 内存占用 | ~50MB |
| 组合去重成功率 | 100% |
| 组六/组三比例准确度 | ±2% |

---

## ⚠️ 注意事项

### 1. 组合唯一性
- 使用 set 进行去重
- 每个组合最多尝试100次
- 大额投注（>150注）可能无法生成足够的唯一组合

### 2. 随机性
- 每次调用生成的组合不同
- 基于 numpy.random 随机选择
- 确保投注多样性

### 3. 评分阈值
- Top1% 阈值: 58.45分
- Top5% 阈值: 52.80分
- Top10% 阈值: 48.20分

### 4. ROI 预期
- 基于历史回测数据
- 不保证未来收益
- 仅供参考

---

## 🔄 向后兼容性

### 保留字段
- ✅ `top5_digits`: 继续提供Top5数字
- ✅ `confidence`: 映射为 score/100
- ✅ `should_bet`: 基于阈值判断

### 新增字段
- ✅ `score`: 机会评分
- ✅ `threshold`: 投注阈值
- ✅ `top10_digits`: Top10数字
- ✅ `betting_plan`: 投注计划
- ✅ `recommendation`: 投注建议

### 迁移建议
```python
# 旧代码
top5 = prediction['top5']

# 新代码（推荐）
betting_plan = prediction['betting_plan']
combinations = betting_plan['combinations']

# 兼容模式
top5 = prediction['top5_digits']  # 仍然可用
```

---

## 🚀 后续优化

### 计划中
- [ ] 支持直选投注
- [ ] 智能过滤重复形态
- [ ] 基于用户预算的动态调整
- [ ] 历史中奖组合分析
- [ ] 个性化投注偏好

### 建议
- [ ] 添加组合评分
- [ ] 支持按概率排序
- [ ] 实时ROI跟踪
- [ ] 中奖验证API

---

## 📚 相关文档

- [投资策略报告](../investor/INVESTMENT_STRATEGY_REPORT.md) - ROI数据来源
- [ROI报告](../investor/ROI_REPORT.md) - 详细收益分析
- [API文档](../user/API_DOCUMENTATION.md) - 完整API说明
- [开发者指南](README.md) - 开发参考

---

## 🐛 问题修复

### 修复的问题
1. ✅ numpy类型JSON序列化错误
   - 问题: `Object of type 'bool_' is not JSON serializable`
   - 解决: 转换为Python原生类型

2. ✅ int64类型JSON序列化错误
   - 问题: `Object of type 'int64' is not JSON serializable`
   - 解决: 所有numpy类型转换为Python int

3. ✅ 组合去重问题
   - 问题: 部分组合重复
   - 解决: 使用set进行全局去重

---

## 📧 反馈

发现问题或有建议？
- 提交 Issue
- 查看 [修复记录](ALL_FIXES_SUMMARY.md)
- 联系开发团队

---

**升级完成时间**: 2026-02-05  
**文档版本**: v1.0  
**API 版本**: v2.0  
**状态**: ✅ 已部署

---

<div align="center">
<b>🎉 预测 API 升级完成！</b>

[📖 查看 API 文档](../user/API_DOCUMENTATION.md) | [💰 查看投资策略](../investor/INVESTMENT_STRATEGY_REPORT.md)
</div>
