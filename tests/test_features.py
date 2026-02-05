"""
特征工程模块测试
"""
import pytest
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from features.base import BaseFeature, register_feature, FeatureRegistry
from features.morphology import SumFeature, ACValueFeature, ShapeFeature
from features.engineer import FeatureEngineer


class TestBaseFeature:
    """测试基础特征类"""
    
    def test_validate(self):
        """测试输入验证"""
        feature = SumFeature()
        
        # 有效输入
        assert feature.validate([1, 2, 3]) is True
        assert feature.validate([0, 0, 0]) is True
        assert feature.validate([9, 9, 9]) is True
        
        # 无效输入
        assert feature.validate([1, 2]) is False  # 长度不足
        assert feature.validate([1, 2, 3, 4]) is False  # 长度过长
        assert feature.validate([1, 2, 10]) is False  # 数字超范围
        assert feature.validate("123") is False  # 类型错误


class TestMorphologyFeatures:
    """测试形态特征"""
    
    def test_sum_feature(self):
        """测试和值特征"""
        feature = SumFeature()
        result = feature.extract([1, 2, 3])
        
        assert result['value'] == 6
        assert result['mod_3'] == 0
        assert result['tail'] == 6
    
    def test_ac_value_feature(self):
        """测试AC值特征"""
        feature = ACValueFeature()
        
        # AC=1: 豹子
        result1 = feature.extract([1, 1, 1])
        assert result1['value'] == 1
        assert result1['is_ac1'] == 1
        
        # AC=2: 对子或部分三不同
        result2 = feature.extract([1, 2, 3])
        assert result2['value'] == 2
        assert result2['is_ac2'] == 1
        
        # AC=3: 完全随机
        result3 = feature.extract([0, 3, 7])
        assert result3['value'] == 3
        assert result3['is_ac3'] == 1
    
    def test_shape_feature(self):
        """测试形态特征"""
        feature = ShapeFeature()
        
        # 豹子
        result1 = feature.extract([5, 5, 5])
        assert result1['is_leopard'] == 1
        assert result1['unique_count'] == 1
        
        # 组三
        result2 = feature.extract([1, 1, 2])
        assert result2['is_group3'] == 1
        assert result2['unique_count'] == 2
        
        # 组六
        result3 = feature.extract([1, 2, 3])
        assert result3['is_group6'] == 1
        assert result3['unique_count'] == 3


class TestFeatureRegistry:
    """测试特征注册表"""
    
    def test_registry_singleton(self):
        """测试单例模式"""
        registry1 = FeatureRegistry()
        registry2 = FeatureRegistry()
        assert registry1 is registry2
    
    def test_feature_registration(self):
        """测试特征注册"""
        registry = FeatureRegistry()
        
        # 检查已注册的特征
        all_features = registry.get_all()
        assert 'sum' in all_features
        assert 'ac_value' in all_features
        assert 'shape' in all_features


class TestFeatureEngineer:
    """测试特征工程引擎"""
    
    def test_extract_single(self):
        """测试单样本特征提取"""
        engineer = FeatureEngineer()
        features = engineer.extract_single([1, 2, 3])
        
        # 检查是否包含各类特征
        assert any('sum' in key for key in features.keys())
        assert any('ac_value' in key for key in features.keys())
        assert any('shape' in key for key in features.keys())
    
    def test_extract_with_history(self):
        """测试带历史数据的特征提取"""
        engineer = FeatureEngineer()
        history = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        features = engineer.extract_single([2, 3, 4], history)
        
        # 应该包含统计特征
        assert features is not None
        assert len(features) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
