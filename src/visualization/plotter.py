"""
可视化工具

生成走势图、遗漏图等报表
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非交互式后端

logger = logging.getLogger(__name__)


class Plotter:
    """可视化绘图工具"""
    
    def __init__(self, output_dir: str = './output'):
        """
        初始化绘图工具
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def plot_sum_trend(self, df: pd.DataFrame, periods: int = 100) -> str:
        """
        绘制和值走势图
        
        Args:
            df: 数据DataFrame（需包含numbers列）
            periods: 显示期数
            
        Returns:
            输出文件路径
        """
        # 计算和值
        sums = [sum(row['numbers']) for _, row in df.tail(periods).iterrows()]
        
        plt.figure(figsize=(15, 6))
        plt.plot(sums, marker='o', markersize=4, linewidth=1.5)
        plt.title('Sum Value Trend', fontsize=16)
        plt.xlabel('Period', fontsize=12)
        plt.ylabel('Sum', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        output_path = self.output_dir / 'sum_trend.png'
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        logger.info(f"Sum trend plot saved to {output_path}")
        return str(output_path)
    
    def plot_omission_chart(self, df: pd.DataFrame, position: int = 2) -> str:
        """
        绘制遗漏值柱状图
        
        Args:
            df: 数据DataFrame
            position: 位置（0=百位, 1=十位, 2=个位）
            
        Returns:
            输出文件路径
        """
        # 计算每个数字的遗漏值
        omissions = {d: 0 for d in range(10)}
        last_seen = {d: -1 for d in range(10)}
        
        for idx, row in df.iterrows():
            numbers = row['numbers']
            if len(numbers) == 3:
                digit = numbers[position]
                last_seen[digit] = idx
        
        current_idx = len(df)
        for digit in range(10):
            if last_seen[digit] == -1:
                omissions[digit] = current_idx
            else:
                omissions[digit] = current_idx - last_seen[digit] - 1
        
        # 绘制柱状图
        digits = list(range(10))
        omission_values = [omissions[d] for d in digits]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(digits, omission_values, color='steelblue', alpha=0.7)
        
        # 标注数值
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=10)
        
        position_names = ['Hundreds', 'Tens', 'Units']
        plt.title(f'Omission Chart - {position_names[position]} Position', fontsize=16)
        plt.xlabel('Digit', fontsize=12)
        plt.ylabel('Omission Periods', fontsize=12)
        plt.xticks(digits)
        plt.grid(True, axis='y', alpha=0.3)
        plt.tight_layout()
        
        output_path = self.output_dir / f'omission_pos{position}.png'
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        logger.info(f"Omission chart saved to {output_path}")
        return str(output_path)
    
    def plot_capital_curve(self, capital_curve: List[float], baseline_curve: Optional[List[float]] = None) -> str:
        """
        绘制资金曲线
        
        Args:
            capital_curve: 资金曲线
            baseline_curve: 基准曲线（可选）
            
        Returns:
            输出文件路径
        """
        plt.figure(figsize=(15, 7))
        
        periods = range(len(capital_curve))
        plt.plot(periods, capital_curve, label='Model Strategy', linewidth=2, color='#2E86AB')
        
        if baseline_curve:
            plt.plot(periods, baseline_curve, label='Random Baseline', 
                    linewidth=2, color='#A23B72', linestyle='--')
        
        plt.axhline(y=capital_curve[0], color='gray', linestyle=':', alpha=0.5, label='Initial Capital')
        
        plt.title('Capital Curve - Backtest Results', fontsize=16)
        plt.xlabel('Period', fontsize=12)
        plt.ylabel('Capital', fontsize=12)
        plt.legend(fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        output_path = self.output_dir / 'capital_curve.png'
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        logger.info(f"Capital curve saved to {output_path}")
        return str(output_path)
    
    def plot_digit_frequency(self, df: pd.DataFrame, periods: int = 100) -> str:
        """
        绘制数字频率分布
        
        Args:
            df: 数据DataFrame
            periods: 统计期数
            
        Returns:
            输出文件路径
        """
        # 统计频率
        freq = {d: 0 for d in range(10)}
        for _, row in df.tail(periods).iterrows():
            for digit in row['numbers']:
                freq[digit] += 1
        
        digits = list(range(10))
        frequencies = [freq[d] for d in digits]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(digits, frequencies, color='coral', alpha=0.7)
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=10)
        
        plt.title(f'Digit Frequency Distribution (Last {periods} Periods)', fontsize=16)
        plt.xlabel('Digit', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.xticks(digits)
        plt.grid(True, axis='y', alpha=0.3)
        plt.tight_layout()
        
        output_path = self.output_dir / 'digit_frequency.png'
        plt.savefig(output_path, dpi=150)
        plt.close()
        
        logger.info(f"Digit frequency plot saved to {output_path}")
        return str(output_path)
