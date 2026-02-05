"""
统计特征模块

包含遗漏值、滚动统计、相关系数等统计型特征
"""
from typing import List, Dict, Any, Optional
import numpy as np
from collections import defaultdict

from .base import BaseFeature, register_feature


@register_feature
class OmissionFeature(BaseFeature):
    """
    遗漏值特征
    
    计算0-9每个数字在各个位置上的遗漏期数
    """
    
    name = "omission"
    description = "0-9各数字在百/十/个位的遗漏期数"
    category = "statistical"
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        features = {}
        
        if history is None or len(history) == 0:
            # 无历史数据时返回默认值
            for pos in range(3):
                for digit in range(10):
                    features[f'pos{pos}_digit{digit}_omission'] = 0
            return features
        
        # 计算每个位置每个数字的遗漏值
        for pos in range(3):  # 三个位置
            last_seen = {d: -1 for d in range(10)}  # 每个数字最后出现的索引
            
            # 遍历历史记录，找到每个数字最后出现的位置
            for idx, hist_numbers in enumerate(history):
                if len(hist_numbers) == 3:
                    digit = hist_numbers[pos]
                    last_seen[digit] = idx
            
            # 计算遗漏期数
            current_idx = len(history)
            for digit in range(10):
                if last_seen[digit] == -1:
                    omission = current_idx  # 从未出现
                else:
                    omission = current_idx - last_seen[digit] - 1
                features[f'pos{pos}_digit{digit}_omission'] = omission
        
        # 当前号码的遗漏值
        for pos, digit in enumerate(numbers):
            features[f'pos{pos}_current_omission'] = features.get(
                f'pos{pos}_digit{digit}_omission', 0
            )
        
        return features


@register_feature
class RollingStatsFeature(BaseFeature):
    """
    滚动统计特征
    
    计算过去N期的和值、跨度等的均值、标准差、偏度
    """
    
    name = "rolling_stats"
    description = "滚动窗口统计特征（均值、标准差、偏度）"
    category = "statistical"
    
    def __init__(self, windows: List[int] = None):
        super().__init__()
        self.windows = windows or [5, 10, 30]
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        features = {}
        
        if history is None or len(history) == 0:
            # 无历史数据时返回默认值
            for window in self.windows:
                features[f'sum_mean_{window}'] = 0.0
                features[f'sum_std_{window}'] = 0.0
                features[f'span_mean_{window}'] = 0.0
                features[f'span_std_{window}'] = 0.0
            return features
        
        # 计算历史的和值和跨度
        sums = []
        spans = []
        for hist_numbers in history:
            if len(hist_numbers) == 3:
                sums.append(sum(hist_numbers))
                spans.append(max(hist_numbers) - min(hist_numbers))
        
        # 对每个窗口大小计算统计量
        for window in self.windows:
            if len(sums) < window:
                window_sums = sums
                window_spans = spans
            else:
                window_sums = sums[-window:]
                window_spans = spans[-window:]
            
            if len(window_sums) > 0:
                # 和值统计
                features[f'sum_mean_{window}'] = np.mean(window_sums)
                features[f'sum_std_{window}'] = np.std(window_sums)
                features[f'sum_min_{window}'] = np.min(window_sums)
                features[f'sum_max_{window}'] = np.max(window_sums)
                
                # 跨度统计
                features[f'span_mean_{window}'] = np.mean(window_spans)
                features[f'span_std_{window}'] = np.std(window_spans)
                
                # 偏度（需要至少3个样本）
                if len(window_sums) >= 3:
                    from scipy import stats
                    features[f'sum_skew_{window}'] = stats.skew(window_sums)
                else:
                    features[f'sum_skew_{window}'] = 0.0
            else:
                # 窗口内无数据
                features[f'sum_mean_{window}'] = 0.0
                features[f'sum_std_{window}'] = 0.0
                features[f'span_mean_{window}'] = 0.0
                features[f'span_std_{window}'] = 0.0
                features[f'sum_skew_{window}'] = 0.0
        
        return features


