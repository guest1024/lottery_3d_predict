#!/usr/bin/env python3
"""
每日投注建议生成工具

功能：
1. 分析最新期次的历史数据
2. 使用模型预测下一期的数字概率
3. 计算置信度评分和百分位排名
4. 基于Top5策略(前5%)决定是否建议投注
5. 如果建议投注，生成具体的投注组合
6. 将建议保存到数据库
"""

import os
import sys
import django
import argparse
import numpy as np
import torch
import itertools
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Django setup
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottery_web.settings')
django.setup()

from lottery.models import LotteryPeriod, Prediction

# Add src to path
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from models.lottery_model import LotteryModel


def calculate_confidence_score(digit_probs: np.ndarray) -> Dict[str, float]:
    """计算模型置信度评分"""
    sorted_probs = np.sort(digit_probs)[::-1]
    
    top5_concentration = np.sum(sorted_probs[:5])
    top3_avg = np.mean(sorted_probs[:3])
    others_avg = np.mean(sorted_probs[3:])
    top3_gap = top3_avg - others_avg if top3_avg > others_avg else 0
    
    epsilon = 1e-10
    entropy = -np.sum(digit_probs * np.log(digit_probs + epsilon))
    max_entropy = -np.log(0.1)
    entropy_score = 1 - (entropy / max_entropy)
    
    top1_prob = sorted_probs[0]
    
    composite_score = (
        top5_concentration * 20 +
        top3_gap * 200 +
        entropy_score * 20 +
        top1_prob * 100
    ) / 3
    
    return {
        'composite_score': composite_score,
        'top5_concentration': top5_concentration,
        'top3_gap': top3_gap,
        'entropy_score': entropy_score,
        'top1_prob': top1_prob,
    }


def calculate_historical_percentile(
    current_score: float,
    lookback_periods: int = 1000
) -> float:
    """
    计算当前置信度在历史数据中的百分位排名
    
    Args:
        current_score: 当前置信度评分
        lookback_periods: 回看的历史期数
    
    Returns:
        百分位排名 (0-100)
    """
    # 加载历史数据并计算置信度
    model_path = os.path.join(project_root, 'models', 'best_model.pth')
    model = LotteryModel.load(model_path, device='cpu')
    model.eval()
    
    all_periods = list(LotteryPeriod.objects.all().order_by('period'))
    total = len(all_periods)
    
    if total < 30 + lookback_periods:
        lookback_periods = total - 30
    
    historical_scores = []
    
    for i in range(lookback_periods):
        idx = total - lookback_periods + i
        history = all_periods[idx-30:idx]
        
        # 准备序列
        sequence = []
        for p in history:
            sequence.append(p.numbers)
        seq_tensor = torch.LongTensor(sequence).unsqueeze(0)
        
        # 预测
        with torch.no_grad():
            outputs = model(seq_tensor)
            probs = outputs['digit_probs'].cpu().numpy()[0]
        
        # 计算置信度
        conf = calculate_confidence_score(probs)
        historical_scores.append(conf['composite_score'])
    
    # 计算百分位
    historical_array = np.array(historical_scores)
    percentile = (historical_array < current_score).sum() / len(historical_array) * 100
    
    return percentile


