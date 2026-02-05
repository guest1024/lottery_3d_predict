"""
策略引擎

根据模型预测结果生成最佳100注购买方案
"""
import logging
from typing import List, Tuple, Dict, Any, Optional
from itertools import combinations, permutations
import numpy as np

logger = logging.getLogger(__name__)


class StrategyEngine:
    """
    策略引擎
    
    负责：
    1. 定胆：选择高概率数字
    2. 杀号：剔除低概率数字
    3. 生成组合
    4. 过滤：根据和值、AC值等条件过滤
    5. 排序：按联合概率排序
    6. 风控：置信度检查
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.5,
        top_n: int = 100,
    ):
        """
        初始化策略引擎
        
        Args:
            confidence_threshold: 最低置信度阈值
            top_n: 输出注数
        """
        self.confidence_threshold = confidence_threshold
        self.top_n = top_n
    
    def generate_recommendations(
        self,
        predictions: Dict[str, np.ndarray],
        strategy: str = 'balanced',
    ) -> Dict[str, Any]:
        """
        生成推荐方案
        
        Args:
            predictions: 模型预测结果
                - digit_probs: (10,) 0-9每个数字的概率
                - shape_probs: (3,) 组六/组三/豹子概率
                - sum_probs: (28,) 和值0-27概率
                - ac_probs: (3,) AC值1-3概率
            strategy: 策略类型 ('conservative', 'balanced', 'aggressive')
            
        Returns:
            推荐方案字典
        """
        # 提取预测概率
        digit_probs = predictions['digit_probs'].flatten()
        shape_probs = predictions['shape_probs'].flatten()
        sum_probs = predictions['sum_probs'].flatten()
        ac_probs = predictions['ac_probs'].flatten()
        
        # 检查置信度
        max_confidence = np.max(digit_probs)
        if max_confidence < self.confidence_threshold:
            logger.warning(f"Low confidence: {max_confidence:.3f}, consider skipping")
            return {
                'status': 'low_confidence',
                'confidence': float(max_confidence),
                'recommendations': [],
                'message': '模型置信度过低，建议观望',
            }
        
        # Step A: 定胆（选择高概率数字）
        if strategy == 'conservative':
            n_core = 3
            n_kill = 4
        elif strategy == 'aggressive':
            n_core = 6
            n_kill = 1
        else:  # balanced
            n_core = 5
            n_kill = 2
        
        core_digits = self._select_core_digits(digit_probs, n_core)
        
        # Step B: 杀号（剔除低概率数字）
        kill_digits = self._select_kill_digits(digit_probs, n_kill)
        available_digits = [d for d in range(10) if d not in kill_digits]
        
        logger.info(f"Core digits: {core_digits}, Kill digits: {kill_digits}")
        
        # Step C: 生成组合
        combinations_list = self._generate_combinations(available_digits, core_digits)
        
        logger.info(f"Generated {len(combinations_list)} initial combinations")
        
        # Step D: 过滤
        filtered_combinations = self._filter_combinations(
            combinations_list,
            sum_probs=sum_probs,
            ac_probs=ac_probs,
            shape_probs=shape_probs,
        )
        
        logger.info(f"After filtering: {len(filtered_combinations)} combinations")
        
        # Step E: 评分和排序
        scored_combinations = self._score_combinations(
            filtered_combinations,
            digit_probs=digit_probs,
        )
        
        # 截取Top N
        top_combinations = scored_combinations[:self.top_n]
        
        # 格式化输出
        recommendations = [
            {
                'numbers': comb,
                'score': score,
                'probability': float(score),  # 使用score作为理论胜率
                'number_str': f"{comb[0]}{comb[1]}{comb[2]}",
            }
            for comb, score in top_combinations
        ]
        
        return {
            'status': 'success',
            'confidence': float(max_confidence),
            'core_digits': core_digits,
            'kill_digits': kill_digits,
            'total_combinations': len(combinations_list),
            'filtered_combinations': len(filtered_combinations),
            'recommendations': recommendations,
            'summary': {
                'top_shape': self._get_shape_name(np.argmax(shape_probs)),
                'top_sum_range': self._get_top_sum_range(sum_probs),
                'top_ac_value': int(np.argmax(ac_probs)) + 1,
            }
        }
    
    def _select_core_digits(self, digit_probs: np.ndarray, n: int) -> List[int]:
        """选择高概率的胆码"""
        top_indices = np.argsort(digit_probs)[-n:]
        return sorted(top_indices.tolist())
    
    def _select_kill_digits(self, digit_probs: np.ndarray, n: int) -> List[int]:
        """选择低概率的杀号"""
        bottom_indices = np.argsort(digit_probs)[:n]
        return bottom_indices.tolist()
    
    def _generate_combinations(
        self,
        available_digits: List[int],
        core_digits: List[int],
    ) -> List[Tuple[int, int, int]]:
        """
        生成所有可能的组合
        
        策略：至少包含一个胆码
        """
        all_combinations = set()
        
        # 生成所有三位数组合（允许重复）
        for d0 in available_digits:
            for d1 in available_digits:
                for d2 in available_digits:
                    # 至少包含一个胆码
                    if any(d in core_digits for d in [d0, d1, d2]):
                        all_combinations.add((d0, d1, d2))
        
        return list(all_combinations)
    
    def _filter_combinations(
        self,
        combinations_list: List[Tuple[int, int, int]],
        sum_probs: np.ndarray,
        ac_probs: np.ndarray,
        shape_probs: np.ndarray,
        top_k_sum: int = 10,
        top_k_ac: int = 2,
    ) -> List[Tuple[int, int, int]]:
        """
        根据和值、AC值、形态过滤组合
        """
        # 获取高概率的和值范围
        top_sum_indices = np.argsort(sum_probs)[-top_k_sum:]
        valid_sums = set(top_sum_indices.tolist())
        
        # 获取高概率的AC值
        top_ac_indices = np.argsort(ac_probs)[-top_k_ac:]
        valid_ac_values = set((i + 1) for i in top_ac_indices.tolist())
        
        # 过滤
        filtered = []
        for comb in combinations_list:
            # 检查和值
            comb_sum = sum(comb)
            if comb_sum not in valid_sums:
                continue
            
            # 检查AC值
            ac_value = self._compute_ac_value(comb)
            if ac_value not in valid_ac_values:
                continue
            
            filtered.append(comb)
        
        return filtered
    
    def _compute_ac_value(self, numbers: Tuple[int, int, int]) -> int:
        """计算AC值"""
        diffs = set()
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                diffs.add(abs(numbers[i] - numbers[j]))
        return len(diffs)
    
    def _score_combinations(
        self,
        combinations_list: List[Tuple[int, int, int]],
        digit_probs: np.ndarray,
    ) -> List[Tuple[Tuple[int, int, int], float]]:
        """
        为组合评分并排序
        
        使用联合概率：P(d0) * P(d1) * P(d2)
        """
        scored = []
        for comb in combinations_list:
            # 计算联合概率
            prob = digit_probs[comb[0]] * digit_probs[comb[1]] * digit_probs[comb[2]]
            scored.append((comb, prob))
        
        # 按概率降序排序
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored
    
    def _get_shape_name(self, shape_idx: int) -> str:
        """获取形态名称"""
        names = ['组六', '组三', '豹子']
        return names[shape_idx]
    
    def _get_top_sum_range(self, sum_probs: np.ndarray, top_k: int = 5) -> str:
        """获取高概率和值范围"""
        top_indices = np.argsort(sum_probs)[-top_k:]
        sum_range = f"{min(top_indices)}-{max(top_indices)}"
        return sum_range
    
    def analyze_recommendations(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """
        分析推荐结果的统计特征
        """
        if not recommendations:
            return {}
        
        numbers_list = [rec['numbers'] for rec in recommendations]
        
        # 数字频率
        digit_freq = {d: 0 for d in range(10)}
        for numbers in numbers_list:
            for d in numbers:
                digit_freq[d] += 1
        
        # 和值分布
        sums = [sum(numbers) for numbers in numbers_list]
        
        # AC值分布
        ac_values = [self._compute_ac_value(numbers) for numbers in numbers_list]
        
        # 形态分布
        shapes = []
        for numbers in numbers_list:
            unique = len(set(numbers))
            if unique == 1:
                shapes.append('豹子')
            elif unique == 2:
                shapes.append('组三')
            else:
                shapes.append('组六')
        
        from collections import Counter
        
        analysis = {
            'digit_frequency': digit_freq,
            'sum_stats': {
                'min': min(sums),
                'max': max(sums),
                'mean': np.mean(sums),
                'std': np.std(sums),
            },
            'ac_distribution': dict(Counter(ac_values)),
            'shape_distribution': dict(Counter(shapes)),
        }
        
        return analysis
