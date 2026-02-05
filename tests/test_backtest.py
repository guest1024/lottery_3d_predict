#!/usr/bin/env python3
"""
测试回测功能（简化版）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_loader.loader import DataLoader
from models.lottery_model import LotteryModel
from strategies.strategy_engine import StrategyEngine
from evaluation.backtester import Backtester


def main():
    print("="*60)
    print("测试回测系统")
    print("="*60)
    
    # 1. 加载数据
    print("\n1. 加载数据...")
    loader = DataLoader(data_dir='./data')
    df = loader.load_from_json()
    
    # 使用后100期作为测试（包含30期warm-up）
    test_data = df.tail(100)
    print(f"   回测数据: {len(test_data)} 期")
    
    # 2. 加载模型
    print("\n2. 加载模型...")
    model = LotteryModel.load('./models/best_model.pth', device='cpu')
    
    # 3. 创建策略引擎
    strategy_engine = StrategyEngine(
        confidence_threshold=0.2,
        top_n=50  # 每期50注降低成本
    )
    
    # 4. 创建回测器
    backtester = Backtester(
        initial_capital=10000.0,
        cost_per_bet=2.0,
        prize_group6=160.0,
        prize_group3=320.0,
        prize_leopard=1000.0,
    )
    
    # 5. 运行回测（20期）
    print("\n3. 运行回测（20期）...")
    results = backtester.run_backtest(
        test_data=test_data,
        model=model,
        strategy_engine=strategy_engine,
        window_size=30,
        num_bets=50,
    )
    
    # 6. 显示结果
    stats = results['statistics']
    
    print("\n" + "="*60)
    print("回测结果")
    print("="*60)
    
    print(f"\n基本统计:")
    print(f"  总交易次数: {stats['total_trades']}")
    print(f"  投注次数: {stats['bet_count']}")
    print(f"  观望次数: {stats['skip_count']}")
    print(f"  中奖次数: {stats['win_count']}")
    print(f"  中奖率: {stats['win_rate']:.2%}")
    
    print(f"\n资金统计:")
    print(f"  初始资金: ¥10,000.00")
    print(f"  最终资金: ¥{stats['final_capital']:.2f}")
    print(f"  总成本: ¥{stats['total_cost']:.2f}")
    print(f"  总奖金: ¥{stats['total_prize']:.2f}")
    print(f"  净利润: ¥{stats['total_profit']:.2f}")
    
    print(f"\n性能指标:")
    print(f"  ROI: {stats['roi']:.2%}")
    print(f"  最大回撤: {stats['max_drawdown']:.2%}")
    print(f"  夏普比率: {stats['sharpe_ratio']:.3f}")
    
    # 显示部分交易记录
    print(f"\n交易记录（最近5期）:")
    print("  " + "-"*70)
    print(f"  {'期数':<6} {'动作':<8} {'成本':<10} {'奖金':<10} {'利润':<10} {'资金':<10}")
    print("  " + "-"*70)
    
    for trade in results['trades'][-5:]:
        action = trade['action']
        cost = f"¥{trade['cost']:.0f}" if action == 'bet' else '-'
        prize = f"¥{trade['prize']:.0f}" if action == 'bet' else '-'
        profit = f"¥{trade['profit']:.0f}" if action == 'bet' else '-'
        capital = f"¥{trade['capital']:.0f}"
        
        print(f"  {trade['period']:<6} {action:<8} {cost:<10} {prize:<10} {profit:<10} {capital:<10}")
    
    print("  " + "-"*70)
    
    # 资金曲线趋势
    capital_curve = results['capital_curve']
    print(f"\n资金曲线:")
    print(f"  起点: ¥{capital_curve[0]:.2f}")
    print(f"  终点: ¥{capital_curve[-1]:.2f}")
    print(f"  峰值: ¥{max(capital_curve):.2f}")
    print(f"  谷值: ¥{min(capital_curve):.2f}")
    
    print("\n" + "="*60)
    print("回测完成！")
    print("="*60)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
