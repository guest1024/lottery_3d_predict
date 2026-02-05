"""
测试新的预测 API
"""
import django
import os
import sys
import json

# 设置 Django 环境
sys.path.insert(0, '/c1/program/lottery_3d_predict')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottery_web.settings')
django.setup()

from lottery.views import generate_prediction, calculate_opportunity_score, generate_betting_plan
from lottery.models import LotteryPeriod
from django.test import RequestFactory
import numpy as np

print("=" * 70)
print("测试新的预测 API 功能")
print("=" * 70)

# 创建模拟请求
factory = RequestFactory()

# 测试1: 测试评分函数
print("\n[测试1] 评分函数")
print("-" * 70)

# 模拟概率分布和历史数据
digit_probs = np.array([0.15, 0.12, 0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.17])
history = np.random.randint(0, 10, size=(30, 3))

score = calculate_opportunity_score(digit_probs, history)
print(f"✓ 评分计算成功: {score:.2f} 分")

# 测试2: 测试投注计划生成
print("\n[测试2] 投注计划生成")
print("-" * 70)

top_digits = [6, 2, 8, 5, 3, 1, 9, 4, 0, 7]
betting_plan = generate_betting_plan(top_digits, score, num_bets=100)

print(f"✓ 投注计划生成成功:")
print(f"  总注数: {betting_plan['num_bets']} 注")
print(f"  总成本: {betting_plan['total_cost']} 元")
print(f"  组六注数: {betting_plan['group6_count']} 注")
print(f"  组三注数: {betting_plan['group3_count']} 注")
print(f"  预期ROI: {betting_plan['expected_roi']:.1f}%")
print(f"  组合示例: {betting_plan['combinations'][:5]}")

# 测试3: 验证组合格式
print("\n[测试3] 验证投注组合")
print("-" * 70)

group6_count = 0
group3_count = 0
invalid_count = 0

for combo in betting_plan['combinations']:
    unique_count = len(set(combo))
    if unique_count == 3:
        group6_count += 1
    elif unique_count == 2:
        group3_count += 1
    else:
        invalid_count += 1

print(f"✓ 组六组合: {group6_count} 个")
print(f"✓ 组三组合: {group3_count} 个")
if invalid_count > 0:
    print(f"✗ 无效组合: {invalid_count} 个")
else:
    print(f"✓ 无无效组合")

# 测试4: 测试不同注数
print("\n[测试4] 测试不同投注注数")
print("-" * 70)

for num_bets in [50, 100, 150, 200]:
    plan = generate_betting_plan(top_digits, score, num_bets)
    print(f"  {num_bets}注 -> 实际生成: {plan['num_bets']}注, 成本: {plan['total_cost']}元")

# 测试5: 模拟 API 调用
print("\n[测试5] 模拟 API 调用")
print("-" * 70)

try:
    # 检查数据库
    period_count = LotteryPeriod.objects.count()
    print(f"✓ 数据库连接成功，历史数据: {period_count} 期")
    
    if period_count >= 30:
        # 创建POST请求
        request_data = json.dumps({'num_bets': 100})
        request = factory.post(
            '/api/predict/',
            data=request_data,
            content_type='application/json'
        )
        
        print("✓ 正在调用 generate_prediction()...")
        response = generate_prediction(request)
        
        # 解析响应
        response_data = json.loads(response.content)
        
        if response_data['status'] == 'success':
            print("✓ API 调用成功")
            prediction = response_data['prediction']
            print(f"\n预测结果:")
            print(f"  期号: {prediction['period']}")
            print(f"  评分: {prediction['score']:.2f} 分")
            print(f"  阈值: {prediction['threshold']} 分")
            print(f"  建议: {prediction['recommendation']}")
            print(f"  是否投注: {'是' if prediction['should_bet'] else '否'}")
            print(f"\n投注计划:")
            plan = prediction['betting_plan']
            print(f"  总注数: {plan['num_bets']} 注")
            print(f"  总成本: {plan['total_cost']} 元")
            print(f"  组六: {plan['group6_count']} 注")
            print(f"  组三: {plan['group3_count']} 注")
            print(f"  预期ROI: {plan['expected_roi']:.1f}%")
            print(f"  组合数量: {len(plan['combinations'])} 个")
            print(f"  示例组合: {plan['combinations'][:3]}")
        else:
            print(f"✗ API 调用失败: {response_data['message']}")
            if 'traceback' in response_data:
                print(f"错误详情:\n{response_data['traceback']}")
    else:
        print(f"⚠ 历史数据不足 (需要30期，当前{period_count}期)")
        
except Exception as e:
    print(f"✗ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