def generate_betting_combinations(
    digit_probs: np.ndarray,
    num_bets: int = 100
) -> List[Dict]:
    """
    生成投注组合
    
    Returns:
        [
            {
                'numbers': (0, 1, 2),
                'type': 'group6',
                'bet_count': 10,
                'cost': 20,
                'expected_prize': 320
            },
            ...
        ]
    """
    # 选择Top10
    top_indices = np.argsort(digit_probs)[-10:][::-1]
    top_probs = digit_probs[top_indices]
    
    # 生成所有组合
    group6_combos = []
    for combo in itertools.combinations(range(10), 3):
        idx = list(combo)
        prob_score = np.prod([top_probs[i] for i in idx])
        actual_combo = tuple(sorted([top_indices[i] for i in idx]))
        group6_combos.append((actual_combo, prob_score, 'group6', 320))
    
    group3_combos = []
    for i in range(10):
        for j in range(10):
            if i != j:
                prob_score = (top_probs[i] ** 2) * top_probs[j]
                actual_combo = tuple(sorted([top_indices[i], top_indices[i], top_indices[j]]))
                group3_combos.append((actual_combo, prob_score, 'group3', 160))
    
    # 合并排序
    all_combos = group6_combos + group3_combos
    all_combos.sort(key=lambda x: x[1], reverse=True)
    
    # 分配注数
    decay_factor = 0.85
    weights = np.array([decay_factor ** i for i in range(len(all_combos))])
    weights = weights / weights.sum()
    bet_counts = np.round(weights * num_bets).astype(int)
    
    # 调整总和
    diff = num_bets - bet_counts.sum()
    if diff > 0:
        for i in range(diff):
            bet_counts[i] += 1
    elif diff < 0:
        for i in range(-diff):
            if bet_counts[-(i+1)] > 0:
                bet_counts[-(i+1)] -= 1
    
    # 构建结果
    combinations = []
    for i, (combo, score, combo_type, prize) in enumerate(all_combos):
        if bet_counts[i] > 0:
            combinations.append({
                'numbers': combo,
                'type': combo_type,
                'bet_count': int(bet_counts[i]),
                'cost': int(bet_counts[i] * 2),
                'expected_prize': prize,
                'probability_score': float(score)
            })
    
    return combinations


