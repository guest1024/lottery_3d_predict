"""
详细分析模型预测效果
"""
import sys
sys.path.insert(0, '/c1/program/lottery_3d_predict')

import json
import numpy as np
import torch
from collections import Counter

from src.models.lottery_model import LotteryModel

def load_data(json_file, num_records=1200):
    """加载数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    recent_data = data['data'][-num_records:]
    sequences = np.array([item['numbers'] for item in recent_data])
    return sequences, recent_data

def analyze_recent_patterns(sequences, n=30):
    """分析最近N期的模式"""
    recent = sequences[-n:]
    
    # 统计每个数字出现频率
    all_nums = recent.flatten()
    freq = Counter(all_nums)
    
    # 统计每个位置的数字频率
    pos_freq = [Counter(recent[:, i]) for i in range(3)]
    
    # 和值分布
    sums = recent.sum(axis=1)
    sum_freq = Counter(sums)
    
    return {
        'overall_freq': dict(freq),
        'position_freq': [dict(f) for f in pos_freq],
        'sum_freq': dict(sum_freq),
        'recent_numbers': recent.tolist()
    }

def predict_with_model(model, sequences, device='cpu'):
    """使用模型进行预测"""
    last_30 = torch.LongTensor(sequences[-30:]).unsqueeze(0).to(device)
    
    model.eval()
    with torch.no_grad():
        predictions = model.predict(last_30)
        
        digit_probs = predictions['digit_probs'][0]
        shape_probs = predictions['shape_probs'][0]
        sum_probs = predictions['sum_probs'][0]
        
        # 获取Top预测
        top5_digits = np.argsort(digit_probs)[-5:][::-1]
        top_shape = np.argmax(shape_probs)
        top_sum = np.argmax(sum_probs)
        
        return {
            'digit_probs': digit_probs,
            'top5_digits': top5_digits,
            'top5_probs': [digit_probs[i] for i in top5_digits],
            'shape_pred': ['组六', '组三', '豹子'][top_shape],
            'shape_probs': shape_probs,
            'sum_pred': top_sum,
            'sum_probs': sum_probs
        }

def generate_recommendations(predictions, n=10):
    """基于预测生成推荐号码"""
    top5 = predictions['top5_digits']
    recommendations = []
    
    # 策略1: 使用Top 5随机组合
    for i in range(n):
        combo = np.random.choice(top5, size=3, replace=True)
        combo_sorted = tuple(sorted(combo))
        if combo_sorted not in [tuple(sorted(r)) for r in recommendations]:
            recommendations.append(combo.tolist())
    
    # 策略2: 考虑形态
    shape = predictions['shape_pred']
    if shape == '豹子':
        # 生成豹子号码
        for d in top5[:3]:
            recommendations.append([int(d), int(d), int(d)])
    elif shape == '组三':
        # 生成组三号码
        for i, d1 in enumerate(top5[:2]):
            for d2 in top5[i+1:i+3]:
                recommendations.append([int(d1), int(d1), int(d2)])
                recommendations.append([int(d1), int(d2), int(d2)])
    
    # 去重并限制数量
    unique_recs = []
    seen = set()
    for rec in recommendations:
        key = tuple(sorted(rec))
        if key not in seen and len(unique_recs) < 10:
            seen.add(key)
            unique_recs.append(rec)
    
    return unique_recs[:10]

def main():
    print("=" * 80)
    print("3D彩票预测详细分析")
    print("=" * 80)
    
    device = torch.device('cpu')
    
    # 1. 加载数据
    print(f"\n[1] 加载数据和模型")
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    sequences, raw_data = load_data(data_file, num_records=1200)
    
    # 加载模型
    model = LotteryModel.load('models/checkpoints/best_model.pth', device=device)
    print(f"✓ 数据范围: {raw_data[0]['period']} 到 {raw_data[-1]['period']}")
    print(f"✓ 模型已加载")
    
    # 2. 分析最近30期模式
    print(f"\n[2] 分析最近30期历史模式")
    patterns = analyze_recent_patterns(sequences, n=30)
    
    print(f"\n整体数字出现频率 (Top 5):")
    sorted_freq = sorted(patterns['overall_freq'].items(), key=lambda x: x[1], reverse=True)
    for num, freq in sorted_freq[:5]:
        print(f"  数字 {num}: {freq}次 ({freq/90*100:.1f}%)")
    
    print(f"\n各位置数字频率 (Top 3):")
    for pos, pos_name in enumerate(['百位', '十位', '个位']):
        sorted_pos = sorted(patterns['position_freq'][pos].items(), key=lambda x: x[1], reverse=True)
        print(f"  {pos_name}:")
        for num, freq in sorted_pos[:3]:
            print(f"    数字 {num}: {freq}次 ({freq/30*100:.1f}%)")
    
    print(f"\n和值分布 (Top 5):")
    sorted_sum = sorted(patterns['sum_freq'].items(), key=lambda x: x[1], reverse=True)
    for s, freq in sorted_sum[:5]:
        print(f"  和值 {s}: {freq}次")
    
    # 3. 模型预测
    print(f"\n[3] 模型预测分析")
    predictions = predict_with_model(model, sequences, device)
    
    print(f"\n数字预测 (Top 5):")
    for i, (num, prob) in enumerate(zip(predictions['top5_digits'], predictions['top5_probs']), 1):
        print(f"  {i}. 数字 {num}: {prob:.2%}")
    
    print(f"\n形态预测:")
    shape_names = ['组六', '组三', '豹子']
    for name, prob in zip(shape_names, predictions['shape_probs']):
        print(f"  {name}: {prob:.2%}")
    
    print(f"\n和值预测 (Top 5):")
    top5_sums = np.argsort(predictions['sum_probs'])[-5:][::-1]
    for s in top5_sums:
        print(f"  和值 {s}: {predictions['sum_probs'][s]:.2%}")
    
    # 4. 生成推荐号码
    print(f"\n[4] 推荐号码组合 (Top 10)")
    recommendations = generate_recommendations(predictions, n=10)
    
    print(f"\n基于模型预测的推荐号码:")
    for i, combo in enumerate(recommendations, 1):
        combo_sum = sum(combo)
        # 判断形态
        unique = len(set(combo))
        if unique == 1:
            shape = '豹子'
        elif unique == 2:
            shape = '组三'
        else:
            shape = '组六'
        print(f"  {i:2d}. {combo[0]} {combo[1]} {combo[2]}  (和值:{combo_sum:2d}, 形态:{shape})")
    
    # 5. 最近5期实际开奖
    print(f"\n[5] 最近5期实际开奖号码")
    for i in range(5, 0, -1):
        item = raw_data[-i]
        nums = item['numbers']
        s = sum(nums)
        print(f"  {item['period']}: {nums[0]} {nums[1]} {nums[2]}  (和值:{s})")
    
    # 6. 对比分析
    print(f"\n[6] 预测与历史对比")
    
    # 最近5期出现的数字
    recent_5 = sequences[-5:].flatten()
    recent_5_freq = Counter(recent_5)
    
    print(f"\n最近5期高频数字:")
    for num, freq in sorted(recent_5_freq.items(), key=lambda x: x[1], reverse=True)[:5]:
        in_pred = "✓" if num in predictions['top5_digits'] else "✗"
        print(f"  数字 {num}: {freq}次 {in_pred}")
    
    print(f"\n模型Top5预测:")
    for num in predictions['top5_digits']:
        recent_count = recent_5_freq.get(num, 0)
        print(f"  数字 {num}: 最近5期出现{recent_count}次")
    
    # 7. 保存详细分析
    # 转换所有numpy类型为Python原生类型
    patterns_clean = {
        'overall_freq': {int(k): int(v) for k, v in patterns['overall_freq'].items()},
        'position_freq': [{int(k): int(v) for k, v in pf.items()} for pf in patterns['position_freq']],
        'sum_freq': {int(k): int(v) for k, v in patterns['sum_freq'].items()},
        'recent_numbers': patterns['recent_numbers']
    }
    
    analysis = {
        'timestamp': raw_data[-1]['period'],
        'historical_analysis': patterns_clean,
        'model_predictions': {
            'top5_digits': [int(x) for x in predictions['top5_digits']],
            'top5_probs': [float(p) for p in predictions['top5_probs']],
            'shape_prediction': predictions['shape_pred'],
            'sum_prediction': int(predictions['sum_pred'])
        },
        'recommendations': recommendations,
        'recent_5_periods': [
            {
                'period': raw_data[-i]['period'],
                'numbers': raw_data[-i]['numbers'],
                'sum': int(sum(raw_data[-i]['numbers']))
            }
            for i in range(5, 0, -1)
        ]
    }
    
    with open('results/prediction_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 详细分析已保存到: results/prediction_analysis.json")
    
    print("\n" + "=" * 80)
    print("预测分析完成!")
    print("=" * 80)

if __name__ == '__main__':
    main()