@register_feature
class RollingCorrelationFeature(BaseFeature):
    """
    滚动相关系数特征
    
    计算各位置之间的相关系数、位置与和值的相关系数
    """
    
    name = "rolling_correlation"
    description = "滚动窗口相关系数（位置间、位置与和值）"
    category = "statistical"
    
    def __init__(self, window: int = 30):
        super().__init__()
        self.window = window
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        features = {}
        
        if history is None or len(history) < 2:
            # 历史数据不足时返回默认值
            features['corr_d0_d1'] = 0.0
            features['corr_d0_d2'] = 0.0
            features['corr_d1_d2'] = 0.0
            features['corr_d0_sum'] = 0.0
            features['corr_d1_sum'] = 0.0
            features['corr_d2_sum'] = 0.0
            return features
        
        # 提取历史数据
        hist_array = np.array([h for h in history if len(h) == 3])
        if len(hist_array) < 2:
            return {
                'corr_d0_d1': 0.0,
                'corr_d0_d2': 0.0,
                'corr_d1_d2': 0.0,
                'corr_d0_sum': 0.0,
                'corr_d1_sum': 0.0,
                'corr_d2_sum': 0.0,
            }
        
        # 截取窗口
        if len(hist_array) > self.window:
            hist_array = hist_array[-self.window:]
        
        # 计算和值
        sums = hist_array.sum(axis=1)
        
        # 计算相关系数
        try:
            # 位置间相关
            features['corr_d0_d1'] = np.corrcoef(hist_array[:, 0], hist_array[:, 1])[0, 1]
            features['corr_d0_d2'] = np.corrcoef(hist_array[:, 0], hist_array[:, 2])[0, 1]
            features['corr_d1_d2'] = np.corrcoef(hist_array[:, 1], hist_array[:, 2])[0, 1]
            
            # 位置与和值相关
            features['corr_d0_sum'] = np.corrcoef(hist_array[:, 0], sums)[0, 1]
            features['corr_d1_sum'] = np.corrcoef(hist_array[:, 1], sums)[0, 1]
            features['corr_d2_sum'] = np.corrcoef(hist_array[:, 2], sums)[0, 1]
            
            # 处理NaN值
            for key in features:
                if np.isnan(features[key]):
                    features[key] = 0.0
                    
        except Exception as e:
            # 计算失败时返回0
            for key in ['corr_d0_d1', 'corr_d0_d2', 'corr_d1_d2', 
                       'corr_d0_sum', 'corr_d1_sum', 'corr_d2_sum']:
                features[key] = 0.0
        
        return features


@register_feature
class TrendFeature(BaseFeature):
    """
    趋势特征
    
    分析最近几期的变化趋势
    """
    
    name = "trend"
    description = "短期趋势特征（连续性、振幅等）"
    category = "statistical"
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        features = {}
        
        if history is None or len(history) == 0:
            features['digit0_delta'] = 0
            features['digit1_delta'] = 0
            features['digit2_delta'] = 0
            features['sum_delta'] = 0
            features['is_continuous'] = 0
            return features
        
        # 获取上一期数据
        prev_numbers = history[-1] if len(history[-1]) == 3 else [0, 0, 0]
        
        # 各位置的变化量
        features['digit0_delta'] = numbers[0] - prev_numbers[0]
        features['digit1_delta'] = numbers[1] - prev_numbers[1]
        features['digit2_delta'] = numbers[2] - prev_numbers[2]
        
        # 和值变化
        features['sum_delta'] = sum(numbers) - sum(prev_numbers)
        
        # 振幅（个位）
        features['digit2_amplitude'] = abs(features['digit2_delta'])
        
        # 是否有连续号码
        sorted_nums = sorted(numbers)
        is_continuous = (
            (sorted_nums[1] == sorted_nums[0] + 1 and sorted_nums[2] == sorted_nums[1] + 1) or
            (sorted_nums[1] == sorted_nums[0] + 1) or
            (sorted_nums[2] == sorted_nums[1] + 1)
        )
        features['is_continuous'] = int(is_continuous)
        
        return features
