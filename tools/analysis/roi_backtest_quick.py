"""
快速收益回测 - 只测试最优策略
"""
import sys
sys.path.insert(0, '/c1/program/lottery_3d_predict')

import json
import numpy as np
import torch
from pathlib import Path
from collections import defaultdict

from src.models.lottery_model import LotteryModel

# 3D彩票奖金设置
PRIZE_CONFIG = {
    'direct': 1040,      # 直选: 1040元
    'group3': 346,       # 组选3: 346元  
    'group6': 173,       # 组选6: 173元
}

TICKET_PRICE = 2

def load_data(json_file, num_records=1200):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    recent_data = data['data'][-num_records:]
    sequences = np.array([item['numbers'] for item in recent_data])
    return sequences, recent_data

def predict_single(model, history_30, device='cpu'):
    input_seq = torch.LongTensor(history_30).unsqueeze(0).to(device)
    model.eval()
    with torch.no_grad():
        predictions = model.predict(input_seq)
        digit_probs = predictions['digit_probs'][0]
        top5_digits = np.argsort(digit_probs)[-5:][::-1]
        return {'digit_probs': digit_probs, 'top5': top5_digits}

def generate_smart_bets(top5_digits, n_bets=100):
    """智能投注策略"""
    combinations = set()
    top3 = top5_digits[:3]
    
    # 60注用Top3
    for _ in range(60):
        combo = tuple(sorted(np.random.choice(top3, size=3, replace=True)))
        combinations.add(combo)
    
    # 30注用Top5
    for _ in range(30):
        combo = tuple(sorted(np.random.choice(top5_digits, size=3, replace=True)))
        combinations.add(combo)
    
    # 10注直选
    for _ in range(10):
        combo = tuple(np.random.choice(top3, size=3, replace=False))
        combinations.add(combo)
    
    return list(combinations)[:n_bets]

def check_win(bet_combo, actual_numbers):
    actual_sorted = tuple(sorted(actual_numbers))
    actual_direct = tuple(actual_numbers)
    bet_sorted = tuple(sorted(bet_combo))
    
    if bet_combo == actual_direct:
        return 'direct', PRIZE_CONFIG['direct']
    
    if bet_sorted == actual_sorted:
        unique = len(set(actual_numbers))
        if unique == 2:
            return 'group3', PRIZE_CONFIG['group3']
        elif unique == 3:
            return 'group6', PRIZE_CONFIG['group6']
    
    return 'miss', 0

