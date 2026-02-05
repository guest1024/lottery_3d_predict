#!/usr/bin/env python3
"""
生成模拟的3D彩票数据用于训练测试
基于真实数据分布生成
"""
import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def generate_realistic_3d_data(num_records=2000):
    """
    生成符合真实分布的3D彩票数据
    
    Args:
        num_records: 生成记录数
        
    Returns:
        数据列表
    """
    records = []
    start_date = datetime(2020, 1, 1)
    
    # 形态分布: 组六60%, 组三35%, 豹子5%
    shape_probs = [0.60, 0.35, 0.05]
    
    for i in range(num_records):
        period = f"2020{str(i+1).zfill(3)}"
        date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        
        # 根据形态分布生成号码
        shape = np.random.choice([2, 1, 0], p=shape_probs)  # 2=组六, 1=组三, 0=豹子
        
        if shape == 0:  # 豹子
            digit = np.random.randint(0, 10)
            numbers = [digit, digit, digit]
        elif shape == 1:  # 组三
            digit1 = np.random.randint(0, 10)
            digit2 = np.random.randint(0, 10)
            while digit2 == digit1:
                digit2 = np.random.randint(0, 10)
            # 随机排列
            numbers = [digit1, digit1, digit2]
            np.random.shuffle(numbers)
        else:  # 组六
            numbers = list(np.random.choice(10, size=3, replace=False))
        
        record = {
            'period': period,
            'date': date,
            'numbers': [int(x) for x in numbers],
            'digit_0': int(numbers[0]),
            'digit_1': int(numbers[1]),
            'digit_2': int(numbers[2]),
            'sales': '',
            'prizes': '',
        }
        records.append(record)
    
    return records

def main():
    print("="*60)
    print("生成模拟3D彩票数据")
    print("="*60)
    
    # 生成数据
    num_records = 2000
    print(f"\n生成 {num_records} 条记录...")
    records = generate_realistic_3d_data(num_records)
    
    # 保存数据
    output_dir = Path('./data')
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"lottery_3d_data_{timestamp}.json"
    
    data = {
        'total': len(records),
        'data': records,
        'note': 'Mock data generated for testing'
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 数据已生成: {output_file}")
    print(f"✓ 总记录数: {len(records)}")
    
    # 统计信息
    sums = [sum(r['numbers']) for r in records]
    shapes = []
    for r in records:
        unique = len(set(r['numbers']))
        if unique == 1:
            shapes.append('豹子')
        elif unique == 2:
            shapes.append('组三')
        else:
            shapes.append('组六')
    
    from collections import Counter
    shape_dist = Counter(shapes)
    
    print(f"\n形态分布:")
    for shape, count in shape_dist.items():
        print(f"  {shape}: {count} ({count/len(records)*100:.1f}%)")
    
    print(f"\n和值范围: {min(sums)} - {max(sums)}")
    print(f"和值均值: {np.mean(sums):.2f}")
    
    print("="*60)
    return True

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
