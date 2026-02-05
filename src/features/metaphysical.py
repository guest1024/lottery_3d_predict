"""
玄学逻辑特征模块

包含五行生克、位置互换等基于传统理论的特征
"""
from typing import List, Dict, Any, Optional
from .base import BaseFeature, register_feature


@register_feature
class WuXingFeature(BaseFeature):
    """
    五行特征
    
    将数字映射到五行（金木水火土），分析生克关系
    
    映射规则：
    - 0, 5 -> 土 (Earth)
    - 1, 6 -> 水 (Water)
    - 2, 7 -> 火 (Fire)
    - 3, 8 -> 木 (Wood)
    - 4, 9 -> 金 (Metal)
    
    生克关系：
    - 相生：木生火、火生土、土生金、金生水、水生木
    - 相克：木克土、土克水、水克火、火克金、金克木
    """
    
    name = "wuxing"
    description = "五行生克关系特征"
    category = "metaphysical"
    
    # 数字到五行的映射
    ELEMENT_MAP = {
        0: 'earth', 5: 'earth',
        1: 'water', 6: 'water',
        2: 'fire', 7: 'fire',
        3: 'wood', 8: 'wood',
        4: 'metal', 9: 'metal',
    }
    
    # 五行编码
    ELEMENT_CODE = {
        'wood': 0, 'fire': 1, 'earth': 2, 'metal': 3, 'water': 4
    }
    
    # 相生关系（A生B）
    GENERATES = {
        'wood': 'fire',
        'fire': 'earth',
        'earth': 'metal',
        'metal': 'water',
        'water': 'wood',
    }
    
    # 相克关系（A克B）
    CONQUERS = {
        'wood': 'earth',
        'earth': 'water',
        'water': 'fire',
        'fire': 'metal',
        'metal': 'wood',
    }
    
    def _get_element(self, number: int) -> str:
        """获取数字对应的五行"""
        return self.ELEMENT_MAP[number]
    
    def _check_relation(self, elem1: str, elem2: str) -> Dict[str, int]:
        """检查两个五行之间的关系"""
        return {
            'generates': int(self.GENERATES.get(elem1) == elem2),  # elem1生elem2
            'generated_by': int(self.GENERATES.get(elem2) == elem1),  # elem2生elem1
            'conquers': int(self.CONQUERS.get(elem1) == elem2),  # elem1克elem2
            'conquered_by': int(self.CONQUERS.get(elem2) == elem1),  # elem2克elem1
        }
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        features = {}
        
        # 当前号码的五行
        elements = [self._get_element(n) for n in numbers]
        features['element_0'] = self.ELEMENT_CODE[elements[0]]
        features['element_1'] = self.ELEMENT_CODE[elements[1]]
        features['element_2'] = self.ELEMENT_CODE[elements[2]]
        
        # 内部生克关系
        rel_01 = self._check_relation(elements[0], elements[1])
        rel_02 = self._check_relation(elements[0], elements[2])
        rel_12 = self._check_relation(elements[1], elements[2])
        
        features['internal_generates'] = (
            rel_01['generates'] + rel_02['generates'] + rel_12['generates']
        )
        features['internal_conquers'] = (
            rel_01['conquers'] + rel_02['conquers'] + rel_12['conquers']
        )
        
        # 与上期的生克关系
        if history is not None and len(history) > 0:
            prev_numbers = history[-1]
            if len(prev_numbers) == 3:
                prev_elements = [self._get_element(n) for n in prev_numbers]
                
                # 计算当前各位与上期对应位的生克
                for i in range(3):
                    rel = self._check_relation(prev_elements[i], elements[i])
                    features[f'prev_to_curr_{i}_generates'] = rel['generates']
                    features[f'prev_to_curr_{i}_conquers'] = rel['conquers']
        else:
            for i in range(3):
                features[f'prev_to_curr_{i}_generates'] = 0
                features[f'prev_to_curr_{i}_conquers'] = 0
        
        return features


