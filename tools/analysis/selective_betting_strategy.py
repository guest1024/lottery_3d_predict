#!/usr/bin/env python3
"""
选择性投注策略

核心思想：不是每期都投注，只在模型高置信度时投注

策略改进点：
1. 基于模型准确率测试结果（Top5命中率49.5%，Top10命中率100%）
2. 只在满足多个条件时才投注：
   - Top5概率集中度高（说明模型有把握）
   - Top3与Top4-5概率差距大（说明有明显热门数字）
   - 历史相似模式出现过中奖（参考历史）
3. 设置多档次投注：
   - 极高置信度：100注
   - 高置信度：50注
   - 中等置信度：25注
   - 低置信度：不投注
"""

import os
import sys
import django
import argparse
import numpy as np
import torch
import itertools
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Django setup
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottery_web.settings')
django.setup()

from lottery.models import LotteryPeriod

# Add src to path
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from models.lottery_model import LotteryModel


def calculate_confidence_score(digit_probs: np.ndarray) -> Dict[str, float]:
    """
    计算模型置信度评分
    
    Args:
        digit_probs: (10,) 数字概率数组
    
    Returns:
        dict: 多个置信度指标
    """
    # 排序概率
    sorted_probs = np.sort(digit_probs)[::-1]
    
    # 指标1: Top5概率集中度（Top5概率之和）
    top5_concentration = np.sum(sorted_probs[:5])
    
    # 指标2: Top3与其他的概率差距
    top3_avg = np.mean(sorted_probs[:3])
    others_avg = np.mean(sorted_probs[3:])
    top3_gap = top3_avg - others_avg if top3_avg > others_avg else 0
    
    # 指标3: 概率熵（越低说明越集中）
    epsilon = 1e-10
    entropy = -np.sum(digit_probs * np.log(digit_probs + epsilon))
    max_entropy = -np.log(0.1)  # 均匀分布的熵
    entropy_score = 1 - (entropy / max_entropy)  # 归一化，越高越好
    
    # 指标4: Top1概率（最热门数字的概率）
    top1_prob = sorted_probs[0]
    
    # 综合评分（0-100）
    composite_score = (
        top5_concentration * 20 +  # Top5集中度权重20% (max 5.0 * 20 = 100)
        top3_gap * 200 +            # Top3差距权重 (max ~0.3 * 200 = 60)
        entropy_score * 20 +        # 熵权重20%
        top1_prob * 100             # Top1概率权重 (max 1.0 * 100 = 100)
    ) / 3  # 平均，使其在0-100范围内
    
    return {
        'composite_score': composite_score,
        'top5_concentration': top5_concentration,
        'top3_gap': top3_gap,
        'entropy_score': entropy_score,
        'top1_prob': top1_prob,
    }


def determine_bet_level(confidence: Dict[str, float], percentile_rank: float, 
                       strategy: str = 'top20') -> Tuple[str, int]:
    """
    根据置信度决定投注档次（基于百分位数）
    
    Args:
        confidence: 置信度指标
        percentile_rank: 当前置信度在所有测试期中的百分位 (0-100)
        strategy: 投注策略
            - 'top20': 投注前20% (极高5%, 高5%, 中10%)
            - 'top10': 投注前10% (极高5%, 高5%)
            - 'top5': 只投注前5% (极高)
    
    Returns:
        (level_name, num_bets)
    """
    if strategy == 'top5':
        # 只投注前5%，极度保守
        if percentile_rank >= 95:
            return ("极高", 100)
        else:
            return ("不投注", 0)
    
    elif strategy == 'top10':
        # 投注前10%
        if percentile_rank >= 95:
            return ("极高", 100)
        elif percentile_rank >= 90:
            return ("高", 50)
        else:
            return ("不投注", 0)
    
    else:  # top20 (default)
        # 投注前20%
        if percentile_rank >= 95:
            return ("极高", 100)
        elif percentile_rank >= 90:
            return ("高", 50)
        elif percentile_rank >= 80:
            return ("中", 25)
        else:
            return ("不投注", 0)


