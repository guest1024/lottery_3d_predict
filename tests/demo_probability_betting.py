#!/usr/bin/env python3
"""
演示基于概率的投注分配 - 完整展示
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottery_web.settings')
django.setup()

from lottery.views import generate_prediction
from django.test import RequestFactory
import json


def demo_probability_betting():
    """演示概率投注分配"""
    print("=" * 90)
    print("【基于概率的智能投注分配系统】")
    print("=" * 90)
    
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
    combinations = plan['combinations']
    
    print(f"\n📅 预测期号: {pred['period']}")
    print(f"📊 机会评分: {pred['score']:.2f} 分 / {pred['threshold']:.2f} 分")
    print(f"💡 投注建议: {pred['recommendation']}")
    print(f"🎯 是否投注: {'✅ 是' if pred['should_bet'] else '❌ 否'}")
    
    print(f"\n🔢 模型预测的数字概率 (Top10):")
    top10 = pred['top10_digits']
    print(f"   数字: {top10}")
    
    print(f"\n💰 智能投注计划:")
    print(f"   总注数: {plan['num_bets']} 注")
    print(f"   总成本: {plan['total_cost']} 元")
    print(f"   组合数: {len(combinations)} 个 (按概率优选)")
    print(f"   覆盖概率: {plan['total_probability']:.4f} ({plan['total_probability']*100:.2f}%)")
    print(f"   期望收益: {plan['total_expected_return']:.2f} 元")
    print(f"   预期ROI: {plan['expected_roi']:+.2f}%")
    
    # 注数分布统计
    bet_counts = [c['bets'] for c in combinations]
    print(f"\n📈 注数分配策略:")
    print(f"   最高注数: {max(bet_counts)} 注 (分配给最高概率组合)")
    print(f"   最低注数: {min(bet_counts)} 注")
    print(f"   平均注数: {sum(bet_counts)/len(bet_counts):.1f} 注")
    print(f"   差异倍数: {max(bet_counts)/min(bet_counts):.1f}x")
    
    # 分组统计
    group6_combos = [c for c in combinations if c['type'] == 'group6']
    group3_combos = [c for c in combinations if c['type'] == 'group3']
    
    print(f"\n📊 组合类型分布:")
    print(f"   组六: {len(group6_combos)} 个组合, {sum(c['bets'] for c in group6_combos)} 注")
    print(f"   组三: {len(group3_combos)} 个组合, {sum(c['bets'] for c in group3_combos)} 注")
    
    # 详细投注表
    print(f"\n🎲 详细投注表 (按概率从高到低排序):")
    print("=" * 90)
    print(f"{'排名':<4} {'组合':<10} {'类型':<6} {'概率':<10} {'注数':<6} {'成本':<8} "
          f"{'期望收益':<12} {'单注期望':<10}")
    print("-" * 90)
    
    for i, combo in enumerate(combinations, 1):
        combo_str = f"{combo['combo'][0]}{combo['combo'][1]}{combo['combo'][2]}"
        type_str = "组六" if combo['type'] == 'group6' else "组三"
        expected_per_bet = combo['expected_return'] / combo['bets']
        
        print(f"{i:<4} {combo_str:<10} {type_str:<6} {combo['probability']:<10.6f} "
              f"{combo['bets']:<6} {combo['cost']:<8} "
              f"{combo['expected_return']:<12.2f} {expected_per_bet:<10.2f}")
    
    # 概率分布分析
    print("\n" + "=" * 90)
    print("📊 概率分布分析")
    print("=" * 90)
    
    prob_ranges = [
        (0.15, float('inf'), "极高概率"),
        (0.10, 0.15, "高概率"),
        (0.05, 0.10, "中等概率"),
        (0.01, 0.05, "低概率"),
        (0, 0.01, "极低概率")
    ]
    
    for min_prob, max_prob, label in prob_ranges:
        range_combos = [c for c in combinations if min_prob <= c['probability'] < max_prob]
        if range_combos:
            total_bets = sum(c['bets'] for c in range_combos)
            print(f"{label} ({min_prob:.2f}-{max_prob:.2f}): "
                  f"{len(range_combos)} 个组合, {total_bets} 注 "
                  f"({total_bets/plan['num_bets']*100:.1f}%)")
    
    # 投注建议
    print("\n" + "=" * 90)
    print("📋 投注说明")
    print("=" * 90)
    print("✅ 优势特点:")
    print("   1. 高概率组合获得更多注数 (最高可达最低的4-5倍)")
    print("   2. 自动计算每个组合的理论中奖概率")
    print("   3. 覆盖30个左右的优质组合,而非盲目铺注")
    print("   4. 期望收益最大化,同时控制成本")
    print()
    print("💡 使用建议:")
    print(f"   - 当前评分: {pred['score']:.2f} 分")
    print(f"   - 投注阈值: {pred['threshold']:.2f} 分")
    if pred['should_bet']:
        print("   ✅ 建议投注: 评分达到Top1%标准,历史胜率100%")
    else:
        print(f"   ❌ 继续观望: 评分低于阈值 {pred['threshold'] - pred['score']:.2f} 分")
    print()
    print("⚠️  风险提示:")
    print("   - 彩票具有随机性,概率仅供参考")
    print("   - 只用闲钱投注,设定止损线")
    print("   - 历史表现不代表未来收益")
    print("=" * 90)


if __name__ == '__main__':
    demo_probability_betting()