@register_feature
class PatternShiftFeature(BaseFeature):
    """
    位置互换特征（公仔换位）
    
    检测号码在不同位置间的互换模式
    例如：上期十位的5出现在本期百位
    """
    
    name = "pattern_shift"
    description = "位置互换模式特征"
    category = "metaphysical"
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        features = {
            'shift_0_to_1': 0,  # 百位移到十位
            'shift_0_to_2': 0,  # 百位移到个位
            'shift_1_to_0': 0,  # 十位移到百位
            'shift_1_to_2': 0,  # 十位移到个位
            'shift_2_to_0': 0,  # 个位移到百位
            'shift_2_to_1': 0,  # 个位移到十位
            'any_shift': 0,     # 是否有任何互换
        }
        
        if history is None or len(history) == 0:
            return features
        
        prev_numbers = history[-1]
        if len(prev_numbers) != 3:
            return features
        
        # 检测各种位置互换
        if prev_numbers[0] == numbers[1]:
            features['shift_0_to_1'] = 1
        if prev_numbers[0] == numbers[2]:
            features['shift_0_to_2'] = 1
        if prev_numbers[1] == numbers[0]:
            features['shift_1_to_0'] = 1
        if prev_numbers[1] == numbers[2]:
            features['shift_1_to_2'] = 1
        if prev_numbers[2] == numbers[0]:
            features['shift_2_to_0'] = 1
        if prev_numbers[2] == numbers[1]:
            features['shift_2_to_1'] = 1
        
        # 是否有任何互换
        features['any_shift'] = int(any(features[k] for k in features if k.startswith('shift_')))
        
        return features


@register_feature
class RepeatFeature(BaseFeature):
    """
    重复号码特征
    
    检测本期与上期相同的号码
    """
    
    name = "repeat"
    description = "重复号码特征"
    category = "metaphysical"
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        features = {
            'repeat_0': 0,  # 百位重复
            'repeat_1': 0,  # 十位重复
            'repeat_2': 0,  # 个位重复
            'repeat_count': 0,  # 重复位数
            'repeat_any': 0,  # 是否有重复
        }
        
        if history is None or len(history) == 0:
            return features
        
        prev_numbers = history[-1]
        if len(prev_numbers) != 3:
            return features
        
        # 检测各位置是否重复
        for i in range(3):
            if numbers[i] == prev_numbers[i]:
                features[f'repeat_{i}'] = 1
                features['repeat_count'] += 1
        
        features['repeat_any'] = int(features['repeat_count'] > 0)
        
        return features


@register_feature
class ConsecutiveFeature(BaseFeature):
    """
    连续号码特征
    
    检测连续号、斜连号等模式
    """
    
    name = "consecutive"
    description = "连续号码特征（连号、斜连）"
    category = "metaphysical"
    
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        sorted_nums = sorted(numbers)
        
        features = {
            'is_full_consecutive': 0,  # 完全连续（如123）
            'has_pair_consecutive': 0,  # 有两个连续
            'consecutive_count': 0,     # 连续对数
        }
        
        # 检测完全连续
        if (sorted_nums[1] == sorted_nums[0] + 1 and 
            sorted_nums[2] == sorted_nums[1] + 1):
            features['is_full_consecutive'] = 1
            features['consecutive_count'] = 2
        # 检测部分连续
        elif sorted_nums[1] == sorted_nums[0] + 1 or sorted_nums[2] == sorted_nums[1] + 1:
            features['has_pair_consecutive'] = 1
            features['consecutive_count'] = 1
        
        # 斜连（与上期的连续关系）
        features['has_diagonal'] = 0
        if history is not None and len(history) > 0:
            prev_numbers = history[-1]
            if len(prev_numbers) == 3:
                # 检查是否有斜连关系
                for curr in numbers:
                    for prev in prev_numbers:
                        if abs(curr - prev) == 1:
                            features['has_diagonal'] = 1
                            break
                    if features['has_diagonal']:
                        break
        
        return features
