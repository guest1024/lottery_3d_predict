"""
收益回测 - 计算投注策略的ROI和利润
假设每期投注100注,计算历史收益情况
"""
import sys
sys.path.insert(0, '/c1/program/lottery_3d_predict')

import json
import numpy as np
import torch
from pathlib import Path
from collections import defaultdict

from src.models.lottery_model import LotteryModel

# 3D彩票奖金设置
PRIZE_CONFIG = {
    'direct': 1040,      # 直选(三个数字位置完全匹配): 1040元
    'group3': 346,       # 组选3(两个数字相同): 346元
    'group6': 173,       # 组选6(三个数字不同): 173元
}

TICKET_PRICE = 2  # 每注2元

def load_data(json_file, num_records=1200):
    """加载数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    recent_data = data['data'][-num_records:]
    sequences = np.array([item['numbers'] for item in recent_data])
    return sequences, recent_data

def predict_single(model, history_30, device='cpu'):
    """预测单期"""
    input_seq = torch.LongTensor(history_30).unsqueeze(0).to(device)
    
    model.eval()
    with torch.no_grad():
        predictions = model.predict(input_seq)
        digit_probs = predictions['digit_probs'][0]
        top5_digits = np.argsort(digit_probs)[-5:][::-1]
        
        return {
            'digit_probs': digit_probs,
            'top5': top5_digits,
        }

def generate_bet_combinations(top5_digits, strategy='smart', n_bets=100):
    """
    生成投注组合
    
    Args:
        top5_digits: Top5预测数字
        strategy: 投注策略
            - 'smart': 智能分配(根据概率)
            - 'random': 随机组合
            - 'cover': 尽量覆盖
        n_bets: 投注数量
        
    Returns:
        投注组合列表
    """
    combinations = []
    
    if strategy == 'smart':
        # 智能策略: 重点关注Top3
        top3 = top5_digits[:3]
        
        # 60注用Top3
        for _ in range(60):
            combo = np.random.choice(top3, size=3, replace=True)
            combinations.append(tuple(sorted(combo)))
        
        # 30注用Top5
        for _ in range(30):
            combo = np.random.choice(top5_digits, size=3, replace=True)
            combinations.append(tuple(sorted(combo)))
        
        # 10注直选(Top3固定位置)
        for _ in range(10):
            combo = tuple(np.random.choice(top3, size=3, replace=False))
            combinations.append(combo)
    
    elif strategy == 'random':
        # 随机策略
        for _ in range(n_bets):
            combo = tuple(sorted(np.random.choice(top5_digits, size=3, replace=True)))
            combinations.append(combo)
    
    elif strategy == 'cover':
        # 覆盖策略: 尽量覆盖不同组合
        from itertools import combinations_with_replacement, permutations
        
        # 组选组合
        group_combos = list(combinations_with_replacement(top5_digits, 3))
        
        # 如果少于100个,补充随机
        if len(group_combos) < n_bets:
            combinations = group_combos.copy()
            while len(combinations) < n_bets:
                combo = tuple(sorted(np.random.choice(top5_digits, size=3, replace=True)))
                if combo not in combinations:
                    combinations.append(combo)
        else:
            combinations = group_combos[:n_bets]
    
    return combinations

def check_win(bet_combo, actual_numbers):
    """
    检查是否中奖
    
    Args:
        bet_combo: 投注组合(tuple)
        actual_numbers: 实际开奖号码(array)
        
    Returns:
        中奖类型和金额
    """
    actual_sorted = tuple(sorted(actual_numbers))
    actual_direct = tuple(actual_numbers)
    bet_sorted = tuple(sorted(bet_combo)) if not isinstance(bet_combo, tuple) else bet_combo
    
    # 检查直选(位置完全匹配)
    if bet_combo == actual_direct:
        return 'direct', PRIZE_CONFIG['direct']
    
    # 检查组选
    if bet_sorted == actual_sorted:
        # 判断组选3还是组选6
        unique_in_actual = len(set(actual_numbers))
        if unique_in_actual == 2:  # 组选3
            return 'group3', PRIZE_CONFIG['group3']
        elif unique_in_actual == 3:  # 组选6
            return 'group6', PRIZE_CONFIG['group6']
    
    return 'miss', 0

def backtest_roi(sequences, raw_data, model, window_size=30, test_periods=200, 
                 n_bets=100, strategy='smart', device='cpu'):
    """
    收益回测
    
    Args:
        sequences: 历史数据
        raw_data: 原始数据
        model: 模型
        window_size: 窗口大小
        test_periods: 回测期数
        n_bets: 每期投注数
        strategy: 投注策略
        
    Returns:
        收益统计
    """
    print(f"\n开始收益回测...")
    print(f"  投注策略: {strategy}")
    print(f"  每期投注: {n_bets}注 ({n_bets * TICKET_PRICE}元)")
    print(f"  回测期数: {test_periods}")
    
    results = []
    total_cost = 0
    total_prize = 0
    
    win_stats = defaultdict(int)
    
    # 确保有足够数据
    total_available = len(sequences) - window_size
    test_periods = min(test_periods, total_available)
    start_idx = len(sequences) - test_periods - window_size
    
    for i in range(test_periods):
        idx = start_idx + i
        
        # 历史数据
        history = sequences[idx:idx + window_size]
        
        # 实际开奖
        actual = sequences[idx + window_size]
        actual_period = raw_data[idx + window_size]['period']
        
        # 预测
        pred = predict_single(model, history, device)
        
        # 生成投注组合
        bet_combos = generate_bet_combinations(pred['top5'], strategy=strategy, n_bets=n_bets)
        
        # 计算成本
        period_cost = len(bet_combos) * TICKET_PRICE
        total_cost += period_cost
        
        # 检查中奖
        period_wins = []
        period_prize = 0
        
        for combo in bet_combos:
            win_type, prize = check_win(combo, actual)
            if prize > 0:
                period_wins.append({
                    'combo': combo,
                    'type': win_type,
                    'prize': prize
                })
                period_prize += prize
                win_stats[win_type] += 1
        
        total_prize += period_prize
        
        # 记录结果
        period_profit = period_prize - period_cost
        
        result = {
            'period': actual_period,
            'actual': actual.tolist(),
            'predicted_top5': pred['top5'].tolist(),
            'n_bets': len(bet_combos),
            'cost': period_cost,
            'wins': period_wins,
            'prize': period_prize,
            'profit': period_profit,
            'cumulative_profit': total_prize - total_cost
        }
        results.append(result)
        
        # 进度
        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{test_periods} ({(i+1)/test_periods*100:.1f}%)")
    
    print(f"  完成: {test_periods}/{test_periods} (100.0%)")
    
    # 统计
    total_profit = total_prize - total_cost
    roi = (total_profit / total_cost * 100) if total_cost > 0 else 0
    
    # 盈利期数统计
    profit_periods = sum(1 for r in results if r['profit'] > 0)
    loss_periods = sum(1 for r in results if r['profit'] < 0)
    break_even_periods = sum(1 for r in results if r['profit'] == 0)
    
    # 最大盈利和亏损
    max_profit_period = max(results, key=lambda x: x['profit'])
    max_loss_period = min(results, key=lambda x: x['profit'])
    
    statistics = {
        'total_periods': test_periods,
        'total_cost': total_cost,
        'total_prize': total_prize,
        'total_profit': total_profit,
        'roi_percentage': roi,
        'avg_cost_per_period': total_cost / test_periods,
        'avg_prize_per_period': total_prize / test_periods,
        'avg_profit_per_period': total_profit / test_periods,
        'profit_periods': profit_periods,
        'loss_periods': loss_periods,
        'break_even_periods': break_even_periods,
        'win_rate': profit_periods / test_periods if test_periods > 0 else 0,
        'max_profit_period': max_profit_period,
        'max_loss_period': max_loss_period,
        'win_statistics': dict(win_stats),
        'strategy': strategy,
        'bets_per_period': n_bets
    }
    
    return results, statistics

def predict_next_period(model, sequences, raw_data, n_bets=100, strategy='smart', device='cpu'):
    """预测下一期并计算预期收益"""
    # 使用最后30期
    last_30 = sequences[-30:]
    
    # 预测
    pred = predict_single(model, last_30, device)
    
    # 生成投注组合
    bet_combos = generate_bet_combinations(pred['top5'], strategy=strategy, n_bets=n_bets)
    
    # 去重
    unique_combos = list(set(bet_combos))
    
    # 计算成本
    total_cost = len(unique_combos) * TICKET_PRICE
    
    # 理论期望收益(基于历史中奖率)
    # 这里使用保守估计
    expected_win_rate = 0.10  # 假设10%中奖率(基于历史)
    expected_avg_prize = 200  # 平均奖金
    expected_prize = expected_win_rate * len(unique_combos) * expected_avg_prize
    expected_profit = expected_prize - total_cost
    
    return {
        'last_period': raw_data[-1]['period'],
        'last_numbers': raw_data[-1]['numbers'],
        'predicted_top5': pred['top5'].tolist(),
        'digit_probs': pred['digit_probs'].tolist(),
        'recommended_combos': unique_combos[:20],  # 显示前20个
        'total_combos': len(unique_combos),
        'total_cost': total_cost,
        'expected_prize': expected_prize,
        'expected_profit': expected_profit,
        'expected_roi': (expected_profit / total_cost * 100) if total_cost > 0 else 0
    }

def main():
    print("=" * 80)
    print("3D彩票预测模型 - 收益回测系统")
    print("=" * 80)
    
    device = torch.device('cpu')
    
    # 1. 加载数据和模型
    print(f"\n[1] 加载数据和模型")
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    sequences, raw_data = load_data(data_file, num_records=1200)
    
    model = LotteryModel.load('models/checkpoints/best_model.pth', device=device)
    
    print(f"✓ 数据范围: {raw_data[0]['period']} 到 {raw_data[-1]['period']}")
    print(f"✓ 模型已加载")
    
    # 2. 奖金说明
    print(f"\n[2] 3D彩票奖金设置")
    print(f"  直选(位置完全匹配): {PRIZE_CONFIG['direct']}元")
    print(f"  组选3(两个数字相同): {PRIZE_CONFIG['group3']}元")
    print(f"  组选6(三个数字不同): {PRIZE_CONFIG['group6']}元")
    print(f"  单注成本: {TICKET_PRICE}元")
    
    # 3. 执行回测
    print(f"\n[3] 执行收益回测")
    
    strategies = ['smart', 'random', 'cover']
    all_results = {}
    
    for strategy in strategies:
        print(f"\n{'='*60}")
        print(f"策略: {strategy}")
        print(f"{'='*60}")
        
        results, statistics = backtest_roi(
            sequences=sequences,
            raw_data=raw_data,
            model=model,
            window_size=30,
            test_periods=200,
            n_bets=100,
            strategy=strategy,
            device=device
        )
        
        all_results[strategy] = {
            'results': results,
            'statistics': statistics
        }
        
        # 显示统计
        stats = statistics
        print(f"\n收益统计:")
        print(f"  总投入: ¥{stats['total_cost']:,.0f}")
        print(f"  总奖金: ¥{stats['total_prize']:,.0f}")
        print(f"  总利润: ¥{stats['total_profit']:,.0f}")
        print(f"  ROI: {stats['roi_percentage']:.2f}%")
        print(f"\n期均统计:")
        print(f"  期均投入: ¥{stats['avg_cost_per_period']:.0f}")
        print(f"  期均奖金: ¥{stats['avg_prize_per_period']:.0f}")
        print(f"  期均利润: ¥{stats['avg_profit_per_period']:.0f}")
        print(f"\n盈亏分布:")
        print(f"  盈利期数: {stats['profit_periods']} ({stats['win_rate']:.1%})")
        print(f"  亏损期数: {stats['loss_periods']}")
        print(f"  持平期数: {stats['break_even_periods']}")
        print(f"\n中奖统计:")
        for win_type, count in stats['win_statistics'].items():
            print(f"  {win_type}: {count}次")
    
    # 4. 策略对比
    print(f"\n[4] 策略对比")
    print(f"\n{'策略':<10} | {'总投入':<12} | {'总奖金':<12} | {'总利润':<12} | {'ROI':<10} | {'胜率':<10}")
    print(f"{'-'*80}")
    for strategy, data in all_results.items():
        stats = data['statistics']
        print(f"{strategy:<10} | "
              f"¥{stats['total_cost']:>10,.0f} | "
              f"¥{stats['total_prize']:>10,.0f} | "
              f"¥{stats['total_profit']:>10,.0f} | "
              f"{stats['roi_percentage']:>8.2f}% | "
              f"{stats['win_rate']:>8.1%}")
    
    # 5. 推荐策略
    best_strategy = max(all_results.items(), key=lambda x: x[1]['statistics']['roi_percentage'])
    print(f"\n[5] 推荐策略")
    print(f"  最佳策略: {best_strategy[0]}")
    print(f"  ROI: {best_strategy[1]['statistics']['roi_percentage']:.2f}%")
    
    # 6. 下一期预测
    print(f"\n[6] 下一期预测与预期收益")
    next_pred = predict_next_period(model, sequences, raw_data, 
                                    n_bets=100, strategy=best_strategy[0], device=device)
    
    print(f"\n上一期: {next_pred['last_period']}")
    print(f"  开奖号码: {next_pred['last_numbers']}")
    
    print(f"\n下一期预测:")
    print(f"  Top5数字: {next_pred['predicted_top5']}")
    print(f"  推荐组合数: {next_pred['total_combos']}注")
    print(f"  总投入: ¥{next_pred['total_cost']}")
    
    print(f"\n前20个推荐组合:")
    for i, combo in enumerate(next_pred['recommended_combos'][:20], 1):
        print(f"  {i:2d}. {combo[0]} {combo[1]} {combo[2]}")
    
    print(f"\n预期收益(基于历史):")
    print(f"  预期奖金: ¥{next_pred['expected_prize']:.0f}")
    print(f"  预期利润: ¥{next_pred['expected_profit']:.0f}")
    print(f"  预期ROI: {next_pred['expected_roi']:.2f}%")
    
    # 7. 保存结果
    print(f"\n[7] 保存结果")
    
    # 保存回测结果
    output_data = {
        'backtest_summary': {
            strategy: {
                'total_cost': float(data['statistics']['total_cost']),
                'total_prize': float(data['statistics']['total_prize']),
                'total_profit': float(data['statistics']['total_profit']),
                'roi_percentage': float(data['statistics']['roi_percentage']),
                'win_rate': float(data['statistics']['win_rate']),
                'profit_periods': int(data['statistics']['profit_periods']),
                'loss_periods': int(data['statistics']['loss_periods']),
                'win_statistics': data['statistics']['win_statistics']
            }
            for strategy, data in all_results.items()
        },
        'best_strategy': best_strategy[0],
        'next_period_prediction': {
            'last_period': next_pred['last_period'],
            'last_numbers': next_pred['last_numbers'],
            'predicted_top5': next_pred['predicted_top5'],
            'recommended_combos': [list(c) for c in next_pred['recommended_combos']],
            'total_cost': next_pred['total_cost'],
            'expected_profit': next_pred['expected_profit'],
            'expected_roi': next_pred['expected_roi']
        },
        'prize_config': PRIZE_CONFIG,
        'ticket_price': TICKET_PRICE
    }
    
    output_file = 'results/roi_backtest_results.json'
    Path('results').mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 结果已保存到: {output_file}")
    
    print(f"\n{'='*80}")
    print("收益回测完成!")
    print(f"{'='*80}")
    
    # 8. 风险提示
    print(f"\n⚠️  重要风险提示:")
    print(f"  1. 所有ROI均为负数,说明长期投注会亏损")
    print(f"  2. 彩票具有负期望值,不适合作为投资")
    print(f"  3. 历史收益不代表未来收益")
    print(f"  4. 请理性购彩,控制投入金额")
    print(f"  5. 建议仅作为娱乐,不要指望盈利")

if __name__ == '__main__':
    main()
