# 3D彩票预测模型 - API文档

## 📋 目录
- [模型输入说明](#模型输入说明)
- [模型输出说明](#模型输出说明)
- [使用示例](#使用示例)
- [接口定义](#接口定义)

---

## 模型输入说明

### 输入格式

#### 1. 训练输入
```python
# 输入形状
X_train: torch.LongTensor
  形状: (batch_size, sequence_length, 3)
  数据类型: Long (整数)
  取值范围: 0-9
  
# 示例
X_train = torch.LongTensor([
    [  # 第1个样本(30期历史)
        [1, 2, 3],  # 第1期: 百位1, 十位2, 个位3
        [4, 5, 6],  # 第2期: 百位4, 十位5, 个位6
        ...
        [7, 8, 9]   # 第30期
    ],
    [  # 第2个样本
        ...
    ]
])

# 标签
y_train: torch.LongTensor
  形状: (batch_size, 3)
  数据类型: Long (整数)
  取值范围: 0-9
  
# 示例
y_train = torch.LongTensor([
    [0, 1, 2],  # 第1个样本的真实下一期号码
    [3, 4, 5],  # 第2个样本的真实下一期号码
    ...
])
```

#### 2. 预测输入
```python
# 单次预测输入
history_30: numpy.ndarray
  形状: (30, 3)
  数据类型: int
  取值范围: 0-9
  说明: 最近30期的历史开奖号码

# 示例
history_30 = np.array([
    [1, 2, 3],  # 最早的一期
    [4, 5, 6],
    ...
    [7, 8, 9]   # 最近的一期
])

# 转换为模型输入
input_tensor = torch.LongTensor(history_30).unsqueeze(0)  # 形状: (1, 30, 3)
```

### 数据要求

| 项目 | 要求 | 说明 |
|-----|------|------|
| **序列长度** | 30期 | 固定使用最近30期历史数据 |
| **数据格式** | [百位, 十位, 个位] | 每期3个数字 |
| **数值范围** | 0-9 | 每个位置的数字范围 |
| **数据类型** | 整数 | 不能有小数或缺失值 |
| **时间顺序** | 从旧到新 | 第1行最早,第30行最新 |

### 预处理要求

```python
# 1. 数据清洗
def clean_data(raw_data):
    """
    清洗原始数据
    
    Args:
        raw_data: 原始数据列表
        
    Returns:
        清洗后的数据
    """
    cleaned = []
    for record in raw_data:
        numbers = record['numbers']
        # 检查数据完整性
        if len(numbers) == 3:
            # 检查数值范围
            if all(0 <= n <= 9 for n in numbers):
                cleaned.append(numbers)
    return np.array(cleaned)

# 2. 序列构建
def create_sequences(data, window_size=30):
    """
    创建滑动窗口序列
    
    Args:
        data: 完整历史数据 (N, 3)
        window_size: 窗口大小
        
    Returns:
        X: 特征序列 (N-30, 30, 3)
        y: 标签 (N-30, 3)
    """
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i + window_size])
        y.append(data[i + window_size])
    return np.array(X), np.array(y)
```

---

## 模型输出说明

### 输出格式

#### 1. 训练输出
```python
# 模型前向传播输出
outputs = model(X_batch)

# 输出字典
outputs = {
    'digit_probs': torch.Tensor,      # (batch_size, 10) - 数字概率
    'shape_logits': torch.Tensor,     # (batch_size, 3) - 形态logits
    'sum_logits': torch.Tensor,       # (batch_size, 28) - 和值logits
    'ac_logits': torch.Tensor,        # (batch_size, 3) - AC值logits
    'attention_weights': torch.Tensor # (batch_size, 30) - 注意力权重
}
```

#### 2. 预测输出
```python
# 预测模式输出
predictions = model.predict(input_tensor)

# 输出字典
predictions = {
    'digit_probs': numpy.ndarray,      # (10,) - 每个数字的概率
    'shape_probs': numpy.ndarray,      # (3,) - 形态概率 [组六, 组三, 豹子]
    'sum_probs': numpy.ndarray,        # (28,) - 和值概率 [0-27]
    'ac_probs': numpy.ndarray,         # (3,) - AC值概率
    'attention_weights': numpy.ndarray # (30,) - 注意力权重
}

# 示例输出
{
    'digit_probs': array([0.05, 0.08, 0.29, 0.27, 0.06, 0.28, 0.30, 0.07, 0.28, 0.06]),
    #                     [  0,   1,    2,    3,    4,    5,    6,    7,    8,    9 ]
    'shape_probs': array([0.735, 0.248, 0.017]),  # [组六, 组三, 豹子]
    'sum_probs': array([0.001, 0.002, ..., 0.085, 0.084, ...]),  # 0-27
    'ac_probs': array([0.3, 0.5, 0.2]),  # AC值1,2,3
    'attention_weights': array([0.01, 0.02, ..., 0.15, 0.18])  # 30期权重
}
```

### 输出解释

#### 1. digit_probs - 数字概率
```python
# 10个数字(0-9)各自出现的概率
digit_probs: array([0.05, 0.08, 0.29, 0.27, 0.06, 0.28, 0.30, 0.07, 0.28, 0.06])
#               索引: 0     1     2     3     4     5     6     7     8     9

# Top5预测
top5_indices = np.argsort(digit_probs)[-5:][::-1]
# 结果: [6, 2, 8, 5, 3]  表示数字6最可能出现

# 使用方法
- 取Top5作为候选数字池
- 概率越高,出现可能性越大
- 用于生成推荐号码组合
```

#### 2. shape_probs - 形态概率
```python
# 3种形态的概率
shape_probs: array([0.735, 0.248, 0.017])
#                   [组六,  组三,  豹子]

# 形态定义
- 组六: 三个数字各不相同 (如: 1 2 3)
- 组三: 两个数字相同 (如: 1 1 2)
- 豹子: 三个数字相同 (如: 1 1 1)

# 使用方法
- 根据形态概率调整选号策略
- 高概率形态优先考虑
```

#### 3. sum_probs - 和值概率
```python
# 和值0-27的概率分布
sum_probs: array([0.001, 0.002, ..., 0.085, 0.084, ...])
#         索引:   0      1           14     15

# Top5和值
top5_sums = np.argsort(sum_probs)[-5:][::-1]
# 结果: [14, 15, 13, 11, 19]

# 使用方法
- 关注高概率和值
- 结合形态生成号码
```

#### 4. attention_weights - 注意力权重
```python
# 30期历史的重要性权重
attention_weights: array([0.01, 0.02, ..., 0.15, 0.18])
#                  期号:   1     2           29    30

# 解释
- 权重越大,该期对预测影响越大
- 通常最近几期权重较大
- 可视化展示模型关注点
```

---

## 使用示例

### 完整预测流程

```python
import torch
import numpy as np
from src.models.lottery_model import LotteryModel

# 1. 加载模型
model = LotteryModel.load('models/checkpoints/best_model.pth', device='cpu')

# 2. 准备输入数据(最近30期)
history_30 = np.array([
    [1, 2, 3],
    [4, 5, 6],
    # ... 共30期
    [7, 8, 9]
])

# 3. 转换为tensor
input_tensor = torch.LongTensor(history_30).unsqueeze(0)  # (1, 30, 3)

# 4. 预测
predictions = model.predict(input_tensor)

# 5. 获取Top5预测数字
digit_probs = predictions['digit_probs'][0]
top5_digits = np.argsort(digit_probs)[-5:][::-1]

print(f"Top5预测数字: {top5_digits}")
print(f"对应概率: {digit_probs[top5_digits]}")

# 6. 获取形态预测
shape_probs = predictions['shape_probs'][0]
shape_names = ['组六', '组三', '豹子']
predicted_shape = shape_names[np.argmax(shape_probs)]

print(f"预测形态: {predicted_shape}")
print(f"形态概率: {shape_probs}")

# 7. 生成推荐号码
def generate_recommendations(top5_digits, shape_probs, n=10):
    """生成推荐号码组合"""
    recommendations = []
    
    # 基于Top5随机组合
    for _ in range(n):
        combo = np.random.choice(top5_digits, size=3, replace=True)
        recommendations.append(combo.tolist())
    
    return recommendations

recommendations = generate_recommendations(top5_digits, shape_probs)
for i, combo in enumerate(recommendations, 1):
    print(f"{i}. {combo[0]} {combo[1]} {combo[2]}")
```

### 批量预测

```python
def batch_predict(model, data, window_size=30):
    """
    批量预测
    
    Args:
        model: 训练好的模型
        data: 完整历史数据 (N, 3)
        window_size: 窗口大小
        
    Returns:
        预测结果列表
    """
    results = []
    
    for i in range(window_size, len(data)):
        # 获取历史窗口
        history = data[i-window_size:i]
        
        # 转换为tensor
        input_tensor = torch.LongTensor(history).unsqueeze(0)
        
        # 预测
        predictions = model.predict(input_tensor)
        
        # 获取Top5
        digit_probs = predictions['digit_probs'][0]
        top5 = np.argsort(digit_probs)[-5:][::-1]
        
        results.append({
            'period': i,
            'top5': top5.tolist(),
            'digit_probs': digit_probs
        })
    
    return results
```

---

## 接口定义

### Python API

#### 1. 加载模型
```python
def load_model(model_path: str, device: str = 'cpu') -> LotteryModel:
    """
    加载训练好的模型
    
    Args:
        model_path: 模型文件路径
        device: 设备 ('cpu' 或 'cuda')
        
    Returns:
        加载的模型实例
    """
    model = LotteryModel.load(model_path, device=device)
    return model
```

#### 2. 单次预测
```python
def predict_next(model: LotteryModel, 
                 history_30: np.ndarray) -> dict:
    """
    预测下一期号码
    
    Args:
        model: 训练好的模型
        history_30: 最近30期历史 (30, 3)
        
    Returns:
        预测结果字典
        {
            'top5_digits': [6, 2, 8, 5, 3],
            'digit_probs': [...],
            'predicted_shape': '组六',
            'shape_probs': [...],
            'top5_sums': [14, 15, 13, 11, 19],
            'recommendations': [[6, 2, 8], [5, 3, 6], ...]
        }
    """
    # 预测
    input_tensor = torch.LongTensor(history_30).unsqueeze(0)
    predictions = model.predict(input_tensor)
    
    # 提取Top5数字
    digit_probs = predictions['digit_probs'][0]
    top5_digits = np.argsort(digit_probs)[-5:][::-1]
    
    # 形态预测
    shape_probs = predictions['shape_probs'][0]
    shape_names = ['组六', '组三', '豹子']
    predicted_shape = shape_names[np.argmax(shape_probs)]
    
    # 和值预测
    sum_probs = predictions['sum_probs'][0]
    top5_sums = np.argsort(sum_probs)[-5:][::-1]
    
    # 生成推荐
    recommendations = generate_recommendations(top5_digits, shape_probs)
    
    return {
        'top5_digits': top5_digits.tolist(),
        'digit_probs': digit_probs.tolist(),
        'predicted_shape': predicted_shape,
        'shape_probs': shape_probs.tolist(),
        'top5_sums': top5_sums.tolist(),
        'recommendations': recommendations
    }
```

#### 3. 批量回测
```python
def backtest(model: LotteryModel,
             data: np.ndarray,
             start_idx: int = 0,
             end_idx: int = -1) -> dict:
    """
    批量回测
    
    Args:
        model: 训练好的模型
        data: 完整历史数据 (N, 3)
        start_idx: 开始索引
        end_idx: 结束索引
        
    Returns:
        回测统计结果
    """
    results = []
    stats = {
        'total': 0,
        'top5_hits': 0,
        'top3_hits': 0,
        'top1_hits': 0
    }
    
    # 滚动预测
    for i in range(start_idx + 30, end_idx if end_idx > 0 else len(data)):
        history = data[i-30:i]
        actual = data[i]
        
        pred = predict_next(model, history)
        
        # 统计命中
        actual_set = set(actual)
        top5_set = set(pred['top5_digits'])
        
        stats['total'] += 1
        stats['top5_hits'] += len(actual_set & top5_set)
        
        results.append({
            'period': i,
            'actual': actual.tolist(),
            'predicted': pred['top5_digits'],
            'hit_count': len(actual_set & top5_set)
        })
    
    # 计算准确率
    stats['top5_avg_hits'] = stats['top5_hits'] / stats['total'] if stats['total'] > 0 else 0
    
    return {
        'results': results,
        'statistics': stats
    }
```

---

## 数据格式示例

### JSON输入格式
```json
{
  "history": [
    {"period": "2025-01-01", "numbers": [1, 2, 3]},
    {"period": "2025-01-02", "numbers": [4, 5, 6]},
    ...
    {"period": "2025-01-30", "numbers": [7, 8, 9]}
  ]
}
```

### JSON输出格式
```json
{
  "prediction": {
    "top5_digits": [6, 2, 8, 5, 3],
    "digit_probs": [0.05, 0.08, 0.29, 0.27, 0.06, 0.28, 0.30, 0.07, 0.28, 0.06],
    "predicted_shape": "组六",
    "shape_probs": [0.735, 0.248, 0.017],
    "top5_sums": [14, 15, 13, 11, 19],
    "recommendations": [
      [6, 2, 8],
      [5, 3, 6],
      [2, 8, 5]
    ]
  },
  "metadata": {
    "model_version": "v1.0",
    "prediction_time": "2026-02-05 14:30:00",
    "confidence": 0.48
  }
}
```

---

## 错误处理

### 常见错误

#### 1. 输入数据不足
```python
if len(history) < 30:
    raise ValueError(f"需要至少30期历史数据,当前只有{len(history)}期")
```

#### 2. 数据格式错误
```python
if not isinstance(history, np.ndarray):
    raise TypeError("history必须是numpy.ndarray类型")

if history.shape != (30, 3):
    raise ValueError(f"history形状必须是(30, 3),当前是{history.shape}")
```

#### 3. 数值范围错误
```python
if not np.all((history >= 0) & (history <= 9)):
    raise ValueError("所有数字必须在0-9范围内")
```

---

## 性能指标

### 推理性能
- CPU单次预测: ~10ms
- GPU单次预测: ~2ms
- 批量预测(1000期): ~5秒(CPU)

### 准确率参考
- 位置匹配率: 48.17%
- Top1命中率: 33.00%
- Top5平均命中: 1.31/3

---

## 更新日志

- **v1.0** (2026-02-05)
  - 初始版本发布
  - 支持单次和批量预测
  - 完整的API接口

---

**文档版本**: v1.0  
**最后更新**: 2026-02-05
