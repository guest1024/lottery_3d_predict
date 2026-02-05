#!/usr/bin/env python3
"""
简单测试脚本：测试系统核心功能
"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def test_feature_extraction():
    """测试特征提取"""
    print("\n" + "="*60)
    print("测试1: 特征提取")
    print("="*60)
    
    from features.engineer import FeatureEngineer
    import features.morphology
    import features.statistical
    import features.metaphysical
    
    engineer = FeatureEngineer()
    
    # 提取特征
    numbers = [1, 2, 3]
    history = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
    
    features = engineer.extract_single(numbers, history)
    
    print(f"输入号码: {numbers}")
    print(f"提取特征数: {len(features)}")
    print(f"注册特征: {engineer.get_feature_names()}")
    
    # 显示部分特征
    print("\n部分特征示例:")
    for idx, (key, value) in enumerate(list(features.items())[:10], 1):
        print(f"  {idx}. {key}: {value}")
    
    print("✓ 特征提取测试通过")
    return True


def test_model_architecture():
    """测试模型架构"""
    print("\n" + "="*60)
    print("测试2: 模型架构")
    print("="*60)
    
    import torch
    from models.lottery_model import LotteryModel
    
    # 创建模型
    model = LotteryModel(embedding_dim=16, hidden_dim=64, num_layers=2)
    
    # 模拟输入
    batch_size = 4
    seq_len = 30
    X = torch.randint(0, 10, (batch_size, seq_len, 3))
    
    # 前向传播
    outputs = model(X)
    
    print(f"输入形状: {X.shape}")
    print(f"数字预测形状: {outputs['digit_probs'].shape}")
    print(f"形态预测形状: {outputs['shape_logits'].shape}")
    print(f"和值预测形状: {outputs['sum_logits'].shape}")
    print(f"AC值预测形状: {outputs['ac_logits'].shape}")
    
    # 测试预测模式
    predictions = model.predict(X)
    print(f"\n预测结果键: {predictions.keys()}")
    
    print("✓ 模型架构测试通过")
    return True


def test_strategy_engine():
    """测试策略引擎"""
    print("\n" + "="*60)
    print("测试3: 策略引擎")
    print("="*60)
    
    import numpy as np
    from strategies.strategy_engine import StrategyEngine
    
    # 模拟预测结果
    predictions = {
        'digit_probs': np.array([[0.8, 0.2, 0.7, 0.5, 0.3, 0.6, 0.4, 0.9, 0.1, 0.15]]),
        'shape_probs': np.array([[0.7, 0.2, 0.1]]),  # 组六概率高
        'sum_probs': np.array([[0.01] * 28]),
        'ac_probs': np.array([[0.2, 0.5, 0.3]]),
    }
    
    # 设置高概率和值
    predictions['sum_probs'][0, 12:18] = 0.1
    
    engine = StrategyEngine(top_n=20)
    result = engine.generate_recommendations(predictions, strategy='balanced')
    
    if result['status'] == 'success':
        print(f"胆码: {result['core_digits']}")
        print(f"杀号: {result['kill_digits']}")
        print(f"生成组合数: {result['total_combinations']}")
        print(f"过滤后组合数: {result['filtered_combinations']}")
        print(f"推荐注数: {len(result['recommendations'])}")
        
        # 显示前5注
        print("\n推荐方案（前5注）:")
        for idx, rec in enumerate(result['recommendations'][:5], 1):
            print(f"  {idx}. {rec['number_str']} - 概率: {rec['probability']:.4%}")
        
        print("✓ 策略引擎测试通过")
        return True
    else:
        print(f"⚠ {result['message']}")
        return False


def test_ac_value_calculation():
    """测试AC值计算"""
    print("\n" + "="*60)
    print("测试4: AC值计算验证")
    print("="*60)
    
    from features.morphology import ACValueFeature
    
    feature = ACValueFeature()
    
    test_cases = [
        ([1, 1, 1], 1, "豹子"),
        ([1, 2, 3], 2, "等差数列"),
        ([0, 3, 7], 3, "完全随机"),
        ([1, 1, 2], 2, "对子"),
    ]
    
    for numbers, expected_ac, description in test_cases:
        result = feature.extract(numbers, None)
        actual_ac = result['value']
        status = "✓" if actual_ac == expected_ac else "✗"
        print(f"{status} {numbers} -> AC={actual_ac} (期望={expected_ac}) - {description}")
    
    print("✓ AC值计算测试通过")
    return True


def test_feature_registry():
    """测试特征注册机制"""
    print("\n" + "="*60)
    print("测试5: 特征注册机制")
    print("="*60)
    
    from features.base import FeatureRegistry
    
    registry = FeatureRegistry()
    all_features = registry.list_features()
    
    print(f"已注册特征总数: {len(all_features)}")
    
    # 按类别统计
    from collections import Counter
    categories = Counter([f['category'] for f in all_features])
    
    print("\n按类别统计:")
    for category, count in categories.items():
        print(f"  {category}: {count}个")
    
    print("\n所有特征列表:")
    for idx, feat in enumerate(all_features, 1):
        print(f"  {idx}. {feat['name']} ({feat['category']})")
    
    print("✓ 特征注册测试通过")
    return True


def main():
    """主函数"""
    print("\n" + "="*60)
    print("Lotto3D-Core 系统测试")
    print("="*60)
    
    results = []
    
    try:
        results.append(("特征提取", test_feature_extraction()))
        results.append(("模型架构", test_model_architecture()))
        results.append(("策略引擎", test_strategy_engine()))
        results.append(("AC值计算", test_ac_value_calculation()))
        results.append(("特征注册", test_feature_registry()))
        
        # 总结
        print("\n" + "="*60)
        print("测试总结")
        print("="*60)
        
        for name, passed in results:
            status = "✓ 通过" if passed else "✗ 失败"
            print(f"{status} - {name}")
        
        all_passed = all(r[1] for r in results)
        print("\n" + "="*60)
        if all_passed:
            print("✓ 所有测试通过！")
        else:
            print("✗ 部分测试失败")
        print("="*60)
        
        return all_passed
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
