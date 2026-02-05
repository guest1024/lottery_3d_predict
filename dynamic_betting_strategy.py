"""
动态投注策略 - 基于可信度的智能投注系统
只考虑组选（组三、组六），不考虑直选

策略核心：
1. 可信度评估：基于模型输出概率和预测一致性
2. 动态决策：只在高可信度时投注
3. 仓位管理：根据可信度调整投注金额
4. 组选专注：降低风险，提高中奖概率
"""

import json
import numpy as np
import torch
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from collections import Counter
from itertools import combinations

# 导入模型
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
from models.lottery_model import LotteryModel

# ==================== 配置参数 ====================
# 奖金结构
GROUP3_PRIZE = 346  # 组三奖金
GROUP6_PRIZE = 173  # 组六奖金
TICKET_PRICE = 2    # 每注成本

# 策略参数
CONFIDENCE_PERCENTILE = 0.10  # 投注可信度分位数
MIN_BET_AMOUNT = 10           # 最小投注金额（元）
MAX_BET_AMOUNT = 500          # 最大投注金额（元）
MAX_RISK_PER_PERIOD = 0.05    # 单期最大风险敞口（5%资金）

# 回测参数
STARTING_CAPITAL = 10000    # 起始资金¥10,000
TEST_PERIODS = 200          # 回测期数


# ==================== 可信度评估系统 ====================
class ConfidenceScorer:
    """评估预测可信度"""
    
    def __init__(self):
        self.history_accuracy = []  # 历史准确率记录
    
    def calculate_confidence(self, digit_probs: np.ndarray, 
                            attention_weights: Optional[np.ndarray] = None) -> Dict:
        """
        计算预测可信度
        
        Args:
            digit_probs: 模型输出的概率分布 [10] (10个数字的概率，sigmoid输出)
            attention_weights: 注意力权重（可选）[seq_len]
            
        Returns:
            confidence_dict: {
                'overall_confidence': float,  # 总体可信度 0-1
                'top_probs': list,            # Top概率值
                'entropy': float,             # 熵值（不确定性）
                'should_bet': bool            # 是否建议投注
            }
        """
        # digit_probs是10个数字的sigmoid输出（多标签分类）
        # 值域[0,1]，但不一定总和为1
        
        # 1. 计算Top5概率的强度
        sorted_indices = np.argsort(digit_probs)[::-1]
        sorted_probs = digit_probs[sorted_indices]
        top5_probs = sorted_probs[:5]
        top_prob_max = sorted_probs[0]
        top_prob_mean = np.mean(top5_probs)
        
        # 2. 计算概率差异（Top1与其他的差距）
        # Top1与Top2差距越大，预测越有信心
        prob_gap = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else 0
        
        # 3. 计算Top5的集中度
        # Top5的概率和占总概率和的比例
        total_prob = np.sum(digit_probs)
        top5_concentration = np.sum(top5_probs) / (total_prob + 1e-10)
        
        # 4. 计算概率分布的标准差
        # 标准差越大，说明预测越有倾向性
        prob_std = np.std(digit_probs)
        
        # 5. 综合可信度评分
        # 由于sigmoid输出值普遍较低，我们需要调整权重
        # 权重：Top5平均35% + 最大概率30% + 概率差距20% + 标准差10% + Top5集中度5%
        confidence_score = (
            top_prob_mean * 0.35 +
            top_prob_max * 0.30 +
            prob_gap * 0.20 +
            prob_std * 0.10 +
            top5_concentration * 0.05
        )
        
        # 6. 如果有注意力权重，考虑序列重要性
        if attention_weights is not None:
            # 注意力集中度：越集中说明模型越关注特定时间点
            attn_max = np.max(attention_weights)
            attn_std = np.std(attention_weights)
            attn_score = attn_max * 0.5 + attn_std * 0.5
            confidence_score = confidence_score * 0.85 + attn_score * 0.15
        
        # 7. 判断是否建议投注（稍后基于分位数决定）
        should_bet = True  # 暂时设为True，稍后基于分位数过滤
        
        return {
            'overall_confidence': float(confidence_score),
            'top_prob_max': float(top_prob_max),
            'top_prob_mean': float(top_prob_mean),
            'prob_gap': float(prob_gap),
            'prob_std': float(prob_std),
            'top5_concentration': float(top5_concentration),
            'should_bet': should_bet
        }


