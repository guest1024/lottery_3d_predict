"""
概率阈值策略对比分析
==================

系统性对比Top10%、Top5%、Top1%三种投注策略的表现
分析不同概率阈值下的收益、风险和入场时机

核心指标：
- 胜率（预测准确率）
- 累计收益率
- 最大回撤
- 夏普比率
- 卡尔玛比率
- 入场次数和频率
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

# ==================== 配置参数 ====================
PRIZE_CONFIG = {
    'direct': 1040,    # 直选奖金
    'group3': 346,     # 组三奖金
    'group6': 173,     # 组六奖金
}

TICKET_PRICE = 2

# 测试策略配置
STRATEGIES = {
    'top10': {
        'name': 'Top10策略（10%概率）',
        'percentile': 0.90,  # 使用置信度最高的10%期数
        'description': '只在模型最有信心的10%期数投注'
    },
    'top5': {
        'name': 'Top5策略（5%概率）',
        'percentile': 0.95,  # 使用置信度最高的5%期数
        'description': '只在模型最有信心的5%期数投注，更加保守'
    },
    'top1': {
        'name': 'Top1策略（1%概率）',
        'percentile': 0.99,  # 使用置信度最高的1%期数
        'description': '只在模型极度有信心的1%期数投注，极度保守'
    }
}


# ==================== 可信度评估 ====================
class ConfidenceScorer:
    """评估预测可信度"""
    
    @staticmethod
    def calculate_confidence(digit_probs: np.ndarray) -> float:
        """
        计算预测可信度分数
        
        基于多个指标的综合评分：
        1. Top5概率的平均值（35%）
        2. Top1概率的最大值（30%）
        3. Top1与Top2的差距（20%）
        4. 概率分布的标准差（10%）
        5. Top5的集中度（5%）
        """
        sorted_indices = np.argsort(digit_probs)[::-1]
        sorted_probs = digit_probs[sorted_indices]
        
        # 1. Top5平均概率
        top5_probs = sorted_probs[:5]
        top_prob_mean = np.mean(top5_probs)
        
        # 2. Top1最大概率
        top_prob_max = sorted_probs[0]
        
        # 3. Top1与Top2差距
        prob_gap = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else 0
        
        # 4. 概率标准差
        prob_std = np.std(digit_probs)
        
        # 5. Top5集中度
        total_prob = np.sum(digit_probs)
        top5_concentration = np.sum(top5_probs) / (total_prob + 1e-10)
        
        # 综合评分
        confidence_score = (
            top_prob_mean * 0.35 +
            top_prob_max * 0.30 +
            prob_gap * 0.20 +
            prob_std * 0.10 +
            top5_concentration * 0.05
        )
        
        return float(confidence_score)


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


def generate_bets_from_top_digits(top_digits: List[int], num_bets: int = 50) -> List[Tuple[int, int, int]]:
    """
    从Top数字生成投注组合
    
    策略：
    - 70% 组六（3个不同数字）
    - 30% 组三（2个相同+1个不同）
    """
    bets = set()
    
    # 组六投注（70%）
    group6_count = int(num_bets * 0.7)
    for _ in range(group6_count * 2):  # 多生成一些，后面去重
        combo = tuple(sorted(np.random.choice(top_digits, size=3, replace=False)))
        if len(set(combo)) == 3:  # 确保是3个不同数字
            bets.add(combo)
    
    # 组三投注（30%）
    group3_count = num_bets - group6_count
    for _ in range(group3_count * 2):
        digit1 = np.random.choice(top_digits)
        digit2 = np.random.choice([d for d in top_digits if d != digit1])
        combo = tuple(sorted([digit1, digit1, digit2]))
        bets.add(combo)
    
    return list(bets)[:num_bets]


def check_win(bet_combo: Tuple[int, int, int], actual_numbers: List[int]) -> Tuple[str, int]:
    """检查是否中奖"""
    bet_sorted = sorted(bet_combo)
    actual_sorted = sorted(actual_numbers)
    
    # 直选检查
    if tuple(bet_combo) == tuple(actual_numbers):
        return 'direct', PRIZE_CONFIG['direct']
    
    # 组选检查
    if bet_sorted == actual_sorted:
        actual_type = get_group_type(actual_numbers)
        if actual_type == 'leopard':
            return 'direct', PRIZE_CONFIG['direct']  # 豹子按直选算
        elif actual_type == 'group3':
            return 'group3', PRIZE_CONFIG['group3']
        elif actual_type == 'group6':
            return 'group6', PRIZE_CONFIG['group6']
    
    return 'miss', 0


# ==================== 回测核心逻辑 ====================
def backtest_strategy(sequences: np.ndarray, raw_data: List[Dict], 
                     model: LotteryModel, device,
                     strategy_name: str, percentile_threshold: float,
                     num_bets: int = 50,
                     test_periods: int = 300,
                     window_size: int = 30) -> Dict:
    """
    回测单个策略
    
    两阶段过程：
    1. 计算所有期的可信度分数
    2. 根据分位数阈值决定是否投注
    """
    print(f"\n{'='*70}")
    print(f"回测策略: {strategy_name}")
    print(f"{'='*70}")
    
    model.eval()
    
    # ==================== 第一阶段：计算可信度 ====================
    print(f"\n[阶段1] 计算所有期的可信度分数...")
    
    start_idx = len(sequences) - test_periods - window_size
    confidence_scores = []
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
        
        # 计算可信度
        confidence = ConfidenceScorer.calculate_confidence(digit_probs)
        confidence_scores.append(confidence)
        
        # 缓存预测结果
        top_indices = np.argsort(digit_probs)[::-1]
        top5_digits = top_indices[:5].tolist()
        
        predictions_cache.append({
            'period': period_data['period'],
            'date': period_data['date'],
            'actual_numbers': actual_numbers.tolist(),
            'confidence': confidence,
            'top5_digits': top5_digits,
            'digit_probs': digit_probs
        })
    
    # 计算可信度阈值
    confidence_threshold = np.percentile(confidence_scores, percentile_threshold * 100)
    expected_bet_periods = sum(1 for c in confidence_scores if c >= confidence_threshold)
    
    print(f"\n[阶段1完成]")
    print(f"  可信度范围: {min(confidence_scores):.4f} - {max(confidence_scores):.4f}")
    print(f"  可信度平均: {np.mean(confidence_scores):.4f}")
    print(f"  阈值({percentile_threshold*100:.0f}分位): {confidence_threshold:.4f}")
    print(f"  预计投注期数: {expected_bet_periods}/{test_periods} ({expected_bet_periods/test_periods*100:.1f}%)")
    
    # ==================== 第二阶段：模拟投注 ====================
    print(f"\n[阶段2] 模拟投注过程...")
    
    bet_periods = 0
    skip_periods = 0
    win_periods = 0
    total_cost = 0
    total_prize = 0
    
    win_details = defaultdict(int)  # 各类型中奖次数
    period_results = []
    
    capital = 10000  # 起始资金
    capital_history = [capital]
    
    for pred_data in predictions_cache:
        confidence = pred_data['confidence']
        actual_numbers = pred_data['actual_numbers']
        period_id = pred_data['period']
        top5_digits = pred_data['top5_digits']
        
        # 决策：是否投注
        should_bet = confidence >= confidence_threshold
        
        if not should_bet:
            skip_periods += 1
            capital_history.append(capital)
            period_results.append({
                'period': period_id,
                'action': 'skip',
                'confidence': confidence,
                'capital': capital
            })
            continue
        
        # 生成投注组合
        bet_combos = generate_bets_from_top_digits(top5_digits, num_bets)
        
        # 计算成本
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
            'confidence': confidence,
            'num_bets': len(bet_combos),
            'cost': period_cost,
            'prize': period_prize,
            'profit': period_profit,
            'capital': capital,
            'wins': period_wins,
            'actual_numbers': actual_numbers
        })
    
    # ==================== 计算指标 ====================
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
    
    # 夏普比率（假设无风险利率为0）
    if bet_periods > 0:
        period_returns = []
        for result in period_results:
            if result['action'] == 'bet':
                period_return = result['profit'] / result['cost'] if result['cost'] > 0 else 0
                period_returns.append(period_return)
        
        if len(period_returns) > 1:
            mean_return = np.mean(period_returns)
            std_return = np.std(period_returns)
            sharpe_ratio = mean_return / std_return if std_return > 0 else 0
        else:
            sharpe_ratio = 0
    else:
        sharpe_ratio = 0
    
    # 卡尔玛比率（年化收益/最大回撤）
    if max_drawdown > 0:
        # 假设测试周期对应1年
        annual_return = roi / 100
        calmar_ratio = annual_return / max_drawdown
    else:
        calmar_ratio = 0
    
    # 连续亏损统计
    consecutive_losses = []
    current_loss_streak = 0
    for result in period_results:
        if result['action'] == 'bet':
            if result['profit'] < 0:
                current_loss_streak += 1
            else:
                if current_loss_streak > 0:
                    consecutive_losses.append(current_loss_streak)
                current_loss_streak = 0
    if current_loss_streak > 0:
        consecutive_losses.append(current_loss_streak)
    
    max_consecutive_losses = max(consecutive_losses) if consecutive_losses else 0
    
    # ==================== 汇总结果 ====================
    summary = {
        'strategy_name': strategy_name,
        'percentile_threshold': percentile_threshold,
        'test_periods': test_periods,
        'bet_periods': bet_periods,
        'skip_periods': skip_periods,
        'bet_frequency': bet_periods / test_periods if test_periods > 0 else 0,
        
        # 收益指标
        'total_cost': total_cost,
        'total_prize': total_prize,
        'total_profit': total_profit,
        'roi_percentage': roi,
        
        # 风险指标
        'max_drawdown': max_drawdown,
        'max_consecutive_losses': max_consecutive_losses,
        
        # 性能指标
        'win_periods': win_periods,
        'win_rate': win_rate,
        'sharpe_ratio': sharpe_ratio,
        'calmar_ratio': calmar_ratio,
        
        # 中奖详情
        'win_details': dict(win_details),
        
        # 资金曲线
        'starting_capital': capital_history[0],
        'final_capital': capital_history[-1],
        'capital_history': capital_history,
        
        # 置信度统计
        'confidence_threshold': confidence_threshold,
        'confidence_range': (min(confidence_scores), max(confidence_scores)),
        'confidence_mean': np.mean(confidence_scores),
    }
    
    print(f"\n[回测完成]")
    print(f"  投注期数: {bet_periods}/{test_periods} ({bet_periods/test_periods*100:.1f}%)")
    print(f"  胜率: {win_rate:.2f}%")
    print(f"  ROI: {roi:.2f}%")
    print(f"  最大回撤: {max_drawdown*100:.2f}%")
    print(f"  夏普比率: {sharpe_ratio:.3f}")
    print(f"  卡尔玛比率: {calmar_ratio:.3f}")
    
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


def compare_strategies():
    """对比所有策略"""
    print("="*80)
    print("3D彩票投注策略对比分析")
    print("="*80)
    
    # 加载数据和模型
    print("\n[1] 加载数据和模型...")
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    sequences, raw_data = load_data(data_file, num_records=1500)
    
    device = torch.device('cpu')
    model = LotteryModel.load('models/checkpoints/best_model.pth', device=device)
    
    print(f"✓ 数据: {len(sequences)}期")
    print(f"✓ 模型已加载")
    
    # 运行所有策略
    all_results = {}
    
    for strategy_key, strategy_config in STRATEGIES.items():
        result = backtest_strategy(
            sequences=sequences,
            raw_data=raw_data,
            model=model,
            device=device,
            strategy_name=strategy_config['name'],
            percentile_threshold=strategy_config['percentile'],
            num_bets=50,
            test_periods=300,
            window_size=30
        )
        all_results[strategy_key] = result
    
    # ==================== 生成对比报告 ====================
    print("\n\n" + "="*80)
    print("策略对比报告")
    print("="*80)
    
    # 表格对比
    print("\n【关键指标对比】")
    print(f"{'指标':<20} {'Top10(10%)':<20} {'Top5(5%)':<20} {'Top1(1%)':<20}")
    print("-"*80)
    
    metrics = [
        ('投注期数', 'bet_periods', '{}期'),
        ('投注频率', 'bet_frequency', '{:.1f}%', 100),
        ('胜率', 'win_rate', '{:.2f}%'),
        ('ROI', 'roi_percentage', '{:.2f}%'),
        ('总投入', 'total_cost', '¥{:,.0f}'),
        ('总奖金', 'total_prize', '¥{:,.0f}'),
        ('总利润', 'total_profit', '¥{:,.0f}'),
        ('最大回撤', 'max_drawdown', '{:.2f}%', 100),
        ('最大连亏', 'max_consecutive_losses', '{}期'),
        ('夏普比率', 'sharpe_ratio', '{:.3f}'),
        ('卡尔玛比率', 'calmar_ratio', '{:.3f}'),
    ]
    
    for metric_name, metric_key, fmt, *multiplier in metrics:
        mult = multiplier[0] if multiplier else 1
        values = []
        for strategy_key in ['top10', 'top5', 'top1']:
            value = all_results[strategy_key]['summary'][metric_key]
            values.append(fmt.format(value * mult))
        
        print(f"{metric_name:<20} {values[0]:<20} {values[1]:<20} {values[2]:<20}")
    
    # 中奖详情对比
    print("\n【中奖类型分布】")
    for strategy_key, strategy_config in STRATEGIES.items():
        win_details = all_results[strategy_key]['summary']['win_details']
        total_wins = sum(win_details.values())
        print(f"\n{strategy_config['name']}:")
        print(f"  总中奖次数: {total_wins}")
        for win_type, count in sorted(win_details.items()):
            print(f"    {win_type}: {count}次")
    
    # 推荐结论
    print("\n\n" + "="*80)
    print("结论与建议")
    print("="*80)
    
    # 找出最佳策略
    best_roi_key = max(all_results.keys(), key=lambda k: all_results[k]['summary']['roi_percentage'])
    best_roi = all_results[best_roi_key]['summary']['roi_percentage']
    
    best_sharpe_key = max(all_results.keys(), key=lambda k: all_results[k]['summary']['sharpe_ratio'])
    best_sharpe = all_results[best_sharpe_key]['summary']['sharpe_ratio']
    
    lowest_drawdown_key = min(all_results.keys(), key=lambda k: all_results[k]['summary']['max_drawdown'])
    lowest_drawdown = all_results[lowest_drawdown_key]['summary']['max_drawdown']
    
    print(f"\n✓ 最高ROI: {STRATEGIES[best_roi_key]['name']} ({best_roi:.2f}%)")
    print(f"✓ 最佳夏普比率: {STRATEGIES[best_sharpe_key]['name']} ({best_sharpe:.3f})")
    print(f"✓ 最低回撤: {STRATEGIES[lowest_drawdown_key]['name']} ({lowest_drawdown*100:.2f}%)")
    
    print("\n策略建议:")
    print("1. 如果追求高收益且能承受风险：选择ROI最高的策略")
    print("2. 如果追求风险调整后收益：选择夏普比率最高的策略")
    print("3. 如果风险厌恶：选择回撤最低的策略")
    
    # 保存结果
    output_data = {
        'comparison_summary': {
            strategy_key: result['summary']
            for strategy_key, result in all_results.items()
        },
        'best_strategies': {
            'best_roi': best_roi_key,
            'best_sharpe': best_sharpe_key,
            'lowest_drawdown': lowest_drawdown_key
        },
        'detailed_results': {
            strategy_key: {
                'summary': result['summary'],
                'period_results': result['period_results'][:100]  # 只保存前100期详情，节省空间
            }
            for strategy_key, result in all_results.items()
        }
    }
    
    output_path = Path('results/strategy_comparison.json')
    output_path.parent.mkdir(exist_ok=True)
    
    # 转换numpy类型为Python原生类型
    def convert_to_serializable(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        else:
            return obj
    
    output_data = convert_to_serializable(output_data)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 详细结果已保存到: {output_path}")
    
    return all_results


if __name__ == '__main__':
    results = compare_strategies()
