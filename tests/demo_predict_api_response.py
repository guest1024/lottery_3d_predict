#!/usr/bin/env python3
"""
演示预测API的完整响应 - 展示组选投注方案
"""
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottery_web.settings')
django.setup()

from lottery.views import generate_prediction
from django.test import RequestFactory


def demo_api_response():
    """演示API完整响应"""
    print("=" * 80)
    print("【3D彩票预测API - 完整响应示例】")
    print("=" * 80)
    
    # 创建请求
    factory = RequestFactory()
    request = factory.post('/api/predict/', 
                          data=json.dumps({'num_bets': 100}),
                          content_type='application/json')
    
    # 获取响应
    response = generate_prediction(request)
    data = json.loads(response.content)
    
    if data['status'] != 'success':
        print(f"错误: {data.get('message')}")
        return
    
    pred = data['prediction']
    plan = pred['betting_plan']
    
    print(f"\n📅 预测期号: {pred['period']}")
    print(f"📊 机会评分: {pred['score']:.2f} 分 (阈值: {pred['threshold']:.2f})")
    print(f"💡 投注建议: {pred['recommendation']}")
    print(f"🎯 是否投注: {'✅ 是' if pred['should_bet'] else '❌ 否'}")
    
    print(f"\n🔢 Top10 推荐数字:")
    print(f"   {pred['top10_digits']}")
    
    print(f"\n💰 投注计划详情:")
    print(f"   总注数: {plan['num_bets']} 注")
    print(f"   总成本: {plan['total_cost']} 元 (每注2元)")
    print(f"   组六: {plan['group6_count']} 注 (中奖173元/注)")
    print(f"   组三: {plan['group3_count']} 注 (中奖346元/注)")
    print(f"   预期ROI: {plan['expected_roi']:+.1f}%")
    
    print(f"\n🎲 具体投注组合 (共{len(plan['combinations'])}注):")
    print("=" * 80)
    
    # 分别显示组六和组三
    group6_combos = [c for c in plan['combinations'] if len(set(c)) == 3]
    group3_combos = [c for c in plan['combinations'] if len(set(c)) == 2]
    
    print(f"\n【组六投注】共 {len(group6_combos)} 注 (每注2元,中奖173元)")
    print("-" * 80)
    for i, combo in enumerate(group6_combos[:20], 1):  # 显示前20注
        print(f"{i:3d}. {combo[0]} {combo[1]} {combo[2]}", end="  ")
        if i % 5 == 0:
            print()  # 每5注换行
    if len(group6_combos) > 20:
        print(f"\n... (还有{len(group6_combos) - 20}注)")
    
    print(f"\n\n【组三投注】共 {len(group3_combos)} 注 (每注2元,中奖346元)")
    print("-" * 80)
    for i, combo in enumerate(group3_combos[:20], 1):  # 显示前20注
        print(f"{i:3d}. {combo[0]} {combo[1]} {combo[2]}", end="  ")
        if i % 5 == 0:
            print()
    if len(group3_combos) > 20:
        print(f"\n... (还有{len(group3_combos) - 20}注)")
    
    print("\n" + "=" * 80)
    print("📋 投注说明:")
    print("=" * 80)
    print("1. 组六 (3个不同数字): 任意顺序开出即中奖,奖金173元")
    print("   例: [1,2,3] 可中: 123, 132, 213, 231, 312, 321")
    print()
    print("2. 组三 (2个相同+1个不同): 任意顺序开出即中奖,奖金346元")
    print("   例: [1,1,2] 可中: 112, 121, 211")
    print()
    print("3. 建议: 只在评分≥58.45分时投注 (历史Top1%策略ROI +405%)")
    print("=" * 80)
    
    # JSON格式完整输出
    print("\n\n📄 API 完整JSON响应:")
    print("=" * 80)
    
    # 为了展示,只显示前5个组合
    display_data = data.copy()
    display_data['prediction']['betting_plan']['combinations'] = plan['combinations'][:5] + ['...']
    
    print(json.dumps(display_data, indent=2, ensure_ascii=False))
    print("=" * 80)


if __name__ == '__main__':
    demo_api_response()
