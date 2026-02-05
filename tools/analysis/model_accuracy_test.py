#!/usr/bin/env python3
"""
模型准确率测试工具

评估 LSTM 模型的预测准确率：
1. Top5 命中率：预测的前5个数字中有多少个出现在开奖号码中
2. Top10 命中率：预测的前10个数字中有多少个出现在开奖号码中
3. 完全命中率：Top5 是否完全包含开奖的3个数字
4. 不同置信度阈值下的命中率表现
"""

import os
import sys
import django
import argparse
import numpy as np
import torch
from collections import defaultdict
from typing import Dict, List, Tuple

# Django setup
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottery_web.settings')
django.setup()

from lottery.models import LotteryPeriod

# 添加 src 目录到路径
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from models.lottery_model import LotteryModel


def load_model(model_path: str, device: str = 'cpu'):
    """加载训练好的模型"""
    model = LotteryModel.load(model_path, device=device)
    model.eval()
    return model


def prepare_sequence(periods: List[LotteryPeriod], window_size: int = 30) -> torch.Tensor:
    """准备输入序列"""
    sequence = []
    for period in periods[-window_size:]:
        numbers = period.numbers  # Use property
        sequence.append(numbers)
    
    # Padding if needed
    while len(sequence) < window_size:
        sequence.insert(0, [10, 10, 10])  # 10 is padding token
    
    return torch.LongTensor(sequence).unsqueeze(0)  # (1, seq_len, 3)


