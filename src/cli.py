#!/usr/bin/env python3
"""
Lotto3D-Core CLI工具

命令行接口，提供数据爬取、特征提取、模型训练、预测、回测等功能
"""
import sys
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import torch
import numpy as np

from utils.logger import setup_logger
from data_loader.crawler import Lottery3DCrawler
from data_loader.loader import DataLoader
from features.engineer import FeatureEngineer
from models.lottery_model import LotteryModel
from strategies.strategy_engine import StrategyEngine
from evaluation.backtester import Backtester
from visualization.plotter import Plotter

# 导入所有特征模块以触发注册
import features.morphology
import features.statistical
import features.metaphysical

console = Console()
logger = setup_logger()


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Lotto3D-Core: 3D彩票预测系统"""
    console.print(Panel.fit(
        "[bold cyan]Lotto3D-Core[/bold cyan]\n"
        "3D Lottery Prediction System",
        border_style="cyan"
    ))


@cli.command()
@click.option('--pages', default=1000, help='要抓取的页数')
@click.option('--workers', default=10, help='并发线程数')
def crawl(pages, workers):
    """抓取3D彩票历史数据"""
    console.print(f"\n[bold green]开始抓取数据:[/bold green] {pages}页")
    
    crawler = Lottery3DCrawler(max_workers=workers)
    stats = crawler.crawl(start_page=1, end_page=pages)
    
    # 显示统计
    table = Table(title="抓取统计")
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")
    
    table.add_row("总页数", str(stats['total_pages']))
    table.add_row("成功页数", str(stats['success_pages']))
    table.add_row("失败页数", str(stats['failed_pages']))
    table.add_row("总记录数", str(stats['total_records']))
    table.add_row("输出文件", str(stats['output_file']))
    
    console.print(table)


@cli.command()
@click.option('--numbers', required=True, help='三个数字，用逗号分隔（如: 1,2,3）')
@click.option('--history-file', help='历史数据文件路径')
def extract(numbers, history_file):
    """提取指定号码的特征"""
    # 解析输入
    try:
        nums = [int(n.strip()) for n in numbers.split(',')]
        if len(nums) != 3 or not all(0 <= n <= 9 for n in nums):
            raise ValueError
    except ValueError:
        console.print("[red]错误: 请输入三个0-9之间的数字[/red]")
        return
    
    console.print(f"\n[bold]提取号码特征:[/bold] {nums}")
    
    # 加载历史数据（如果提供）
    history = None
    if history_file:
        loader = DataLoader()
        df = loader.load_from_json(history_file)
        history = [row['numbers'] for _, row in df.tail(30).iterrows()]
    
    # 提取特征
    engineer = FeatureEngineer()
    features = engineer.extract_single(nums, history)
    
    # 显示特征
    table = Table(title=f"特征提取结果: {nums}")
    table.add_column("特征名", style="cyan")
    table.add_column("特征值", style="yellow")
    
    for key, value in sorted(features.items()):
        table.add_row(key, str(value))
    
    console.print(table)
    
    # 显示可用特征列表
    console.print(f"\n[bold]已注册特征:[/bold] {len(engineer.get_feature_names())}个")
    for info in engineer.get_feature_info():
        console.print(f"  • {info['name']} ({info['category']}): {info['description']}")


@cli.command()
@click.option('--history', default=30, help='使用最近N期历史数据')
@click.option('--top', default=100, help='输出前N注')
@click.option('--model-path', default='./models/best_model.pth', help='模型文件路径')
@click.option('--strategy', default='balanced', type=click.Choice(['conservative', 'balanced', 'aggressive']))
def predict(history, top, model_path, strategy):
    """预测下一期号码"""
    console.print(f"\n[bold green]预测模式:[/bold green] 使用最近{history}期数据")
    
    try:
        # 加载数据
        loader = DataLoader()
        df = loader.load_from_json()
        history_data = df.tail(history)
        
        # 准备输入
        numbers_list = [row['numbers'] for _, row in history_data.iterrows()]
        X = torch.tensor(numbers_list, dtype=torch.long).unsqueeze(0)
        
        # 加载模型
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = LotteryModel.load(model_path, device=device)
        
        # 预测
        predictions = model.predict(X)
        
        # 生成推荐
        strategy_engine = StrategyEngine(top_n=top)
        recommendations = strategy_engine.generate_recommendations(predictions, strategy=strategy)
        
        if recommendations['status'] != 'success':
            console.print(f"[yellow]{recommendations['message']}[/yellow]")
            return
        
        # 显示结果
        console.print(f"\n[bold]置信度:[/bold] {recommendations['confidence']:.2%}")
        console.print(f"[bold]胆码:[/bold] {recommendations['core_digits']}")
        console.print(f"[bold]杀号:[/bold] {recommendations['kill_digits']}")
        
        summary = recommendations['summary']
        console.print(f"[bold]推荐形态:[/bold] {summary['top_shape']}")
        console.print(f"[bold]推荐和值范围:[/bold] {summary['top_sum_range']}")
        console.print(f"[bold]推荐AC值:[/bold] {summary['top_ac_value']}")
        
        # 显示前20注
        table = Table(title=f"推荐方案 (前20注)")
        table.add_column("排名", style="cyan")
        table.add_column("号码", style="yellow")
        table.add_column("理论胜率", style="green")
        
        for idx, rec in enumerate(recommendations['recommendations'][:20], 1):
            table.add_row(
                str(idx),
                rec['number_str'],
                f"{rec['probability']:.4%}"
            )
        
        console.print(table)
        console.print(f"\n[dim]完整的{top}注方案已生成[/dim]")
        
    except FileNotFoundError as e:
        console.print(f"[red]错误: 数据或模型文件未找到[/red]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        logger.exception("Prediction failed")


@cli.command()
@click.option('--periods', default=50, help='回测期数')
@click.option('--model-path', default='./models/best_model.pth', help='模型文件路径')
@click.option('--baseline', is_flag=True, help='同时运行Monte Carlo基准测试')
def backtest(periods, model_path, baseline):
    """回测模型性能"""
    console.print(f"\n[bold green]回测模式:[/bold green] 最近{periods}期")
    
    try:
        # 加载数据
        loader = DataLoader()
        df = loader.load_from_json()
        test_data = df.tail(periods + 30)  # 额外30期作为初始窗口
        
        # 加载模型
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = LotteryModel.load(model_path, device=device)
        
        # 策略引擎
        strategy_engine = StrategyEngine()
        
        # 回测器
        backtester = Backtester()
        
        # 运行回测
        console.print("\n[cyan]运行模型回测...[/cyan]")
        results = backtester.run_backtest(test_data, model, strategy_engine)
        
        # 显示结果
        stats = results['statistics']
        
        table = Table(title="回测结果")
        table.add_column("指标", style="cyan")
        table.add_column("数值", style="yellow")
        
        table.add_row("总交易次数", str(stats['total_trades']))
        table.add_row("投注次数", str(stats['bet_count']))
        table.add_row("观望次数", str(stats['skip_count']))
        table.add_row("中奖次数", str(stats['win_count']))
        table.add_row("中奖率", f"{stats['win_rate']:.2%}")
        table.add_row("总成本", f"¥{stats['total_cost']:.2f}")
        table.add_row("总奖金", f"¥{stats['total_prize']:.2f}")
        table.add_row("净利润", f"¥{stats['total_profit']:.2f}")
        table.add_row("ROI", f"{stats['roi']:.2%}")
        table.add_row("最大回撤", f"{stats['max_drawdown']:.2%}")
        table.add_row("夏普比率", f"{stats['sharpe_ratio']:.3f}")
        table.add_row("最终资金", f"¥{stats['final_capital']:.2f}")
        
        console.print(table)
        
        # 绘制资金曲线
        plotter = Plotter()
        plot_path = plotter.plot_capital_curve(results['capital_curve'])
        console.print(f"\n[dim]资金曲线已保存: {plot_path}[/dim]")
        
        # Monte Carlo基准测试
        if baseline:
            console.print("\n[cyan]运行Monte Carlo基准测试...[/cyan]")
            baseline_results = backtester.run_monte_carlo_baseline(test_data.tail(periods))
            
            baseline_stats = baseline_results['statistics']
            
            table2 = Table(title="随机基准统计")
            table2.add_column("指标", style="cyan")
            table2.add_column("数值", style="magenta")
            
            table2.add_row("平均ROI", f"{baseline_stats['mean_roi']:.2%}")
            table2.add_row("ROI标准差", f"{baseline_stats['std_roi']:.2%}")
            table2.add_row("5%分位数", f"{baseline_stats['percentile_5']:.2%}")
            table2.add_row("95%分位数", f"{baseline_stats['percentile_95']:.2%}")
            table2.add_row("盈利概率", f"{baseline_stats['win_rate']:.2%}")
            
            console.print(table2)
            
            # 对比
            comparison = backtester.compare_with_baseline(stats, baseline_stats)
            
            if comparison['is_significantly_better']:
                console.print(f"\n[bold green]✓ {comparison['conclusion']}[/bold green]")
            else:
                console.print(f"\n[bold yellow]! {comparison['conclusion']}[/bold yellow]")
            
            console.print(f"ROI提升: {comparison['roi_improvement']:.2%}")
        
    except FileNotFoundError:
        console.print("[red]错误: 数据或模型文件未找到[/red]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        logger.exception("Backtest failed")


@cli.command()
@click.option('--periods', default=100, help='显示期数')
def visualize(periods):
    """生成可视化报表"""
    console.print(f"\n[bold green]生成可视化报表:[/bold green] 最近{periods}期")
    
    try:
        # 加载数据
        loader = DataLoader()
        df = loader.load_from_json()
        
        plotter = Plotter()
        
        # 生成图表
        console.print("[cyan]生成和值走势图...[/cyan]")
        path1 = plotter.plot_sum_trend(df, periods)
        
        console.print("[cyan]生成遗漏图...[/cyan]")
        path2 = plotter.plot_omission_chart(df, position=2)
        
        console.print("[cyan]生成数字频率图...[/cyan]")
        path3 = plotter.plot_digit_frequency(df, periods)
        
        console.print(f"\n[bold green]✓ 报表已生成:[/bold green]")
        console.print(f"  • {path1}")
        console.print(f"  • {path2}")
        console.print(f"  • {path3}")
        
    except FileNotFoundError:
        console.print("[red]错误: 数据文件未找到，请先运行 crawl 命令[/red]")
    except Exception as e:
        console.print(f"[red]错误: {e}[/red]")
        logger.exception("Visualization failed")


@cli.command()
def info():
    """显示系统信息"""
    from features.base import FeatureRegistry
    
    registry = FeatureRegistry()
    features = registry.list_features()
    
    table = Table(title="系统信息")
    table.add_column("模块", style="cyan")
    table.add_column("状态", style="green")
    
    table.add_row("Python版本", sys.version.split()[0])
    table.add_row("PyTorch版本", torch.__version__)
    table.add_row("CUDA可用", "是" if torch.cuda.is_available() else "否")
    table.add_row("已注册特征", f"{len(features)}个")
    
    console.print(table)
    
    # 特征列表
    table2 = Table(title="已注册特征")
    table2.add_column("名称", style="cyan")
    table2.add_column("类别", style="yellow")
    table2.add_column("描述", style="white")
    
    for feat in features:
        table2.add_row(feat['name'], feat['category'], feat['description'])
    
    console.print(table2)


if __name__ == '__main__':
    cli()