def generate_daily_recommendation(
    model_path: str = None,
    strategy: str = 'top5',
    window_size: int = 30,
    device: str = 'cpu',
    save_to_db: bool = True
) -> Dict:
    """
    生成每日投注建议
    
    Returns:
        {
            'date': datetime,
            'next_period': str,
            'confidence_score': float,
            'percentile_rank': float,
            'recommendation': 'bet' | 'no_bet',
            'reason': str,
            'combinations': [...] if bet else None,
            'total_cost': int,
            'top5_digits': [...]
        }
    """
    print("=" * 80)
    print("每日投注建议生成")
    print("=" * 80)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"策略: {strategy.upper()}")
    print()
    
    # 加载模型
    if model_path is None:
        model_path = os.path.join(project_root, 'models', 'best_model.pth')
    
    print(f"加载模型: {model_path}")
    model = LotteryModel.load(model_path, device=device)
    model.eval()
    
    # 获取最新数据
    print("获取最新历史数据...")
    all_periods = list(LotteryPeriod.objects.all().order_by('period'))
    
    if len(all_periods) < window_size:
        return {
            'error': f'数据不足，需要至少{window_size}期历史数据'
        }
    
    latest_periods = all_periods[-window_size:]
    latest_period = all_periods[-1]
    
    print(f"最新期号: {latest_period.period}")
    print(f"开奖日期: {latest_period.date}")
    print(f"历史窗口: {window_size}期")
    print()
    
    # 预测下一期
    print("预测下一期...")
    sequence = []
    for p in latest_periods:
        sequence.append(p.numbers)
    
    seq_tensor = torch.LongTensor(sequence).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(seq_tensor)
        digit_probs = outputs['digit_probs'].cpu().numpy()[0]
    
    # 计算置信度
    print("计算置信度...")
    confidence = calculate_confidence_score(digit_probs)
    
    print(f"  综合得分: {confidence['composite_score']:.2f}")
    print(f"  Top5集中度: {confidence['top5_concentration']:.3f}")
    print(f"  Top3差距: {confidence['top3_gap']:.3f}")
    print()
    
    # 计算百分位（基于历史1000期）
    print("计算历史百分位排名（这可能需要几分钟）...")
    percentile = calculate_historical_percentile(confidence['composite_score'], lookback_periods=1000)
    
    print(f"  百分位排名: {percentile:.1f}%")
    print()
    
    # 决定是否投注
    if strategy == 'top5':
        threshold = 95
        num_bets = 100
    elif strategy == 'top10':
        threshold = 90
        num_bets = 50 if percentile >= 95 else 100
    else:  # top20
        if percentile >= 95:
            num_bets = 100
        elif percentile >= 90:
            num_bets = 50
        else:
            num_bets = 25
        threshold = 80
    
    should_bet = percentile >= threshold
    
    # 生成建议
    top5_indices = np.argsort(digit_probs)[-5:][::-1]
    top5_digits = [int(i) for i in top5_indices]
    top5_probs = [float(digit_probs[i]) for i in top5_indices]
    
    # 生成下一期号（基于当前日期+1天）
    from datetime import timedelta
    next_date = latest_period.date + timedelta(days=1)
    next_period_str = next_date.strftime('%Y-%m-%d')
    
    recommendation = {
        'date': datetime.now(),
        'current_period': latest_period.period,
        'next_period': next_period_str,
        'confidence_score': float(confidence['composite_score']),
        'percentile_rank': float(percentile),
        'recommendation': 'bet' if should_bet else 'no_bet',
        'top5_digits': top5_digits,
        'top5_probs': top5_probs,
        'strategy': strategy,
    }
    
    if should_bet:
        print("✅ 建议投注")
        print(f"  档次: {'极高' if percentile >= 95 else '高' if percentile >= 90 else '中'}")
        print(f"  建议注数: {num_bets}注")
        print(f"  预计成本: {num_bets * 2}元")
        print()
        
        # 生成投注组合
        print("生成投注组合...")
        combinations = generate_betting_combinations(digit_probs, num_bets)
        
        recommendation['combinations'] = combinations
        recommendation['total_cost'] = num_bets * 2
        recommendation['reason'] = f"置信度排名前{100-threshold}%，建议投注{num_bets}注"
        
        print(f"  共生成 {len(combinations)} 个组合")
        print(f"  总成本: {recommendation['total_cost']}元")
        print()
        
        print("Top 5 投注组合:")
        for i, combo in enumerate(combinations[:5], 1):
            print(f"  {i}. {combo['numbers']} ({combo['type']}) - {combo['bet_count']}注, "
                  f"成本{combo['cost']}元, 奖金{combo['expected_prize']}元")
    
    else:
        print("⚠️  不建议投注")
        print(f"  原因: 置信度排名 {percentile:.1f}%，未达到投注阈值({threshold}%)")
        print(f"  建议: 等待更高置信度的时机")
        print()
        
        recommendation['combinations'] = None
        recommendation['total_cost'] = 0
        recommendation['reason'] = f"置信度排名{percentile:.1f}%，未达到{strategy}策略阈值"
    
    print("Top 5 预测数字:")
    for i, (digit, prob) in enumerate(zip(top5_digits, top5_probs), 1):
        print(f"  {i}. 数字 {digit}: 概率 {prob:.3f}")
    print()
    
    # 保存到数据库
    if save_to_db:
        print("保存建议到数据库...")
        try:
            pred = Prediction.objects.create(
                period=latest_period,
                predicted_for_period=recommendation['next_period'],
                top5_digits=top5_digits,
                digit_probs=digit_probs.tolist(),
                confidence_score=recommendation['confidence_score'],
                attention_weights=None,
                # 新的投注建议字段
                recommendation=recommendation['recommendation'],
                percentile_rank=recommendation['percentile_rank'],
                strategy=strategy,
                betting_combinations=recommendation.get('combinations'),
                total_cost=recommendation.get('total_cost', 0),
                bet_count=num_bets if should_bet else 0,
                recommendation_reason=recommendation.get('reason', ''),
                # 兼容旧字段
                should_bet=should_bet,
                recommended_bets=recommendation.get('combinations'),
                bet_amount=recommendation.get('total_cost', 0),
            )
            print(f"  保存成功，ID: {pred.id}")
            recommendation['prediction_id'] = pred.id
        except Exception as e:
            print(f"  保存失败: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 80)
    
    return recommendation


def main():
    parser = argparse.ArgumentParser(description='每日投注建议生成工具')
    parser.add_argument('--model', type=str,
                       default=None,
                       help='模型路径（默认: models/best_model.pth）')
    parser.add_argument('--strategy', type=str, default='top5',
                       choices=['top5', 'top10', 'top20'],
                       help='投注策略: top5(前5%), top10(前10%), top20(前20%)')
    parser.add_argument('--window', type=int, default=30,
                       help='历史窗口大小')
    parser.add_argument('--device', type=str, default='cpu',
                       choices=['cpu', 'cuda'],
                       help='计算设备')
    parser.add_argument('--no-save', action='store_true',
                       help='不保存到数据库')
    
    args = parser.parse_args()
    
    # 生成建议
    recommendation = generate_daily_recommendation(
        model_path=args.model,
        strategy=args.strategy,
        window_size=args.window,
        device=args.device,
        save_to_db=not args.no_save
    )
    
    # 返回建议供其他程序使用
    return recommendation


if __name__ == '__main__':
    main()
