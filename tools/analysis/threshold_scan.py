"""
阈值扫描工具 - 找到最优投注阈值
扫描不同评分阈值,计算每个阈值下的ROI、胜率和投注率
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
import argparse

from lottery.models import LotteryPeriod
from lottery.views import calculate_opportunity_score, calculate_combination_probability
from src.models.lottery_model import LotteryModel

PRIZE_CONFIG = {'group3': 346, 'group6': 173}
TICKET_PRICE = 2


def generate_probability_bets(digit_probs: np.ndarray, num_bets: int = 100):
    """生成概率投注计划"""
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
    
    weights = np.array([0.85 ** i for i in range(len(selected))])
    weights = weights / np.sum(weights)
    
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


def backtest_single_threshold(model, all_periods, threshold, num_bets=100, 
                              test_periods=500, window_size=30, device='cpu'):
    """
    对单个阈值进行回测
    
    Returns:
        回测统计结果
    """
    total_available = len(all_periods) - window_size
    test_periods = min(test_periods, total_available)
    start_idx = len(all_periods) - test_periods - window_size
    
    total_cost = 0
    total_prize = 0
    bet_periods = 0
    win_periods = 0
    win_by_type = defaultdict(int)
    
    for i in range(test_periods):
        idx = start_idx + i
        
        history_periods = all_periods[idx:idx + window_size]
        history = np.array([[p.digit1, p.digit2, p.digit3] for p in history_periods])
        
        actual_period = all_periods[idx + window_size]
        actual = np.array([actual_period.digit1, actual_period.digit2, actual_period.digit3])
        
        # 预测
        input_seq = torch.LongTensor(history).unsqueeze(0).to(device)
        with torch.no_grad():
            predictions = model.predict(input_seq)
            digit_probs = predictions['digit_probs'][0]
        
        # 计算评分
        score = calculate_opportunity_score(digit_probs, history)
        should_bet = score >= threshold
        
        if not should_bet:
            continue
        
        # 生成投注
        betting_plan = generate_probability_bets(digit_probs, num_bets)
        
        period_cost = sum(b['bets'] for b in betting_plan) * TICKET_PRICE
        total_cost += period_cost
        bet_periods += 1
        
        # 检查中奖
        period_prize = 0
        
        for plan in betting_plan:
            win_type, single_prize = check_win(plan['combo'], tuple(actual))
            if single_prize > 0:
                total_win = single_prize * plan['bets']
                period_prize += total_win
                win_by_type[win_type] += plan['bets']
        
        total_prize += period_prize
        if period_prize > 0:
            win_periods += 1
    
    # 计算统计
    roi = ((total_prize - total_cost) / total_cost * 100) if total_cost > 0 else 0
    win_rate = (win_periods / bet_periods * 100) if bet_periods > 0 else 0
    bet_rate = (bet_periods / test_periods * 100) if test_periods > 0 else 0
    profit = total_prize - total_cost
    
    return {
        'threshold': threshold,
        'test_periods': test_periods,
        'bet_periods': bet_periods,
        'bet_rate': bet_rate,
        'win_periods': win_periods,
        'win_rate': win_rate,
        'total_cost': total_cost,
        'total_prize': total_prize,
        'profit': profit,
        'roi': roi,
        'win_by_type': dict(win_by_type)
    }


def threshold_scan(model_path, min_threshold=50, max_threshold=75, step=2, 
                  test_periods=500, num_bets=100):
    """
    扫描阈值范围
    
    Args:
        model_path: 模型路径
        min_threshold: 最小阈值
        max_threshold: 最大阈值
        step: 步长
        test_periods: 回测期数
        num_bets: 每期投注数
    """
    print("=" * 100)
    print("阈值扫描工具 - 寻找最优投注点")
    print("=" * 100)
    
    # 加载模型
    print("\n[1] 加载模型...")
    device = torch.device('cpu')
    model = LotteryModel.load(model_path, device=device)
    model.eval()
    print("✓ 模型加载成功")
    
    # 加载数据
    print("\n[2] 加载数据...")
    all_periods = list(LotteryPeriod.objects.all().order_by('period'))
    print(f"✓ 加载 {len(all_periods)} 期数据")
    
    # 扫描参数
    thresholds = np.arange(min_threshold, max_threshold + step, step)
    
    print(f"\n[3] 扫描参数:")
    print(f"  阈值范围: {min_threshold} ~ {max_threshold} 分")
    print(f"  步长: {step} 分")
    print(f"  扫描点数: {len(thresholds)} 个")
    print(f"  每期投注: {num_bets} 注 ({num_bets * TICKET_PRICE}元)")
    print(f"  回测期数: {test_periods}")
    
    # 执行扫描
    print(f"\n[4] 执行扫描...")
    print("-" * 100)
    
    results = []
    
    for threshold in thresholds:
        print(f"  扫描阈值 {threshold:.1f} 分...", end=" ", flush=True)
        
        result = backtest_single_threshold(
            model=model,
            all_periods=all_periods,
            threshold=threshold,
            num_bets=num_bets,
            test_periods=test_periods
        )
        
        results.append(result)
        
        print(f"投注率 {result['bet_rate']:.1f}%, ROI {result['roi']:+.2f}%, 胜率 {result['win_rate']:.1f}%")
    
    # 分析结果
    print("\n" + "=" * 100)
    print("扫描结果分析")
    print("=" * 100)
    
    # 完整结果表
    print(f"\n📊 完整结果表:")
    print("-" * 100)
    print(f"{'阈值':<8} {'投注率':<10} {'投注期':<8} {'中奖期':<8} {'胜率':<10} "
          f"{'成本':<12} {'收益':<12} {'利润':<12} {'ROI':<10}")
    print("-" * 100)
    
    for r in results:
        print(f"{r['threshold']:<8.1f} {r['bet_rate']:<10.1f}% {r['bet_periods']:<8} "
              f"{r['win_periods']:<8} {r['win_rate']:<10.1f}% "
              f"{r['total_cost']:<12,} {r['total_prize']:<12,} {r['profit']:<12,} "
              f"{r['roi']:<10.2f}%")
    
    # 找到最优阈值
    print("\n" + "=" * 100)
    print("最优阈值分析")
    print("=" * 100)
    
    # 按不同指标排序
    positive_roi = [r for r in results if r['roi'] > 0]
    
    if positive_roi:
        best_roi = max(positive_roi, key=lambda x: x['roi'])
        best_profit = max(positive_roi, key=lambda x: x['profit'])
        best_winrate = max(positive_roi, key=lambda x: x['win_rate'])
        
        print(f"\n🏆 最佳ROI:")
        print(f"  阈值: {best_roi['threshold']:.1f} 分")
        print(f"  ROI: {best_roi['roi']:+.2f}%")
        print(f"  利润: {best_roi['profit']:+,} 元")
        print(f"  胜率: {best_roi['win_rate']:.1f}%")
        print(f"  投注率: {best_roi['bet_rate']:.1f}% ({best_roi['bet_periods']}/{test_periods}期)")
        
        print(f"\n💰 最大利润:")
        print(f"  阈值: {best_profit['threshold']:.1f} 分")
        print(f"  利润: {best_profit['profit']:+,} 元")
        print(f"  ROI: {best_profit['roi']:+.2f}%")
        print(f"  胜率: {best_profit['win_rate']:.1f}%")
        
        print(f"\n🎯 最高胜率:")
        print(f"  阈值: {best_winrate['threshold']:.1f} 分")
        print(f"  胜率: {best_winrate['win_rate']:.1f}%")
        print(f"  ROI: {best_winrate['roi']:+.2f}%")
        print(f"  投注期: {best_winrate['bet_periods']}期")
        
        # 推荐阈值
        print(f"\n" + "=" * 100)
        print("💡 推荐阈值")
        print("=" * 100)
        
        # 综合评分: ROI权重50%, 胜率30%, 投注率20%
        for r in positive_roi:
            r['composite_score'] = (
                r['roi'] * 0.5 +
                r['win_rate'] * 0.3 +
                (r['bet_rate'] if r['bet_rate'] <= 20 else 20) * 0.2
            )
        
        best_composite = max(positive_roi, key=lambda x: x['composite_score'])
        
        print(f"\n推荐阈值: {best_composite['threshold']:.1f} 分")
        print(f"  ROI: {best_composite['roi']:+.2f}%")
        print(f"  胜率: {best_composite['win_rate']:.1f}%")
        print(f"  投注率: {best_composite['bet_rate']:.1f}%")
        print(f"  利润: {best_composite['profit']:+,} 元")
        print(f"  综合评分: {best_composite['composite_score']:.2f}")
        
    else:
        print("\n⚠️  警告: 没有找到ROI为正的阈值!")
        print("  所有阈值都表现为亏损")
        
        # 显示最小亏损
        min_loss = min(results, key=lambda x: abs(x['roi']))
        print(f"\n  最小亏损阈值: {min_loss['threshold']:.1f} 分")
        print(f"  ROI: {min_loss['roi']:+.2f}%")
        print(f"  利润: {min_loss['profit']:+,} 元")
    
    print("=" * 100)
    
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='阈值扫描工具')
    parser.add_argument('--min', type=float, default=50, help='最小阈值')
    parser.add_argument('--max', type=float, default=75, help='最大阈值')
    parser.add_argument('--step', type=float, default=2, help='步长')
    parser.add_argument('--periods', type=int, default=500, help='回测期数')
    parser.add_argument('--bets', type=int, default=100, help='每期投注数')
    
    args = parser.parse_args()
    
    model_path = str(project_root / 'models' / 'checkpoints' / 'best_model.pth')
    
    results = threshold_scan(
        model_path=model_path,
        min_threshold=args.min,
        max_threshold=args.max,
        step=args.step,
        test_periods=args.periods,
        num_bets=args.bets
    )
