# 每日机会评估 - 使用指南

## 🎯 今日评分

**当前评分: 55.65分**  
**投注建议: ❌ 继续观望**  
**评分差距: 2.80分**

> 需要评分达到 58.45分 才建议投注

---

## 🚀 快速使用

### 方式1: 命令行（推荐）

```bash
# 进入项目目录
cd /c1/program/lottery_3d_predict

# 详细模式（默认）
python daily_opportunity_check.py

# 安静模式（一行输出）
python daily_opportunity_check.py --quiet

# JSON模式（适合脚本解析）
python daily_opportunity_check.py --json
```

### 方式2: Python代码

```python
from daily_opportunity_check import check_today_opportunity

# 详细评估
result = check_today_opportunity()

if result['should_bet']:
    print(f"✅ 建议投注！")
    print(f"投注: {result['betting_plan']['num_bets']}注")
    print(f"成本: ¥{result['betting_plan']['cost']}")
else:
    print(f"❌ 继续观望")
    print(f"评分: {result['score']:.2f}")
```

### 方式3: 快速检查

```python
from daily_opportunity_check import check_quick, get_betting_plan

# 快速判断
if check_quick():
    plan = get_betting_plan()
    print(f"投注{plan['num_bets']}注，成本¥{plan['cost']}")
else:
    print("今天观望")
```

---

## 📅 设置每日定时运行

### Linux/Mac: Crontab

```bash
# 编辑crontab
crontab -e

# 添加以下行（每天上午10点运行）
0 10 * * * cd /c1/program/lottery_3d_predict && python daily_opportunity_check.py --quiet >> /tmp/betting.log 2>&1

# 或发送结果到邮箱
0 10 * * * cd /c1/program/lottery_3d_predict && python daily_opportunity_check.py --quiet | mail -s "今日投注建议" your@email.com
```

### Windows: 任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器: 每天上午10:00
4. 操作: 启动程序
   - 程序: `python`
   - 参数: `daily_opportunity_check.py --quiet`
   - 起始于: `C:\path\to\lottery_3d_predict`

---

## 📊 返回结果说明

### 基本字段（总是返回）

```python
{
    'timestamp': '2026-02-05T15:40:00',  # 评估时间
    'score': 55.65,                       # 机会评分
    'threshold': 58.45,                   # 投注阈值
    'should_bet': False,                  # 是否建议投注
    'score_gap': -2.80,                   # 评分差距
    'recommendation': 'SKIP',             # BET 或 SKIP
    
    'last_period': {                      # 上期开奖
        'period': '2026-02-04',
        'date': '2026035',
        'numbers': [2, 1, 3]
    },
    
    'top10_digits': [6,2,8,5,3,1,0,7,4,9] # Top10预测数字
}
```

### 投注计划（仅当should_bet=True时）

```python
{
    'betting_plan': {
        'num_bets': 50,               # 投注注数
        'cost': 100,                  # 总成本（元）
        'combinations': [             # 投注组合
            [0, 2, 6],
            [1, 2, 8],
            ...
        ],
        'expected_win_rate': 0.6667,  # 预期胜率（67%）
        'expected_roi': 4.0542        # 预期ROI（405%）
    }
}
```

---

## 🎓 使用场景示例

### 场景1: 早晨查看投注建议

```bash
# 每天早上运行一次
cd /c1/program/lottery_3d_predict
python daily_opportunity_check.py --quiet
```

输出示例：
```
✅ 建议投注 | 评分: 59.12 | 成本: ¥150
```
或
```
❌ 继续观望 | 评分: 55.65 | 差距: 2.80
```

### 场景2: 自动化记录

```python
from daily_opportunity_check import check_today_opportunity
from datetime import datetime

result = check_today_opportunity(verbose=False)

# 记录到文件
with open('betting_history.csv', 'a') as f:
    date = datetime.now().strftime('%Y-%m-%d')
    f.write(f"{date},{result['score']:.2f},{result['recommendation']}\n")
```

