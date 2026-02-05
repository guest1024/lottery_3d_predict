"""
形态特征模块

包含AC值、形态编码、和值、跨度等基础形态特征
"""
from typing import List, Dict, Any, Optional
import numpy as np
from collections import Counter

from .base import BaseFeature, register_feature


@register_feature
class SumFeature(BaseFeature):
    """和值特征"""
    
    name = "sum"
    description = "三个号码的和值 (0-27)"
    category = "morphology"
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        total = sum(numbers)
        return {
            'value': total,
            'normalized': total / 27.0,  # 归一化到[0, 1]
            'mod_3': total % 3,  # 和尾012路
            'tail': total % 10,  # 和尾个位数
        }


@register_feature
class SpanFeature(BaseFeature):
    """跨度特征"""
    
    name = "span"
    description = "最大值与最小值的差 (0-9)"
    category = "morphology"
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        span = max(numbers) - min(numbers)
        return {
            'value': span,
            'normalized': span / 9.0,
            'is_large': int(span >= 5),  # 大跨度
            'is_small': int(span <= 3),  # 小跨度
        }


@register_feature
class ACValueFeature(BaseFeature):
    """
    AC值特征（算术复杂性）
    
    AC值定义：三个号码两两差值的去重个数
    例如：[1, 2, 3]
        - 差值：|1-2|=1, |1-3|=2, |2-3|=1
        - 去重：{1, 2}
        - AC值：2
    
    AC值范围：1-3
    - AC=1: 豹子（如111）或特殊对子
    - AC=2: 普通对子或部分三不同
    - AC=3: 完全随机的三不同
    """
    
    name = "ac_value"
    description = "算术复杂性（AC值），衡量号码的离散度"
    category = "morphology"
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        # 计算两两差值
        diffs = set()
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                diffs.add(abs(numbers[i] - numbers[j]))
        
        ac_value = len(diffs)
        
        return {
            'value': ac_value,
            'is_ac1': int(ac_value == 1),
            'is_ac2': int(ac_value == 2),
            'is_ac3': int(ac_value == 3),
        }


@register_feature
class ShapeFeature(BaseFeature):
    """形态特征（组三/组六/豹子）"""
    
    name = "shape"
    description = "号码形态：豹子（三同）、组三（对子）、组六（三不同）"
    category = "morphology"
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        counter = Counter(numbers)
        unique_count = len(counter)
        
        # 豹子：三个号码相同
        is_leopard = unique_count == 1
        
        # 组三：有两个号码相同
        is_group3 = unique_count == 2
        
        # 组六：三个号码都不同
        is_group6 = unique_count == 3
        
        return {
            'is_leopard': int(is_leopard),
            'is_group3': int(is_group3),
            'is_group6': int(is_group6),
            'unique_count': unique_count,
        }


@register_feature
class RatioFeature(BaseFeature):
    """比例特征（奇偶比、大小比、质合比）"""
    
    name = "ratio"
    description = "奇偶比、大小比、质合比"
    category = "morphology"
    
    # 质数列表
    PRIMES = {2, 3, 5, 7}
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        # 奇偶比
        odd_count = sum(1 for n in numbers if n % 2 == 1)
        even_count = 3 - odd_count
        
        # 大小比（5及以上为大）
        large_count = sum(1 for n in numbers if n >= 5)
        small_count = 3 - large_count
        
        # 质合比
        prime_count = sum(1 for n in numbers if n in self.PRIMES)
        composite_count = 3 - prime_count
        
        return {
            'odd_count': odd_count,
            'even_count': even_count,
            'odd_ratio': odd_count / 3.0,
            'large_count': large_count,
            'small_count': small_count,
            'large_ratio': large_count / 3.0,
            'prime_count': prime_count,
            'composite_count': composite_count,
            'prime_ratio': prime_count / 3.0,
        }


@register_feature
class Mod3Feature(BaseFeature):
    """012路特征"""
    
    name = "mod3"
    description = "号码除以3的余数（012路分析）"
    category = "morphology"
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        mods = [n % 3 for n in numbers]
        counter = Counter(mods)
        
        return {
            'digit0_mod3': mods[0],
            'digit1_mod3': mods[1],
            'digit2_mod3': mods[2],
            'mod0_count': counter.get(0, 0),
            'mod1_count': counter.get(1, 0),
            'mod2_count': counter.get(2, 0),
        }


@register_feature
class DigitDistributionFeature(BaseFeature):
    """数字分布特征"""
    
    name = "digit_distribution"
    description = "0-9各个数字的分布情况"
    category = "morphology"
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        features = {}
        
        # 每个位置的数字
        features['digit_0'] = numbers[0]  # 百位
        features['digit_1'] = numbers[1]  # 十位
        features['digit_2'] = numbers[2]  # 个位
        
        # 归一化
        features['digit_0_norm'] = numbers[0] / 9.0
        features['digit_1_norm'] = numbers[1] / 9.0
        features['digit_2_norm'] = numbers[2] / 9.0
        
        # 最大最小值
        features['max_digit'] = max(numbers)
        features['min_digit'] = min(numbers)
        features['median_digit'] = sorted(numbers)[1]
        
        return features
