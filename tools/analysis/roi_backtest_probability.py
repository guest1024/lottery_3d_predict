"""
概率模型回测 - 使用新的概率分配策略
基于每个组合的理论概率进行权重分配
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

import json
import numpy as np
import torch
from collections import defaultdict
from itertools import combinations

from src.models.lottery_model import LotteryModel

# 3D彩票奖金设置
PRIZE_CONFIG = {
    'direct': 1040,      # 直选: 1040元
    'group3': 346,       # 组选3: 346元
    'group6': 173,       # 组选6: 173元
}

TICKET_PRICE = 2  # 每注2元


def calculate_combination_probability(combo: tuple, digit_probs: np.ndarray) -> float:
    """
    计算组合的理论中奖概率
    """
    unique_digits = set(combo)
    
    if len(unique_digits) == 3:
        # 组六: P = P(d1) * P(d2) * P(d3) * 6
        prob = digit_probs[combo[0]] * digit_probs[combo[1]] * digit_probs[combo[2]] * 6
    else:
        # 组三: P = P(d1)^2 * P(d2) * 3
        unique_list = list(unique_digits)
        if combo[0] == combo[1]:
            prob = digit_probs[combo[0]]**2 * digit_probs[combo[2]] * 3
        else:
            prob = digit_probs[combo[1]]**2 * digit_probs[combo[0]] * 3
    
    return float(prob)


def generate_probability_based_bets(digit_probs: np.ndarray, num_bets: int = 100):
    """
    基于概率生成投注计划 (复用views.py的逻辑)
    
    Args:
        digit_probs: 10个数字的预测概率
        num_bets: 总投注注数
        
    Returns:
        投注计划列表 [{'combo': (d1,d2,d3), 'bets': n, 'probability': p}, ...]
    """
    # 获取Top10数字
    top_indices = np.argsort(digit_probs)[::-1][:10]
    top10_digits = top_indices.tolist()
    
    # 生成所有候选组合
    candidates = []
    
    # 组六组合
    for combo in combinations(top10_digits, 3):
        combo_sorted = tuple(sorted(combo))
        prob = calculate_combination_probability(combo_sorted, digit_probs)
        candidates.append({
            'combo': combo_sorted,
            'type': 'group6',
            'probability': prob,
            'prize': PRIZE_CONFIG['group6']
        })
    
    # 组三组合
    for d1 in top10_digits:
        for d2 in top10_digits:
            if d1 != d2:
                combo_sorted = tuple(sorted([d1, d1, d2]))
                prob = calculate_combination_probability(combo_sorted, digit_probs)
                candidates.append({
                    'combo': combo_sorted,
                    'type': 'group3',
                    'probability': prob,
                    'prize': PRIZE_CONFIG['group3']
                })
    
    # 按概率排序
    candidates.sort(key=lambda x: x['probability'], reverse=True)
    
    # 选择Top候选
    top_n = min(max(int(num_bets * 0.25), 15), len(candidates))
    selected_candidates = candidates[:top_n]
    
    # 指数衰减权重分配
    weights = []
    decay_rate = 0.85
    for i in range(len(selected_candidates)):
        weight = decay_rate ** i
        weights.append(weight)
    
    weights = np.array(weights)
    weights = weights / np.sum(weights)
    
    # 分配注数
    theoretical_bets = []
    for weight in weights:
        bets = max(1, round(num_bets * weight))
        theoretical_bets.append(bets)
    
    # 调整总数
    total_theoretical = sum(theoretical_bets)
    if total_theoretical != num_bets:
        adjustment_factor = num_bets / total_theoretical
        theoretical_bets = [max(1, round(b * adjustment_factor)) for b in theoretical_bets]
        
        diff = num_bets - sum(theoretical_bets)
        idx = len(theoretical_bets) - 1
        while diff != 0 and idx >= 0:
            if diff > 0 and theoretical_bets[idx] < num_bets:
                theoretical_bets[idx] += 1
                diff -= 1
            elif diff < 0 and theoretical_bets[idx] > 1:
                theoretical_bets[idx] -= 1
                diff += 1
            idx -= 1
    
    # 创建最终投注计划
    betting_plan = []
    for i, candidate in enumerate(selected_candidates):
        bets = theoretical_bets[i]
        if bets > 0:
            betting_plan.append({
                'combo': candidate['combo'],
                'type': candidate['type'],
                'probability': candidate['probability'],
                'bets': bets,
                'prize': candidate['prize']
            })
    
    return betting_plan


def check_win(bet_combo: tuple, actual_numbers: np.ndarray):
    """
    检查组合是否中奖
    """
    actual_sorted = tuple(sorted(actual_numbers))
    
    # 只检查组选(我们的投注都是组选)
    if bet_combo == actual_sorted:
        unique_in_actual = len(set(actual_numbers))
        if unique_in_actual == 2:
            return 'group3', PRIZE_CONFIG['group3']
        elif unique_in_actual == 3:
            return 'group6', PRIZE_CONFIG['group6']
    
    return 'miss', 0


def calculate_opportunity_score_simple(digit_probs: np.ndarray) -> float:
    """
    简化的机会评分 (只用模型特征)
    返回0-100分
    """
    sorted_probs = np.sort(digit_probs)[::-1]
    
    # 归一化特征到0-1
    features = {
        'top1_prob': min(1.0, sorted_probs[0] / 0.3),  # 假设最大概率约0.3
        'top3_mean': min(1.0, np.mean(sorted_probs[:3]) / 0.25),
        'gap_1_2': min(1.0, (sorted_probs[0] - sorted_probs[1]) / 0.1),
        'prob_std': min(1.0, np.std(digit_probs) / 0.15),
        'top3_concentration': min(1.0, np.sum(sorted_probs[:3]) / 0.6)
    }
    
    # 加权求和(总权重100)
    score = (
        features['top1_prob'] * 30 +
        features['top3_mean'] * 25 +
        features['gap_1_2'] * 20 +
        features['prob_std'] * 15 +
        features['top3_concentration'] * 10
    )
    
    return float(np.clip(score, 0, 100))


def backtest_with_probability(model_path, data_path, num_bets=100, test_periods=200, 
                              threshold=58.45, device='cpu'):
    """
    使用概率模型进行回测
    
    Args:
        model_path: 模型路径
        data_path: 数据路径
        num_bets: 每期投注数
        test_periods: 回测期数
        threshold: 投注阈值
        device: 设备
    """
    print("=" * 80)
    print("概率模型回测系统")
    print("=" * 80)
    
    # 加载模型
    print("\n[1] 加载模型...")
    model = LotteryModel.load(model_path, device=device)
    model.eval()
    print(f"✓ 模型加载成功")
    
    # 加载数据
    print("\n[2] 加载数据...")
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_data = data['data']
    sequences = np.array([item['numbers'] for item in all_data])
    print(f"✓ 加载 {len(sequences)} 期数据")
    
    # 回测参数
    window_size = 30
    total_available = len(sequences) - window_size
    test_periods = min(test_periods, total_available)
    start_idx = len(sequences) - test_periods - window_size
    
    print(f"\n[3] 回测参数:")
    print(f"  投注策略: 概率权重分配")
    print(f"  每期投注: {num_bets} 注 ({num_bets * TICKET_PRICE} 元)")
    print(f"  投注阈值: {threshold} 分")
    print(f"  回测期数: {test_periods}")
    print(f"  起始期号: {all_data[start_idx + window_size]['period']}")
    
    # 回测统计
    results = []
    total_cost = 0
    total_prize = 0
    total_bet_periods = 0
    win_periods = 0
    
    win_by_type = defaultdict(int)
    score_distribution = []
    
    print(f"\n[4] 执行回测...")
    print("-" * 80)
    
    for i in range(test_periods):
        idx = start_idx + i
        
        # 获取历史和实际开奖
        history = sequences[idx:idx + window_size]
        actual = sequences[idx + window_size]
        period_info = all_data[idx + window_size]
        period_id = period_info['period']
        
        # 模型预测
        input_seq = torch.LongTensor(history).unsqueeze(0).to(device)
        with torch.no_grad():
            predictions = model.predict(input_seq)
            digit_probs = predictions['digit_probs'][0]
        
        # 计算评分
        score = calculate_opportunity_score_simple(digit_probs)
        score_distribution.append(score)
        should_bet = score >= threshold
        
        if not should_bet:
            results.append({
                'period': period_id,
                'score': score,
                'bet': False,
                'cost': 0,
                'prize': 0,
                'profit': 0
            })
            continue
        
        # 生成投注计划
        betting_plan = generate_probability_based_bets(digit_probs, num_bets)
        
        # 计算成本
        period_cost = sum(b['bets'] for b in betting_plan) * TICKET_PRICE
        total_cost += period_cost
        total_bet_periods += 1
        
        # 检查中奖
        period_prize = 0
        period_wins = []
        
        for plan in betting_plan:
            combo = plan['combo']
            bets = plan['bets']
            
            win_type, single_prize = check_win(combo, actual)
            if single_prize > 0:
                total_win = single_prize * bets
                period_prize += total_win
                period_wins.append({
                    'combo': combo,
                    'type': win_type,
                    'bets': bets,
                    'prize': total_win
                })
                win_by_type[win_type] += bets
        
        total_prize += period_prize
        if period_prize > 0:
            win_periods += 1
        
        profit = period_prize - period_cost
        
        results.append({
            'period': period_id,
            'score': score,
            'bet': True,
            'cost': period_cost,
            'prize': period_prize,
            'profit': profit,
            'wins': period_wins,
            'actual': list(actual)
        })
        
        # 显示关键结果
        if period_prize > 0:
            print(f"  ✓ {period_id}: 评分{score:.2f} 投注{period_cost}元 "
                  f"中奖{period_prize}元 利润{profit:+d}元")
    
    # 汇总统计
    print("\n" + "=" * 80)
    print("回测结果汇总")
    print("=" * 80)
    
    roi = ((total_prize - total_cost) / total_cost * 100) if total_cost > 0 else 0
    win_rate = (win_periods / total_bet_periods * 100) if total_bet_periods > 0 else 0
    avg_score = np.mean(score_distribution)
    
    print(f"\n📊 整体统计:")
    print(f"  回测期数: {test_periods}")
    print(f"  投注期数: {total_bet_periods} ({total_bet_periods/test_periods*100:.1f}%)")
    print(f"  观望期数: {test_periods - total_bet_periods}")
    print(f"  平均评分: {avg_score:.2f} 分")
    
    print(f"\n💰 收益统计:")
    print(f"  总成本: {total_cost} 元")
    print(f"  总收益: {total_prize} 元")
    print(f"  净利润: {total_prize - total_cost:+d} 元")
    print(f"  ROI: {roi:+.2f}%")
    
    print(f"\n🎯 中奖统计:")
    print(f"  中奖期数: {win_periods} / {total_bet_periods}")
    print(f"  胜率: {win_rate:.2f}%")
    
    if win_by_type:
        print(f"\n  中奖明细:")
        for win_type, count in win_by_type.items():
            prize = PRIZE_CONFIG[win_type]
            print(f"    {win_type}: {count} 注 × {prize}元 = {count * prize}元")
    
    # 按评分分层统计
    print(f"\n📈 按评分分层:")
    score_ranges = [
        (60, float('inf'), "≥60分 (超高)"),
        (58.45, 60, "58.45-60 (高)"),
        (55, 58.45, "55-58.45 (中高)"),
        (50, 55, "50-55 (中)"),
        (0, 50, "<50 (低)")
    ]
    
    for min_score, max_score, label in score_ranges:
        range_results = [r for r in results if r['bet'] and min_score <= r['score'] < max_score]
        if range_results:
            range_cost = sum(r['cost'] for r in range_results)
            range_prize = sum(r['prize'] for r in range_results)
            range_roi = ((range_prize - range_cost) / range_cost * 100) if range_cost > 0 else 0
            range_win = sum(1 for r in range_results if r['prize'] > 0)
            range_rate = (range_win / len(range_results) * 100) if range_results else 0
            
            print(f"  {label}: {len(range_results)}期, ROI {range_roi:+.2f}%, 胜率 {range_rate:.1f}%")
    
    print("=" * 80)
    
    return {
        'results': results,
        'total_cost': total_cost,
        'total_prize': total_prize,
        'roi': roi,
        'win_rate': win_rate,
        'total_bet_periods': total_bet_periods
    }


if __name__ == '__main__':
    model_path = project_root / 'models' / 'checkpoints' / 'best_model.pth'
    # 使用最新的完整数据文件
    data_path = project_root / 'data' / 'lottery_3d_real_20260205_155413.json'
    
    # 运行回测
    results = backtest_with_probability(
        model_path=str(model_path),
        data_path=str(data_path),
        num_bets=100,
        test_periods=200,
        threshold=58.45,
        device='cpu'
    )
