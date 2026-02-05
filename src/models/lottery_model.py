"""
3D彩票预测深度学习模型

使用LSTM + Attention实现多任务学习
"""
import logging
from typing import Dict, Tuple, Optional
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


class AttentionLayer(nn.Module):
    """Self-Attention机制"""
    
    def __init__(self, hidden_dim: int):
        super().__init__()
        self.attention = nn.Linear(hidden_dim, 1)
    
    def forward(self, lstm_output):
        """
        Args:
            lstm_output: (batch_size, seq_len, hidden_dim)
            
        Returns:
            context: (batch_size, hidden_dim)
            attention_weights: (batch_size, seq_len)
        """
        # 计算注意力分数
        attention_scores = self.attention(lstm_output)  # (batch, seq_len, 1)
        attention_weights = F.softmax(attention_scores.squeeze(-1), dim=1)  # (batch, seq_len)
        
        # 加权求和
        context = torch.bmm(
            attention_weights.unsqueeze(1),  # (batch, 1, seq_len)
            lstm_output  # (batch, seq_len, hidden_dim)
        ).squeeze(1)  # (batch, hidden_dim)
        
        return context, attention_weights


class LotteryModel(nn.Module):
    """
    3D彩票预测模型
    
    架构：
    - Embedding层：将0-9数字映射到嵌入空间
    - Bi-LSTM层：捕捉时间序列依赖
    - Attention层：关注重要的历史时刻
    - 多任务输出头：
        1. 数字预测头（10个数字的概率）
        2. 形态分类头（组六/组三/豹子）
        3. 和值预测头（0-27）
        4. AC值预测头（1-3）
    """
    
    def __init__(
        self,
        embedding_dim: int = 16,
        hidden_dim: int = 128,
        num_layers: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()
        
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Embedding层（0-9数字 + padding）
        self.embedding = nn.Embedding(11, embedding_dim, padding_idx=10)
        
        # Bi-LSTM层
        self.lstm = nn.LSTM(
            input_size=embedding_dim * 3,  # 三个位置
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        
        # Attention层
        self.attention = AttentionLayer(hidden_dim * 2)  # *2 for bidirectional
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
        
        # 多任务输出头
        context_dim = hidden_dim * 2
        
        # 1. 数字预测头（每个数字出现的概率）
        self.digit_head = nn.Sequential(
            nn.Linear(context_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 10),  # 10个数字
            nn.Sigmoid()  # 多标签分类
        )
        
        # 2. 形态分类头（组六/组三/豹子）
        self.shape_head = nn.Sequential(
            nn.Linear(context_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 3),  # 3种形态
        )
        
        # 3. 和值预测头（0-27）
        self.sum_head = nn.Sequential(
            nn.Linear(context_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 28),  # 0-27共28个值
        )
        
        # 4. AC值预测头（1-3）
        self.ac_head = nn.Sequential(
            nn.Linear(context_dim, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 3),  # AC值1, 2, 3
        )
    
    def forward(self, x):
        """
        前向传播
        
        Args:
            x: (batch_size, seq_len, 3) - 三个位置的数字序列
            
        Returns:
            dict with keys:
                - digit_probs: (batch_size, 10)
                - shape_logits: (batch_size, 3)
                - sum_logits: (batch_size, 28)
                - ac_logits: (batch_size, 3)
                - attention_weights: (batch_size, seq_len)
        """
        batch_size, seq_len, _ = x.shape
        
        # Embedding
        embedded = self.embedding(x)  # (batch, seq_len, 3, emb_dim)
        embedded = embedded.view(batch_size, seq_len, -1)  # (batch, seq_len, 3*emb_dim)
        
        # LSTM
        lstm_out, _ = self.lstm(embedded)  # (batch, seq_len, hidden_dim*2)
        
        # Attention
        context, attention_weights = self.attention(lstm_out)
        context = self.dropout(context)
        
        # 多任务输出
        outputs = {
            'digit_probs': self.digit_head(context),
            'shape_logits': self.shape_head(context),
            'sum_logits': self.sum_head(context),
            'ac_logits': self.ac_head(context),
            'attention_weights': attention_weights,
        }
        
        return outputs
    
    def predict(self, x):
        """
        预测模式（返回概率）
        
        Args:
            x: (batch_size, seq_len, 3)
            
        Returns:
            dict with probabilities
        """
        self.eval()
        with torch.no_grad():
            outputs = self.forward(x)
            
            # 转换为概率
            predictions = {
                'digit_probs': outputs['digit_probs'].cpu().numpy(),
                'shape_probs': F.softmax(outputs['shape_logits'], dim=1).cpu().numpy(),
                'sum_probs': F.softmax(outputs['sum_logits'], dim=1).cpu().numpy(),
                'ac_probs': F.softmax(outputs['ac_logits'], dim=1).cpu().numpy(),
                'attention_weights': outputs['attention_weights'].cpu().numpy(),
            }
            
        return predictions
    
    def compute_loss(self, outputs, targets, weights=None):
        """
        计算多任务损失
        
        Args:
            outputs: 模型输出
            targets: dict with keys:
                - digits: (batch_size, 3) 真实数字
                - shape: (batch_size,) 形态标签
                - sum: (batch_size,) 和值
                - ac: (batch_size,) AC值
            weights: 各任务权重
            
        Returns:
            total_loss, loss_dict
        """
        if weights is None:
            weights = {'digit': 2.0, 'shape': 1.0, 'sum': 1.5, 'ac': 1.0}
        
        # 1. 数字预测损失（多标签BCE）
        digit_target = torch.zeros(targets['digits'].size(0), 10, device=outputs['digit_probs'].device)
        for i in range(targets['digits'].size(0)):
            for j in range(3):
                digit_target[i, targets['digits'][i, j]] = 1.0
        
        digit_loss = F.binary_cross_entropy(outputs['digit_probs'], digit_target)
        
        # 2. 形态分类损失
        shape_loss = F.cross_entropy(outputs['shape_logits'], targets['shape'])
        
        # 3. 和值预测损失
        sum_loss = F.cross_entropy(outputs['sum_logits'], targets['sum'])
        
        # 4. AC值预测损失（targets['ac']已经是0-2范围）
        ac_loss = F.cross_entropy(outputs['ac_logits'], targets['ac'])
        
        # 总损失
        total_loss = (
            weights['digit'] * digit_loss +
            weights['shape'] * shape_loss +
            weights['sum'] * sum_loss +
            weights['ac'] * ac_loss
        )
        
        loss_dict = {
            'total': total_loss.item(),
            'digit': digit_loss.item(),
            'shape': shape_loss.item(),
            'sum': sum_loss.item(),
            'ac': ac_loss.item(),
        }
        
        return total_loss, loss_dict
    
    def save(self, path: str):
        """保存模型"""
        torch.save({
            'model_state_dict': self.state_dict(),
            'config': {
                'embedding_dim': self.embedding_dim,
                'hidden_dim': self.hidden_dim,
                'num_layers': self.num_layers,
            }
        }, path)
        logger.info(f"Model saved to {path}")
    
    @classmethod
    def load(cls, path: str, device='cpu'):
        """加载模型"""
        checkpoint = torch.load(path, map_location=device)
        config = checkpoint['config']
        
        model = cls(**config)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(device)
        
        logger.info(f"Model loaded from {path}")
        return model
