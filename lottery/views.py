"""
3D彩票预测Web视图
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
import numpy as np

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator

from .models import LotteryPeriod, Prediction, BacktestResult, DataUpdateLog


# ==================== 投注策略辅助函数 ====================

def calculate_opportunity_score(digit_probs: np.ndarray, history: np.ndarray) -> float:
    """
    计算机会评分（0-100分）
    复用daily_opportunity_check.py中的评分逻辑
    """
    # 特征权重
    FEATURE_WEIGHTS = {
        'top1_prob': 15,
        'top3_mean_prob': 15,
        'gap_1_2': 10,
        'prob_std': 10,
        'top3_concentration': 10,
        'digit_freq_std': 8,
        'shape_entropy': 7,
        'sum_std': 5,
        'recent_5_unique_count': 5,
        'max_consecutive_shape': 5,
    }
    
    # 模型特征
    sorted_indices = np.argsort(digit_probs)[::-1]
    sorted_probs = digit_probs[sorted_indices]
    
    top1_prob = sorted_probs[0]
    top3_mean_prob = np.mean(sorted_probs[:3])
    gap_1_2 = sorted_probs[0] - sorted_probs[1] if len(sorted_probs) > 1 else 0
    prob_std = np.std(digit_probs)
    top3_concentration = np.sum(sorted_probs[:3]) / (np.sum(digit_probs) + 1e-10)
    
    # 序列特征
    flat_history = history.flatten()
    digit_counts = Counter(flat_history)
    digit_freq_std = np.std(list(digit_counts.values()))
    
    # 形态统计
    def get_shape(numbers):
        sorted_nums = sorted(numbers)
        if sorted_nums[0] == sorted_nums[1] == sorted_nums[2]:
            return 'leopard'
        elif sorted_nums[0] == sorted_nums[1] or sorted_nums[1] == sorted_nums[2]:
            return 'group3'
        else:
            return 'group6'
    
    shape_counts = Counter()
    for numbers in history:
        shape = get_shape(numbers)
        shape_counts[shape] += 1
    
    # 计算熵
    total = sum(shape_counts.values())
    shape_entropy = 0
    if total > 0:
        for count in shape_counts.values():
            if count > 0:
                p = count / total
                shape_entropy -= p * np.log2(p)
        max_entropy = np.log2(min(3, len(shape_counts)))
        if max_entropy > 0:
            shape_entropy /= max_entropy
    
    sum_values = [np.sum(numbers) for numbers in history]
    sum_std = np.std(sum_values)
    
    recent_5 = history[-5:]
    recent_5_unique_count = len(set(map(tuple, recent_5)))
    
    # 最大连续相同形态
    shapes = [get_shape(numbers) for numbers in history]
    max_consecutive_shape = 1
    current_count = 1
    for i in range(1, len(shapes)):
        if shapes[i] == shapes[i-1]:
            current_count += 1
            max_consecutive_shape = max(max_consecutive_shape, current_count)
        else:
            current_count = 1
    
    # 计算评分
    features = {
        'top1_prob': min(1.0, top1_prob / 0.3),
        'top3_mean_prob': min(1.0, top3_mean_prob / 0.3),
        'gap_1_2': min(1.0, gap_1_2 / 0.1),
        'prob_std': min(1.0, prob_std / 0.3),
        'top3_concentration': min(1.0, top3_concentration),
        'digit_freq_std': min(1.0, digit_freq_std / 5.0),
        'shape_entropy': min(1.0, shape_entropy),
        'sum_std': min(1.0, sum_std / 5.0),
        'recent_5_unique_count': min(1.0, recent_5_unique_count / 5.0),
        'max_consecutive_shape': min(1.0, max_consecutive_shape / 10.0),
    }
    
    score = sum(features[k] * FEATURE_WEIGHTS[k] for k in features.keys())
    return score


def generate_betting_plan(top_digits: list, score: float, num_bets: int = 100) -> dict:
    """
    生成投注计划
    
    Args:
        top_digits: Top10数字列表
        score: 机会评分
        num_bets: 总投注注数
        
    Returns:
        {
            'num_bets': 100,
            'total_cost': 200,
            'combinations': [[0, 1, 2], [0, 1, 3], ...],
            'group6_count': 70,
            'group3_count': 30,
            'expected_roi': 405.0,
            'prize_breakdown': {
                'group6_prize': 173,
                'group3_prize': 346,
                'direct_prize': 1040
            }
        }
    """
    # 根据评分调整组三/组六比例
    if score >= 63.3:  # Top1% 极高评分
        group6_ratio = 0.75  # 更多组六
    elif score >= 62.9:  # Top5%
        group6_ratio = 0.70
    else:
        group6_ratio = 0.65
    
    group6_count = int(num_bets * group6_ratio)
    group3_count = num_bets - group6_count
    
    combinations = []
    used_combos = set()
    
    # 生成组六投注（三个不同数字）
    for _ in range(group6_count):
        attempts = 0
        while attempts < 100:
            combo = tuple(sorted(np.random.choice(top_digits, size=3, replace=False)))
            if len(set(combo)) == 3 and combo not in used_combos:
                combinations.append([int(x) for x in combo])  # 转换为 Python int
                used_combos.add(combo)
                break
            attempts += 1
    
    # 生成组三投注（两个相同数字 + 一个不同）
    for _ in range(group3_count):
        attempts = 0
        while attempts < 100:
            digit1 = np.random.choice(top_digits)
            digit2 = np.random.choice([d for d in top_digits if d != digit1])
            combo = tuple(sorted([digit1, digit1, digit2]))
            if combo not in used_combos:
                combinations.append([int(x) for x in combo])  # 转换为 Python int
                used_combos.add(combo)
                break
            attempts += 1
    
    # 计算成本
    total_cost = len(combinations) * 2  # 每注2元
    
    # 预期ROI（基于历史Top1%策略数据）
    if score >= 58.45:  # Top1%阈值
        expected_roi = 405.0  # 历史ROI +405%
    elif score >= 52.80:  # Top5%阈值
        expected_roi = -57.0
    else:
        expected_roi = -13.0
    
    return {
        'num_bets': int(len(combinations)),
        'total_cost': int(total_cost),
        'combinations': combinations,
        'group6_count': int(group6_count),
        'group3_count': int(group3_count),
        'expected_roi': float(expected_roi),
        'prize_breakdown': {
            'group6_prize': 173,
            'group3_prize': 346,
            'direct_prize': 1040
        }
    }


def index(request):
    """首页 - 仪表板"""
    context = {
        'total_periods': LotteryPeriod.objects.count(),
        'latest_period': LotteryPeriod.objects.first(),
        'latest_prediction': Prediction.objects.first(),
    }
    
    # 获取最新回测结果
    backtest_results = BacktestResult.objects.all()[:5]
    context['backtest_results'] = backtest_results
    
    # 最近更新日志
    update_logs = DataUpdateLog.objects.all()[:5]
    context['update_logs'] = update_logs
    
    return render(request, 'lottery/index.html', context)


def dashboard(request):
    """仪表板 - Tab视图"""
    context = {}
    
    # 统计数据
    context['total_periods'] = LotteryPeriod.objects.count()
    context['latest_period'] = LotteryPeriod.objects.first()
    
    # 最新预测
    latest_prediction = Prediction.objects.first()
    context['latest_prediction'] = latest_prediction
    
    # 回测结果对比
    backtest_results = BacktestResult.objects.all().order_by('-created_at')[:5]
    context['backtest_results'] = backtest_results
    
    # 最佳策略
    best_strategy = BacktestResult.objects.order_by('-roi_percentage').first()
    context['best_strategy'] = best_strategy
    
    # 数据更新状态
    latest_update = DataUpdateLog.objects.first()
    context['latest_update'] = latest_update
    
    return render(request, 'lottery/dashboard.html', context)


def history_list(request):
    """历史开奖列表"""
    periods = LotteryPeriod.objects.all()
    
    # 搜索
    query = request.GET.get('q', '')
    if query:
        periods = periods.filter(
            Q(period__icontains=query) | 
            Q(numbers_str__icontains=query)
        )
    
    # 分页
    paginator = Paginator(periods, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    
    return render(request, 'lottery/history_list.html', context)


def period_detail(request, period):
    """期号详情"""
    period_obj = get_object_or_404(LotteryPeriod, period=period)
    
    # 获取该期的预测（如果有）
    predictions = period_obj.predictions.all()
    
    # 获取前30期历史（用于特征提取）
    all_periods = list(LotteryPeriod.objects.all())
    current_index = next((i for i, p in enumerate(all_periods) if p.period == period), None)
    
    history_30 = None
    if current_index is not None and current_index + 30 < len(all_periods):
        history_30 = all_periods[current_index+1:current_index+31]
        history_30.reverse()  # 按时间正序
    
    context = {
        'period': period_obj,
        'predictions': predictions,
        'history_30': history_30,
    }
    
    return render(request, 'lottery/period_detail.html', context)


def backtest_detail(request, pk):
    """回测详情"""
    backtest = get_object_or_404(BacktestResult, pk=pk)
    
    # 解析period_results用于图表
    period_results = backtest.period_results
    capital_history = backtest.capital_history
    
    context = {
        'backtest': backtest,
        'period_results': json.dumps(period_results),
        'capital_history': json.dumps(capital_history),
    }
    
    return render(request, 'lottery/backtest_detail.html', context)


def predictions_list(request):
    """预测列表"""
    predictions = Prediction.objects.all()
    
    # 筛选
    should_bet = request.GET.get('should_bet')
    if should_bet == 'true':
        predictions = predictions.filter(should_bet=True)
    elif should_bet == 'false':
        predictions = predictions.filter(should_bet=False)
    
    # 分页
    paginator = Paginator(predictions, 30)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'should_bet': should_bet,
    }
    
    return render(request, 'lottery/predictions_list.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def crawl_latest_data(request):
    """爬取最新数据API"""
    try:
        # 导入爬虫模块
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        from data_loader.crawler_simple import SimpleLottery3DCrawler
        
        # 创建爬虫并抓取前3页（约60条最新数据）
        crawler = SimpleLottery3DCrawler(
            output_dir=str(Path(__file__).parent.parent / 'data'),
            max_workers=3
        )
        
        # 抓取前3页
        stats = crawler.crawl(start_page=1, end_page=3)
        
        if stats['total_records'] == 0:
            return JsonResponse({
                'status': 'error',
                'message': '爬取数据失败，未获取到数据'
            })
        
        # 读取最新生成的JSON文件
        json_file = stats.get('json_file')
        if not json_file or not Path(json_file).exists():
            return JsonResponse({
                'status': 'error',
                'message': '未找到爬取的数据文件'
            })
        
        import json as json_lib
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json_lib.load(f)
        
        data_list = data.get('data', [])
        
        # 导入到数据库
        added_count = 0
        updated_count = 0
        
        for item in data_list:
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
        
        # 记录日志
        DataUpdateLog.objects.create(
            update_type='crawler',
            periods_added=added_count,
            periods_updated=updated_count,
            status='success',
            message=f'成功爬取{len(data_list)}条数据'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'成功导入数据！新增{added_count}期，更新{updated_count}期',
            'added': added_count,
            'updated': updated_count,
            'total': len(data_list)
        })
        
    except Exception as e:
        # 记录错误日志
        DataUpdateLog.objects.create(
            update_type='crawler',
            periods_added=0,
            periods_updated=0,
            status='failed',
            message=str(e)
        )
        
        import traceback
        error_detail = traceback.format_exc()
        
        return JsonResponse({
            'status': 'error',
            'message': f'爬取失败: {str(e)}'
        })


@csrf_exempt
@require_http_methods(["POST"])
def generate_prediction(request):
    """
    生成预测API - 返回完整的投注计划
    
    返回格式:
    {
        "status": "success",
        "prediction": {
            "period": "2026-02-06",
            "score": 55.65,
            "threshold": 58.45,
            "should_bet": false,
            "top10_digits": [6, 2, 8, 5, 3, 1, 9, 4, 0, 7],
            "betting_plan": {
                "num_bets": 100,
                "total_cost": 200,
                "combinations": [...],  // 具体的投注组合
                "group6_count": 70,     // 组六注数
                "group3_count": 30,     // 组三注数
                "expected_roi": 405.0,  // 预期ROI%
                "prize_breakdown": {...}
            }
        }
    }
    """
    try:
        # 导入必要模块
        import sys
        import torch
        import numpy as np
        from collections import Counter
        sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
        from models.lottery_model import LotteryModel
        
        # 从请求中获取投注注数（默认100注）
        try:
            body = json.loads(request.body) if request.body else {}
            num_bets = int(body.get('num_bets', 100))
        except:
            num_bets = 100
        
        # 加载模型
        model_path = Path(__file__).parent.parent / 'models' / 'checkpoints' / 'best_model.pth'
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = LotteryModel.load(str(model_path), device=device)
        
        # 获取最近30期数据
        recent_periods = list(LotteryPeriod.objects.order_by('-period')[:30])
        if len(recent_periods) < 30:
            return JsonResponse({
                'status': 'error',
                'message': '历史数据不足30期，无法生成预测'
            })
        
        recent_periods.reverse()  # 按时间正序
        
        # 准备输入序列
        sequences = np.array([[p.digit1, p.digit2, p.digit3] for p in recent_periods])
        
        # 模型预测
        with torch.no_grad():
            input_seq = torch.LongTensor(sequences).unsqueeze(0).to(device)
            predictions = model.predict(input_seq)
            digit_probs = predictions['digit_probs'][0]
            attention_weights = predictions['attention_weights'][0]
        
        # 获取Top10数字（用于生成投注组合）
        top_indices = np.argsort(digit_probs)[::-1][:10]
        top10_digits = top_indices.tolist()
        
        # 计算机会评分（使用完整的评分系统）
        score = calculate_opportunity_score(digit_probs, sequences)
        threshold = 58.45  # Top1%阈值
        should_bet = score >= threshold
        
        # 确定下一期号
        latest_period = recent_periods[-1]
        from datetime import datetime, timedelta
        try:
            current_date = datetime.strptime(latest_period.period, '%Y-%m-%d')
            next_date = current_date + timedelta(days=1)
            next_period = next_date.strftime('%Y-%m-%d')
        except:
            next_period = f"预测-{latest_period.date}"
        
        # 生成投注计划
        betting_plan = generate_betting_plan(top10_digits, score, num_bets)
        
        # 保存预测到数据库
        prediction = Prediction.objects.create(
            period=latest_period,
            predicted_for_period=next_period,
            top5_digits=top10_digits[:5],
            digit_probs=digit_probs.tolist(),
            confidence_score=score / 100.0,  # 转换为0-1范围
            attention_weights=attention_weights.tolist(),
            should_bet=bool(should_bet),  # 转换为Python bool
            bet_amount=betting_plan['total_cost'] if should_bet else 0
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'成功生成{next_period}期预测',
            'prediction': {
                'period': next_period,
                'score': float(round(score, 2)),  # 确保是 Python float
                'threshold': float(threshold),
                'should_bet': bool(should_bet),  # 转换为Python bool
                'top10_digits': top10_digits,
                'top5_digits': top10_digits[:5],  # 兼容旧版
                'betting_plan': betting_plan,
                'recommendation': '建议投注' if should_bet else '继续观望'
            }
        })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'status': 'error',
            'message': f'预测失败: {str(e)}',
            'traceback': traceback.format_exc()
        })


def feature_extraction_view(request, period):
    """特征提取视图"""
    period_obj = get_object_or_404(LotteryPeriod, period=period)
    
    # 获取前30期作为输入特征
    all_periods = list(LotteryPeriod.objects.all())
    current_index = next((i for i, p in enumerate(all_periods) if p.period == period), None)
    
    if current_index is None or current_index + 30 >= len(all_periods):
        context = {
            'period': period_obj,
            'error': '历史数据不足30期'
        }
        return render(request, 'lottery/feature_extraction.html', context)
    
    # 获取输入序列（前30期）
    history_30 = all_periods[current_index+1:current_index+31]
    history_30.reverse()
    
    # 提取特征
    sequences = [[p.digit1, p.digit2, p.digit3] for p in history_30]
    
    # 统计分析
    all_digits = [d for seq in sequences for d in seq]
    digit_freq = Counter(all_digits)
    
    # 和值统计
    sum_values = [sum(seq) for seq in sequences]
    
    # 形态统计
    shapes = []
    for seq in sequences:
        counter = Counter(seq)
        if len(counter) == 1:
            shapes.append('豹子')
        elif len(counter) == 2:
            shapes.append('组三')
        else:
            shapes.append('组六')
    shape_freq = Counter(shapes)
    
    # 计算形态百分比
    shape_freq_with_pct = {}
    for shape, count in shape_freq.items():
        shape_freq_with_pct[shape] = {
            'count': count,
            'percentage': round(count / 30 * 100, 1)
        }
    
    context = {
        'period': period_obj,
        'history_30': list(zip(history_30, sequences)),
        'digit_freq': dict(sorted(digit_freq.items())),
        'sum_values': {
            'min': min(sum_values),
            'max': max(sum_values),
            'avg': sum(sum_values) / len(sum_values)
        },
        'shape_freq': shape_freq_with_pct,
        'sequences_json': json.dumps(sequences),
    }
    
    return render(request, 'lottery/feature_extraction.html', context)


def investment_strategy_view(request):
    """投资策略分析视图"""
    # 读取分析结果
    results_dir = Path(__file__).parent.parent / 'results'
    
    # 读取当前机会评估
    current_opportunity = None
    opportunity_file = results_dir / 'current_opportunity.json'
    if opportunity_file.exists():
        try:
            with open(opportunity_file, 'r', encoding='utf-8') as f:
                current_opportunity = json.load(f)
        except json.JSONDecodeError as e:
            print(f"警告: current_opportunity.json 解析失败: {e}")
            current_opportunity = None
    
    # 读取策略对比结果（如果存在）
    strategy_comparison = None
    comparison_file = results_dir / 'strategy_comparison.json'
    if comparison_file.exists():
        try:
            with open(comparison_file, 'r', encoding='utf-8') as f:
                strategy_comparison = json.load(f)
        except json.JSONDecodeError as e:
            print(f"警告: strategy_comparison.json 解析失败: {e}")
            strategy_comparison = None
    
    # 读取golden opportunities（如果存在）
    golden_opportunities = None
    golden_file = results_dir / 'golden_opportunities.json'
    if golden_file.exists():
        try:
            with open(golden_file, 'r', encoding='utf-8') as f:
                golden_opportunities = json.load(f)
        except json.JSONDecodeError as e:
            print(f"警告: golden_opportunities.json 解析失败: {e}")
            golden_opportunities = None
    
    context = {
        'current_opportunity': current_opportunity,
        'strategy_comparison': strategy_comparison,
        'golden_opportunities': golden_opportunities,
        'total_periods': LotteryPeriod.objects.count(),
    }
    
    return render(request, 'lottery/investment_strategy.html', context)


def scheduler_status_view(request):
    """调度器状态视图"""
    from lottery.scheduler import get_scheduler_status
    from django_apscheduler.models import DjangoJobExecution
    
    # 获取调度器状态
    status = get_scheduler_status()
    
    # 获取最近的任务执行记录
    recent_executions = DjangoJobExecution.objects.order_by('-run_time')[:20]
    
    context = {
        'scheduler_status': status,
        'recent_executions': recent_executions,
    }
    
    return render(request, 'lottery/scheduler_status.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def run_task_now(request):
    """立即运行指定任务的API"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        
        if not task_id:
            return JsonResponse({
                'status': 'error',
                'message': '缺少task_id参数'
            })
        
        from lottery.scheduler import run_job_now
        success = run_job_now(task_id)
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': f'任务 {task_id} 已执行'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'任务 {task_id} 不存在或执行失败'
            })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'执行失败: {str(e)}'
        })
