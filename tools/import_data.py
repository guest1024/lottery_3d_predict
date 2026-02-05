"""
导入历史数据到Django数据库
"""
import os
import sys
import json
import django
from datetime import datetime
from collections import Counter

# 设置Django环境
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottery_web.settings')
django.setup()

from lottery.models import LotteryPeriod, BacktestResult


def import_lottery_data():
    """导入彩票数据"""
    print("开始导入彩票数据...")
    
    data_file = 'data/lottery_3d_real_20260205_125506.json'
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    periods_data = data['data']
    added_count = 0
    updated_count = 0
    
    for item in periods_data:
        period_id = item['period']
        date_str = item['date']
        numbers = item['numbers']
        
        # 解析日期
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            date_obj = datetime.now().date()
        
        # 计算形态
        counter = Counter(numbers)
        if len(counter) == 1:
            shape = '豹子'
        elif len(counter) == 2:
            shape = '组三'
        else:
            shape = '组六'
        
        # 保存或更新
        obj, created = LotteryPeriod.objects.update_or_create(
            period=period_id,
            defaults={
                'date': date_obj,
                'digit1': numbers[0],
                'digit2': numbers[1],
                'digit3': numbers[2],
                'sum_value': sum(numbers),
                'shape': shape,
            }
        )
        
        if created:
            added_count += 1
        else:
            updated_count += 1
        
        if (added_count + updated_count) % 100 == 0:
            print(f"  处理: {added_count + updated_count}期...")
    
    print(f"✓ 彩票数据导入完成！新增{added_count}期，更新{updated_count}期")
    return added_count, updated_count


def import_backtest_results():
    """导入回测结果"""
    print("\n开始导入回测结果...")
    
    result_file = 'results/dynamic_betting_results.json'
    if not os.path.exists(result_file):
        print("  跳过：回测结果文件不存在")
        return
    
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summary = data['summary']
    period_results = data['period_results']
    
    # 确定期号范围
    bet_periods = [p for p in period_results if p.get('action') == 'bet']
    if bet_periods:
        start_period = bet_periods[-1].get('period', 'Unknown')
        end_period = bet_periods[0].get('period', 'Unknown')
    else:
        start_period = end_period = 'Unknown'
    
    # 保存回测结果
    backtest = BacktestResult.objects.create(
        strategy_name='Top 10% Dynamic',
        start_period=start_period,
        end_period=end_period,
        total_periods=summary['total_periods'],
        starting_capital=summary['starting_capital'],
        final_capital=summary['final_capital'],
        total_profit=summary['total_profit'],
        roi_percentage=summary['roi_percentage'],
        max_drawdown=summary['max_drawdown'],
        bet_periods=summary['bet_periods'],
        skip_periods=summary['skip_periods'],
        win_periods=summary['win_periods'],
        win_rate=summary['win_rate'],
        total_invested=summary['total_invested'],
        total_prizes=summary['total_prizes'],
        period_results=period_results,
        capital_history=summary['capital_history']
    )
    
    print(f"✓ 回测结果导入完成！策略: {backtest.strategy_name}, ROI: {backtest.roi_percentage:.2f}%")


def main():
    print("="*60)
    print("3D彩票数据导入工具")
    print("="*60)
    
    # 导入彩票数据
    added, updated = import_lottery_data()
    
    # 导入回测结果
    import_backtest_results()
    
    print(f"\n{'='*60}")
    print(f"导入完成！")
    print(f"彩票数据: 新增{added}期, 更新{updated}期")
    print(f"总期数: {LotteryPeriod.objects.count()}")
    print(f"回测记录: {BacktestResult.objects.count()}条")
    print(f"{'='*60}\n")
    
    print("启动Web服务:")
    print("  python manage.py runserver 0.0.0.0:8000")
    print("\n访问地址:")
    print("  http://localhost:8000/")


if __name__ == '__main__':
    main()