def main():
    print("=" * 80)
    print("3D彩票预测 - 收益回测报告")
    print("=" * 80)
    
    device = torch.device('cpu')
    
    print(f"\n[1] 加载数据和模型")
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    sequences, raw_data = load_data(data_file, num_records=1200)
    model = LotteryModel.load('models/checkpoints/best_model.pth', device=device)
    print(f"✓ 数据: {len(sequences)}期")
    print(f"✓ 模型已加载")
    
    print(f"\n[2] 奖金设置")
    print(f"  直选: ¥{PRIZE_CONFIG['direct']}")
    print(f"  组选3: ¥{PRIZE_CONFIG['group3']}")
    print(f"  组选6: ¥{PRIZE_CONFIG['group6']}")
    print(f"  单注: ¥{TICKET_PRICE}")
    
    print(f"\n[3] 执行回测(200期)")
    
    results = []
    total_cost = 0
    total_prize = 0
    win_stats = defaultdict(int)
    
    test_periods = 200
    window_size = 30
    n_bets = 100
    
    start_idx = len(sequences) - test_periods - window_size
    
    for i in range(test_periods):
        idx = start_idx + i
        history = sequences[idx:idx + window_size]
        actual = sequences[idx + window_size]
        actual_period = raw_data[idx + window_size]['period']
        
        pred = predict_single(model, history, device)
        bet_combos = generate_smart_bets(pred['top5'], n_bets=n_bets)
        
        period_cost = len(bet_combos) * TICKET_PRICE
        total_cost += period_cost
        
        period_wins = []
        period_prize = 0
        
        for combo in bet_combos:
            win_type, prize = check_win(combo, actual)
            if prize > 0:
                period_wins.append({'combo': combo, 'type': win_type, 'prize': prize})
                period_prize += prize
                win_stats[win_type] += 1
        
        total_prize += period_prize
        period_profit = period_prize - period_cost
        
        results.append({
            'period': actual_period,
            'actual': actual.tolist(),
            'cost': period_cost,
            'prize': period_prize,
            'profit': period_profit,
            'cumulative_profit': total_prize - total_cost
        })
        
        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{test_periods}")
    
    print(f"  完成!")
    
    # 统计
    total_profit = total_prize - total_cost
    roi = (total_profit / total_cost * 100) if total_cost > 0 else 0
    profit_periods = sum(1 for r in results if r['profit'] > 0)
    
    print(f"\n[4] 收益统计")
    print(f"{'='*60}")
    print(f"总投入: ¥{total_cost:,.0f}")
    print(f"总奖金: ¥{total_prize:,.0f}")
    print(f"总利润: ¥{total_profit:,.0f}")
    print(f"ROI: {roi:.2f}%")
    print(f"{'='*60}")
    
    print(f"\n期均数据:")
    print(f"  期均投入: ¥{total_cost/test_periods:.0f}")
    print(f"  期均奖金: ¥{total_prize/test_periods:.0f}")
    print(f"  期均利润: ¥{total_profit/test_periods:.0f}")
    
    print(f"\n盈亏分布:")
    print(f"  盈利期数: {profit_periods} ({profit_periods/test_periods:.1%})")
    print(f"  亏损期数: {test_periods - profit_periods}")
    
    print(f"\n中奖统计:")
    total_wins = sum(win_stats.values())
    print(f"  总中奖次数: {total_wins}")
    for win_type, count in sorted(win_stats.items()):
        print(f"  {win_type}: {count}次")
    
    # 最佳/最差期
    best = max(results, key=lambda x: x['profit'])
    worst = min(results, key=lambda x: x['profit'])
    
    print(f"\n极值统计:")
    print(f"  最佳期: {best['period']}, 利润¥{best['profit']}")
    print(f"  最差期: {worst['period']}, 利润¥{worst['profit']}")
    
    # 累计利润走势
    print(f"\n累计利润走势(每50期):")
    for i in range(0, len(results), 50):
        period = results[min(i+49, len(results)-1)]
        print(f"  第{i+1}-{min(i+50, len(results))}期: ¥{period['cumulative_profit']:,.0f}")
    
    # 下一期预测
    print(f"\n[5] 下一期预测")
    last_30 = sequences[-30:]
    pred = predict_single(model, last_30, device)
    bet_combos = generate_smart_bets(pred['top5'], n_bets=100)
    
    print(f"\n上期: {raw_data[-1]['period']}")
    print(f"  开奖: {raw_data[-1]['numbers']}")
    
    print(f"\n下期预测:")
    print(f"  Top5: {pred['top5'].tolist()}")
    print(f"  推荐{len(bet_combos)}注, 成本¥{len(bet_combos)*TICKET_PRICE}")
    
    print(f"\n前20注推荐:")
    for i, combo in enumerate(bet_combos[:20], 1):
        print(f"  {i:2d}. {combo[0]} {combo[1]} {combo[2]}")
    
    # 预期收益(基于历史)
    expected_wins = total_wins / test_periods * 1  # 预期下期中奖次数
    expected_prize = (total_prize / test_periods) if test_periods > 0 else 0
    expected_profit = expected_prize - (len(bet_combos) * TICKET_PRICE)
    
    print(f"\n预期收益(基于历史):")
    print(f"  预期中奖: {expected_wins:.2f}次")
    print(f"  预期奖金: ¥{expected_prize:.0f}")
    print(f"  预期利润: ¥{expected_profit:.0f}")
    
    # 保存
    output = {
        'summary': {
            'total_periods': int(test_periods),
            'total_cost': float(total_cost),
            'total_prize': float(total_prize),
            'total_profit': float(total_profit),
            'roi_percentage': float(roi),
            'win_rate': float(profit_periods / test_periods)
        },
        'next_period': {
            'last_period': raw_data[-1]['period'],
            'last_numbers': [int(x) for x in raw_data[-1]['numbers']],
            'predicted_top5': [int(x) for x in pred['top5']],
            'recommendations': [[int(x) for x in c] for c in bet_combos],
            'total_cost': int(len(bet_combos) * TICKET_PRICE),
            'expected_prize': float(expected_prize),
            'expected_profit': float(expected_profit)
        }
    }
    
    with open('results/roi_report.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 已保存到: results/roi_report.json")
    
    print(f"\n{'='*80}")
    print(f"⚠️  风险提示:")
    print(f"  ROI为负({roi:.2f}%), 长期投注会亏损")
    print(f"  彩票是负期望游戏, 不适合作为投资")
    print(f"  请理性购彩, 仅作娱乐")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
