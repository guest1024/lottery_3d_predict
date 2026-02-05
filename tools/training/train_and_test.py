"""
使用真实数据训练LSTM+Attention模型并测试预测效果
使用最近的1200条数据
"""
import sys
sys.path.insert(0, '/c1/program/lottery_3d_predict')

import json
import numpy as np
from pathlib import Path

from src.data_loader.data_processor import DataProcessor
from src.models.lstm_attention import LSTMAttentionModel
from src.training.trainer import ModelTrainer
from src.evaluation.metrics import calculate_metrics
from src.utils.logger import setup_logger

def main():
    logger = setup_logger('train_test', 'logs/train_test.log')
    
    print("=" * 80)
    print("3D彩票预测模型训练与测试")
    print("=" * 80)
    
    # 1. 加载最新的真实数据
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    print(f"\n[1] 加载数据: {data_file}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_records = len(data['data'])
    print(f"✓ 总记录数: {total_records}")
    
    # 取最近的1200条数据
    recent_data = data['data'][-1200:]
    print(f"✓ 使用最近的1200条数据")
    print(f"  时间范围: {recent_data[0]['period']} 到 {recent_data[-1]['period']}")
    
    # 2. 数据预处理
    print(f"\n[2] 数据预处理")
    processor = DataProcessor(
        sequence_length=30,  # 使用30期历史数据
        test_ratio=0.2,      # 20%作为测试集
        val_ratio=0.1        # 10%作为验证集
    )
    
    # 转换数据格式
    records = []
    for item in recent_data:
        records.append({
            'period': item['period'],
            'numbers': item['numbers']
        })
    
    # 处理数据
    train_data, val_data, test_data = processor.process_data(records)
    
    print(f"✓ 序列长度: {processor.sequence_length}")
    print(f"✓ 训练集: {len(train_data['X'])} 样本")
    print(f"✓ 验证集: {len(val_data['X'])} 样本")
    print(f"✓ 测试集: {len(test_data['X'])} 样本")
    
    # 3. 创建模型
    print(f"\n[3] 创建LSTM+Attention模型")
    model = LSTMAttentionModel(
        input_dim=30,           # 特征维度(10个数字的one-hot * 3个位置)
        hidden_dim=128,         # LSTM隐藏层维度
        num_layers=2,           # LSTM层数
        num_classes=10,         # 输出类别数(0-9)
        dropout=0.3,            # Dropout比率
        attention_heads=4       # 注意力头数
    )
    
    print(f"✓ 输入维度: 30")
    print(f"✓ 隐藏层维度: 128")
    print(f"✓ LSTM层数: 2")
    print(f"✓ 注意力头数: 4")
    print(f"✓ Dropout: 0.3")
    
    # 4. 训练模型
    print(f"\n[4] 开始训练模型")
    trainer = ModelTrainer(
        model=model,
        learning_rate=0.001,
        batch_size=32,
        num_epochs=50,
        device='cpu',
        save_dir='models/checkpoints'
    )
    
    print(f"✓ 学习率: 0.001")
    print(f"✓ 批次大小: 32")
    print(f"✓ 训练轮数: 50")
    print(f"✓ 设备: CPU")
    print()
    
    history = trainer.train(
        train_data=train_data,
        val_data=val_data,
        early_stopping_patience=10
    )
    
    print(f"\n✓ 训练完成!")
    print(f"  最佳验证损失: {history['best_val_loss']:.4f}")
    print(f"  最佳轮次: {history['best_epoch']}")
    
    # 5. 在测试集上评估
    print(f"\n[5] 测试集评估")
    
    # 加载最佳模型
    trainer.load_checkpoint('models/checkpoints/best_model.pth')
    
    # 预测
    predictions = trainer.predict(test_data['X'])
    
    # 计算指标
    metrics = calculate_metrics(
        y_true=test_data['y'],
        y_pred=predictions
    )
    
    print(f"\n测试集性能指标:")
    print(f"  位置0准确率: {metrics['digit_0_accuracy']:.2%}")
    print(f"  位置1准确率: {metrics['digit_1_accuracy']:.2%}")
    print(f"  位置2准确率: {metrics['digit_2_accuracy']:.2%}")
    print(f"  平均准确率: {metrics['mean_accuracy']:.2%}")
    print(f"  完全匹配率: {metrics['exact_match_rate']:.2%}")
    
    # 6. 预测未来一期
    print(f"\n[6] 预测下一期号码")
    
    # 使用最后30期数据
    last_30 = np.array([r['numbers'] for r in recent_data[-30:]])
    
    # 预测
    next_pred = model.predict_next(last_30)
    
    print(f"\n预测结果:")
    print(f"  下一期预测号码: {next_pred[0]} {next_pred[1]} {next_pred[2]}")
    
    # 显示每个位置的概率分布(Top 3)
    last_30_tensor = processor._prepare_sequence(last_30)
    import torch
    with torch.no_grad():
        outputs = model(last_30_tensor.unsqueeze(0))
        
        print(f"\n各位置概率分布 (Top 3):")
        for i, (name, output) in enumerate(zip(['百位', '十位', '个位'], outputs)):
            probs = torch.softmax(output[0], dim=0).numpy()
            top3_idx = np.argsort(probs)[-3:][::-1]
            
            print(f"\n  {name}:")
            for idx in top3_idx:
                print(f"    数字 {idx}: {probs[idx]:.2%}")
    
    # 7. 保存结果
    print(f"\n[7] 保存结果")
    
    results = {
        'data_info': {
            'total_records': total_records,
            'used_records': 1200,
            'time_range': f"{recent_data[0]['period']} 到 {recent_data[-1]['period']}"
        },
        'training_info': {
            'sequence_length': 30,
            'train_samples': len(train_data['X']),
            'val_samples': len(val_data['X']),
            'test_samples': len(test_data['X']),
            'num_epochs': 50,
            'best_epoch': history['best_epoch'],
            'best_val_loss': float(history['best_val_loss'])
        },
        'test_metrics': {
            'digit_0_accuracy': float(metrics['digit_0_accuracy']),
            'digit_1_accuracy': float(metrics['digit_1_accuracy']),
            'digit_2_accuracy': float(metrics['digit_2_accuracy']),
            'mean_accuracy': float(metrics['mean_accuracy']),
            'exact_match_rate': float(metrics['exact_match_rate'])
        },
        'prediction': {
            'next_period': next_pred.tolist(),
            'last_30_periods': recent_data[-30:]
        }
    }
    
    result_file = 'results/training_results.json'
    Path('results').mkdir(exist_ok=True)
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 结果已保存到: {result_file}")
    
    print("\n" + "=" * 80)
    print("训练和测试完成!")
    print("=" * 80)

if __name__ == '__main__':
    main()