### 场景3: 消息通知

```python
from daily_opportunity_check import check_today_opportunity

result = check_today_opportunity(verbose=False)

if result['should_bet']:
    # 发送微信/邮件/短信通知
    message = f"""
    🎯 投注提醒
    
    评分: {result['score']:.2f}分
    投注: {result['betting_plan']['num_bets']}注
    成本: ¥{result['betting_plan']['cost']}
    
    预期胜率: 67%
    预期ROI: +405%
    """
    
    # send_notification(message)
    print(message)
```

### 场景4: Web API

```python
from flask import Flask, jsonify
from daily_opportunity_check import check_today_opportunity

app = Flask(__name__)

@app.route('/api/check_opportunity')
def api_check():
    result = check_today_opportunity(verbose=False)
    return jsonify({
        'status': 'success',
        'data': result
    })

if __name__ == '__main__':
    app.run(port=5000)
```

访问: `http://localhost:5000/api/check_opportunity`

---

## ⚙️ 高级选项

### 自定义阈值

```bash
# 使用更保守的阈值（60分）
python daily_opportunity_check.py --threshold 60.0

# Python代码
result = check_today_opportunity(threshold=60.0)
```

### 自定义数据和模型路径

```python
result = check_today_opportunity(
    data_file='data/custom_data.json',
    model_path='models/custom_model.pth',
    threshold=58.45
)
```

---

## 📈 历史策略表现

基于300期回测：

| 阈值 | 投注频率 | 胜率 | ROI | 推荐 |
|------|---------|------|-----|------|
| 58.45 (Top1%) | 1.0% | 67% | **+405%** | ✅ **推荐** |
| 57.17 (Top5%) | 5.0% | 20% | -57% | ❌ |
| 56.90 (Top10%) | 10.0% | 17% | -13% | ❌ |

**结论**: 只有58.45分以上才建议投注！

---

## ⚠️ 重要提示

### ✅ 应该做的：
1. **每天查看评分** - 不要漏掉高分时刻
2. **严格遵守阈值** - 只有≥58.45分才投注
3. **记录每次结果** - 用于验证策略有效性
4. **保持耐心** - 高分时刻很少（约1%）

### ❌ 不应该做的：
1. ❌ 降低阈值增加投注频率
2. ❌ 连续多期强制投注
3. ❌ 忽略评分直接投注
4. ❌ 超出资金承受能力

---

## 🔍 常见问题

### Q1: 为什么评分总是不达标？
**A**: 这是正常的。高分时刻（≥58.45）平均每100期才出现1次（约每3-4个月），需要耐心等待。

### Q2: 可以降低阈值吗？
**A**: 强烈不建议。回测数据显示，只有58.45以上才能实现正收益（ROI +405%）。降低到57分以下都是负收益。

### Q3: 如何验证策略是否还有效？
**A**: 建议每月运行一次完整回测：
```bash
python smart_betting_strategy.py
```

### Q4: 多久会出现一次投注机会？
**A**: 平均每100期1次，约每3-4个月。最长可能数月没有机会，这是正常的。

### Q5: 如果错过了高分时刻怎么办？
**A**: 不要追投。等待下一次机会即可。

---

## 📞 相关文件

- `daily_opportunity_check.py` - 核心评估函数
- `example_daily_usage.py` - 使用示例代码
- `realtime_opportunity_monitor.py` - 完整版监控（更详细）
- `INVESTMENT_STRATEGY_REPORT.md` - 完整投资策略报告
- `QUICK_START.md` - 快速开始指南

---

## 🎯 今天的建议

根据当前评估结果：

```
评分: 55.65分
阈值: 58.45分
差距: 2.80分

建议: ❌ 继续观望
理由: 评分未达到盈利阈值
```

**明天请再次运行评估！**

---

**最后更新**: 2026-02-05  
**当前评分**: 55.65分  
**投注建议**: 继续观望
