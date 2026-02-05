"""
基于数据库的概率模型回测
使用Django ORM直接从数据库读取数据
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottery_web.settings')
django.setup()

import numpy as np
import torch
from collections import defaultdict
from itertools import combinations

from lottery.models import LotteryPeriod
from lottery.views import calculate_opportunity_score, calculate_combination_probability
from src.models.lottery_model import LotteryModel

# 奖金配置
PRIZE_CONFIG = {
    'group3': 346,
    'group6': 173,
}

TICKET_PRICE = 2


def generate_probability_bets(digit_probs: np.ndarray, num_bets: int = 100):
    """生成基于概率的投注计划"""
    top_indices = np.argsort(digit_probs)[::-1][:10]
    top10_digits = top_indices.tolist()
    
    candidates = []
    
    # 组六
    for combo in combinations(top10_digits, 3):
        combo_sorted = tuple(sorted(combo))
        prob = calculate_combination_probability(combo_sorted, digit_probs)
        candidates.append({
            'combo': combo_sorted,
            'type': 'group6',
            'probability': prob,
            'prize': 173
        })
    
    # 组三
    for d1 in top10_digits:
        for d2 in top10_digits:
            if d1 != d2:
                combo_sorted = tuple(sorted([d1, d1, d2]))
                prob = calculate_combination_probability(combo_sorted, digit_probs)
                candidates.append({
                    'combo': combo_sorted,
                    'type': 'group3',
                    'probability': prob,
                    'prize': 346
                })
    
    candidates.sort(key=lambda x: x['probability'], reverse=True)
    
    top_n = min(max(int(num_bets * 0.25), 15), len(candidates))
    selected = candidates[:top_n]
    
    # 指数衰减权重
    weights = np.array([0.85 ** i for i in range(len(selected))])
    weights = weights / np.sum(weights)
    
    # 分配注数
    theoretical_bets = [max(1, round(num_bets * w)) for w in weights]
    
    diff = num_bets - sum(theoretical_bets)
    idx = len(theoretical_bets) - 1
    while diff != 0 and idx >= 0:
        if diff > 0:
            theoretical_bets[idx] += 1
            diff -= 1
        elif diff < 0 and theoretical_bets[idx] > 1:
            theoretical_bets[idx] -= 1
            diff += 1
        idx -= 1
    
    result = []
    for i, cand in enumerate(selected):
        if theoretical_bets[i] > 0:
            result.append({
                'combo': cand['combo'],
                'type': cand['type'],
                'probability': cand['probability'],
                'bets': theoretical_bets[i],
                'prize': cand['prize']
            })
    
    return result


def check_win(bet_combo: tuple, actual: tuple):
    """检查中奖"""
    actual_sorted = tuple(sorted(actual))
    
    if bet_combo == actual_sorted:
        unique = len(set(actual))
        if unique == 2:
            return 'group3', 346
        elif unique == 3:
            return 'group6', 173
    
    return 'miss', 0


def backtest_from_database(model_path, num_bets=100, test_periods=200, threshold=58.45):
    """从数据库回测"""
    print("=" * 90)
    print("基于数据库的概率模型回测")
    print("=" * 90)
    
    # 加载模型
    print("\n[1] 加载模型...")
    device = torch.device('cpu')
    model = LotteryModel.load(model_path, device=device)
    model.eval()
    print("✓ 模型加载成功")
    
    # 获取数据
    print("\n[2] 从数据库加载数据...")
    all_periods = list(LotteryPeriod.objects.all().order_by('period'))
    print(f"✓ 加载 {len(all_periods)} 期数据")
    print(f"  时间范围: {all_periods[0].period} ~ {all_periods[-1].period}")
    
    # 准备回测
    window_size = 30
    total_available = len(all_periods) - window_size
    test_periods = min(test_periods, total_available)
    start_idx = len(all_periods) - test_periods - window_size
    
    print(f"\n[3] 回测参数:")
    print(f"  投注策略: 概率权重分配")
    print(f"  每期投注: {num_bets} 注 ({num_bets * TICKET_PRICE} 元)")
    print(f"  投注阈值: {threshold} 分")
    print(f"  回测期数: {test_periods}")
    print(f"  起始期号: {all_periods[start_idx + window_size].period}")
    
    # 执行回测
    results = []
    total_cost = 0
    total_prize = 0
    bet_periods = 0
    win_periods = 0
    win_by_type = defaultdict(int)
    
    print(f"\n[4] 执行回测...")
    print("-" * 90)
    
    for i in range(test_periods):
        idx = start_idx + i
        
        # 历史序列
        history_periods = all_periods[idx:idx + window_size]
        history = np.array([[p.digit1, p.digit2, p.digit3] for p in history_periods])
        
        # 实际开奖
        actual_period = all_periods[idx + window_size]
        actual = np.array([actual_period.digit1, actual_period.digit2, actual_period.digit3])
        
        # 预测
        input_seq = torch.LongTensor(history).unsqueeze(0).to(device)
        with torch.no_grad():
            predictions = model.predict(input_seq)
            digit_probs = predictions['digit_probs'][0]
        
        # 计算评分(使用完整评分函数)
        score = calculate_opportunity_score(digit_probs, history)
        should_bet = score >= threshold
        
        if not should_bet:
            results.append({
                'period': actual_period.period,
                'score': score,
                'bet': False,
                'cost': 0,
                'prize': 0,
                'profit': 0
            })
            continue
        
        # 生成投注
        betting_plan = generate_probability_bets(digit_probs, num_bets)
        
        period_cost = sum(b['bets'] for b in betting_plan) * TICKET_PRICE
        total_cost += period_cost
        bet_periods += 1
        
        # 检查中奖
        period_prize = 0
        period_wins = []
        
        for plan in betting_plan:
            win_type, single_prize = check_win(plan['combo'], tuple(actual))
            if single_prize > 0:
                total_win = single_prize * plan['bets']
                period_prize += total_win
                period_wins.append({
                    'combo': plan['combo'],
                    'bets': plan['bets'],
                    'prize': total_win
                })
                win_by_type[win_type] += plan['bets']
        
        total_prize += period_prize
        if period_prize > 0:
            win_periods += 1
        
        profit = period_prize - period_cost
        
        results.append({
            'period': actual_period.period,
            'score': score,
            'bet': True,
            'cost': period_cost,
            'prize': period_prize,
            'profit': profit,
            'wins': period_wins
        })
        
        if period_prize > 0:
            print(f"  ✓ {actual_period.period}: 评分{score:.2f} 成本{period_cost}元 "
                  f"中奖{period_prize}元 利润{profit:+d}元")
    
    # 统计结果
    print("\n" + "=" * 90)
    print("回测结果汇总")
    print("=" * 90)
    
    roi = ((total_prize - total_cost) / total_cost * 100) if total_cost > 0 else 0
    win_rate = (win_periods / bet_periods * 100) if bet_periods > 0 else 0
    
    print(f"\n📊 整体统计:")
    print(f"  回测期数: {test_periods}")
    print(f"  投注期数: {bet_periods} ({bet_periods/test_periods*100:.1f}%)")
    print(f"  观望期数: {test_periods - bet_periods}")
    
    print(f"\n💰 收益统计:")
    print(f"  总成本: {total_cost:,} 元")
    print(f"  总收益: {total_prize:,} 元")
    print(f"  净利润: {total_prize - total_cost:+,} 元")
    print(f"  ROI: {roi:+.2f}%")
    
    print(f"\n🎯 中奖统计:")
    print(f"  中奖期数: {win_periods} / {bet_periods}")
    print(f"  胜率: {win_rate:.2f}%")
    
    if win_by_type:
        print(f"\n  中奖明细:")
        for wtype, count in sorted(win_by_type.items()):
            prize_per = PRIZE_CONFIG[wtype]
            print(f"    {wtype}: {count} 注 × {prize_per}元 = {count * prize_per:,}元")
    
    # 评分分层
    print(f"\n📈 按评分分层:")
    score_ranges = [
        (60, 100, "≥60分"),
        (58.45, 60, "58.45-60"),
        (55, 58.45, "55-58.45"),
        (50, 55, "50-55"),
    ]
    
    for min_s, max_s, label in score_ranges:
        range_r = [r for r in results if r['bet'] and min_s <= r['score'] < max_s]
        if range_r:
            r_cost = sum(r['cost'] for r in range_r)
            r_prize = sum(r['prize'] for r in range_r)
            r_roi = ((r_prize - r_cost) / r_cost * 100) if r_cost > 0 else 0
            r_win = sum(1 for r in range_r if r['prize'] > 0)
            r_rate = (r_win / len(range_r) * 100) if range_r else 0
            
            print(f"  {label}: {len(range_r)}期, ROI {r_roi:+.2f}%, 胜率 {r_rate:.1f}%")
    
    print("=" * 90)
    
    return results


if __name__ == '__main__':
    model_path = str(project_root / 'models' / 'checkpoints' / 'best_model.pth')
    
    results = backtest_from_database(
        model_path=model_path,
        num_bets=100,
        test_periods=200,
        threshold=58.45
    )
