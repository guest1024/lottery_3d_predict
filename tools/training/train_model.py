#!/usr/bin/env python3
"""
模型训练脚本
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from tqdm import tqdm

from data_loader.loader import DataLoader as LotteryDataLoader
from models.lottery_model import LotteryModel


class LotteryDataset(Dataset):
    """彩票数据集"""
    
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.long)
        self.y = torch.tensor(y, dtype=torch.long)
    
    def __len__(self):
        return len(self.X)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


def prepare_targets(y_batch):
    """
    准备训练目标
    
    Args:
        y_batch: (batch_size, 3) 真实号码
        
    Returns:
        targets字典
    """
    batch_size = y_batch.size(0)
    device = y_batch.device
    
    targets = {}
    
    # 1. 数字目标
    targets['digits'] = y_batch  # (batch_size, 3)
    
    # 2. 形态目标
    shape_labels = []
    for i in range(batch_size):
        numbers = y_batch[i].cpu().numpy()
        unique_count = len(set(numbers.tolist()))
        if unique_count == 1:
            shape_labels.append(2)  # 豹子
        elif unique_count == 2:
            shape_labels.append(1)  # 组三
        else:
            shape_labels.append(0)  # 组六
    targets['shape'] = torch.tensor(shape_labels, dtype=torch.long, device=device)
    
    # 3. 和值目标 (确保在0-27范围内)
    sum_labels = y_batch.sum(dim=1)  # (batch_size,)
    sum_labels = torch.clamp(sum_labels, 0, 27)  # 限制范围
    targets['sum'] = sum_labels
    
    # 4. AC值目标 (确保在0-2范围内，对应AC值1-3)
    ac_labels = []
    for i in range(batch_size):
        numbers = y_batch[i].cpu().numpy()
        diffs = set()
        for j in range(3):
            for k in range(j+1, 3):
                diffs.add(abs(int(numbers[j]) - int(numbers[k])))
        ac_value = len(diffs)
        ac_value = max(1, min(3, ac_value))  # 确保在1-3范围内
        ac_labels.append(ac_value - 1)  # 映射到0-2
    targets['ac'] = torch.tensor(ac_labels, dtype=torch.long, device=device)
    
    return targets


def train_epoch(model, train_loader, optimizer, device):
    """训练一个epoch"""
    model.train()
    total_loss = 0
    loss_details = {'digit': 0, 'shape': 0, 'sum': 0, 'ac': 0}
    
    pbar = tqdm(train_loader, desc='Training')
    for X_batch, y_batch in pbar:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        
        # 前向传播
        outputs = model(X_batch)
        
        # 准备目标
        targets = prepare_targets(y_batch)
        
        # 计算损失
        loss, loss_dict = model.compute_loss(outputs, targets)
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # 统计
        total_loss += loss.item()
        for key in loss_details:
            loss_details[key] += loss_dict[key]
        
        pbar.set_postfix({'loss': f'{loss.item():.4f}'})
    
    avg_loss = total_loss / len(train_loader)
    for key in loss_details:
        loss_details[key] /= len(train_loader)
    
    return avg_loss, loss_details


def evaluate(model, test_loader, device):
    """评估模型"""
    model.eval()
    total_loss = 0
    loss_details = {'digit': 0, 'shape': 0, 'sum': 0, 'ac': 0}
    
    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)
            
            outputs = model(X_batch)
            targets = prepare_targets(y_batch)
            loss, loss_dict = model.compute_loss(outputs, targets)
            
            total_loss += loss.item()
            for key in loss_details:
                loss_details[key] += loss_dict[key]
    
    avg_loss = total_loss / len(test_loader)
    for key in loss_details:
        loss_details[key] /= len(test_loader)
    
    return avg_loss, loss_details


def main():
    print("="*60)
    print("开始训练3D彩票预测模型")
    print("="*60)
    
    # 1. 加载数据
    print("\n1. 加载数据...")
    loader = LotteryDataLoader(data_dir='./data')
    df = loader.load_from_json()
    print(f"   加载 {len(df)} 条记录")
    
    # 2. 准备序列数据
    print("\n2. 准备训练数据...")
    window_size = 30
    test_size = 0.2
    X_train, y_train, X_test, y_test = loader.prepare_sequences(
        window_size=window_size,
        test_size=test_size
    )
    print(f"   训练集: {len(X_train)} 样本")
    print(f"   测试集: {len(X_test)} 样本")
    
    # 3. 创建数据加载器
    batch_size = 32
    train_dataset = LotteryDataset(X_train, y_train)
    test_dataset = LotteryDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # 4. 创建模型
    print("\n3. 创建模型...")
    device = torch.device('cpu')  # 使用CPU避免CUDA问题
    print(f"   使用设备: {device}")
    
    model = LotteryModel(
        embedding_dim=16,
        hidden_dim=128,
        num_layers=2,
        dropout=0.3
    ).to(device)
    
    print(f"   模型参数: {sum(p.numel() for p in model.parameters()):,}")
    
    # 5. 训练配置
    print("\n4. 训练配置...")
    num_epochs = 10  # 减少epoch数加快训练
    learning_rate = 0.001
    
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=3, verbose=True
    )
    
    # 6. 训练循环
    print("\n5. 开始训练...")
    best_loss = float('inf')
    model_dir = Path('./models')
    model_dir.mkdir(exist_ok=True)
    
    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch+1}/{num_epochs}")
        print("-" * 40)
        
        # 训练
        train_loss, train_details = train_epoch(model, train_loader, optimizer, device)
        
        # 评估
        test_loss, test_details = evaluate(model, test_loader, device)
        
        # 输出
        print(f"Train Loss: {train_loss:.4f}")
        print(f"  - Digit: {train_details['digit']:.4f}")
        print(f"  - Shape: {train_details['shape']:.4f}")
        print(f"  - Sum: {train_details['sum']:.4f}")
        print(f"  - AC: {train_details['ac']:.4f}")
        
        print(f"Test Loss: {test_loss:.4f}")
        print(f"  - Digit: {test_details['digit']:.4f}")
        print(f"  - Shape: {test_details['shape']:.4f}")
        print(f"  - Sum: {test_details['sum']:.4f}")
        print(f"  - AC: {test_details['ac']:.4f}")
        
        # 学习率调度
        scheduler.step(test_loss)
        
        # 保存最佳模型
        if test_loss < best_loss:
            best_loss = test_loss
            model_path = model_dir / 'best_model.pth'
            model.save(str(model_path))
            print(f"✓ 保存最佳模型: {model_path}")
    
    print("\n" + "="*60)
    print("训练完成！")
    print(f"最佳测试损失: {best_loss:.4f}")
    print(f"模型已保存: {model_dir / 'best_model.pth'}")
    print("="*60)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
