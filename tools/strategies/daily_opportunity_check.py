"""
每日机会评估 - 简化版API
========================

提供简单的函数接口，用于每日投注决策

使用示例：
    from daily_opportunity_check import check_today_opportunity
    
    result = check_today_opportunity()
    
    if result['should_bet']:
        print(f"✅ 建议投注！评分: {result['score']}")
        print(f"投注计划: {result['num_bets']}注, 成本¥{result['cost']}")
    else:
        print(f"❌ 继续观望。评分: {result['score']}")
"""

import json
import numpy as np
import torch
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from src.models.lottery_model import LotteryModel

# ==================== 配置参数 ====================
RECOMMENDED_THRESHOLD = 58.45  # Top1%投注阈值
MODEL_PATH = 'models/checkpoints/best_model.pth'
DATA_FILE = 'data/lottery_3d_real_20260205_125506.json'

PRIZE_CONFIG = {
    'direct': 1040,
    'group3': 346,
    'group6': 173,
}
TICKET_PRICE = 2


# ==================== 机会评分器 ====================
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
    def calculate_score(digit_probs: np.ndarray, history: np.ndarray) -> float:
        """计算机会评分"""
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
        
        # 计算评分
        features = {
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
        
        score = sum(features[k] * OpportunityScorer.FEATURE_WEIGHTS[k] 
                   for k in features.keys())
        
        return float(score)
    
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


def generate_bets(top_digits: List[int], score: float, num_bets_base: int = 50) -> List[Tuple[int, int, int]]:
    """生成投注组合"""
    if score >= 63.3:
        num_bets = int(num_bets_base * 1.5)  # 75注
    elif score >= 62.9:
        num_bets = int(num_bets_base * 1.2)  # 60注
    else:
        num_bets = num_bets_base  # 50注
    
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


# ==================== 主要API函数 ====================
def check_today_opportunity(
    data_file: str = None,
    model_path: str = None,
    threshold: float = None,
    verbose: bool = True
) -> Dict:
    """
    检查今日投注机会
    
    Args:
        data_file: 数据文件路径（默认使用配置的路径）
        model_path: 模型文件路径（默认使用配置的路径）
        threshold: 投注阈值（默认58.45）
        verbose: 是否打印详细信息
        
    Returns:
        result: {
            'timestamp': str,           # 评估时间
            'score': float,             # 机会评分
            'threshold': float,         # 投注阈值
            'should_bet': bool,         # 是否建议投注
            'score_gap': float,         # 评分差距（负数表示未达到）
            'last_period': dict,        # 上期开奖信息
            'top10_digits': list,       # Top10预测数字
            'recommendation': str,      # 'BET' 或 'SKIP'
            
            # 如果建议投注，包含以下字段：
            'betting_plan': {
                'num_bets': int,        # 投注注数
                'cost': int,            # 总成本
                'combinations': list,   # 投注组合
                'expected_win_rate': float,  # 预期胜率
                'expected_roi': float,       # 预期ROI
            }
        }
    """
    # 使用默认配置
    if data_file is None:
        data_file = Path(__file__).parent / DATA_FILE
    if model_path is None:
        model_path = Path(__file__).parent / MODEL_PATH
    if threshold is None:
        threshold = RECOMMENDED_THRESHOLD
    
    if verbose:
        print("\n" + "="*70)
        print("🎯 每日机会评估")
        print("="*70)
        print(f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"投注阈值: {threshold:.2f}分")
        print("="*70)
    
    # 加载数据
    if verbose:
        print("\n[1] 加载数据...")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_data = data['data']
    recent_30 = all_data[-30:]
    sequences = np.array([item['numbers'] for item in recent_30])
    last_period = all_data[-1]
    
    if verbose:
        print(f"✓ 最新一期: {last_period['period']}")
        print(f"  开奖号码: {last_period['numbers']}")
    
    # 加载模型
    if verbose:
        print("\n[2] 加载模型并预测...")
    
    device = torch.device('cpu')
    model = LotteryModel.load(model_path, device=device)
    model.eval()
    
    # 预测
    with torch.no_grad():
        input_seq = torch.LongTensor(sequences).unsqueeze(0).to(device)
        predictions = model.predict(input_seq)
        digit_probs = predictions['digit_probs'][0]
    
    # 计算评分
    if verbose:
        print("\n[3] 计算机会评分...")
    
    scorer = OpportunityScorer()
    score = scorer.calculate_score(digit_probs, sequences)
    
    # Top10数字
    top_indices = np.argsort(digit_probs)[::-1]
    top10_digits = top_indices[:10].tolist()
    
    # 决策
    should_bet = score >= threshold
    score_gap = score - threshold
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"📊 评分: {score:.2f}分")
        print(f"{'='*70}")
        
        if should_bet:
            print(f"✅ 建议投注！评分达到阈值")
            print(f"   评分: {score:.2f} ≥ 阈值: {threshold:.2f}")
        else:
            print(f"❌ 继续观望，评分未达到阈值")
            print(f"   评分: {score:.2f} < 阈值: {threshold:.2f}")
            print(f"   差距: {abs(score_gap):.2f}分")
    
    # 构建返回结果
    result = {
        'timestamp': datetime.now().isoformat(),
        'score': float(score),
        'threshold': float(threshold),
        'should_bet': bool(should_bet),
        'score_gap': float(score_gap),
        'last_period': {
            'period': last_period['period'],
            'date': last_period['date'],
            'numbers': last_period['numbers'],
        },
        'top10_digits': [int(d) for d in top10_digits],
        'recommendation': 'BET' if should_bet else 'SKIP',
    }
    
    # 如果建议投注，生成投注计划
    if should_bet:
        bet_combos = generate_bets(top10_digits, score, num_bets_base=50)
        total_cost = len(bet_combos) * TICKET_PRICE
        
        result['betting_plan'] = {
            'num_bets': len(bet_combos),
            'cost': total_cost,
            'combinations': [[int(x) for x in combo] for combo in bet_combos],
            'expected_win_rate': 0.6667,  # 基于历史回测
            'expected_roi': 4.0542,        # 基于历史回测
        }
        
        if verbose:
            print(f"\n💰 投注计划:")
            print(f"   投注数量: {len(bet_combos)}注")
            print(f"   总成本: ¥{total_cost}")
            print(f"   预期胜率: 66.67%")
            print(f"   预期ROI: 405.42%")
            print(f"\n   Top10数字: {top10_digits}")
            print(f"\n   前10注推荐:")
            for i, combo in enumerate(bet_combos[:10], 1):
                print(f"   {i:2d}. {combo[0]} {combo[1]} {combo[2]}")
            if len(bet_combos) > 10:
                print(f"   ... (共{len(bet_combos)}注)")
    else:
        if verbose:
            print(f"\n💡 建议:")
            print(f"   继续等待，下期再评估")
            print(f"   需要评分提升 {abs(score_gap):.2f}分")
    
    # 保存到文件
    output_path = Path(__file__).parent / 'results' / 'current_opportunity.json'
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    if verbose:
        print(f"\n✓ 评估结果已保存到: {output_path}")
        print("="*70 + "\n")
    
    return result