# ==================== 组选投注策略 ====================
class GroupBettingStrategy:
    """组选投注策略生成器"""
    
    @staticmethod
    def get_group_type(numbers: List[int]) -> str:
        """判断号码类型"""
        counter = Counter(numbers)
        if len(counter) == 2:  # 有重复
            return 'group3'
        elif len(counter) == 3:  # 无重复
            return 'group6'
        else:
            return 'unknown'
    
    @staticmethod
    def generate_group3_bets(top_digits: List[int], max_bets: int = 20) -> List[List[int]]:
        """
        生成组三投注组合
        组三：2个相同 + 1个不同，如 [1,1,2]
        
        Strategy:
        - 从top_digits中选择2个数字
        - 一个出现2次，一个出现1次
        """
        bets = []
        
        # 遍历所有可能的组三组合
        for i in range(len(top_digits)):
            for j in range(len(top_digits)):
                if i != j:
                    digit1 = top_digits[i]  # 出现2次
                    digit2 = top_digits[j]  # 出现1次
                    
                    # 组三有3种排列：AAB, ABA, BAA
                    combo = sorted([digit1, digit1, digit2])
                    if combo not in bets:
                        bets.append(combo)
                        
                    if len(bets) >= max_bets:
                        return bets
        
        return bets
    
    @staticmethod
    def generate_group6_bets(top_digits: List[int], max_bets: int = 30) -> List[List[int]]:
        """
        生成组六投注组合
        组六：3个不同数字，如 [1,2,3]
        
        Strategy:
        - 从top_digits中选择3个不同数字的组合
        """
        bets = []
        
        # C(n,3) 组合
        for combo in combinations(top_digits, 3):
            bets.append(sorted(list(combo)))
            if len(bets) >= max_bets:
                break
        
        return bets
    
    @staticmethod
    def generate_mixed_bets(top_digits: List[int], confidence: float, 
                           max_total_bets: int = 50) -> List[List[int]]:
        """
        生成混合投注组合（组三+组六）
        根据可信度动态调整比例
        
        Args:
            top_digits: 预测的高概率数字
            confidence: 可信度分数 0-1
            max_total_bets: 最大总投注数
            
        Returns:
            bet_combinations: 投注组合列表
        """
        # 根据可信度调整组三/组六比例
        # 高可信度：更多组三（奖金高但难中）
        # 低可信度：更多组六（奖金低但易中）
        if confidence >= 0.75:
            group3_ratio = 0.6
        elif confidence >= 0.65:
            group3_ratio = 0.5
        else:
            group3_ratio = 0.4
        
        group3_count = int(max_total_bets * group3_ratio)
        group6_count = max_total_bets - group3_count
        
        # 生成投注组合
        group3_bets = GroupBettingStrategy.generate_group3_bets(top_digits, group3_count)
        group6_bets = GroupBettingStrategy.generate_group6_bets(top_digits, group6_count)
        
        all_bets = group3_bets + group6_bets
        
        # 去重
        unique_bets = []
        seen = set()
        for bet in all_bets:
            bet_tuple = tuple(bet)
            if bet_tuple not in seen:
                unique_bets.append(bet)
                seen.add(bet_tuple)
        
        return unique_bets