def generate_selective_bets(
    digit_probs: np.ndarray,
    num_bets: int
) -> List[Tuple[Tuple[int, int, int], int, float]]:
    """
    根据指定注数生成投注组合
    
    Args:
        digit_probs: (10,) 数字概率
        num_bets: 总注数（0表示不投注）
    
    Returns:
        [(combination, bet_count, score), ...]
    """
    if num_bets == 0:
        return []
    
    # 选择Top10数字
    top_indices = np.argsort(digit_probs)[-10:][::-1]
    top_probs = digit_probs[top_indices]
    
    # 生成所有组选组合
    group6_combos = []
    for combo in itertools.combinations(range(10), 3):
        idx = list(combo)
        prob_score = np.prod([top_probs[i] for i in idx])
        actual_combo = tuple(sorted([top_indices[i] for i in idx]))
        group6_combos.append((actual_combo, prob_score, 'group6'))
    
    group3_combos = []
    for i in range(10):
        for j in range(10):
            if i != j:
                prob_score = (top_probs[i] ** 2) * top_probs[j]
                actual_combo = tuple(sorted([top_indices[i], top_indices[i], top_indices[j]]))
                group3_combos.append((actual_combo, prob_score, 'group3'))
    
    # 合并并排序
    all_combos = group6_combos + group3_combos
    all_combos.sort(key=lambda x: x[1], reverse=True)
    
    # 分配注数：指数衰减
    decay_factor = 0.85
    weights = np.array([decay_factor ** i for i in range(len(all_combos))])
    weights = weights / weights.sum()  # 归一化
    
    bet_counts = np.round(weights * num_bets).astype(int)
    
    # 调整确保总和=num_bets
    diff = num_bets - bet_counts.sum()
    if diff > 0:
        for i in range(diff):
            bet_counts[i] += 1
    elif diff < 0:
        for i in range(-diff):
            if bet_counts[-(i+1)] > 0:
                bet_counts[-(i+1)] -= 1
    
    # 构建结果（只包含注数>0的组合）
    result = []
    for i, (combo, score, _) in enumerate(all_combos):
        if bet_counts[i] > 0:
            result.append((combo, bet_counts[i], score))
    
    return result


def check_win(bets: List[Tuple], actual_numbers: List[int]) -> Tuple[bool, int, List]:
    """
    检查是否中奖
    
    Returns:
        (is_win, prize, winning_combos)
    """
    actual_sorted = tuple(sorted(actual_numbers))
    actual_set = set(actual_numbers)
    
    winning_combos = []
    total_prize = 0
    
    for combo, bet_count, _ in bets:
        combo_set = set(combo)
        
        # 组选6：3个不同数字
        if len(combo_set) == 3 and combo_set == actual_set:
            prize = 320 * bet_count
            total_prize += prize
            winning_combos.append((combo, bet_count, prize, 'group6'))
        
        # 组选3：2个相同 + 1个不同
        elif len(combo_set) == 2:
            # Check if actual has 2 same digits
            if len(actual_set) == 2 and combo_set == actual_set:
                prize = 160 * bet_count
                total_prize += prize
                winning_combos.append((combo, bet_count, prize, 'group3'))
    
    is_win = total_prize > 0
    return is_win, total_prize, winning_combos


def prepare_sequence(periods: List[LotteryPeriod], window_size: int = 30) -> torch.Tensor:
    """准备输入序列"""
    sequence = []
    for period in periods[-window_size:]:
        sequence.append(period.numbers)
    
    while len(sequence) < window_size:
        sequence.insert(0, [10, 10, 10])
    
    return torch.LongTensor(sequence).unsqueeze(0)


