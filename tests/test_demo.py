#!/usr/bin/env python3
"""
演示脚本：测试系统各模块功能

运行方式：python test_demo.py
"""
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def test_feature_extraction():
    """测试特征提取"""
    console.print("\n[bold cyan]测试1: 特征提取[/bold cyan]")
    
    from features.engineer import FeatureEngineer
    import features.morphology
    import features.statistical
    import features.metaphysical
    
    engineer = FeatureEngineer()
    
    # 提取特征
    numbers = [1, 2, 3]
    history = [[9, 8, 7], [6, 5, 4], [3, 2, 1]]
    
    features = engineer.extract_single(numbers, history)
    
    console.print(f"输入号码: {numbers}")
    console.print(f"提取特征数: {len(features)}")
    console.print(f"注册特征: {engineer.get_feature_names()}")
    
    # 显示部分特征
    table = Table(title="部分特征示例")
    table.add_column("特征名", style="cyan")
    table.add_column("特征值", style="yellow")
    
    for key, value in list(features.items())[:10]:
        table.add_row(key, str(value))
    
    console.print(table)
    console.print("[green]✓ 特征提取测试通过[/green]")


def test_model_architecture():
    """测试模型架构"""
    console.print("\n[bold cyan]测试2: 模型架构[/bold cyan]")
    
    import torch
    from models.lottery_model import LotteryModel
    
    # 创建模型
    model = LotteryModel(embedding_dim=16, hidden_dim=64, num_layers=2)
    
    # 模拟输入
    batch_size = 4
    seq_len = 30
    X = torch.randint(0, 10, (batch_size, seq_len, 3))
    
    # 前向传播
    outputs = model(X)
    
    console.print(f"输入形状: {X.shape}")
    console.print(f"数字预测形状: {outputs['digit_probs'].shape}")
    console.print(f"形态预测形状: {outputs['shape_logits'].shape}")
    console.print(f"和值预测形状: {outputs['sum_logits'].shape}")
    console.print(f"AC值预测形状: {outputs['ac_logits'].shape}")
    
    console.print("[green]✓ 模型架构测试通过[/green]")


def test_strategy_engine():
    """测试策略引擎"""
    console.print("\n[bold cyan]测试3: 策略引擎[/bold cyan]")
    
    import numpy as np
    from strategies.strategy_engine import StrategyEngine
    
    # 模拟预测结果
    predictions = {
        'digit_probs': np.array([[0.8, 0.2, 0.7, 0.5, 0.3, 0.6, 0.4, 0.9, 0.1, 0.15]]),
        'shape_probs': np.array([[0.7, 0.2, 0.1]]),  # 组六概率高
        'sum_probs': np.array([[0.01] * 28]),
        'ac_probs': np.array([[0.2, 0.5, 0.3]]),
    }
    
    # 设置高概率和值
    predictions['sum_probs'][0, 12:18] = 0.1
    
    engine = StrategyEngine(top_n=20)
    result = engine.generate_recommendations(predictions, strategy='balanced')
    
    if result['status'] == 'success':
        console.print(f"胆码: {result['core_digits']}")
        console.print(f"杀号: {result['kill_digits']}")
        console.print(f"生成组合数: {result['total_combinations']}")
        console.print(f"过滤后组合数: {result['filtered_combinations']}")
        console.print(f"推荐注数: {len(result['recommendations'])}")
        
        # 显示前5注
        table = Table(title="推荐方案（前5注）")
        table.add_column("排名", style="cyan")
        table.add_column("号码", style="yellow")
        table.add_column("概率", style="green")
        
        for idx, rec in enumerate(result['recommendations'][:5], 1):
            table.add_row(
                str(idx),
                rec['number_str'],
                f"{rec['probability']:.4%}"
            )
        
        console.print(table)
        console.print("[green]✓ 策略引擎测试通过[/green]")
    else:
        console.print(f"[yellow]{result['message']}[/yellow]")


def test_data_loader():
    """测试数据加载（如果数据存在）"""
    console.print("\n[bold cyan]测试4: 数据加载[/bold cyan]")
    
    from data_loader.loader import DataLoader
    
    try:
        loader = DataLoader()
        df = loader.load_from_json()
        stats = loader.get_statistics()
        
        console.print(f"总记录数: {stats['total_records']}")
        console.print(f"日期范围: {stats['date_range']['start']} ~ {stats['date_range']['end']}")
        console.print(f"期号范围: {stats['period_range']['start']} ~ {stats['period_range']['end']}")
        
        console.print("[green]✓ 数据加载测试通过[/green]")
    except FileNotFoundError:
        console.print("[yellow]⚠ 数据文件未找到，请先运行 crawl 命令[/yellow]")


def test_visualization():
    """测试可视化（如果数据存在）"""
    console.print("\n[bold cyan]测试5: 可视化[/bold cyan]")
    
    from visualization.plotter import Plotter
    from data_loader.loader import DataLoader
    import numpy as np
    
    try:
        loader = DataLoader()
        df = loader.load_from_json()
        
        plotter = Plotter(output_dir='./test_output')
        
        # 生成测试图表
        path1 = plotter.plot_sum_trend(df, periods=50)
        console.print(f"和值走势图: {path1}")
        
        path2 = plotter.plot_digit_frequency(df, periods=100)
        console.print(f"数字频率图: {path2}")
        
        # 测试资金曲线
        capital_curve = [20000 + i * 100 - (i % 10) * 500 for i in range(50)]
        path3 = plotter.plot_capital_curve(capital_curve)
        console.print(f"资金曲线图: {path3}")
        
        console.print("[green]✓ 可视化测试通过[/green]")
    except FileNotFoundError:
        console.print("[yellow]⚠ 数据文件未找到，跳过可视化测试[/yellow]")
    except Exception as e:
        console.print(f"[yellow]⚠ 可视化测试失败: {e}[/yellow]")


def main():
    """主函数"""
    console.print(Panel.fit(
        "[bold cyan]Lotto3D-Core 系统测试[/bold cyan]\n"
        "Testing all modules...",
        border_style="cyan"
    ))
    
    try:
        test_feature_extraction()
        test_model_architecture()
        test_strategy_engine()
        test_data_loader()
        test_visualization()
        
        console.print("\n" + "="*60)
        console.print("[bold green]所有测试完成！[/bold green]")
        console.print("="*60)
        
    except Exception as e:
        console.print(f"\n[bold red]测试失败: {e}[/bold red]")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