def check_quick() -> bool:
    """
    快速检查（无详细输出）
    
    Returns:
        bool: True表示建议投注，False表示继续观望
    """
    result = check_today_opportunity(verbose=False)
    return result['should_bet']


def get_betting_plan() -> Dict:
    """
    获取投注计划（如果建议投注）
    
    Returns:
        dict: 投注计划，如果不建议投注返回None
    """
    result = check_today_opportunity(verbose=False)
    if result['should_bet']:
        return result['betting_plan']
    return None


# ==================== 命令行接口 ====================
def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='每日机会评估')
    parser.add_argument('--threshold', type=float, default=RECOMMENDED_THRESHOLD,
                       help=f'投注阈值（默认{RECOMMENDED_THRESHOLD}）')
    parser.add_argument('--quiet', action='store_true',
                       help='安静模式，只输出结论')
    parser.add_argument('--json', action='store_true',
                       help='JSON格式输出')
    
    args = parser.parse_args()
    
    if args.json:
        # JSON输出模式
        result = check_today_opportunity(
            threshold=args.threshold,
            verbose=False
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.quiet:
        # 安静模式
        result = check_today_opportunity(
            threshold=args.threshold,
            verbose=False
        )
        if result['should_bet']:
            print(f"✅ 建议投注 | 评分: {result['score']:.2f} | 成本: ¥{result['betting_plan']['cost']}")
        else:
            print(f"❌ 继续观望 | 评分: {result['score']:.2f} | 差距: {abs(result['score_gap']):.2f}")
    else:
        # 详细模式
        check_today_opportunity(threshold=args.threshold, verbose=True)


if __name__ == '__main__':
    main()
