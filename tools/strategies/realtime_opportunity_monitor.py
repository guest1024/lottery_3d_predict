"""
实时机会监控系统
================

功能：
1. 实时计算最新一期的机会评分
2. 判断是否达到投注阈值
3. 如果达到阈值，生成投注建议
4. 输出详细的特征分析和投注计划
"""

import json
import numpy as np
import torch
from pathlib import Path
from collections import Counter
from typing import List, Dict
import sys
from datetime import datetime

sys.path.insert(0, '/c1/program/lottery_3d_predict')
from src.models.lottery_model import LotteryModel

PRIZE_CONFIG = {
    'direct': 1040,
    'group3': 346,
    'group6': 173,
}
TICKET_PRICE = 2

# 评分阈值（基于历史回测）
SCORE_THRESHOLDS = {
    'top1': 58.45,   # Top1% - ROI 405%, 胜率67%
    'top5': 57.17,   # Top5% - ROI -57%, 胜率20%
    'top10': 56.90,  # Top10% - ROI -13%, 胜率17%
}

# 推荐策略
RECOMMENDED_STRATEGY = 'top1'
RECOMMENDED_THRESHOLD = SCORE_THRESHOLDS['top1']


class OpportunityScorer:
    """机会评分系统"""
    
    FEATURE_WEIGHTS = {
        'top1_prob': 15,
        'top3_mean_prob': 15,
        'gap_1_2': 10,
        'prob_std': 10,
        'top3_concentration': 10,
        'digit_freq_std': 8,
        'shape_entropy': 7,
        'sum_std': 5,
        'recent_5_unique_count': 5,
        'max_consecutive_shape': 5,
    }
    
    @staticmethod
    def calculate_score_with_details(digit_probs: np.ndarray, history: np.ndarray) -> Dict:
        """计算评分并返回详细特征"""
        # 模型特征
        sorted_indices = np.argsort(digit_probs)[::-1]
        sorted_probs = digit_probs[sorted_indices]
        
        top1_prob = sorted_probs[0]
        top3_mean_prob = np.mean(sorted_probs[:3])
        gap_1_2 = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else 0
        prob_std = np.std(digit_probs)
        top3_concentration = np.sum(sorted_probs[:3]) / (np.sum(digit_probs) + 1e-10)
        
        # 序列特征
        flat_history = history.flatten()
        digit_counts = Counter(flat_history)
        digit_freq_std = np.std(list(digit_counts.values()))
        
        shape_counts = Counter()
        for numbers in history:
            shape = OpportunityScorer._get_shape(numbers)
            shape_counts[shape] += 1
        shape_entropy = OpportunityScorer._calculate_entropy(shape_counts)
        
        sum_values = [np.sum(numbers) for numbers in history]
        sum_std = np.std(sum_values)
        
        recent_5 = history[-5:]
        recent_5_unique_count = len(set(map(tuple, recent_5)))
        
        shapes = [OpportunityScorer._get_shape(numbers) for numbers in history]
        max_consecutive_shape = OpportunityScorer._max_consecutive(shapes)
        
        # 原始特征值
        raw_features = {
            'top1_prob': top1_prob,
            'top3_mean_prob': top3_mean_prob,
            'gap_1_2': gap_1_2,
            'prob_std': prob_std,
            'top3_concentration': top3_concentration,
            'digit_freq_std': digit_freq_std,
            'shape_entropy': shape_entropy,
            'sum_std': sum_std,
            'recent_5_unique_count': recent_5_unique_count,
            'max_consecutive_shape': max_consecutive_shape,
        }
        
        # 归一化特征
        normalized_features = {
            'top1_prob': min(1.0, top1_prob / 0.3),
            'top3_mean_prob': min(1.0, top3_mean_prob / 0.3),
            'gap_1_2': min(1.0, gap_1_2 / 0.1),
            'prob_std': min(1.0, prob_std / 0.3),
            'top3_concentration': min(1.0, top3_concentration),
            'digit_freq_std': min(1.0, digit_freq_std / 5.0),
            'shape_entropy': min(1.0, shape_entropy),
            'sum_std': min(1.0, sum_std / 5.0),
            'recent_5_unique_count': min(1.0, recent_5_unique_count / 5.0),
            'max_consecutive_shape': min(1.0, max_consecutive_shape / 10.0),
        }
        
        # 计算各特征贡献分数
        feature_contributions = {
            k: normalized_features[k] * OpportunityScorer.FEATURE_WEIGHTS[k]
            for k in normalized_features.keys()
        }
        
        # 总分
        total_score = sum(feature_contributions.values())
        
        return {
            'total_score': float(total_score),
            'raw_features': raw_features,
            'normalized_features': normalized_features,
            'feature_contributions': feature_contributions,
            'feature_weights': OpportunityScorer.FEATURE_WEIGHTS,
        }
    
    @staticmethod
    def _get_shape(numbers: np.ndarray) -> str:
        counter = Counter(numbers)
        if len(counter) == 1:
            return 'leopard'
        elif len(counter) == 2:
            return 'group3'
        else:
            return 'group6'
    
    @staticmethod
    def _calculate_entropy(counter: Counter) -> float:
        total = sum(counter.values())
        if total == 0:
            return 0
        probs = [count / total for count in counter.values()]
        return -sum(p * np.log(p + 1e-10) for p in probs)
    
    @staticmethod
    def _max_consecutive(sequence: List) -> int:
        if not sequence:
            return 0
        max_count = 1
        current_count = 1
        for i in range(1, len(sequence)):
            if sequence[i] == sequence[i-1]:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 1
        return max_count


