#!/usr/bin/env python3
"""
测试预测功能
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
    print("测试3D彩票预测功能")
    print("="*60)
    
    # 1. 加载数据
    print("\n1. 加载历史数据...")
    loader = DataLoader(data_dir='./data')
    df = loader.load_from_json()
    print(f"   总记录数: {len(df)}")
    
    # 获取最近30期
    history_data = df.tail(30)
    numbers_list = [row['numbers'] for _, row in history_data.iterrows()]
    print(f"   使用最近 {len(numbers_list)} 期数据")
    
    # 2. 加载模型
    print("\n2. 加载训练好的模型...")
    model_path = './models/best_model.pth'
    device = 'cpu'
    model = LotteryModel.load(model_path, device=device)
    model.eval()
    print(f"   模型已加载: {model_path}")
    
    # 3. 准备输入
    X = torch.tensor([numbers_list], dtype=torch.long)  # (1, 30, 3)
    print(f"   输入形状: {X.shape}")
    
    # 4. 模型预测
    print("\n3. 执行预测...")
    predictions = model.predict(X)
    
    print("\n预测结果:")
    print(f"  • 数字概率 shape: {predictions['digit_probs'].shape}")
    print(f"  • 形态概率 shape: {predictions['shape_probs'].shape}")
    print(f"  • 和值概率 shape: {predictions['sum_probs'].shape}")
    print(f"  • AC值概率 shape: {predictions['ac_probs'].shape}")
    
    # 显示数字概率（Top 5）
    digit_probs = predictions['digit_probs'][0]
    top_digits = np.argsort(digit_probs)[-5:][::-1]
    print("\n高概率数字 (Top 5):")
    for digit in top_digits:
        print(f"  数字 {digit}: {digit_probs[digit]:.2%}")
    
    # 显示形态概率
    shape_probs = predictions['shape_probs'][0]
    shape_names = ['组六', '组三', '豹子']
    print("\n形态预测:")
    for i, name in enumerate(shape_names):
        print(f"  {name}: {shape_probs[i]:.2%}")
    
    # 显示和值预测（Top 5）
    sum_probs = predictions['sum_probs'][0]
    top_sums = np.argsort(sum_probs)[-5:][::-1]
    print("\n高概率和值 (Top 5):")
    for s in top_sums:
        print(f"  和值 {s}: {sum_probs[s]:.2%}")
    
    # 显示AC值预测
    ac_probs = predictions['ac_probs'][0]
    print("\nAC值预测:")
    for i in range(3):
        print(f"  AC={i+1}: {ac_probs[i]:.2%}")
    
    # 5. 生成推荐方案
    print("\n" + "="*60)
    print("4. 生成推荐方案...")
    print("="*60)
    
    strategy_engine = StrategyEngine(top_n=20)
    recommendations = strategy_engine.generate_recommendations(
        predictions, 
        strategy='balanced'
    )
    
    if recommendations['status'] == 'success':
        print(f"\n✓ 推荐生成成功!")
        print(f"  • 置信度: {recommendations['confidence']:.2%}")
        print(f"  • 胆码: {recommendations['core_digits']}")
        print(f"  • 杀号: {recommendations['kill_digits']}")
        print(f"  • 生成组合: {recommendations['total_combinations']}")
        print(f"  • 过滤后: {recommendations['filtered_combinations']}")
        
        summary = recommendations['summary']
        print(f"\n推荐摘要:")
        print(f"  • 形态: {summary['top_shape']}")
        print(f"  • 和值范围: {summary['top_sum_range']}")
        print(f"  • AC值: {summary['top_ac_value']}")
        
        print(f"\n推荐号码 (Top 20):")
        print("  " + "-"*50)
        print(f"  {'排名':<6} {'号码':<10} {'理论胜率':<12}")
        print("  " + "-"*50)
        
        for idx, rec in enumerate(recommendations['recommendations'][:20], 1):
            print(f"  {idx:<6} {rec['number_str']:<10} {rec['probability']:.4%}")
        
        print("  " + "-"*50)
        
        # 显示最近几期历史作为对比
        print(f"\n最近5期历史开奖:")
        recent_5 = df.tail(5)
        for _, row in recent_5.iterrows():
            numbers = row['numbers']
            period = row['period']
            number_str = ''.join(map(str, numbers))
            print(f"  期号 {period}: {number_str}")
        
    else:
        print(f"\n⚠ {recommendations['message']}")
        print(f"  置信度: {recommendations['confidence']:.2%}")
    
    print("\n" + "="*60)
    print("预测测试完成！")
    print("="*60)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
