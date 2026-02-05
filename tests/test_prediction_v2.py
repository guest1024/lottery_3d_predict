#!/usr/bin/env python3
"""
测试预测功能（降低置信度阈值）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

import torch
import numpy as np

from data_loader.loader import DataLoader
from models.lottery_model import LotteryModel
from strategies.strategy_engine import StrategyEngine


def main():
    print("="*60)
    print("测试3D彩票预测功能（完整版）")
    print("="*60)
    
    # 1. 加载数据
    print("\n1. 加载历史数据...")
    loader = DataLoader(data_dir='./data')
    df = loader.load_from_json()
    
    # 获取最近30期
    history_data = df.tail(30)
    numbers_list = [row['numbers'] for _, row in history_data.iterrows()]
    
    # 2. 加载模型
    print("2. 加载模型...")
    model = LotteryModel.load('./models/best_model.pth', device='cpu')
    model.eval()
    
    # 3. 预测
    X = torch.tensor([numbers_list], dtype=torch.long)
    predictions = model.predict(X)
    
    # 显示预测详情
    digit_probs = predictions['digit_probs'][0]
    shape_probs = predictions['shape_probs'][0]
    sum_probs = predictions['sum_probs'][0]
    ac_probs = predictions['ac_probs'][0]
    
    print(f"\n预测详情:")
    print(f"  高概率数字: {np.argsort(digit_probs)[-5:][::-1].tolist()}")
    print(f"  最可能形态: {['组六', '组三', '豹子'][np.argmax(shape_probs)]}")
    print(f"  最可能和值: {np.argmax(sum_probs)}")
    print(f"  最可能AC值: {np.argmax(ac_probs)+1}")
    
    # 4. 生成推荐（降低阈值）
    print("\n3. 生成推荐方案...")
    strategy_engine = StrategyEngine(
        confidence_threshold=0.2,  # 降低阈值
        top_n=100
    )
    
    recommendations = strategy_engine.generate_recommendations(
        predictions, 
        strategy='balanced'
    )
    
    if recommendations['status'] == 'success':
        print(f"\n✓ 推荐生成成功!")
        print(f"  置信度: {recommendations['confidence']:.2%}")
        print(f"  胆码: {recommendations['core_digits']}")
        print(f"  杀号: {recommendations['kill_digits']}")
        
        # 显示Top 30注
        print(f"\n推荐号码 (Top 30):")
        print("  " + "-"*55)
        print(f"  {'排名':<6} {'号码':<8} {'百/十/个':<12} {'理论胜率':<12}")
        print("  " + "-"*55)
        
        for idx, rec in enumerate(recommendations['recommendations'][:30], 1):
            nums = rec['numbers']
            print(f"  {idx:<6} {rec['number_str']:<8} {nums[0]}/{nums[1]}/{nums[2]:<10} {rec['probability']:.4%}")
        
        print("  " + "-"*55)
        
        # 统计分析
        analysis = strategy_engine.analyze_recommendations(
            recommendations['recommendations'][:100]
        )
        
        print(f"\n推荐方案统计:")
        print(f"  数字频率: {analysis['digit_frequency']}")
        print(f"  和值范围: {analysis['sum_stats']['min']}-{analysis['sum_stats']['max']}")
        print(f"  和值均值: {analysis['sum_stats']['mean']:.1f}")
        print(f"  形态分布: {analysis['shape_distribution']}")
        print(f"  AC值分布: {analysis['ac_distribution']}")
        
        # 最近5期对比
        print(f"\n最近5期历史:")
        recent_5 = df.tail(5)
        for _, row in recent_5.iterrows():
            nums = row['numbers']
            sum_val = sum(nums)
            print(f"  期号 {row['period']}: {''.join(map(str, nums))} (和值={sum_val})")
        
        # 下一期期号
        last_period = df.iloc[-1]['period']
        next_period = str(int(last_period) + 1)
        print(f"\n预测期号: {next_period}")
        
    else:
        print(f"\n⚠ {recommendations['message']}")
    
    print("\n" + "="*60)
    print("预测完成！")
    print("="*60)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
