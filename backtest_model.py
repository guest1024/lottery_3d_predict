"""
回测模型在历史数据上的准确率
使用滑动窗口方式进行walk-forward回测
"""
import sys
sys.path.insert(0, '/c1/program/lottery_3d_predict')

import json
import numpy as np
import torch
from collections import defaultdict
from pathlib import Path

from src.models.lottery_model import LotteryModel

def load_data(json_file, num_records=1200):
    """加载数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    recent_data = data['data'][-num_records:]
    sequences = np.array([item['numbers'] for item in recent_data])
    return sequences, recent_data

def predict_single(model, history_30, device='cpu'):
    """
    预测单期号码
    
    Args:
        model: 训练好的模型
        history_30: 最近30期历史数据 (30, 3)
        
    Returns:
        预测的数字概率分布和Top预测
    """
    input_seq = torch.LongTensor(history_30).unsqueeze(0).to(device)
    
    model.eval()
    with torch.no_grad():
        predictions = model.predict(input_seq)
        digit_probs = predictions['digit_probs'][0]
        
        # Top 5预测
        top5_digits = np.argsort(digit_probs)[-5:][::-1]
        
        return {
            'digit_probs': digit_probs,
            'top5': top5_digits,
            'top3': top5_digits[:3],
            'top1': top5_digits[0]
        }

def evaluate_prediction(pred, actual):
    """
    评估单次预测
    
    Args:
        pred: 预测结果
        actual: 实际号码 [d0, d1, d2]
        
    Returns:
        评估指标
    """
    metrics = {
        'exact_match': False,
        'position_match': [False, False, False],
        'any_digit_match': False,
        'top5_hit_count': 0,
        'top3_hit_count': 0,
        'top1_hit': False
    }
    
    # 完全匹配
    if np.array_equal(pred['top1'], actual):
        metrics['exact_match'] = True
    
    # 位置匹配 (检查Top5中是否包含该位置的数字)
    for i, digit in enumerate(actual):
        if digit in pred['top5']:
            metrics['position_match'][i] = True
    
    # 任意数字命中
    actual_set = set(actual)
    top5_set = set(pred['top5'])
    if actual_set & top5_set:
        metrics['any_digit_match'] = True
    
    # Top5命中数
    metrics['top5_hit_count'] = len(actual_set & top5_set)
    
    # Top3命中数
    top3_set = set(pred['top3'])
    metrics['top3_hit_count'] = len(actual_set & top3_set)
    
    # Top1命中
    if pred['top1'] in actual_set:
        metrics['top1_hit'] = True
    
    return metrics

def backtest_rolling(sequences, raw_data, model, window_size=30, test_periods=200, device='cpu'):
    """
    滚动窗口回测
    
    Args:
        sequences: 所有历史数据
        raw_data: 原始数据(包含期号)
        model: 训练好的模型
        window_size: 历史窗口大小
        test_periods: 回测期数
        
    Returns:
        回测结果统计
    """
    print(f"\n开始滚动窗口回测...")
    print(f"  窗口大小: {window_size}")
    print(f"  回测期数: {test_periods}")
    
    results = []
    aggregate_metrics = defaultdict(int)
    
    # 确保有足够的数据
    total_available = len(sequences) - window_size
    test_periods = min(test_periods, total_available)
    
    start_idx = len(sequences) - test_periods - window_size
    
    for i in range(test_periods):
        idx = start_idx + i
        
        # 获取历史30期
        history = sequences[idx:idx + window_size]
        
        # 实际号码
        actual = sequences[idx + window_size]
        actual_period = raw_data[idx + window_size]['period']
        
        # 预测
        pred = predict_single(model, history, device)
        
        # 评估
        metrics = evaluate_prediction(pred, actual)
        
        # 记录结果
        result = {
            'period': actual_period,
            'actual': actual.tolist(),
            'predicted_top5': pred['top5'].tolist(),
            'predicted_top3': pred['top3'].tolist(),
            'predicted_top1': int(pred['top1']),
            'metrics': metrics
        }
        results.append(result)
        
        # 累计统计
        aggregate_metrics['total'] += 1
        aggregate_metrics['exact_match'] += int(metrics['exact_match'])
        aggregate_metrics['any_digit_match'] += int(metrics['any_digit_match'])
        aggregate_metrics['top1_hit'] += int(metrics['top1_hit'])
        
        for pos in range(3):
            aggregate_metrics[f'position_{pos}_match'] += int(metrics['position_match'][pos])
        
        aggregate_metrics['top5_hit_total'] += metrics['top5_hit_count']
        aggregate_metrics['top3_hit_total'] += metrics['top3_hit_count']
        
        # 进度显示
        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{test_periods} ({(i+1)/test_periods*100:.1f}%)")
    
    print(f"  完成: {test_periods}/{test_periods} (100.0%)")
    
    # 计算统计指标
    n = aggregate_metrics['total']
    statistics = {
        'total_predictions': n,
        'exact_match_rate': aggregate_metrics['exact_match'] / n,
        'any_digit_match_rate': aggregate_metrics['any_digit_match'] / n,
        'top1_hit_rate': aggregate_metrics['top1_hit'] / n,
        'position_0_match_rate': aggregate_metrics['position_0_match'] / n,
        'position_1_match_rate': aggregate_metrics['position_1_match'] / n,
        'position_2_match_rate': aggregate_metrics['position_2_match'] / n,
        'avg_position_match_rate': (
            aggregate_metrics['position_0_match'] +
            aggregate_metrics['position_1_match'] +
            aggregate_metrics['position_2_match']
        ) / (n * 3),
        'avg_top5_hits': aggregate_metrics['top5_hit_total'] / n,
        'avg_top3_hits': aggregate_metrics['top3_hit_total'] / n,
    }
    
    return results, statistics

def analyze_by_time_period(results):
    """按时间段分析准确率"""
    # 分段统计
    segment_size = 50
    segments = []
    
    for i in range(0, len(results), segment_size):
        segment = results[i:i + segment_size]
        
        stats = {
            'start_period': segment[0]['period'],
            'end_period': segment[-1]['period'],
            'count': len(segment),
            'top1_hit_rate': sum(r['metrics']['top1_hit'] for r in segment) / len(segment),
            'avg_position_match': sum(
                sum(r['metrics']['position_match']) for r in segment
            ) / (len(segment) * 3),
            'any_digit_match_rate': sum(r['metrics']['any_digit_match'] for r in segment) / len(segment)
        }
        
        segments.append(stats)
    
    return segments

def analyze_by_digit_frequency(results, sequences):
    """分析不同数字的预测准确率"""
    digit_stats = defaultdict(lambda: {'predicted': 0, 'actual': 0, 'hit': 0})
    
    for result in results:
        actual_set = set(result['actual'])
        top5_set = set(result['predicted_top5'])
        
        # 统计预测
        for d in top5_set:
            digit_stats[d]['predicted'] += 1
            if d in actual_set:
                digit_stats[d]['hit'] += 1
        
        # 统计实际
        for d in actual_set:
            digit_stats[d]['actual'] += 1
    
    # 计算准确率
    digit_analysis = {}
    for digit in range(10):
        stats = digit_stats[digit]
        digit_analysis[digit] = {
            'predicted_count': stats['predicted'],
            'actual_count': stats['actual'],
            'hit_count': stats['hit'],
            'precision': stats['hit'] / stats['predicted'] if stats['predicted'] > 0 else 0,
            'recall': stats['hit'] / stats['actual'] if stats['actual'] > 0 else 0
        }
    
    return digit_analysis

def main():
    print("=" * 80)
    print("3D彩票预测模型回测系统")
    print("=" * 80)
    
    device = torch.device('cpu')
    
    # 1. 加载数据和模型
    print(f"\n[1] 加载数据和模型")
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    sequences, raw_data = load_data(data_file, num_records=1200)
    
    model = LotteryModel.load('models/checkpoints/best_model.pth', device=device)
    
    print(f"✓ 数据范围: {raw_data[0]['period']} 到 {raw_data[-1]['period']}")
    print(f"✓ 总记录数: {len(sequences)}")
    print(f"✓ 模型已加载")
    
    # 2. 执行回测
    print(f"\n[2] 执行滚动窗口回测")
    results, statistics = backtest_rolling(
        sequences=sequences,
        raw_data=raw_data,
        model=model,
        window_size=30,
        test_periods=200,  # 回测最近200期
        device=device
    )
    
    # 3. 显示整体统计
    print(f"\n[3] 整体回测统计")
    print(f"\n{'='*60}")
    print(f"总体性能指标 (回测{statistics['total_predictions']}期)")
    print(f"{'='*60}")
    
    print(f"\n核心指标:")
    print(f"  平均位置匹配率: {statistics['avg_position_match_rate']:.2%}")
    print(f"    - 位置0匹配率: {statistics['position_0_match_rate']:.2%}")
    print(f"    - 位置1匹配率: {statistics['position_1_match_rate']:.2%}")
    print(f"    - 位置2匹配率: {statistics['position_2_match_rate']:.2%}")
    
    print(f"\nTop预测性能:")
    print(f"  Top1命中率: {statistics['top1_hit_rate']:.2%}")
    print(f"  Top3平均命中数: {statistics['avg_top3_hits']:.2f}/3")
    print(f"  Top5平均命中数: {statistics['avg_top5_hits']:.2f}/3")
    print(f"  任意数字命中率: {statistics['any_digit_match_rate']:.2%}")
    
    print(f"\n完全匹配:")
    print(f"  完全匹配率: {statistics['exact_match_rate']:.2%}")
    
    # 4. 时间段分析
    print(f"\n[4] 时间段表现分析")
    segments = analyze_by_time_period(results)
    
    print(f"\n每50期统计:")
    print(f"{'时间段':<30} | {'Top1命中':<10} | {'位置匹配':<10} | {'任意命中':<10}")
    print(f"{'-'*70}")
    for seg in segments:
        period_range = f"{seg['start_period'][:10]} ~ {seg['end_period'][:10]}"
        print(f"{period_range:<30} | "
              f"{seg['top1_hit_rate']:>8.1%}  | "
              f"{seg['avg_position_match']:>8.1%}  | "
              f"{seg['any_digit_match_rate']:>8.1%}")
    
    # 5. 数字级别分析
    print(f"\n[5] 各数字预测表现")
    digit_analysis = analyze_by_digit_frequency(results, sequences)
    
    print(f"\n{'数字':<6} | {'预测次数':<10} | {'实际次数':<10} | {'命中次数':<10} | {'精确率':<10} | {'召回率':<10}")
    print(f"{'-'*75}")
    for digit in range(10):
        stats = digit_analysis[digit]
        print(f"{digit:<6} | "
              f"{stats['predicted_count']:>8}  | "
              f"{stats['actual_count']:>8}  | "
              f"{stats['hit_count']:>8}  | "
              f"{stats['precision']:>8.1%}  | "
              f"{stats['recall']:>8.1%}")
    
    # 6. 最近10期详细结果
    print(f"\n[6] 最近10期预测详情")
    print(f"\n{'期号':<15} | {'实际号码':<12} | {'Top5预测':<20} | {'命中情况':<15}")
    print(f"{'-'*70}")
    for result in results[-10:]:
        actual_str = ' '.join(map(str, result['actual']))
        top5_str = ' '.join(map(str, result['predicted_top5']))
        
        # 标记命中
        hit_marks = []
        actual_set = set(result['actual'])
        for d in result['predicted_top5']:
            hit_marks.append('✓' if d in actual_set else '✗')
        hit_str = ' '.join(hit_marks)
        
        print(f"{result['period']:<15} | "
              f"{actual_str:<12} | "
              f"{top5_str:<20} | "
              f"{hit_str:<15}")
    
    # 7. 保存回测结果
    print(f"\n[7] 保存回测结果")
    
    backtest_report = {
        'summary': {
            'total_predictions': statistics['total_predictions'],
            'data_range': {
                'start': raw_data[-statistics['total_predictions']]['period'],
                'end': raw_data[-1]['period']
            },
            'overall_statistics': {
                'avg_position_match_rate': float(statistics['avg_position_match_rate']),
                'position_0_match_rate': float(statistics['position_0_match_rate']),
                'position_1_match_rate': float(statistics['position_1_match_rate']),
                'position_2_match_rate': float(statistics['position_2_match_rate']),
                'top1_hit_rate': float(statistics['top1_hit_rate']),
                'top3_avg_hits': float(statistics['avg_top3_hits']),
                'top5_avg_hits': float(statistics['avg_top5_hits']),
                'any_digit_match_rate': float(statistics['any_digit_match_rate']),
                'exact_match_rate': float(statistics['exact_match_rate'])
            }
        },
        'time_segments': [
            {
                'start_period': seg['start_period'],
                'end_period': seg['end_period'],
                'count': seg['count'],
                'top1_hit_rate': float(seg['top1_hit_rate']),
                'avg_position_match': float(seg['avg_position_match']),
                'any_digit_match_rate': float(seg['any_digit_match_rate'])
            }
            for seg in segments
        ],
        'digit_analysis': {
            str(d): {
                'predicted_count': stats['predicted_count'],
                'actual_count': stats['actual_count'],
                'hit_count': stats['hit_count'],
                'precision': float(stats['precision']),
                'recall': float(stats['recall'])
            }
            for d, stats in digit_analysis.items()
        },
        'recent_10_predictions': [
            {
                'period': r['period'],
                'actual': r['actual'],
                'predicted_top5': r['predicted_top5'],
                'predicted_top3': r['predicted_top3'],
                'top5_hit_count': r['metrics']['top5_hit_count'],
                'position_match': r['metrics']['position_match']
            }
            for r in results[-10:]
        ]
    }
    
    output_file = 'results/backtest_results.json'
    Path('results').mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(backtest_report, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 回测结果已保存到: {output_file}")
    
    # 8. 性能总结
    print(f"\n{'='*80}")
    print("回测性能总结")
    print(f"{'='*80}")
    
    print(f"\n✅ 优势:")
    if statistics['avg_position_match_rate'] > 0.25:
        print(f"  - 位置匹配率{statistics['avg_position_match_rate']:.1%}显著高于随机水平(10%)")
    if statistics['avg_top5_hits'] > 1.0:
        print(f"  - Top5平均命中{statistics['avg_top5_hits']:.2f}个数字,表现良好")
    if statistics['any_digit_match_rate'] > 0.80:
        print(f"  - {statistics['any_digit_match_rate']:.1%}的期数至少命中一个数字")
    
    print(f"\n⚠️  局限:")
    if statistics['exact_match_rate'] < 0.01:
        print(f"  - 完全匹配率{statistics['exact_match_rate']:.2%},精确预测仍然极其困难")
    if statistics['top1_hit_rate'] < 0.40:
        print(f"  - Top1命中率{statistics['top1_hit_rate']:.1%},单一预测准确性有限")
    
    print(f"\n💡 建议:")
    print(f"  - 使用Top5预测作为候选池,而非单一号码")
    print(f"  - 结合历史统计和模型预测综合决策")
    print(f"  - 模型适合辅助分析,不能保证盈利")
    print(f"  - 理性购彩,娱乐为主")
    
    print("\n" + "=" * 80)
    print("回测完成!")
    print("=" * 80)

if __name__ == '__main__':
    main()
