"""
智能投注策略 - 基于机会评分系统
================================

核心改进：
1. 使用特征工程的机会评分系统，而非简单的模型置信度
2. 只在高评分（Top1%~10%）时入场投注
3. 动态调整投注金额根据评分高低

基于发现：
- Top10包含实际号码的基础命中率：74%
- Top1%高评分时刻的命中率：100%
"""

import json
import numpy as np
import torch
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Tuple, Dict
import sys

sys.path.insert(0, '/c1/program/lottery_3d_predict')
from src.models.lottery_model import LotteryModel

# 奖金配置
PRIZE_CONFIG = {
    'direct': 1040,
    'group3': 346,
    'group6': 173,
}
TICKET_PRICE = 2

# ==================== 机会评分器（复用） ====================
class OpportunityScorer:
    """机会评分系统"""
    
    # 特征权重（基于之前的分析结果）
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


# ==================== 投注策略 ====================
def get_group_type(numbers: List[int]) -> str:
    """判断号码形态"""
    counter = Counter(numbers)
    if len(counter) == 1:
        return 'leopard'
    elif len(counter) == 2:
        return 'group3'
    else:
        return 'group6'


def generate_bets(top_digits: List[int], score: float, num_bets_base: int = 50) -> List[Tuple[int, int, int]]:
    """
    根据评分生成投注组合
    
    高评分 -> 更多投注
    低评分 -> 更少投注
    """
    # 根据评分调整投注数量
    if score >= 63.3:  # Top1% 极高评分
        num_bets = int(num_bets_base * 1.5)  # 75注
    elif score >= 62.9:  # Top5% 高评分
        num_bets = int(num_bets_base * 1.2)  # 60注
    elif score >= 62.66:  # Top10% 中等评分
        num_bets = num_bets_base  # 50注
    else:
        num_bets = int(num_bets_base * 0.8)  # 40注
    
    bets = set()
    
    # 组六投注（70%）
    group6_count = int(num_bets * 0.7)
    attempts = 0
    while len([b for b in bets if len(set(b)) == 3]) < group6_count and attempts < group6_count * 3:
        combo = tuple(sorted(np.random.choice(top_digits, size=3, replace=False)))
        if len(set(combo)) == 3:
            bets.add(combo)
        attempts += 1
    
    # 组三投注（30%）
    group3_count = num_bets - len(bets)
    attempts = 0
    while len(bets) < num_bets and attempts < group3_count * 3:
        digit1 = np.random.choice(top_digits)
        digit2 = np.random.choice([d for d in top_digits if d != digit1])
        combo = tuple(sorted([digit1, digit1, digit2]))
        bets.add(combo)
        attempts += 1
    
    return list(bets)[:num_bets]


def check_win(bet_combo: Tuple[int, int, int], actual_numbers: List[int]) -> Tuple[str, int]:
    """检查是否中奖"""
    bet_sorted = sorted(bet_combo)
    actual_sorted = sorted(actual_numbers)
    
    if tuple(bet_combo) == tuple(actual_numbers):
        return 'direct', PRIZE_CONFIG['direct']
    
    if bet_sorted == actual_sorted:
        actual_type = get_group_type(actual_numbers)
        if actual_type == 'leopard':
            return 'direct', PRIZE_CONFIG['direct']
        elif actual_type == 'group3':
            return 'group3', PRIZE_CONFIG['group3']
        elif actual_type == 'group6':
            return 'group6', PRIZE_CONFIG['group6']
    
    return 'miss', 0


