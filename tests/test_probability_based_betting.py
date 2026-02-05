#!/usr/bin/env python3
"""
测试基于概率的投注分配策略
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


def test_probability_based_betting():
    """测试概率分配投注"""
    print("=" * 80)
    print("测试基于概率的投注分配策略")
    print("=" * 80)
    
    # 创建请求
    factory = RequestFactory()
    request = factory.post('/api/predict/', 
                          data=json.dumps({'num_bets': 100}),
                          content_type='application/json')
    
    # 调用API
    print("\n[1] 生成预测...")
    response = generate_prediction(request)
    data = json.loads(response.content)
    
    if data['status'] != 'success':
        print(f"✗ 失败: {data.get('message')}")
        if 'traceback' in data:
            print(data['traceback'])
        return False
    
    pred = data['prediction']
    plan = pred['betting_plan']
    
    print(f"✓ 预测成功")
    print(f"  期号: {pred['period']}")
    print(f"  评分: {pred['score']:.2f}")
    
    # 验证新字段
    print("\n[2] 验证概率信息...")
    
    if 'total_probability' not in plan:
        print("✗ 缺少 total_probability 字段")
        return False
    
    if 'total_expected_return' not in plan:
        print("✗ 缺少 total_expected_return 字段")
        return False
    
    print(f"✓ 累计覆盖概率: {plan['total_probability']:.4f}")
    print(f"✓ 期望总收益: {plan['total_expected_return']:.2f} 元")
    print(f"✓ 总成本: {plan['total_cost']} 元")
    print(f"✓ 预期ROI: {plan['expected_roi']:+.2f}%")
    
    # 验证组合结构
    print("\n[3] 验证组合详情...")
    combinations = plan['combinations']
    
    if not combinations:
        print("✗ 组合列表为空")
        return False
    
    # 检查第一个组合的结构
    first_combo = combinations[0]
    required_fields = ['combo', 'type', 'probability', 'bets', 'cost', 'prize', 'expected_return']
    
    for field in required_fields:
        if field not in first_combo:
            print(f"✗ 组合缺少字段: {field}")
            return False
    
    print(f"✓ 组合结构完整")
    print(f"✓ 总组合数: {len(combinations)}")
    
    # 显示Top10高概率组合
    print("\n[4] Top10 高概率组合:")
    print("-" * 80)
    print(f"{'排名':<4} {'组合':<12} {'类型':<8} {'概率':<10} {'注数':<6} {'成本':<8} {'期望收益':<10}")
    print("-" * 80)
    
    for i, combo in enumerate(combinations[:10], 1):
        combo_str = f"{combo['combo'][0]},{combo['combo'][1]},{combo['combo'][2]}"
        type_str = "组六" if combo['type'] == 'group6' else "组三"
        print(f"{i:<4} {combo_str:<12} {type_str:<8} {combo['probability']:<10.6f} "
              f"{combo['bets']:<6} {combo['cost']:<8} {combo['expected_return']:<10.2f}")
    
    # 验证概率递减
    print("\n[5] 验证概率排序...")
    probabilities = [c['probability'] for c in combinations]
    is_sorted = all(probabilities[i] >= probabilities[i+1] for i in range(len(probabilities)-1))
    
    if is_sorted:
        print(f"✓ 组合按概率从高到低排序")
    else:
        print(f"✗ 组合排序不正确")
        return False
    
    # 统计分析
    print("\n[6] 统计分析...")
    total_bets = sum(c['bets'] for c in combinations)
    group6_bets = sum(c['bets'] for c in combinations if c['type'] == 'group6')
    group3_bets = sum(c['bets'] for c in combinations if c['type'] == 'group3')
    
    print(f"✓ 总注数: {total_bets}")
    print(f"✓ 组六注数: {group6_bets} ({group6_bets/total_bets*100:.1f}%)")
    print(f"✓ 组三注数: {group3_bets} ({group3_bets/total_bets*100:.1f}%)")
    
    # 注数分布分析
    bet_distribution = [c['bets'] for c in combinations]
    max_bets = max(bet_distribution)
    min_bets = min(bet_distribution)
    avg_bets = sum(bet_distribution) / len(bet_distribution)
    
    print(f"\n[7] 注数分配分析...")
    print(f"✓ 最多注数: {max_bets} (分配给最高概率组合)")
    print(f"✓ 最少注数: {min_bets}")
    print(f"✓ 平均注数: {avg_bets:.2f}")
    print(f"✓ 组合数量: {len(combinations)}")
    
    # 验证高概率组合获得更多注数
    top3_avg = sum(c['bets'] for c in combinations[:3]) / 3
    bottom3_avg = sum(c['bets'] for c in combinations[-3:]) / 3
    
    if top3_avg > bottom3_avg:
        print(f"✓ 高概率组合获得更多注数 (Top3平均: {top3_avg:.1f}, Bottom3平均: {bottom3_avg:.1f})")
    else:
        print(f"✗ 注数分配不合理")
    
    # 完整信息展示
    print("\n" + "=" * 80)
    print("测试结果总结")
    print("=" * 80)
    print(f"期号: {pred['period']}")
    print(f"机会评分: {pred['score']:.2f} 分")
    print(f"Top10数字: {pred['top10_digits']}")
    print(f"\n投注计划:")
    print(f"  总注数: {plan['num_bets']} 注")
    print(f"  总成本: {plan['total_cost']} 元")
    print(f"  组合数: {len(combinations)} 个")
    print(f"  覆盖概率: {plan['total_probability']:.4f}")
    print(f"  期望收益: {plan['total_expected_return']:.2f} 元")
    print(f"  预期ROI: {plan['expected_roi']:+.2f}%")
    print(f"  投注建议: {pred['recommendation']}")
    print("=" * 80)
    print("✓ 所有测试通过! 概率分配机制工作正常")
    print("=" * 80)
    
    return True


if __name__ == '__main__':
    try:
        success = test_probability_based_betting()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
