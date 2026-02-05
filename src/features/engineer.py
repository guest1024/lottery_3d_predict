"""
特征工程主引擎

统一管理所有特征的提取和处理
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from .base import FeatureRegistry, BaseFeature

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    特征工程引擎
    
    负责调用所有注册的特征类，生成完整的特征向量
    """
    
    def __init__(self, feature_names: Optional[List[str]] = None):
        """
        初始化特征工程引擎
        
        Args:
            feature_names: 要使用的特征名称列表，None表示使用所有注册的特征
        """
        self.registry = FeatureRegistry()
        self.feature_names = feature_names
        self._feature_instances: Dict[str, BaseFeature] = {}
        self._initialize_features()
    
    def _initialize_features(self):
        """初始化特征实例"""
        all_features = self.registry.get_all()
        
        if self.feature_names is None:
            # 使用所有注册的特征
            self.feature_names = list(all_features.keys())
        
        for name in self.feature_names:
            feature_class = all_features.get(name)
            if feature_class is None:
                logger.warning(f"Feature '{name}' not found in registry")
                continue
            
            try:
                self._feature_instances[name] = feature_class()
            except Exception as e:
                logger.error(f"Failed to initialize feature '{name}': {e}")
        
        logger.info(f"Initialized {len(self._feature_instances)} features")
    
    def extract_single(self, numbers: List[int], 
                      history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        """
        提取单个样本的所有特征
        
        Args:
            numbers: 当前号码 [百位, 十位, 个位]
            history: 历史号码序列
            
        Returns:
            特征字典
        """
        features = {}
        
        for name, feature_instance in self._feature_instances.items():
            try:
                if not feature_instance.validate(numbers):
                    logger.warning(f"Invalid numbers for feature '{name}': {numbers}")
                    continue
                
                feature_dict = feature_instance.extract(numbers, history)
                
                # 添加前缀以避免特征名冲突
                prefixed_features = {
                    f"{name}_{k}": v for k, v in feature_dict.items()
                }
                features.update(prefixed_features)
                
            except Exception as e:
                logger.error(f"Error extracting feature '{name}': {e}")
        
        return features
    
    def extract_batch(self, numbers_list: List[List[int]], 
                     window_size: int = 30) -> pd.DataFrame:
        """
        批量提取特征
        
        Args:
            numbers_list: 号码列表
            window_size: 历史窗口大小
            
        Returns:
            特征DataFrame
        """
        all_features = []
        
        for i in range(len(numbers_list)):
            numbers = numbers_list[i]
            
            # 获取历史数据
            start_idx = max(0, i - window_size)
            history = numbers_list[start_idx:i] if i > 0 else None
            
            # 提取特征
            features = self.extract_single(numbers, history)
            all_features.append(features)
        
        df = pd.DataFrame(all_features)
        logger.info(f"Extracted features for {len(df)} samples, {len(df.columns)} features")
        
        return df
    
    def extract_from_dataframe(self, df: pd.DataFrame, 
                              numbers_col: str = 'numbers',
                              window_size: int = 30) -> pd.DataFrame:
        """
        从DataFrame提取特征
        
        Args:
            df: 包含号码数据的DataFrame
            numbers_col: 号码列名
            window_size: 历史窗口大小
            
        Returns:
            特征DataFrame
        """
        numbers_list = df[numbers_col].tolist()
        feature_df = self.extract_batch(numbers_list, window_size)
        
        # 合并原始数据和特征
        result = pd.concat([df.reset_index(drop=True), feature_df], axis=1)
        return result
    
    def get_feature_names(self) -> List[str]:
        """
        获取所有特征名称
        
        Returns:
            特征名称列表
        """
        return list(self._feature_instances.keys())
    
    def get_feature_info(self) -> List[Dict[str, str]]:
        """
        获取特征信息
        
        Returns:
            特征信息列表
        """
        return [
            {
                'name': name,
                'class': instance.__class__.__name__,
                'category': instance.category,
                'description': instance.description,
            }
            for name, instance in self._feature_instances.items()
        ]
    
    def export_features_to_numpy(self, df: pd.DataFrame, 
                                exclude_cols: Optional[List[str]] = None) -> np.ndarray:
        """
        将特征DataFrame转换为NumPy数组
        
        Args:
            df: 特征DataFrame
            exclude_cols: 要排除的列名列表
            
        Returns:
            特征数组
        """
        if exclude_cols is None:
            exclude_cols = ['period', 'date', 'numbers', 'sales', 'prizes']
        
        # 选择数值列
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        X = df[feature_cols].values
        logger.info(f"Exported features shape: {X.shape}")
        
        return X