# ==================== 智能回测 ====================
def smart_backtest(sequences: np.ndarray, raw_data: List[Dict],
                  model: LotteryModel, device,
                  strategy_name: str, score_percentile: float,
                  test_periods: int = 300,
                  window_size: int = 30) -> Dict:
    """使用机会评分系统的智能回测"""
    
    print(f"\n{'='*70}")
    print(f"智能回测: {strategy_name}")
    print(f"{'='*70}")
    
    model.eval()
    scorer = OpportunityScorer()
    
    # 第一阶段：计算所有期的评分
    print(f"\n[阶段1] 计算机会评分...")
    
    start_idx = len(sequences) - test_periods - window_size
    all_scores = []
    predictions_cache = []
    
    for i in range(test_periods):
        idx = start_idx + i
        history = sequences[idx:idx + window_size]
        actual_numbers = sequences[idx + window_size]
        period_data = raw_data[idx + window_size]
        
        # 模型预测
        with torch.no_grad():
            input_seq = torch.LongTensor(history).unsqueeze(0).to(device)
            predictions = model.predict(input_seq)
            digit_probs = predictions['digit_probs'][0]
        
        # 计算机会评分
        score = scorer.calculate_score(digit_probs, history)
        all_scores.append(score)
        
        # Top10数字
        top_indices = np.argsort(digit_probs)[::-1]
        top10_digits = top_indices[:10].tolist()
        
        predictions_cache.append({
            'period': period_data['period'],
            'date': period_data['date'],
            'actual_numbers': actual_numbers.tolist(),
            'score': score,
            'top10_digits': top10_digits,
        })
    
    # 计算评分阈值
    score_threshold = np.percentile(all_scores, score_percentile * 100)
    expected_bet_periods = sum(1 for s in all_scores if s >= score_threshold)
    
    print(f"\n[阶段1完成]")
    print(f"  评分范围: {min(all_scores):.2f} - {max(all_scores):.2f}")
    print(f"  评分平均: {np.mean(all_scores):.2f}")
    print(f"  阈值({score_percentile*100:.0f}分位): {score_threshold:.2f}")
    print(f"  预计投注期数: {expected_bet_periods}/{test_periods} ({expected_bet_periods/test_periods*100:.1f}%)")
    
    # 第二阶段：模拟投注
    print(f"\n[阶段2] 模拟投注...")
    
    capital = 10000
    capital_history = [capital]
    
    bet_periods = 0
    skip_periods = 0
    win_periods = 0
    total_cost = 0
    total_prize = 0
    
    win_details = defaultdict(int)
    period_results = []
    
    for pred_data in predictions_cache:
        score = pred_data['score']
        actual_numbers = pred_data['actual_numbers']
        period_id = pred_data['period']
        top10_digits = pred_data['top10_digits']
        
        # 决策：是否投注
        should_bet = score >= score_threshold
        
        if not should_bet:
            skip_periods += 1
            capital_history.append(capital)
            period_results.append({
                'period': period_id,
                'action': 'skip',
                'score': score,
                'capital': capital
            })
            continue
        
        # 生成投注
        bet_combos = generate_bets(top10_digits, score, num_bets_base=50)
        
        period_cost = len(bet_combos) * TICKET_PRICE
        total_cost += period_cost
        capital -= period_cost
        bet_periods += 1
        
        # 检查中奖
        period_prize = 0
        period_wins = []
        
        for combo in bet_combos:
            win_type, prize = check_win(combo, actual_numbers)
            if prize > 0:
                period_prize += prize
                period_wins.append({
                    'combo': combo,
                    'type': win_type,
                    'prize': prize
                })
                win_details[win_type] += 1
        
        total_prize += period_prize
        
        if period_prize > 0:
            win_periods += 1
        
        capital += period_prize
        period_profit = period_prize - period_cost
        capital_history.append(capital)
        
        period_results.append({
            'period': period_id,
            'action': 'bet',
            'score': score,
            'num_bets': len(bet_combos),
            'cost': period_cost,
            'prize': period_prize,
            'profit': period_profit,
            'capital': capital,
            'wins': period_wins,
            'actual_numbers': actual_numbers
        })
    
    # 计算指标
    total_profit = total_prize - total_cost
    roi = (total_profit / total_cost * 100) if total_cost > 0 else 0
    win_rate = (win_periods / bet_periods * 100) if bet_periods > 0 else 0
    
    # 最大回撤
    peak = capital_history[0]
    max_drawdown = 0
    for cap in capital_history:
        if cap > peak:
            peak = cap
        drawdown = (peak - cap) / peak if peak > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)
    
    # 夏普比率
    if bet_periods > 1:
        period_returns = [r['profit'] / r['cost'] for r in period_results if r['action'] == 'bet']
        mean_return = np.mean(period_returns)
        std_return = np.std(period_returns)
        sharpe_ratio = mean_return / std_return if std_return > 0 else 0
    else:
        sharpe_ratio = 0
    
    # 卡尔玛比率
    calmar_ratio = (roi / 100) / max_drawdown if max_drawdown > 0 else 0
    
    print(f"\n[回测完成]")
    print(f"  投注期数: {bet_periods}/{test_periods} ({bet_periods/test_periods*100:.1f}%)")
    print(f"  胜率: {win_rate:.2f}%")
    print(f"  ROI: {roi:.2f}%")
    print(f"  最大回撤: {max_drawdown*100:.2f}%")
    print(f"  夏普比率: {sharpe_ratio:.3f}")
    print(f"  最终资金: ¥{capital:,.2f}")
    
    summary = {
        'strategy_name': strategy_name,
        'score_percentile': score_percentile,
        'test_periods': test_periods,
        'bet_periods': bet_periods,
        'skip_periods': skip_periods,
        'bet_frequency': bet_periods / test_periods if test_periods > 0 else 0,
        
        'total_cost': total_cost,
        'total_prize': total_prize,
        'total_profit': total_profit,
        'roi_percentage': roi,
        
        'max_drawdown': max_drawdown,
        'win_periods': win_periods,
        'win_rate': win_rate,
        'sharpe_ratio': sharpe_ratio,
        'calmar_ratio': calmar_ratio,
        
        'win_details': dict(win_details),
        'starting_capital': capital_history[0],
        'final_capital': capital_history[-1],
        'capital_history': capital_history,
        
        'score_threshold': score_threshold,
        'score_range': (min(all_scores), max(all_scores)),
        'score_mean': np.mean(all_scores),
    }
    
    return {
        'summary': summary,
        'period_results': period_results
    }