def get_top_predictions(model, input_seq: torch.Tensor, device: str, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    """
    获取模型预测的 Top-K 数字
    
    Returns:
        top_indices: Top-K 数字的索引 [0-9]
        top_probs: 对应的概率值
    """
    with torch.no_grad():
        input_seq = input_seq.to(device)
        outputs = model(input_seq)
        probs = outputs['digit_probs'].cpu().numpy()[0]  # (10,)
        
        top_indices = np.argsort(probs)[-top_k:][::-1]
        top_probs = probs[top_indices]
        
        return top_indices, top_probs


def calculate_hit_rate(predicted: np.ndarray, actual: List[int]) -> Dict[str, float]:
    """
    计算命中率
    
    Args:
        predicted: 预测的数字列表
        actual: 实际开奖的3个数字
    
    Returns:
        dict: 包含各种命中率指标
    """
    actual_set = set(actual)
    predicted_set = set(predicted)
    
    # 命中数字个数
    hits = len(actual_set & predicted_set)
    
    # 命中率 = 命中数字数 / 实际数字数 (3)
    hit_rate = hits / len(actual_set)
    
    # 是否完全命中（预测包含所有3个开奖数字）
    full_hit = (hits == 3)
    
    # 是否至少命中2个（组选可能中奖）
    partial_hit = (hits >= 2)
    
    return {
        'hits': hits,
        'hit_rate': hit_rate,
        'full_hit': full_hit,
        'partial_hit': partial_hit
    }


def test_model_accuracy(
    model_path: str,
    test_periods: int = 500,
    window_size: int = 30,
    device: str = 'cpu'
) -> Dict:
    """
    测试模型准确率
    
    Args:
        model_path: 模型路径
        test_periods: 测试期数
        window_size: 窗口大小
        device: 计算设备
    
    Returns:
        dict: 测试结果统计
    """
    print("=" * 80)
    print("模型准确率测试")
    print("=" * 80)
    print(f"模型路径: {model_path}")
    print(f"测试期数: {test_periods}")
    print(f"窗口大小: {window_size}")
    print(f"设备: {device}")
    print()
    
    # 加载模型
    print("加载模型...")
    model = load_model(model_path, device)
    
    # 加载数据
    print("加载历史数据...")
    all_periods = list(LotteryPeriod.objects.all().order_by('period'))
    total_periods = len(all_periods)
    
    if total_periods < window_size + test_periods:
        print(f"⚠️  警告: 数据不足，总期数 {total_periods}，需要至少 {window_size + test_periods}")
        test_periods = total_periods - window_size
    
    print(f"总期数: {total_periods}")
    print(f"实际测试期数: {test_periods}")
    print()
    
    # 初始化统计变量
    stats = {
        'top5': {'hits': [], 'hit_rates': [], 'full_hits': 0, 'partial_hits': 0},
        'top10': {'hits': [], 'hit_rates': [], 'full_hits': 0, 'partial_hits': 0},
        'top3': {'hits': [], 'hit_rates': [], 'full_hits': 0, 'partial_hits': 0},
    }
    
    # 按模型评分分组统计
    score_buckets = defaultdict(lambda: {
        'count': 0,
        'top5_hit_rate': [],
        'top10_hit_rate': [],
        'full_hits': 0
    })
    
    print("开始测试...")
    print("-" * 80)
    
    # 测试每一期
    for i in range(test_periods):
        test_idx = total_periods - test_periods + i
        
        # 准备输入
        history = all_periods[test_idx - window_size:test_idx]
        current = all_periods[test_idx]
        actual_numbers = current.numbers  # Use property
        
        # 预测
        input_seq = prepare_sequence(history, window_size)
        
        # Top3, Top5, Top10
        top10_indices, top10_probs = get_top_predictions(model, input_seq, device, top_k=10)
        top5_indices = top10_indices[:5]
        top3_indices = top10_indices[:3]
        
        # 计算命中率
        top5_result = calculate_hit_rate(top5_indices, actual_numbers)
        top10_result = calculate_hit_rate(top10_indices, actual_numbers)
        top3_result = calculate_hit_rate(top3_indices, actual_numbers)
        
        # 统计 Top5
        stats['top5']['hits'].append(top5_result['hits'])
        stats['top5']['hit_rates'].append(top5_result['hit_rate'])
        if top5_result['full_hit']:
            stats['top5']['full_hits'] += 1
        if top5_result['partial_hit']:
            stats['top5']['partial_hits'] += 1
        
        # 统计 Top10
        stats['top10']['hits'].append(top10_result['hits'])
        stats['top10']['hit_rates'].append(top10_result['hit_rate'])
        if top10_result['full_hit']:
            stats['top10']['full_hits'] += 1
        if top10_result['partial_hit']:
            stats['top10']['partial_hits'] += 1
        
        # 统计 Top3
        stats['top3']['hits'].append(top3_result['hits'])
        stats['top3']['hit_rates'].append(top3_result['hit_rate'])
        if top3_result['full_hit']:
            stats['top3']['full_hits'] += 1
        if top3_result['partial_hit']:
            stats['top3']['partial_hits'] += 1
        
        # 计算模型评分（基于概率）
        # 评分 = Top5 平均概率 * 100
        score = float(np.mean(top10_probs[:5]) * 100)
        score_bucket = int(score // 10) * 10  # 分组: 0-9, 10-19, ..., 90-99
        
        score_buckets[score_bucket]['count'] += 1
        score_buckets[score_bucket]['top5_hit_rate'].append(top5_result['hit_rate'])
        score_buckets[score_bucket]['top10_hit_rate'].append(top10_result['hit_rate'])
        if top5_result['full_hit']:
            score_buckets[score_bucket]['full_hits'] += 1
        
        # 每100期打印一次进度
        if (i + 1) % 100 == 0:
            print(f"已测试 {i + 1}/{test_periods} 期...")
    
    print("测试完成！")
    print()
    
    # 计算总体统计
    results = {
        'test_periods': test_periods,
        'top3': {
            'avg_hits': np.mean(stats['top3']['hits']),
            'avg_hit_rate': np.mean(stats['top3']['hit_rates']) * 100,
            'full_hit_rate': stats['top3']['full_hits'] / test_periods * 100,
            'partial_hit_rate': stats['top3']['partial_hits'] / test_periods * 100,
        },
        'top5': {
            'avg_hits': np.mean(stats['top5']['hits']),
            'avg_hit_rate': np.mean(stats['top5']['hit_rates']) * 100,
            'full_hit_rate': stats['top5']['full_hits'] / test_periods * 100,
            'partial_hit_rate': stats['top5']['partial_hits'] / test_periods * 100,
        },
        'top10': {
            'avg_hits': np.mean(stats['top10']['hits']),
            'avg_hit_rate': np.mean(stats['top10']['hit_rates']) * 100,
            'full_hit_rate': stats['top10']['full_hits'] / test_periods * 100,
            'partial_hit_rate': stats['top10']['partial_hits'] / test_periods * 100,
        },
        'score_buckets': score_buckets
    }
    
    return results


def print_results(results: Dict):
    """打印测试结果"""
    print("=" * 80)
    print("测试结果总结")
    print("=" * 80)
    print()
    
    print(f"📊 总测试期数: {results['test_periods']}")
    print()
    
    # Top3 结果
    print("🎯 Top3 预测准确率（最保守）")
    print(f"  平均命中数字数: {results['top3']['avg_hits']:.2f} / 3")
    print(f"  平均命中率: {results['top3']['avg_hit_rate']:.1f}%")
    print(f"  完全命中率（3个全中）: {results['top3']['full_hit_rate']:.1f}%")
    print(f"  至少2个命中: {results['top3']['partial_hit_rate']:.1f}%")
    print()
    
    # Top5 结果
    print("🎯 Top5 预测准确率（推荐）")
    print(f"  平均命中数字数: {results['top5']['avg_hits']:.2f} / 3")
    print(f"  平均命中率: {results['top5']['avg_hit_rate']:.1f}%")
    print(f"  完全命中率（3个全中）: {results['top5']['full_hit_rate']:.1f}%")
    print(f"  至少2个命中: {results['top5']['partial_hit_rate']:.1f}%")
    print()
    
    # Top10 结果
    print("🎯 Top10 预测准确率（最宽松）")
    print(f"  平均命中数字数: {results['top10']['avg_hits']:.2f} / 3")
    print(f"  平均命中率: {results['top10']['avg_hit_rate']:.1f}%")
    print(f"  完全命中率（3个全中）: {results['top10']['full_hit_rate']:.1f}%")
    print(f"  至少2个命中: {results['top10']['partial_hit_rate']:.1f}%")
    print()
    
    # 评分分组结果
    print("📈 不同模型评分区间的准确率表现")
    print("-" * 80)
    print(f"{'评分区间':<12} {'期数':<8} {'Top5命中率':<12} {'Top10命中率':<12} {'完全命中':<10}")
    print("-" * 80)
    
    for score in sorted(results['score_buckets'].keys()):
        bucket = results['score_buckets'][score]
        if bucket['count'] > 0:
            top5_rate = np.mean(bucket['top5_hit_rate']) * 100
            top10_rate = np.mean(bucket['top10_hit_rate']) * 100
            full_rate = bucket['full_hits'] / bucket['count'] * 100
            
            print(f"{score:>3}-{score+9:<5} {bucket['count']:>6}  "
                  f"{top5_rate:>10.1f}%  {top10_rate:>10.1f}%  {full_rate:>8.1f}%")
    
    print("-" * 80)
    print()
    
    # 关键指标评估
    print("=" * 80)
    print("💡 关键发现")
    print("=" * 80)
    
    top5_hit = results['top5']['avg_hit_rate']
    top5_full = results['top5']['full_hit_rate']
    top5_partial = results['top5']['partial_hit_rate']
    
    print()
    print("1. 模型预测能力评估:")
    if top5_hit >= 80:
        print(f"   ✅ 优秀！Top5 命中率 {top5_hit:.1f}% - 模型预测能力很强")
    elif top5_hit >= 60:
        print(f"   ✅ 良好！Top5 命中率 {top5_hit:.1f}% - 模型有一定预测能力")
    elif top5_hit >= 40:
        print(f"   ⚠️  一般。Top5 命中率 {top5_hit:.1f}% - 模型预测能力有限")
    else:
        print(f"   ❌ 较差。Top5 命中率 {top5_hit:.1f}% - 模型预测能力不足")
    
    print()
    print("2. 投注策略建议:")
    if top5_full >= 30:
        print(f"   ✅ 可以尝试投注！Top5 完全命中率 {top5_full:.1f}%")
        print(f"   💡 建议：基于 Top5 构建投注组合")
    elif top5_partial >= 40:
        print(f"   ⚠️  谨慎投注。至少2个命中率 {top5_partial:.1f}%")
        print(f"   💡 建议：仅在高置信度（评分>60）时投注")
    else:
        print(f"   ❌ 不建议投注。完全命中率仅 {top5_full:.1f}%")
        print(f"   💡 建议：继续优化模型或仅作分析工具")
    
    print()
    print("3. 置信度阈值建议:")
    
    # 找到命中率最高的评分区间
    best_score = None
    best_hit_rate = 0
    for score in sorted(results['score_buckets'].keys(), reverse=True):
        bucket = results['score_buckets'][score]
        if bucket['count'] >= 10:  # 至少10个样本
            hit_rate = np.mean(bucket['top5_hit_rate']) * 100
            if hit_rate > best_hit_rate:
                best_hit_rate = hit_rate
                best_score = score
    
    if best_score is not None and best_hit_rate >= 60:
        print(f"   ✅ 建议只在评分 >= {best_score} 时投注")
        print(f"   📊 该区间 Top5 命中率: {best_hit_rate:.1f}%")
    elif best_score is not None:
        print(f"   ⚠️  即使在最高评分区间（>={best_score}），命中率也只有 {best_hit_rate:.1f}%")
        print(f"   💡 建议：提高阈值或不投注")
    else:
        print(f"   ❌ 所有评分区间命中率都较低")
        print(f"   💡 建议：模型需要重新训练或调整架构")
    
    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='模型准确率测试工具')
    parser.add_argument('--model', type=str, 
                       default='models/saved_models/best_model.pth',
                       help='模型路径')
    parser.add_argument('--periods', type=int, default=500,
                       help='测试期数')
    parser.add_argument('--window', type=int, default=30,
                       help='窗口大小')
    parser.add_argument('--device', type=str, default='cpu',
                       choices=['cpu', 'cuda'],
                       help='计算设备')
    
    args = parser.parse_args()
    
    # 运行测试
    results = test_model_accuracy(
        model_path=args.model,
        test_periods=args.periods,
        window_size=args.window,
        device=args.device
    )
    
    # 打印结果
    print_results(results)


if __name__ == '__main__':
    main()