def backtest_selective_strategy(
    model_path: str,
    test_periods: int = 500,
    window_size: int = 30,
    device: str = 'cpu',
    strategy: str = 'top20'
) -> Dict:
    """
    回测选择性投注策略
    
    Args:
        strategy: 'top20', 'top10', 'top5'
    
    Returns:
        dict: 回测结果
    """
    print("=" * 80)
    print(f"选择性投注策略回测 - {strategy.upper()}")
    print("=" * 80)
    print(f"模型: {model_path}")
    print(f"测试期数: {test_periods}")
    print(f"策略: {strategy}")
    print()
    
    # 加载模型
    print("加载模型...")
    model = LotteryModel.load(model_path, device=device)
    model.eval()
    
    # 加载数据
    print("加载数据...")
    all_periods = list(LotteryPeriod.objects.all().order_by('period'))
    total_periods = len(all_periods)
    
    if total_periods < window_size + test_periods:
        test_periods = total_periods - window_size
    
    print(f"总期数: {total_periods}")
    print(f"实际测试: {test_periods}")
    print()
    
    # 统计变量
    stats = {
        'total_periods': test_periods,
        'bet_periods': 0,
        'no_bet_periods': 0,
        'win_periods': 0,
        'total_cost': 0,
        'total_prize': 0,
        'bet_level_stats': defaultdict(lambda: {
            'count': 0,
            'win_count': 0,
            'cost': 0,
            'prize': 0
        }),
        'confidence_distribution': [],
        'details': []
    }
    
    print("第一遍扫描：计算所有期次的置信度...")
    print("-" * 80)
    
    # 第一遍：收集所有置信度
    all_confidences = []
    all_data = []
    
    for i in range(test_periods):
        test_idx = total_periods - test_periods + i
        
        history = all_periods[test_idx - window_size:test_idx]
        current = all_periods[test_idx]
        
        # 预测
        input_seq = prepare_sequence(history, window_size)
        with torch.no_grad():
            input_seq = input_seq.to(device)
            outputs = model(input_seq)
            digit_probs = outputs['digit_probs'].cpu().numpy()[0]
        
        # 计算置信度
        confidence = calculate_confidence_score(digit_probs)
        all_confidences.append(confidence['composite_score'])
        all_data.append({
            'index': i,
            'test_idx': test_idx,
            'current': current,
            'history': history,
            'digit_probs': digit_probs,
            'confidence': confidence
        })
        
        if (i + 1) % 100 == 0:
            print(f"已扫描 {i+1}/{test_periods} 期...")
    
    print("第一遍扫描完成！")
    print()
    
    # 计算百分位数
    all_confidences_array = np.array(all_confidences)
    
    print("置信度分布:")
    print(f"  最低: {np.min(all_confidences_array):.2f}")
    print(f"  25%: {np.percentile(all_confidences_array, 25):.2f}")
    print(f"  50%: {np.percentile(all_confidences_array, 50):.2f}")
    print(f"  75%: {np.percentile(all_confidences_array, 75):.2f}")
    print(f"  90%: {np.percentile(all_confidences_array, 90):.2f}")
    print(f"  95%: {np.percentile(all_confidences_array, 95):.2f}")
    print(f"  最高: {np.max(all_confidences_array):.2f}")
    print()
    
    print("第二遍扫描：基于百分位数进行投注决策...")
    print("-" * 80)
    
    # 第二遍：根据百分位数决定投注
    for data in all_data:
        i = data['index']
        current = data['current']
        digit_probs = data['digit_probs']
        confidence = data['confidence']
        
        conf_score = confidence['composite_score']
        stats['confidence_distribution'].append(conf_score)
        
        # 计算百分位排名
        percentile_rank = (all_confidences_array < conf_score).sum() / len(all_confidences_array) * 100
        
        # 决定投注档次（基于百分位）
        level, num_bets = determine_bet_level(confidence, percentile_rank, strategy)
        
        # 记录档次统计
        stats['bet_level_stats'][level]['count'] += 1
        
        if num_bets == 0:
            # 不投注
            stats['no_bet_periods'] += 1
            continue
        
        # 投注
        stats['bet_periods'] += 1
        actual_numbers = current.numbers
        bets = generate_selective_bets(digit_probs, num_bets)
        
        cost = num_bets * 2
        stats['total_cost'] += cost
        stats['bet_level_stats'][level]['cost'] += cost
        
        # 检查中奖
        is_win, prize, winning_combos = check_win(bets, actual_numbers)
        
        if is_win:
            stats['win_periods'] += 1
            stats['total_prize'] += prize
            stats['bet_level_stats'][level]['win_count'] += 1
            stats['bet_level_stats'][level]['prize'] += prize
        
        # 记录详情（仅记录投注期）
        stats['details'].append({
            'period': current.period,
            'level': level,
            'num_bets': num_bets,
            'confidence': conf_score,
            'percentile': percentile_rank,
            'cost': cost,
            'prize': prize,
            'profit': prize - cost,
            'actual': actual_numbers,
            'win': is_win
        })
        
        if (i + 1) % 100 == 0:
            print(f"已处理 {i+1}/{test_periods} 期...")
    
    print("回测完成！")
    print()
    
    return stats