def generate_bets(top_digits: List[int], score: float, num_bets_base: int = 50) -> List[tuple]:
    """生成投注组合"""
    if score >= SCORE_THRESHOLDS['top1']:
        num_bets = int(num_bets_base * 1.5)  # 75注
    else:
        num_bets = num_bets_base
    
    bets = set()
    
    # 组六（70%）
    group6_count = int(num_bets * 0.7)
    attempts = 0
    while len([b for b in bets if len(set(b)) == 3]) < group6_count and attempts < group6_count * 3:
        combo = tuple(sorted(np.random.choice(top_digits, size=3, replace=False)))
        if len(set(combo)) == 3:
            bets.add(combo)
        attempts += 1
    
    # 组三（30%）
    group3_count = num_bets - len(bets)
    attempts = 0
    while len(bets) < num_bets and attempts < group3_count * 3:
        digit1 = np.random.choice(top_digits)
        digit2 = np.random.choice([d for d in top_digits if d != digit1])
        combo = tuple(sorted([digit1, digit1, digit2]))
        bets.add(combo)
        attempts += 1
    
    return list(bets)[:num_bets]


def monitor_current_opportunity():
    """监控当前机会"""
    print("="*80)
    print("🎯 实时机会监控系统")
    print("="*80)
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"推荐策略: Top1%极度保守策略")
    print(f"投注阈值: {RECOMMENDED_THRESHOLD:.2f}分")
    print("="*80)
    
    # 加载数据
    print("\n[1] 加载数据和模型...")
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_data = data['data']
    
    # 最新30期作为输入
    recent_30 = all_data[-30:]
    sequences = np.array([item['numbers'] for item in recent_30])
    
    # 上一期开奖结果
    last_period = all_data[-1]
    
    print(f"✓ 数据加载完成")
    print(f"  最新一期: {last_period['period']}")
    print(f"  开奖日期: {last_period['date']}")
    print(f"  开奖号码: {last_period['numbers']}")
    
    # 加载模型
    device = torch.device('cpu')
    model = LotteryModel.load('models/checkpoints/best_model.pth', device=device)
    print(f"✓ 模型加载完成")
    
    # 预测下一期
    print(f"\n[2] 预测下一期...")
    model.eval()
    with torch.no_grad():
        input_seq = torch.LongTensor(sequences).unsqueeze(0).to(device)
        predictions = model.predict(input_seq)
        digit_probs = predictions['digit_probs'][0]
    
    # 计算机会评分
    print(f"\n[3] 计算机会评分...")
    scorer = OpportunityScorer()
    score_details = scorer.calculate_score_with_details(digit_probs, sequences)
    
    total_score = score_details['total_score']
    
    print(f"\n{'='*80}")
    print(f"📊 机会评分: {total_score:.2f}分")
    print(f"{'='*80}")
    
    # 阈值对比
    print(f"\n阈值对比:")
    for strategy_name, threshold in SCORE_THRESHOLDS.items():
        status = "✅ 达到" if total_score >= threshold else "❌ 未达到"
        print(f"  {strategy_name.upper():<6} (阈值{threshold:.2f}): {status}")
    
    # 特征详情
    print(f"\n[4] 特征详情分析:")
    print(f"\n{'特征名称':<25} {'原始值':<12} {'归一化':<12} {'权重':<8} {'贡献分':<10}")
    print("-"*80)
    
    for feat_name in score_details['feature_contributions'].keys():
        raw_val = score_details['raw_features'][feat_name]
        norm_val = score_details['normalized_features'][feat_name]
        weight = score_details['feature_weights'][feat_name]
        contrib = score_details['feature_contributions'][feat_name]
        
        print(f"{feat_name:<25} {raw_val:<12.4f} {norm_val:<12.4f} {weight:<8} {contrib:<10.2f}")
    
    print(f"\n总分: {total_score:.2f}")
    
    # Top数字
    top_indices = np.argsort(digit_probs)[::-1]
    top10_digits = top_indices[:10].tolist()
    top10_probs = digit_probs[top_indices[:10]]
    
    print(f"\n[5] Top10预测数字:")
    print(f"{'排名':<6} {'数字':<6} {'概率':<10}")
    print("-"*30)
    for i, (digit, prob) in enumerate(zip(top10_digits, top10_probs), 1):
        print(f"{i:<6} {digit:<6} {prob:<10.4f}")
    
    # 投注建议
    print(f"\n{'='*80}")
    print(f"🎰 投注建议")
    print(f"{'='*80}")
    
    if total_score >= RECOMMENDED_THRESHOLD:
        print(f"\n✅ 当前评分 {total_score:.2f} ≥ 推荐阈值 {RECOMMENDED_THRESHOLD:.2f}")
        print(f"✅ 建议进行投注！")
        
        # 生成投注组合
        bet_combos = generate_bets(top10_digits, total_score, num_bets_base=50)
        total_cost = len(bet_combos) * TICKET_PRICE
        
        print(f"\n投注计划:")
        print(f"  投注数量: {len(bet_combos)}注")
        print(f"  总成本: ¥{total_cost}")
        print(f"  基于历史回测:")
        print(f"    - 预期胜率: 66.67%")
        print(f"    - 预期ROI: 405.42%")
        print(f"    - 预期收益: ¥{total_cost * 4.05:.0f}")
        
        # 分类统计
        group6_bets = [b for b in bet_combos if len(set(b)) == 3]
        group3_bets = [b for b in bet_combos if len(set(b)) == 2]
        
        print(f"\n投注组合分类:")
        print(f"  组六: {len(group6_bets)}注 (每注中奖¥173)")
        print(f"  组三: {len(group3_bets)}注 (每注中奖¥346)")
        
        print(f"\n前30注推荐:")
        for i, combo in enumerate(bet_combos[:30], 1):
            combo_type = "组六" if len(set(combo)) == 3 else "组三"
            print(f"  {i:2d}. {combo[0]} {combo[1]} {combo[2]} ({combo_type})")
        
        if len(bet_combos) > 30:
            print(f"  ... (共{len(bet_combos)}注)")
        
        # 保存投注计划
        output = {
            'timestamp': datetime.now().isoformat(),
            'last_period': {
                'period': last_period['period'],
                'date': last_period['date'],
                'numbers': last_period['numbers'],
            },
            'opportunity_score': total_score,
            'threshold': RECOMMENDED_THRESHOLD,
            'recommendation': 'BET',
            'betting_plan': {
                'num_bets': len(bet_combos),
                'total_cost': total_cost,
                'combinations': [[int(x) for x in combo] for combo in bet_combos],
                'expected_win_rate': 0.6667,
                'expected_roi': 4.0542,
            },
            'score_details': {
                'total_score': total_score,
                'feature_contributions': {
                    k: float(v) for k, v in score_details['feature_contributions'].items()
                },
            },
            'top10_digits': [int(d) for d in top10_digits],
            'top10_probs': [float(p) for p in top10_probs],
        }
        
        output_path = Path('results/current_opportunity.json')
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 投注计划已保存到: {output_path}")
        
    else:
        print(f"\n❌ 当前评分 {total_score:.2f} < 推荐阈值 {RECOMMENDED_THRESHOLD:.2f}")
        print(f"❌ 不建议投注，继续观望")
        print(f"\n评分差距: {RECOMMENDED_THRESHOLD - total_score:.2f}分")
        print(f"\n建议: 等待评分≥{RECOMMENDED_THRESHOLD:.2f}时再入场")
        
        # 保存观望记录
        output = {
            'timestamp': datetime.now().isoformat(),
            'last_period': {
                'period': last_period['period'],
                'date': last_period['date'],
                'numbers': last_period['numbers'],
            },
            'opportunity_score': total_score,
            'threshold': RECOMMENDED_THRESHOLD,
            'recommendation': 'SKIP',
            'score_gap': RECOMMENDED_THRESHOLD - total_score,
            'top10_digits': [int(d) for d in top10_digits],
        }
        
        output_path = Path('results/current_opportunity.json')
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ 观望记录已保存到: {output_path}")
    
    print(f"\n{'='*80}")
    print(f"⚠️  投资风险提示")
    print(f"{'='*80}")
    print(f"• 彩票是概率游戏，历史业绩不代表未来表现")
    print(f"• 即使Top1%策略历史胜率67%，仍有33%概率亏损")
    print(f"• 建议单次投注金额≤总资金的5%")
    print(f"• 理性购彩，娱乐为主")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    monitor_current_opportunity()