# ==================== 仓位管理系统 ====================
class PositionSizer:
    """动态仓位管理"""
    
    @staticmethod
    def calculate_bet_size(capital: float, confidence: float, 
                          historical_win_rate: float = 0.1) -> int:
        """
        计算本期应投注金额
        
        使用修改版Kelly准则:
        f = (p * b - q) / b
        其中:
        - f: 投注比例
        - p: 胜率（基于历史和可信度）
        - q: 败率 (1-p)
        - b: 赔率（期望收益/投注成本）
        
        Args:
            capital: 当前资金
            confidence: 本期可信度
            historical_win_rate: 历史胜率
            
        Returns:
            bet_amount: 建议投注金额（元）
        """
        # 1. 估计胜率（结合历史和可信度）
        estimated_win_rate = historical_win_rate * 0.4 + confidence * 0.6
        
        # 2. 估计平均赔率
        # 假设组三和组六各占50%，中奖时的平均回报
        avg_prize = (GROUP3_PRIZE + GROUP6_PRIZE) / 2
        avg_odds = avg_prize / TICKET_PRICE  # ~130倍
        
        # 3. Kelly公式
        p = estimated_win_rate
        q = 1 - p
        b = avg_odds
        
        kelly_fraction = (p * b - q) / b
        
        # 4. 保守调整（使用1/4 Kelly，降低风险）
        conservative_fraction = max(0, kelly_fraction * 0.25)
        
        # 5. 应用风险限制
        max_risk_amount = capital * MAX_RISK_PER_PERIOD
        suggested_amount = capital * conservative_fraction
        
        # 6. 限制在合理范围
        bet_amount = min(suggested_amount, max_risk_amount)
        bet_amount = max(MIN_BET_AMOUNT, min(bet_amount, MAX_BET_AMOUNT))
        
        return int(bet_amount)
    
    @staticmethod
    def calculate_num_bets(bet_amount: int) -> int:
        """根据投注金额计算投注注数"""
        return max(1, bet_amount // TICKET_PRICE)


# ==================== 中奖检查 ====================
def check_group_win(bet_combo: List[int], actual_numbers: List[int]) -> Tuple[str, int]:
    """
    检查组选是否中奖
    
    Returns:
        (win_type, prize): ('group3'|'group6'|'miss', prize_amount)
    """
    bet_sorted = sorted(bet_combo)
    actual_sorted = sorted(actual_numbers)
    
    if bet_sorted == actual_sorted:
        # 判断是组三还是组六
        bet_type = GroupBettingStrategy.get_group_type(bet_combo)
        if bet_type == 'group3':
            return ('group3', GROUP3_PRIZE)
        elif bet_type == 'group6':
            return ('group6', GROUP6_PRIZE)
    
    return ('miss', 0)


# ==================== 动态回测系统 ====================
def dynamic_backtest(sequences: np.ndarray, raw_data: List[Dict], 
                    model: LotteryModel,
                    starting_capital: float = STARTING_CAPITAL,
                    test_periods: int = TEST_PERIODS,
                    window_size: int = 30) -> Dict:
    """
    动态投注策略回测（两阶段）
    
    第一阶段：计算所有期的可信度分数
    第二阶段：基于可信度分位数决定投注，模拟资金变化
    
    Args:
        sequences: 输入序列 [N, 3] - 所有历史数据
        raw_data: 原始数据
        model: 训练好的模型
        starting_capital: 起始资金
        test_periods: 回测期数
        window_size: 输入窗口大小
        
    Returns:
        backtest_results: 回测结果详情
    """
    model.eval()
    device = next(model.parameters()).device
    
    # 初始化
    confidence_scorer = ConfidenceScorer()
    
    print(f"\n{'='*80}")
    print(f"动态投注策略回测（两阶段）")
    print(f"{'='*80}\n")
    
    print(f"[阶段1] 计算所有期的可信度分数...")
    
    # ==================== 第一阶段：计算可信度 ====================
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
            attention_weights = predictions['attention_weights'][0]
        
        # 评估可信度
        confidence_result = confidence_scorer.calculate_confidence(
            digit_probs, attention_weights
        )
        
        confidence_scores.append(confidence_result['overall_confidence'])
        
        # 缓存预测结果
        top_indices = np.argsort(digit_probs)[::-1]
        top5_digits = top_indices[:5].tolist()
        
        predictions_cache.append({
            'period_id': period_data['period'],
            'actual_numbers': actual_numbers.tolist(),
            'confidence': confidence_result['overall_confidence'],
            'top5_digits': top5_digits,
            'digit_probs': digit_probs
        })
        
        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{test_periods}")
    
    # 计算可信度阈值（基于分位数）
    confidence_threshold = np.percentile(confidence_scores, (1 - CONFIDENCE_PERCENTILE) * 100)
    
    print(f"\n[阶段1完成]")
    print(f"  可信度范围: {min(confidence_scores):.4f} - {max(confidence_scores):.4f}")
    print(f"  可信度平均: {np.mean(confidence_scores):.4f}")
    print(f"  动态阈值(Top {CONFIDENCE_PERCENTILE*100:.0f}%): {confidence_threshold:.4f}")
    print(f"  预计投注期数: {sum(1 for c in confidence_scores if c >= confidence_threshold)}")
    
    print(f"\n[阶段2] 模拟投注过程...")
    
    # ==================== 第二阶段：模拟投注 ====================
    capital = starting_capital
    capital_history = [capital]
    
    total_periods = 0
    bet_periods = 0
    skip_periods = 0
    win_periods = 0
    total_invested = 0
    total_prizes = 0
    
    period_results = []
    historical_win_rate = 0.1  # 初始估计
    
    for pred_data in predictions_cache:
        total_periods += 1
        confidence = pred_data['confidence']
        actual_numbers = pred_data['actual_numbers']
        period_id = pred_data['period_id']
        top5_digits = pred_data['top5_digits']
        
        # 决策：是否投注（基于可信度阈值）
        should_bet = confidence >= confidence_threshold
        
        if not should_bet or capital < MIN_BET_AMOUNT:
            skip_periods += 1
            period_results.append({
                'period': period_id,
                'action': 'skip',
                'confidence': confidence,
                'capital': capital,
                'reason': 'low_confidence' if not should_bet else 'insufficient_capital'
            })
            capital_history.append(capital)
            continue
        
        # 计算投注金额和注数
        bet_amount = PositionSizer.calculate_bet_size(capital, confidence, historical_win_rate)
        num_bets = PositionSizer.calculate_num_bets(bet_amount)
        
        # 确保不超资
        actual_cost = num_bets * TICKET_PRICE
        if actual_cost > capital:
            num_bets = int(capital // TICKET_PRICE)
            actual_cost = num_bets * TICKET_PRICE
        
        if num_bets == 0:
            skip_periods += 1
            capital_history.append(capital)
            continue
        
        bet_periods += 1
        
        # 生成投注组合
        bet_combos = GroupBettingStrategy.generate_mixed_bets(
            top5_digits, confidence, max_total_bets=num_bets
        )
        
        actual_num_bets = len(bet_combos)
        actual_cost = actual_num_bets * TICKET_PRICE
        
        # 扣除投注成本
        capital -= actual_cost
        total_invested += actual_cost
        
        # 检查中奖
        period_prize = 0
        win_details = []
        
        for bet_combo in bet_combos:
            win_type, prize = check_group_win(bet_combo, actual_numbers)
            if prize > 0:
                period_prize += prize
                win_details.append({'combo': bet_combo, 'type': win_type, 'prize': prize})
        
        # 添加奖金
        if period_prize > 0:
            win_periods += 1
            capital += period_prize
            total_prizes += period_prize
        
        period_profit = period_prize - actual_cost
        capital_history.append(capital)
        
        # 更新历史胜率
        if bet_periods > 0:
            historical_win_rate = win_periods / bet_periods
        
        # 记录本期结果
        period_results.append({
            'period': period_id,
            'action': 'bet',
            'confidence': confidence,
            'bet_count': actual_num_bets,
            'cost': actual_cost,
            'prize': period_prize,
            'profit': period_profit,
            'capital': capital,
            'actual_numbers': actual_numbers,
            'win_details': win_details
        })
        
        if total_periods % 50 == 0:
            print(f"  进度: {total_periods}/{test_periods} | "
                  f"资金: ¥{capital:,.0f} | "
                  f"投注: {bet_periods} | "
                  f"胜率: {historical_win_rate*100:.1f}%")
    
    print(f"\n[阶段2完成]")
    print(f"  最终资金: ¥{capital:,.2f}")
    print(f"  投注期数: {bet_periods}/{test_periods} ({bet_periods/test_periods*100:.1f}%)")
    print(f"  盈利期数: {win_periods}/{bet_periods} ({win_periods/bet_periods*100:.1f}%)" if bet_periods > 0 else "  盈利期数: 0")
    
    # ==================== 汇总结果 ====================
    final_capital = capital
    total_profit = final_capital - starting_capital
    roi = (total_profit / starting_capital) * 100 if starting_capital > 0 else 0
    
    # 计算最大回撤
    peak = starting_capital
    max_drawdown = 0
    for cap in capital_history:
        if cap > peak:
            peak = cap
        drawdown = (peak - cap) / peak if peak > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)
    
    summary = {
        'starting_capital': starting_capital,
        'final_capital': final_capital,
        'total_profit': total_profit,
        'roi_percentage': roi,
        'total_periods': total_periods,
        'bet_periods': bet_periods,
        'skip_periods': skip_periods,
        'win_periods': win_periods,
        'win_rate': win_periods / bet_periods if bet_periods > 0 else 0,
        'total_invested': total_invested,
        'total_prizes': total_prizes,
        'avg_bet_per_period': total_invested / bet_periods if bet_periods > 0 else 0,
        'avg_prize_per_win': total_prizes / win_periods if win_periods > 0 else 0,
        'max_drawdown': max_drawdown,
        'capital_history': capital_history
    }
    
    return {
        'summary': summary,
        'period_results': period_results
    }


# ==================== 主程序 ====================
def load_data(json_file: str, num_records: int = 1200):
    """加载彩票数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    recent_data = data['data'][-num_records:]
    sequences = np.array([item['numbers'] for item in recent_data])
    return sequences, recent_data


def main():
    print("正在加载数据和模型...")
    
    # 加载数据
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    sequences, raw_data = load_data(data_file, num_records=1200)
    
    # 加载模型
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = LotteryModel.load('models/checkpoints/best_model.pth', device=device)
    
    print(f"模型加载完成！设备: {device}")
    print(f"数据总量: {len(sequences)}期")
    print(f"回测期数: {TEST_PERIODS}")
    print(f"起始资金: ¥{STARTING_CAPITAL:,.0f}")
    print(f"投注策略: Top {CONFIDENCE_PERCENTILE*100:.0f}% 可信度期数")
    print(f"单期最大风险: {MAX_RISK_PER_PERIOD*100}%")
    
    # 运行回测
    results = dynamic_backtest(sequences, raw_data, model, STARTING_CAPITAL, TEST_PERIODS, window_size=30)
    
    # ==================== 打印结果 ====================
    summary = results['summary']
    
    print(f"\n{'='*80}")
    print(f"动态投注策略回测结果")
    print(f"{'='*80}\n")
    
    print(f"💰 资金情况:")
    print(f"   起始资金: ¥{summary['starting_capital']:,.0f}")
    print(f"   最终资金: ¥{summary['final_capital']:,.2f}")
    print(f"   总收益: ¥{summary['total_profit']:,.2f}")
    print(f"   ROI: {summary['roi_percentage']:.2f}%")
    print(f"   最大回撤: {summary['max_drawdown']*100:.2f}%\n")
    
    print(f"📊 投注统计:")
    print(f"   总期数: {summary['total_periods']}")
    print(f"   投注期数: {summary['bet_periods']} ({summary['bet_periods']/summary['total_periods']*100:.1f}%)")
    print(f"   跳过期数: {summary['skip_periods']} ({summary['skip_periods']/summary['total_periods']*100:.1f}%)")
    print(f"   盈利期数: {summary['win_periods']}")
    print(f"   胜率: {summary['win_rate']*100:.2f}%\n")
    
    print(f"💵 投入产出:")
    print(f"   总投入: ¥{summary['total_invested']:,.0f}")
    print(f"   总奖金: ¥{summary['total_prizes']:,.0f}")
    print(f"   平均每期投注: ¥{summary['avg_bet_per_period']:.0f}")
    print(f"   平均每次中奖: ¥{summary['avg_prize_per_win']:.0f}\n")
    
    # 保存详细结果
    output_data = {
        'summary': {k: float(v) if isinstance(v, (np.floating, np.integer)) else 
                   ([float(x) for x in v] if isinstance(v, list) else v)
                   for k, v in summary.items()},
        'period_results': [
            {k: (float(v) if isinstance(v, (np.floating, np.integer)) else 
                ([int(x) for x in v] if isinstance(v, list) and k == 'actual_numbers' else v))
             for k, v in period.items()}
            for period in results['period_results']
        ]
    }
    
    output_path = Path('results/dynamic_betting_results.json')
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 详细结果已保存到: {output_path}")
    
    return results


if __name__ == '__main__':
    results = main()