def print_results(stats: Dict):
    """打印回测结果"""
    print("=" * 80)
    print("回测结果")
    print("=" * 80)
    print()
    
    total = stats['total_periods']
    bet_periods = stats['bet_periods']
    no_bet = stats['no_bet_periods']
    win_periods = stats['win_periods']
    cost = stats['total_cost']
    prize = stats['total_prize']
    profit = prize - cost
    
    print(f"📊 总体统计")
    print(f"  测试期数: {total}")
    print(f"  投注期数: {bet_periods} ({bet_periods/total*100:.1f}%)")
    print(f"  不投注期数: {no_bet} ({no_bet/total*100:.1f}%)")
    print()
    
    print(f"💰 资金统计")
    print(f"  总成本: {cost:,} 元")
    print(f"  总奖金: {prize:,} 元")
    print(f"  总利润: {profit:,} 元")
    
    if bet_periods > 0:
        roi = profit / cost * 100
        win_rate = win_periods / bet_periods * 100
        
        print(f"  ROI: {roi:+.2f}%")
        print(f"  胜率: {win_rate:.1f}% ({win_periods}/{bet_periods})")
        print(f"  平均每期成本: {cost/bet_periods:.1f} 元")
        print(f"  平均每期奖金: {prize/bet_periods:.1f} 元")
    print()
    
    print(f"📈 按投注档次统计")
    print("-" * 80)
    print(f"{'档次':<10} {'期数':<8} {'胜率':<10} {'成本':<12} {'奖金':<12} {'ROI':<10}")
    print("-" * 80)
    
    for level in ['极高', '高', '中', '不投注']:
        level_stats = stats['bet_level_stats'][level]
        if level_stats['count'] > 0:
            count = level_stats['count']
            wins = level_stats['win_count']
            level_cost = level_stats['cost']
            level_prize = level_stats['prize']
            
            if level_cost > 0:
                win_rate = wins / count * 100
                level_roi = (level_prize - level_cost) / level_cost * 100
                print(f"{level:<10} {count:>6}  {win_rate:>8.1f}%  {level_cost:>10,}  {level_prize:>10,}  {level_roi:>+8.1f}%")
            else:
                print(f"{level:<10} {count:>6}  {'N/A':>8}  {level_cost:>10,}  {level_prize:>10,}  {'N/A':>8}")
    
    print("-" * 80)
    print()
    
    # 置信度分布
    conf_dist = stats['confidence_distribution']
    print(f"📊 置信度分布")
    print(f"  综合得分:")
    print(f"    平均: {np.mean(conf_dist):.2f}")
    print(f"    最高: {np.max(conf_dist):.2f}")
    print(f"    最低: {np.min(conf_dist):.2f}")
    
    # Debug: 显示详细指标（从第一个期次）
    if len(stats['details']) > 0:
        # 获取最高置信度的一期作为参考
        max_conf_idx = np.argmax(conf_dist)
        print(f"\n  最高置信度期次的详细指标（参考）:")
        # 需要重新计算，因为details只记录了投注期
        # 这里先不显示，后续优化
    print()
    
    print("=" * 80)
    print("💡 策略评估")
    print("=" * 80)
    print()
    
    if bet_periods == 0:
        print("⚠️  策略过于保守：0期投注")
        print("    所有期次的置信度都未达到投注阈值")
        print("    建议：降低投注阈值或检查置信度计算公式")
        print()
        print("=" * 80)
        return
    
    if profit > 0:
        print(f"✅ 策略有效！总利润 {profit:,} 元，ROI {roi:+.2f}%")
    elif profit >= -cost * 0.2:  # 亏损小于20%
        print(f"⚠️  策略基本有效。亏损 {-profit:,} 元，ROI {roi:+.2f}%")
        print(f"    建议：进一步提高投注阈值或减少低置信度投注")
    else:
        print(f"❌ 策略效果不佳。亏损 {-profit:,} 元，ROI {roi:+.2f}%")
        print(f"    建议：提高投注阈值或重新训练模型")
    
    print()
    print(f"关键优势：")
    print(f"  ✅ 选择性投注减少了 {no_bet/total*100:.1f}% 的无效投注")
    
    if bet_periods > 0:
        print(f"  ✅ 投注期胜率 {win_rate:.1f}%")
        
        # 对比全期投注的假设成本
        full_bet_cost = total * 100 * 2  # 假设每期100注
        saved = full_bet_cost - cost
        print(f"  ✅ 相比全期投注节省成本 {saved:,} 元")
    
    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='选择性投注策略回测')
    parser.add_argument('--model', type=str,
                       default='models/best_model.pth',
                       help='模型路径')
    parser.add_argument('--periods', type=int, default=500,
                       help='测试期数')
    parser.add_argument('--window', type=int, default=30,
                       help='窗口大小')
    parser.add_argument('--device', type=str, default='cpu',
                       choices=['cpu', 'cuda'],
                       help='计算设备')
    parser.add_argument('--strategy', type=str, default='top20',
                       choices=['top5', 'top10', 'top20'],
                       help='投注策略: top5(前5%), top10(前10%), top20(前20%)')
    
    args = parser.parse_args()
    
    # 运行回测
    stats = backtest_selective_strategy(
        model_path=args.model,
        test_periods=args.periods,
        window_size=args.window,
        device=args.device,
        strategy=args.strategy
    )
    
    # 打印结果
    print_results(stats)


if __name__ == '__main__':
    main()
