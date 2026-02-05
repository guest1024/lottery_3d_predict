"""
识别"天赐良机" - 高胜率入场信号分析
=====================================

目标：
1. 找出历史上预测特别准确的时刻
2. 分析这些时刻的共同特征
3. 建立入场信号评分系统

核心思路：
不是简单地使用模型置信度分位数，而是分析预测成功时的特征模式
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

# ==================== 特征提取器 ====================
class OpportunityFeatureExtractor:
    """提取预测成功时的特征"""
    
    @staticmethod
    def extract_model_features(digit_probs: np.ndarray) -> Dict:
        """提取模型输出特征"""
        sorted_indices = np.argsort(digit_probs)[::-1]
        sorted_probs = digit_probs[sorted_indices]
        
        features = {
            # 概率分布特征
            'top1_prob': float(sorted_probs[0]),
            'top3_mean_prob': float(np.mean(sorted_probs[:3])),
            'top5_mean_prob': float(np.mean(sorted_probs[:5])),
            'top10_sum_prob': float(np.sum(sorted_probs)),
            
            # 概率差距特征
            'gap_1_2': float(sorted_probs[0] - sorted_probs[1]),
            'gap_2_3': float(sorted_probs[1] - sorted_probs[2]),
            'gap_3_4': float(sorted_probs[2] - sorted_probs[3]),
            
            # 分布形状特征
            'prob_std': float(np.std(digit_probs)),
            'prob_entropy': float(-np.sum(digit_probs * np.log(digit_probs + 1e-10))),
            'prob_gini': float(OpportunityFeatureExtractor._calculate_gini(digit_probs)),
            
            # Top数字集中度
            'top3_concentration': float(np.sum(sorted_probs[:3]) / np.sum(digit_probs)),
            'top5_concentration': float(np.sum(sorted_probs[:5]) / np.sum(digit_probs)),
        }
        
        return features
    
    @staticmethod
    def _calculate_gini(probs: np.ndarray) -> float:
        """计算基尼系数，衡量概率分布的不均匀程度"""
        sorted_probs = np.sort(probs)
        n = len(sorted_probs)
        cumsum = np.cumsum(sorted_probs)
        return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0
    
    @staticmethod
    def extract_sequence_features(history: np.ndarray) -> Dict:
        """提取历史序列特征"""
        # history: [window_size, 3]
        flat_history = history.flatten()
        
        # 数字频率统计
        digit_counts = Counter(flat_history)
        
        # 形态统计
        shape_counts = Counter()
        for numbers in history:
            shape = OpportunityFeatureExtractor._get_shape(numbers)
            shape_counts[shape] += 1
        
        # 和值统计
        sum_values = [np.sum(numbers) for numbers in history]
        
        # 趋势特征
        recent_5 = history[-5:]
        recent_10 = history[-10:]
        
        features = {
            # 数字分布
            'digit_freq_std': float(np.std(list(digit_counts.values()))),
            'digit_freq_max': int(max(digit_counts.values())),
            'digit_freq_min': int(min(digit_counts.values())),
            'unique_digits_count': len(digit_counts),
            
            # 形态分布
            'shape_group6_ratio': float(shape_counts['group6'] / len(history)),
            'shape_group3_ratio': float(shape_counts['group3'] / len(history)),
            'shape_leopard_ratio': float(shape_counts['leopard'] / len(history)),
            'shape_entropy': float(OpportunityFeatureExtractor._calculate_entropy(shape_counts)),
            
            # 和值统计
            'sum_mean': float(np.mean(sum_values)),
            'sum_std': float(np.std(sum_values)),
            'sum_trend': float(np.mean(sum_values[-5:]) - np.mean(sum_values[:5])),
            
            # 重复模式
            'recent_5_unique_count': len(set(map(tuple, recent_5))),
            'recent_10_unique_count': len(set(map(tuple, recent_10))),
            
            # 连续性
            'max_consecutive_shape': int(OpportunityFeatureExtractor._max_consecutive([
                OpportunityFeatureExtractor._get_shape(numbers) for numbers in history
            ])),
        }
        
        return features
    
    @staticmethod
    def _get_shape(numbers: np.ndarray) -> str:
        """获取号码形态"""
        counter = Counter(numbers)
        if len(counter) == 1:
            return 'leopard'
        elif len(counter) == 2:
            return 'group3'
        else:
            return 'group6'
    
    @staticmethod
    def _calculate_entropy(counter: Counter) -> float:
        """计算熵"""
        total = sum(counter.values())
        probs = [count / total for count in counter.values()]
        return -sum(p * np.log(p + 1e-10) for p in probs)
    
    @staticmethod
    def _max_consecutive(sequence: List) -> int:
        """计算最大连续相同元素数"""
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


# ==================== 机会识别器 ====================
def analyze_predictions(sequences: np.ndarray, raw_data: List[Dict],
                       model: LotteryModel, device,
                       test_periods: int = 500,
                       window_size: int = 30) -> Dict:
    """
    分析所有预测，识别成功和失败的模式
    """
    print("="*80)
    print("分析历史预测，识别高胜率模式")
    print("="*80)
    
    model.eval()
    extractor = OpportunityFeatureExtractor()
    
    # 存储所有预测记录
    all_records = []
    
    start_idx = len(sequences) - test_periods - window_size
    
    print(f"\n[1] 收集预测数据...")
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
        
        # 提取特征
        model_features = extractor.extract_model_features(digit_probs)
        sequence_features = extractor.extract_sequence_features(history)
        
        # Top数字
        top_indices = np.argsort(digit_probs)[::-1]
        top3_digits = set(top_indices[:3].tolist())
        top5_digits = set(top_indices[:5].tolist())
        top10_digits = set(top_indices[:10].tolist())
        
        # 检查预测准确性
        actual_set = set(actual_numbers.tolist())
        
        # 计算命中率
        hit_in_top3 = len(actual_set & top3_digits)
        hit_in_top5 = len(actual_set & top5_digits)
        hit_in_top10 = len(actual_set & top10_digits)
        
        # 判断是否完全命中（所有3个数字都在TopN中）
        full_hit_top3 = (hit_in_top3 == 3)
        full_hit_top5 = (hit_in_top5 == 3)
        full_hit_top10 = (hit_in_top10 == 3)
        
        # 记录
        record = {
            'period': period_data['period'],
            'date': period_data['date'],
            'actual_numbers': actual_numbers.tolist(),
            
            # 命中情况
            'hit_in_top3': hit_in_top3,
            'hit_in_top5': hit_in_top5,
            'hit_in_top10': hit_in_top10,
            'full_hit_top3': full_hit_top3,
            'full_hit_top5': full_hit_top5,
            'full_hit_top10': full_hit_top10,
            
            # 特征
            'model_features': model_features,
            'sequence_features': sequence_features,
            
            # 综合评分（稍后计算）
            'opportunity_score': 0.0
        }
        
        all_records.append(record)
        
        if (i + 1) % 100 == 0:
            print(f"  进度: {i+1}/{test_periods}")
    
    print(f"\n[2] 分析成功和失败的模式...")
    
    # 分类记录
    full_hit_records = [r for r in all_records if r['full_hit_top10']]
    partial_hit_records = [r for r in all_records if r['hit_in_top10'] > 0 and not r['full_hit_top10']]
    miss_records = [r for r in all_records if r['hit_in_top10'] == 0]
    
    print(f"\n预测结果分布:")
    print(f"  完全命中(Top10包含全部3个数字): {len(full_hit_records)}/{test_periods} ({len(full_hit_records)/test_periods*100:.1f}%)")
    print(f"  部分命中(Top10包含1-2个数字): {len(partial_hit_records)}/{test_periods} ({len(partial_hit_records)/test_periods*100:.1f}%)")
    print(f"  完全失误(Top10不包含任何数字): {len(miss_records)}/{test_periods} ({len(miss_records)/test_periods*100:.1f}%)")
    
    # 计算特征均值
    def calculate_feature_means(records: List[Dict]) -> Dict:
        """计算一组记录的特征均值"""
        if not records:
            return {}
        
        model_feat_sums = defaultdict(float)
        seq_feat_sums = defaultdict(float)
        
        for record in records:
            for key, value in record['model_features'].items():
                model_feat_sums[key] += value
            for key, value in record['sequence_features'].items():
                seq_feat_sums[key] += value
        
        n = len(records)
        return {
            'model': {k: v/n for k, v in model_feat_sums.items()},
            'sequence': {k: v/n for k, v in seq_feat_sums.items()}
        }
    
    full_hit_means = calculate_feature_means(full_hit_records)
    miss_means = calculate_feature_means(miss_records)
    
    print(f"\n[3] 关键特征对比（完全命中 vs 完全失误）:")
    
    if full_hit_means and miss_means:
        print(f"\n模型特征对比:")
        for key in full_hit_means['model'].keys():
            hit_val = full_hit_means['model'][key]
            miss_val = miss_means['model'][key]
            diff = hit_val - miss_val
            diff_pct = (diff / miss_val * 100) if miss_val != 0 else 0
            print(f"  {key:<25} | 命中: {hit_val:>8.4f} | 失误: {miss_val:>8.4f} | 差异: {diff:>+8.4f} ({diff_pct:>+6.1f}%)")
        
        print(f"\n序列特征对比:")
        for key in full_hit_means['sequence'].keys():
            hit_val = full_hit_means['sequence'][key]
            miss_val = miss_means['sequence'][key]
            diff = hit_val - miss_val
            diff_pct = (diff / miss_val * 100) if miss_val != 0 else 0
            print(f"  {key:<25} | 命中: {hit_val:>8.4f} | 失误: {miss_val:>8.4f} | 差异: {diff:>+8.4f} ({diff_pct:>+6.1f}%)")
    
    print(f"\n[4] 构建入场信号评分系统...")
    
    # 基于特征差异构建评分函数
    # 策略：使用显著区分命中和失误的特征
    feature_weights = {
        # 模型特征权重（基于经验调整）
        'top1_prob': 15,
        'top3_mean_prob': 15,
        'gap_1_2': 10,
        'prob_std': 10,
        'top3_concentration': 10,
        
        # 序列特征权重
        'digit_freq_std': 8,
        'shape_entropy': 7,
        'sum_std': 5,
        'recent_5_unique_count': 5,
        'max_consecutive_shape': 5,
    }
    
    # 计算每条记录的机会评分
    for record in all_records:
        score = 0.0
        
        # 模型特征评分
        for feat_key, weight in feature_weights.items():
            if feat_key in record['model_features']:
                value = record['model_features'][feat_key]
                # 归一化到0-1范围（简化处理）
                normalized_value = min(1.0, max(0.0, value / 0.3))  # 假设0.3是上限
                score += normalized_value * weight
            elif feat_key in record['sequence_features']:
                value = record['sequence_features'][feat_key]
                # 根据特征类型归一化
                if 'ratio' in feat_key or 'entropy' in feat_key:
                    normalized_value = min(1.0, max(0.0, value))
                elif 'std' in feat_key:
                    normalized_value = min(1.0, max(0.0, value / 5.0))
                elif 'count' in feat_key:
                    normalized_value = min(1.0, max(0.0, value / 10.0))
                else:
                    normalized_value = min(1.0, max(0.0, value / 3.0))
                score += normalized_value * weight
        
        record['opportunity_score'] = score
    
    # 按评分排序
    all_records_sorted = sorted(all_records, key=lambda x: x['opportunity_score'], reverse=True)
    
    # 分析评分分布
    scores = [r['opportunity_score'] for r in all_records]
    
    print(f"\n机会评分分布:")
    print(f"  最高分: {max(scores):.2f}")
    print(f"  平均分: {np.mean(scores):.2f}")
    print(f"  中位数: {np.median(scores):.2f}")
    print(f"  最低分: {min(scores):.2f}")
    
    # 评分分段分析
    percentiles = [90, 95, 99]
    for p in percentiles:
        threshold = np.percentile(scores, p)
        high_score_records = [r for r in all_records if r['opportunity_score'] >= threshold]
        high_score_hit_rate = sum(1 for r in high_score_records if r['full_hit_top10']) / len(high_score_records) if high_score_records else 0
        print(f"  Top{100-p}% (评分≥{threshold:.2f}): 命中率 {high_score_hit_rate*100:.1f}%")
    
    print(f"\n[5] 展示Top20高分案例...")
    print(f"\n{'期号':<12} {'日期':<12} {'实际号码':<15} {'Top10命中':<10} {'评分':<10}")
    print("-"*80)
    for i, record in enumerate(all_records_sorted[:20], 1):
        actual_str = str(record['actual_numbers'])
        hit_str = "✓" if record['full_hit_top10'] else f"{record['hit_in_top10']}/3"
        print(f"{record['period']:<12} {record['date']:<12} {actual_str:<15} {hit_str:<10} {record['opportunity_score']:<10.2f}")
    
    # 保存结果
    output = {
        'summary': {
            'total_periods': test_periods,
            'full_hit_count': len(full_hit_records),
            'partial_hit_count': len(partial_hit_records),
            'miss_count': len(miss_records),
            'full_hit_rate': len(full_hit_records) / test_periods,
        },
        'feature_analysis': {
            'full_hit_means': full_hit_means,
            'miss_means': miss_means,
        },
        'scoring_system': {
            'feature_weights': feature_weights,
            'score_distribution': {
                'max': float(max(scores)),
                'mean': float(np.mean(scores)),
                'median': float(np.median(scores)),
                'min': float(min(scores)),
                'percentile_90': float(np.percentile(scores, 90)),
                'percentile_95': float(np.percentile(scores, 95)),
                'percentile_99': float(np.percentile(scores, 99)),
            }
        },
        'top_opportunities': [
            {
                'period': r['period'],
                'date': r['date'],
                'actual_numbers': r['actual_numbers'],
                'opportunity_score': r['opportunity_score'],
                'full_hit_top10': r['full_hit_top10'],
                'hit_in_top10': r['hit_in_top10'],
            }
            for r in all_records_sorted[:50]
        ],
        'all_records': all_records  # 完整记录
    }
    
    return output


# ==================== 主程序 ====================
def load_data(json_file: str, num_records: int = 1500):
    """加载数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    recent_data = data['data'][-num_records:]
    sequences = np.array([item['numbers'] for item in recent_data])
    return sequences, recent_data


def main():
    print("\n加载数据和模型...")
    
    # 加载数据
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    sequences, raw_data = load_data(data_file, num_records=1500)
    
    # 加载模型
    device = torch.device('cpu')
    model = LotteryModel.load('models/checkpoints/best_model.pth', device=device)
    
    print(f"✓ 数据: {len(sequences)}期")
    print(f"✓ 模型已加载\n")
    
    # 分析预测
    results = analyze_predictions(
        sequences=sequences,
        raw_data=raw_data,
        model=model,
        device=device,
        test_periods=500,
        window_size=30
    )
    
    # 保存结果
    output_path = Path('results/golden_opportunities.json')
    output_path.parent.mkdir(exist_ok=True)
    
    # 为了节省空间，不保存all_records中的所有详细特征
    save_data = {
        'summary': results['summary'],
        'feature_analysis': results['feature_analysis'],
        'scoring_system': results['scoring_system'],
        'top_opportunities': results['top_opportunities'],
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 分析结果已保存到: {output_path}")
    
    return results


if __name__ == '__main__':
    results = main()