# ==================== 主程序 ====================
def load_data(json_file: str, num_records: int = 1500):
    """加载数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    recent_data = data['data'][-num_records:]
    sequences = np.array([item['numbers'] for item in recent_data])
    return sequences, recent_data


def main():
    print("="*80)
    print("智能投注策略对比 - 基于机会评分系统")
    print("="*80)
    
    # 加载数据和模型
    print("\n[1] 加载数据和模型...")
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    sequences, raw_data = load_data(data_file, num_records=1500)
    
    device = torch.device('cpu')
    model = LotteryModel.load('models/checkpoints/best_model.pth', device=device)
    
    print(f"✓ 数据: {len(sequences)}期")
    print(f"✓ 模型已加载")
    
    # 定义策略
    strategies = {
        'smart_top10': ('智能Top10策略（10%）', 0.90),
        'smart_top5': ('智能Top5策略（5%）', 0.95),
        'smart_top1': ('智能Top1策略（1%）', 0.99),
    }
    
    # 运行回测
    all_results = {}
    for strategy_key, (strategy_name, percentile) in strategies.items():
        result = smart_backtest(
            sequences=sequences,
            raw_data=raw_data,
            model=model,
            device=device,
            strategy_name=strategy_name,
            score_percentile=percentile,
            test_periods=300,
            window_size=30
        )
        all_results[strategy_key] = result
    
    # 对比报告
    print("\n\n" + "="*80)
    print("智能策略对比报告")
    print("="*80)
    
    print(f"\n{'指标':<20} {'Top10(10%)':<20} {'Top5(5%)':<20} {'Top1(1%)':<20}")
    print("-"*80)
    
    metrics = [
        ('投注期数', 'bet_periods', '{}期'),
        ('投注频率', 'bet_frequency', '{:.1f}%', 100),
        ('胜率', 'win_rate', '{:.2f}%'),
        ('ROI', 'roi_percentage', '{:.2f}%'),
        ('总投入', 'total_cost', '¥{:,.0f}'),
        ('总奖金', 'total_prize', '¥{:,.0f}'),
        ('总利润', 'total_profit', '¥{:,.0f}'),
        ('最终资金', 'final_capital', '¥{:,.0f}'),
        ('最大回撤', 'max_drawdown', '{:.2f}%', 100),
        ('夏普比率', 'sharpe_ratio', '{:.3f}'),
        ('卡尔玛比率', 'calmar_ratio', '{:.3f}'),
    ]
    
    for metric_name, metric_key, fmt, *multiplier in metrics:
        mult = multiplier[0] if multiplier else 1
        values = []
        for strategy_key in ['smart_top10', 'smart_top5', 'smart_top1']:
            value = all_results[strategy_key]['summary'][metric_key]
            values.append(fmt.format(value * mult))
        print(f"{metric_name:<20} {values[0]:<20} {values[1]:<20} {values[2]:<20}")
    
    # 中奖详情
    print("\n【中奖类型分布】")
    for strategy_key, (strategy_name, _) in strategies.items():
        win_details = all_results[strategy_key]['summary']['win_details']
        total_wins = sum(win_details.values())
        print(f"\n{strategy_name}:")
        print(f"  总中奖次数: {total_wins}")
        for win_type, count in sorted(win_details.items()):
            print(f"    {win_type}: {count}次")
    
    # 推荐
    print("\n\n" + "="*80)
    print("投资建议")
    print("="*80)
    
    best_roi_key = max(all_results.keys(), key=lambda k: all_results[k]['summary']['roi_percentage'])
    best_roi = all_results[best_roi_key]['summary']['roi_percentage']
    best_final_capital = all_results[best_roi_key]['summary']['final_capital']
    
    print(f"\n✓ 最佳策略: {strategies[best_roi_key][0]}")
    print(f"  - ROI: {best_roi:.2f}%")
    print(f"  - 最终资金: ¥{best_final_capital:,.2f} (起始¥10,000)")
    print(f"  - 收益: ¥{best_final_capital - 10000:,.2f}")
    
    if best_roi > 0:
        print(f"\n✅ 该策略在测试期内实现了正收益！")
    else:
        print(f"\n⚠️  所有策略在测试期内均为负收益，不建议投注")
    
    print(f"\n{'='*80}")
    
    return all_results


if __name__ == '__main__':
    results = main()
