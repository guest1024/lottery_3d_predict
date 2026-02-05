"""
特征工程基础架构

提供插件式的特征注册和管理机制
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Type, Optional
import logging

logger = logging.getLogger(__name__)


class BaseFeature(ABC):
    """
    特征提取基类
    
    所有具体特征类必须继承此类并实现extract方法
    """
    
    # 特征名称（子类必须定义）
    name: str = "base_feature"
    
    # 特征描述
    description: str = "Base feature class"
    
    # 特征类别
    category: str = "basic"
    
    @abstractmethod
    def extract(self, numbers: List[int], history: Optional[List[List[int]]] = None) -> Dict[str, Any]:
        """
        提取特征
        
        Args:
            numbers: 当前号码 [百位, 十位, 个位]
            history: 历史号码序列，用于计算统计型特征
            
        Returns:
            特征字典 {feature_name: feature_value}
        """
        pass
    
    def validate(self, numbers: List[int]) -> bool:
        """
        验证输入数据
        
        Args:
            numbers: 号码列表
            
        Returns:
            是否有效
        """
        if not isinstance(numbers, list):
            return False
        if len(numbers) != 3:
            return False
        if not all(isinstance(n, int) and 0 <= n <= 9 for n in numbers):
            return False
        return True
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"


class FeatureRegistry:
    """
    特征注册表
    
    使用单例模式管理所有注册的特征类
    """
    
    _instance: Optional['FeatureRegistry'] = None
    _features: Dict[str, Type[BaseFeature]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, feature_class: Type[BaseFeature]):
        """
        注册特征类
        
        Args:
            feature_class: 特征类（必须继承BaseFeature）
        """
        if not issubclass(feature_class, BaseFeature):
            raise TypeError(f"{feature_class} must inherit from BaseFeature")
        
        name = feature_class.name
        if name in self._features:
            logger.warning(f"Feature '{name}' already registered, overwriting")
        
        self._features[name] = feature_class
        logger.info(f"Registered feature: {name} ({feature_class.__name__})")
    
    def get(self, name: str) -> Optional[Type[BaseFeature]]:
        """
        获取特征类
        
        Args:
            name: 特征名称
            
        Returns:
            特征类或None
        """
        return self._features.get(name)
    
    def get_all(self) -> Dict[str, Type[BaseFeature]]:
        """
        获取所有注册的特征类
        
        Returns:
            特征字典 {name: feature_class}
        """
        return self._features.copy()
    
    def get_by_category(self, category: str) -> Dict[str, Type[BaseFeature]]:
        """
        按类别获取特征
        
        Args:
            category: 特征类别
            
        Returns:
            该类别的所有特征
        """
        return {
            name: cls for name, cls in self._features.items()
            if cls.category == category
        }
    
    def list_features(self) -> List[Dict[str, str]]:
        """
        列出所有特征信息
        
        Returns:
            特征信息列表
        """
        return [
            {
                'name': cls.name,
                'class': cls.__name__,
                'category': cls.category,
                'description': cls.description,
            }
            for cls in self._features.values()
        ]
    
    def clear(self):
        """清空注册表（主要用于测试）"""
        self._features.clear()


# 全局注册表实例
registry = FeatureRegistry()


def register_feature(feature_class: Type[BaseFeature]) -> Type[BaseFeature]:
    """
    特征注册装饰器
    
    使用示例:
        @register_feature
        class MyFeature(BaseFeature):
            name = "my_feature"
            
            def extract(self, numbers, history):
                return {'my_value': 42}
    
    Args:
        feature_class: 特征类
        
    Returns:
        原特征类（支持链式调用）
    """
    registry.register(feature_class)
    return feature_class
