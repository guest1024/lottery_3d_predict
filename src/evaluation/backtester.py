"""
回测与评估模块

实现滚动窗口回测和Monte Carlo基准对比
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from tqdm import tqdm

logger = logging.getLogger(__name__)


class Backtester:
    """
    回测器
    
    使用Walk-Forward Validation进行滚动回测
    """
    
    def __init__(
        self,
        initial_capital: float = 20000.0,
        cost_per_bet: float = 2.0,
        prize_group6: float = 160.0,
        prize_group3: float = 320.0,
        prize_leopard: float = 1000.0,
    ):
        """
        初始化回测器
        
        Args:
            initial_capital: 初始资金
            cost_per_bet: 每注成本
            prize_group6: 组六奖金
            prize_group3: 组三奖金
            prize_leopard: 豹子奖金
        """
        self.initial_capital = initial_capital
        self.cost_per_bet = cost_per_bet
        self.prize_group6 = prize_group6
        self.prize_group3 = prize_group3
        self.prize_leopard = prize_leopard
    
    def run_backtest(
        self,
        test_data: pd.DataFrame,
        model,
        strategy_engine,
        window_size: int = 30,
        num_bets: int = 100,
    ) -> Dict[str, Any]:
        """
        执行回测
        
        Args:
            test_data: 测试数据（必须包含'numbers'列）
            model: 训练好的模型
            strategy_engine: 策略引擎
            window_size: 历史窗口大小
            num_bets: 每期购买注数
            
        Returns:
            回测结果字典
        """
        import torch
        
        capital = self.initial_capital
        capital_curve = [capital]
        trades = []
        
        logger.info(f"Starting backtest: {len(test_data)} periods")
        
        for i in tqdm(range(window_size, len(test_data)), desc="Backtesting"):
            # 获取历史数据
            history = test_data.iloc[i - window_size:i]
            history_numbers = [row['numbers'] for _, row in history.iterrows()]
            
            # 准备模型输入
            X = torch.tensor(history_numbers, dtype=torch.long).unsqueeze(0)  # (1, window, 3)
            
            # 模型预测
            predictions = model.predict(X)
            
            # 生成推荐
            recommendations = strategy_engine.generate_recommendations(predictions)
            
            if recommendations['status'] != 'success':
                # 置信度过低，不投注
                trades.append({
                    'period': i,
                    'action': 'skip',
                    'confidence': recommendations.get('confidence', 0),
                    'cost': 0,
                    'profit': 0,
                    'capital': capital,
                })
                capital_curve.append(capital)
                continue
            
            # 获取实际结果
            actual_numbers = tuple(test_data.iloc[i]['numbers'])
            
            # 投注前N注
            bets = recommendations['recommendations'][:num_bets]
            cost = len(bets) * self.cost_per_bet
            
            # 检查是否中奖
            hit = False
            prize = 0
            for bet in bets:
                bet_numbers = bet['numbers']
                if self._check_win(bet_numbers, actual_numbers):
                    hit = True
                    prize += self._calculate_prize(bet_numbers)
            
            # 更新资金
            profit = prize - cost
            capital += profit
            capital_curve.append(capital)
            
            # 记录交易
            trades.append({
                'period': i,
                'action': 'bet',
                'num_bets': len(bets),
                'cost': cost,
                'prize': prize,
                'profit': profit,
                'capital': capital,
                'hit': hit,
                'actual_numbers': actual_numbers,
                'confidence': recommendations['confidence'],
            })
        
        # 计算统计指标
        stats = self._calculate_statistics(trades, capital_curve)
        
        return {
            'trades': trades,
            'capital_curve': capital_curve,
            'statistics': stats,
        }
    
    def run_monte_carlo_baseline(
        self,
        test_data: pd.DataFrame,
        num_simulations: int = 1000,
        num_bets: int = 100,
    ) -> Dict[str, Any]:
        """
        运行Monte Carlo随机基准测试
        
        Args:
            test_data: 测试数据
            num_simulations: 模拟次数
            num_bets: 每期购买注数
            
        Returns:
            基准测试结果
        """
        all_final_capitals = []
        all_roi = []
        
        logger.info(f"Running Monte Carlo baseline: {num_simulations} simulations")
        
        for sim in tqdm(range(num_simulations), desc="Monte Carlo"):
            capital = self.initial_capital
            
            for i in range(len(test_data)):
                # 随机生成投注
                random_bets = [
                    tuple(np.random.randint(0, 10, size=3))
                    for _ in range(num_bets)
                ]
                
                # 获取实际结果
                actual_numbers = tuple(test_data.iloc[i]['numbers'])
                
                # 计算成本和奖金
                cost = num_bets * self.cost_per_bet
                prize = 0
                for bet in random_bets:
                    if self._check_win(bet, actual_numbers):
                        prize += self._calculate_prize(bet)
                
                # 更新资金
                capital += prize - cost
            
            all_final_capitals.append(capital)
            all_roi.append((capital - self.initial_capital) / self.initial_capital)
        
        # 统计
        final_capitals = np.array(all_final_capitals)
        roi_array = np.array(all_roi)
        
        stats = {
            'mean_final_capital': np.mean(final_capitals),
            'std_final_capital': np.std(final_capitals),
            'mean_roi': np.mean(roi_array),
            'std_roi': np.std(roi_array),
            'percentile_5': np.percentile(roi_array, 5),
            'percentile_95': np.percentile(roi_array, 95),
            'win_rate': np.sum(final_capitals > self.initial_capital) / num_simulations,
        }
        
        return {
            'final_capitals': final_capitals.tolist(),
            'roi_array': roi_array.tolist(),
            'statistics': stats,
        }
    
    def _check_win(self, bet: Tuple[int, ...], actual: Tuple[int, ...]) -> bool:
        """检查是否中奖（组选）"""
        return sorted(bet) == sorted(actual)
    
    def _calculate_prize(self, numbers: Tuple[int, ...]) -> float:
        """计算奖金"""
        unique_count = len(set(numbers))
        if unique_count == 1:
            return self.prize_leopard
        elif unique_count == 2:
            return self.prize_group3
        else:
            return self.prize_group6
    
    def _calculate_statistics(self, trades: List[Dict], capital_curve: List[float]) -> Dict:
        """计算统计指标"""
        df_trades = pd.DataFrame(trades)
        
        # 基本统计
        total_trades = len(df_trades)
        bet_trades = df_trades[df_trades['action'] == 'bet']
        
        if len(bet_trades) == 0:
            return {
                'total_trades': total_trades,
                'bet_count': 0,
                'skip_count': total_trades,
                'win_count': 0,
                'win_rate': 0,
                'total_cost': 0,
                'total_prize': 0,
                'total_profit': 0,
                'roi': 0,
                'max_drawdown': 0,
                'final_capital': capital_curve[-1] if capital_curve else self.initial_capital,
            }
        
        win_count = bet_trades['hit'].sum()
        total_cost = bet_trades['cost'].sum()
        total_prize = bet_trades['prize'].sum()
        total_profit = bet_trades['profit'].sum()
        
        # 计算最大回撤
        max_drawdown = self._calculate_max_drawdown(capital_curve)
        
        # ROI
        roi = (capital_curve[-1] - self.initial_capital) / self.initial_capital
        
        stats = {
            'total_trades': total_trades,
            'bet_count': len(bet_trades),
            'skip_count': total_trades - len(bet_trades),
            'win_count': int(win_count),
            'win_rate': float(win_count / len(bet_trades)) if len(bet_trades) > 0 else 0,
            'total_cost': float(total_cost),
            'total_prize': float(total_prize),
            'total_profit': float(total_profit),
            'roi': float(roi),
            'max_drawdown': float(max_drawdown),
            'final_capital': float(capital_curve[-1]),
            'sharpe_ratio': self._calculate_sharpe_ratio(bet_trades['profit'].tolist()),
        }
        
        return stats
    
    def _calculate_max_drawdown(self, capital_curve: List[float]) -> float:
        """计算最大回撤"""
        if not capital_curve:
            return 0
        
        peak = capital_curve[0]
        max_dd = 0
        
        for capital in capital_curve:
            if capital > peak:
                peak = capital
            dd = (peak - capital) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_sharpe_ratio(self, profits: List[float], risk_free_rate: float = 0.0) -> float:
        """计算夏普比率"""
        if not profits or len(profits) < 2:
            return 0.0
        
        returns = np.array(profits)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        sharpe = (mean_return - risk_free_rate) / std_return
        return float(sharpe)
    
    def compare_with_baseline(
        self,
        model_stats: Dict,
        baseline_stats: Dict,
    ) -> Dict[str, Any]:
        """
        对比模型与随机基准
        
        Returns:
            对比结果
        """
        model_roi = model_stats['roi']
        baseline_mean_roi = baseline_stats['mean_roi']
        baseline_ci_95 = baseline_stats['percentile_95']
        
        # 判断模型是否显著优于基准
        is_better = model_roi > baseline_ci_95
        
        comparison = {
            'model_roi': model_roi,
            'baseline_mean_roi': baseline_mean_roi,
            'baseline_95_percentile': baseline_ci_95,
            'is_significantly_better': is_better,
            'roi_improvement': model_roi - baseline_mean_roi,
            'conclusion': (
                "模型显著优于随机基准" if is_better 
                else "模型未能显著优于随机基准"
            ),
        }
        
        return comparison
