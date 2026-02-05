"""
数据加载和预处理模块
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataLoader:
    """数据加载器"""
    
    def __init__(self, data_dir: str = "./data"):
        """
        初始化数据加载器
        
        Args:
            data_dir: 数据目录
        """
        self.data_dir = Path(data_dir)
        self.df: Optional[pd.DataFrame] = None
        
    def load_from_json(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        从JSON文件加载数据
        
        Args:
            filepath: JSON文件路径，如果为None则加载最新文件
            
        Returns:
            DataFrame格式的数据
        """
        if filepath is None:
            # 查找最新的JSON文件
            json_files = list(self.data_dir.glob("lottery_3d_data_*.json"))
            if not json_files:
                raise FileNotFoundError(f"No data files found in {self.data_dir}")
            filepath = max(json_files, key=lambda p: p.stat().st_mtime)
        else:
            filepath = Path(filepath)
        
        logger.info(f"Loading data from {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 转换为DataFrame
        df = pd.DataFrame(data['data'])
        
        # 数据类型转换
        df['period'] = df['period'].astype(str)
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # 确保numbers列是列表类型
        if 'numbers' in df.columns:
            df['numbers'] = df['numbers'].apply(lambda x: x if isinstance(x, list) else [])
        
        # 按期号排序
        df = df.sort_values('period').reset_index(drop=True)
        
        self.df = df
        logger.info(f"Loaded {len(df)} records")
        
        return df
    
    def prepare_sequences(self, window_size: int = 30, 
                         test_size: float = 0.2) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        准备时间序列数据用于模型训练
        
        Args:
            window_size: 滑动窗口大小
            test_size: 测试集比例
            
        Returns:
            (X_train, y_train, X_test, y_test)
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_from_json() first.")
        
        # 提取数字序列
        sequences = []
        for idx in range(len(self.df)):
            numbers = self.df.iloc[idx]['numbers']
            if isinstance(numbers, list) and len(numbers) == 3:
                sequences.append(numbers)
        
        sequences = np.array(sequences)
        
        # 创建滑动窗口
        X, y = [], []
        for i in range(len(sequences) - window_size):
            X.append(sequences[i:i + window_size])
            y.append(sequences[i + window_size])
        
        X = np.array(X)  # Shape: (samples, window_size, 3)
        y = np.array(y)  # Shape: (samples, 3)
        
        # 划分训练集和测试集
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        logger.info(f"Prepared sequences: train={len(X_train)}, test={len(X_test)}")
        
        return X_train, y_train, X_test, y_test
    
    def get_history(self, periods: int = 30) -> pd.DataFrame:
        """
        获取最近N期的历史数据
        
        Args:
            periods: 期数
            
        Returns:
            历史数据DataFrame
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_from_json() first.")
        
        return self.df.tail(periods).reset_index(drop=True)
    
    def get_by_period(self, period: str) -> Optional[Dict]:
        """
        根据期号获取数据
        
        Args:
            period: 期号
            
        Returns:
            该期数据字典
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_from_json() first.")
        
        result = self.df[self.df['period'] == period]
        if len(result) == 0:
            return None
        
        return result.iloc[0].to_dict()
    
    def get_statistics(self) -> Dict:
        """
        获取数据统计信息
        
        Returns:
            统计信息字典
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_from_json() first.")
        
        stats = {
            'total_records': len(self.df),
            'date_range': {
                'start': str(self.df['date'].min()),
                'end': str(self.df['date'].max()),
            },
            'period_range': {
                'start': self.df['period'].iloc[0],
                'end': self.df['period'].iloc[-1],
            },
        }
        
        # 数字频率统计
        all_numbers = []
        for numbers in self.df['numbers']:
            if isinstance(numbers, list):
                all_numbers.extend(numbers)
        
        if all_numbers:
            unique, counts = np.unique(all_numbers, return_counts=True)
            stats['number_frequency'] = dict(zip(unique.tolist(), counts.tolist()))
        
        return stats
    
    def save_to_csv(self, output_path: str):
        """
        保存数据为CSV格式
        
        Args:
            output_path: 输出文件路径
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_from_json() first.")
        
        # 展开numbers列
        df_export = self.df.copy()
        if 'numbers' in df_export.columns:
            df_export['number_str'] = df_export['numbers'].apply(
                lambda x: '-'.join(map(str, x)) if isinstance(x, list) else ''
            )
        
        df_export.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"Data saved to {output_path}")
