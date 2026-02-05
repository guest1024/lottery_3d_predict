"""
使用真实数据训练LSTM+Attention模型并测试预测效果
使用最近的1200条数据
"""
import sys
sys.path.insert(0, '/c1/program/lottery_3d_predict')

import json
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
from torch.utils.data import DataLoader as TorchDataLoader, TensorDataset

from src.models.lottery_model import LotteryModel

def load_data(json_file, num_records=1200):
    """加载最近的N条数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 取最近的records
    recent_data = data['data'][-num_records:]
    
    # 提取数字序列
    sequences = []
    for item in recent_data:
        sequences.append(item['numbers'])
    
    return np.array(sequences), recent_data

def prepare_datasets(sequences, window_size=30, test_ratio=0.2, val_ratio=0.1):
    """准备训练、验证和测试数据集"""
    X, y = [], []
    
    # 创建滑动窗口
    for i in range(len(sequences) - window_size):
        X.append(sequences[i:i + window_size])
        y.append(sequences[i + window_size])
    
    X = np.array(X)  # (samples, window_size, 3)
    y = np.array(y)  # (samples, 3)
    
    # 计算分割点
    n_samples = len(X)
    n_test = int(n_samples * test_ratio)
    n_val = int(n_samples * val_ratio)
    n_train = n_samples - n_test - n_val
    
    # 分割数据
    X_train, y_train = X[:n_train], y[:n_train]
    X_val, y_val = X[n_train:n_train+n_val], y[n_train:n_train+n_val]
    X_test, y_test = X[n_train+n_val:], y[n_train+n_val:]
    
    return (X_train, y_train), (X_val, y_val), (X_test, y_test)

def compute_targets(y_batch):
    """计算多任务目标"""
    batch_size = y_batch.size(0)
    device = y_batch.device
    
    # 数字目标
    digits = y_batch  # (batch, 3)
    
    # 形态目标 (组六=0, 组三=1, 豹子=2)
    shape = torch.zeros(batch_size, dtype=torch.long, device=device)
    for i in range(batch_size):
        nums = y_batch[i].cpu().numpy()
        unique_count = len(set(nums))
        if unique_count == 1:  # 豹子
            shape[i] = 2
        elif unique_count == 2:  # 组三
            shape[i] = 1
        else:  # 组六
            shape[i] = 0
    
    # 和值目标
    sum_val = y_batch.sum(dim=1)  # (batch,)
    
    # AC值目标 (简化: 根据形态)
    ac = torch.zeros(batch_size, dtype=torch.long, device=device)
    for i in range(batch_size):
        nums = sorted(y_batch[i].cpu().numpy())
        diffs = [abs(nums[j] - nums[k]) for j in range(len(nums)) for k in range(j+1, len(nums))]
        unique_diffs = len(set(diffs))
        ac[i] = min(unique_diffs - 1, 2)  # AC值范围1-3, 映射到0-2
    
    return {
        'digits': digits,
        'shape': shape,
        'sum': sum_val,
        'ac': ac
    }

def train_epoch(model, dataloader, optimizer, device):
    """训练一个epoch"""
    model.train()
    total_loss = 0
    n_batches = 0
    
    for X_batch, y_batch in dataloader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        
        # 前向传播
        outputs = model(X_batch)
        
        # 计算目标
        targets = compute_targets(y_batch)
        
        # 计算损失
        loss, loss_dict = model.compute_loss(outputs, targets)
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        n_batches += 1
    
    return total_loss / n_batches

def evaluate(model, dataloader, device):
    """评估模型"""
    model.eval()
    total_loss = 0
    n_batches = 0
    correct_digits = [0, 0, 0]  # 三个位置的准确率
    total_samples = 0
    exact_match = 0
    
    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)
            
            # 前向传播
            outputs = model(X_batch)
            
            # 计算损失
            targets = compute_targets(y_batch)
            loss, _ = model.compute_loss(outputs, targets)
            total_loss += loss.item()
            n_batches += 1
            
            # 预测数字
            digit_probs = outputs['digit_probs'].cpu().numpy()
            y_true = y_batch.cpu().numpy()
            
            # 使用Top 3策略预测
            for i in range(len(digit_probs)):
                top3 = np.argsort(digit_probs[i])[-3:]
                pred_numbers = []
                
                # 为每个位置选择最可能的数字
                for pos in range(3):
                    # 简单策略: 从top3中选择
                    if y_true[i, pos] in top3:
                        correct_digits[pos] += 1
                    pred_numbers.append(top3[-1])  # 使用概率最高的
                
                # 完全匹配
                if all(pred_numbers[j] == y_true[i, j] for j in range(3)):
                    exact_match += 1
                
                total_samples += 1
    
    metrics = {
        'loss': total_loss / n_batches,
        'digit_0_acc': correct_digits[0] / total_samples,
        'digit_1_acc': correct_digits[1] / total_samples,
        'digit_2_acc': correct_digits[2] / total_samples,
        'mean_acc': np.mean(correct_digits) / total_samples,
        'exact_match': exact_match / total_samples
    }
    
    return metrics

def main():
    print("=" * 80)
    print("3D彩票预测模型训练与测试")
    print("=" * 80)
    
    # 设置随机种子
    torch.manual_seed(42)
    np.random.seed(42)
    
    device = torch.device('cpu')
    
    # 1. 加载数据
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    print(f"\n[1] 加载数据: {data_file}")
    
    sequences, raw_data = load_data(data_file, num_records=1200)
    print(f"✓ 使用最近的1200条数据")
    print(f"  时间范围: {raw_data[0]['period']} 到 {raw_data[-1]['period']}")
    print(f"  数据形状: {sequences.shape}")
    
    # 2. 准备数据集
    print(f"\n[2] 准备训练数据")
    train_data, val_data, test_data = prepare_datasets(sequences, window_size=30)
    
    X_train, y_train = train_data
    X_val, y_val = val_data
    X_test, y_test = test_data
    
    print(f"✓ 训练集: {len(X_train)} 样本")
    print(f"✓ 验证集: {len(X_val)} 样本")
    print(f"✓ 测试集: {len(X_test)} 样本")
    
    # 转换为PyTorch tensors
    train_dataset = TensorDataset(
        torch.LongTensor(X_train),
        torch.LongTensor(y_train)
    )
    val_dataset = TensorDataset(
        torch.LongTensor(X_val),
        torch.LongTensor(y_val)
    )
    test_dataset = TensorDataset(
        torch.LongTensor(X_test),
        torch.LongTensor(y_test)
    )
    
    # 创建DataLoader
    train_loader = TorchDataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = TorchDataLoader(val_dataset, batch_size=32, shuffle=False)
    test_loader = TorchDataLoader(test_dataset, batch_size=32, shuffle=False)
    
    # 3. 创建模型
    print(f"\n[3] 创建LSTM+Attention模型")
    model = LotteryModel(
        embedding_dim=16,
        hidden_dim=128,
        num_layers=2,
        dropout=0.3
    ).to(device)
    
    print(f"✓ Embedding维度: 16")
    print(f"✓ 隐藏层维度: 128")
    print(f"✓ LSTM层数: 2")
    print(f"✓ Dropout: 0.3")
    
    # 优化器
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 4. 训练模型
    print(f"\n[4] 开始训练模型")
    print(f"✓ 学习率: 0.001")
    print(f"✓ 批次大小: 32")
    print(f"✓ 训练轮数: 50")
    print()
    
    best_val_loss = float('inf')
    best_epoch = 0
    patience = 10
    patience_counter = 0
    
    Path('models/checkpoints').mkdir(parents=True, exist_ok=True)
    
    for epoch in range(50):
        # 训练
        train_loss = train_epoch(model, train_loader, optimizer, device)
        
        # 验证
        val_metrics = evaluate(model, val_loader, device)
        
        print(f"Epoch {epoch+1:2d}/50 - "
              f"训练损失: {train_loss:.4f} - "
              f"验证损失: {val_metrics['loss']:.4f} - "
              f"验证准确率: {val_metrics['mean_acc']:.2%}")
        
        # 早停
        if val_metrics['loss'] < best_val_loss:
            best_val_loss = val_metrics['loss']
            best_epoch = epoch + 1
            patience_counter = 0
            # 保存最佳模型
            model.save('models/checkpoints/best_model.pth')
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\n早停于第 {epoch+1} 轮")
                break
    
    print(f"\n✓ 训练完成!")
    print(f"  最佳验证损失: {best_val_loss:.4f}")
    print(f"  最佳轮次: {best_epoch}")
    
    # 5. 测试集评估
    print(f"\n[5] 测试集评估")
    
    # 加载最佳模型
    model = LotteryModel.load('models/checkpoints/best_model.pth', device=device)
    
    test_metrics = evaluate(model, test_loader, device)
    
    print(f"\n测试集性能指标:")
    print(f"  位置0准确率: {test_metrics['digit_0_acc']:.2%}")
    print(f"  位置1准确率: {test_metrics['digit_1_acc']:.2%}")
    print(f"  位置2准确率: {test_metrics['digit_2_acc']:.2%}")
    print(f"  平均准确率: {test_metrics['mean_acc']:.2%}")
    print(f"  完全匹配率: {test_metrics['exact_match']:.2%}")
    
    # 6. 预测下一期
    print(f"\n[6] 预测下一期号码")
    
    # 使用最后30期数据
    last_30 = torch.LongTensor(sequences[-30:]).unsqueeze(0).to(device)
    
    model.eval()
    with torch.no_grad():
        predictions = model.predict(last_30)
        digit_probs = predictions['digit_probs'][0]
        
        # 选择Top 3数字
        top3_indices = np.argsort(digit_probs)[-3:][::-1]
        
        print(f"\n预测结果 (基于概率Top 3):")
        print(f"  最可能的3个数字: {top3_indices}")
        print(f"  概率分布:")
        for idx in top3_indices:
            print(f"    数字 {idx}: {digit_probs[idx]:.2%}")
        
        # 生成一个预测组合 (使用Top 3随机组合)
        pred_combination = np.random.choice(top3_indices, size=3, replace=True)
        print(f"\n  推荐号码组合: {pred_combination[0]} {pred_combination[1]} {pred_combination[2]}")
    
    # 7. 保存结果
    print(f"\n[7] 保存结果")
    
    results = {
        'data_info': {
            'used_records': 1200,
            'time_range': f"{raw_data[0]['period']} 到 {raw_data[-1]['period']}"
        },
        'training_info': {
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'test_samples': len(X_test),
            'best_epoch': best_epoch,
            'best_val_loss': float(best_val_loss)
        },
        'test_metrics': {
            'digit_0_accuracy': float(test_metrics['digit_0_acc']),
            'digit_1_accuracy': float(test_metrics['digit_1_acc']),
            'digit_2_accuracy': float(test_metrics['digit_2_acc']),
            'mean_accuracy': float(test_metrics['mean_acc']),
            'exact_match_rate': float(test_metrics['exact_match'])
        },
        'prediction': {
            'top3_numbers': top3_indices.tolist(),
            'top3_probs': [float(digit_probs[i]) for i in top3_indices],
            'recommended_combination': pred_combination.tolist()
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
