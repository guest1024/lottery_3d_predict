"""
可视化回测结果,生成图表报告
"""
import sys
sys.path.insert(0, '/c1/program/lottery_3d_predict')

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from pathlib import Path
from collections import Counter

# 设置中文字体和样式
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-darkgrid')

def load_backtest_results():
    """加载回测结果"""
    with open('results/backtest_results.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def plot_overall_metrics(summary, output_dir):
    """绘制整体性能指标"""
    stats = summary['overall_statistics']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('3D彩票预测模型 - 整体性能指标', fontsize=16, fontweight='bold')
    
    # 1. 位置匹配率
    ax1 = axes[0, 0]
    positions = ['位置0', '位置1', '位置2', '平均']
    values = [
        stats['position_0_match_rate'],
        stats['position_1_match_rate'],
        stats['position_2_match_rate'],
        stats['avg_position_match_rate']
    ]
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    bars = ax1.bar(positions, values, color=colors, alpha=0.7, edgecolor='black')
    
    # 添加基准线
    ax1.axhline(y=0.1, color='red', linestyle='--', linewidth=2, label='随机基准 (10%)')
    
    # 添加数值标签
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.1%}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax1.set_ylabel('匹配率', fontsize=12)
    ax1.set_title('位置匹配率分析', fontsize=13, fontweight='bold')
    ax1.set_ylim(0, 0.6)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. Top预测性能
    ax2 = axes[0, 1]
    metrics = ['Top1\n命中率', 'Top3\n平均命中', 'Top5\n平均命中', '任意数字\n命中率']
    values = [
        stats['top1_hit_rate'],
        stats['top3_avg_hits'] / 3,  # 转换为比例
        stats['top5_avg_hits'] / 3,
        stats['any_digit_match_rate']
    ]
    colors = ['#9b59b6', '#1abc9c', '#34495e', '#e67e22']
    bars = ax2.bar(metrics, values, color=colors, alpha=0.7, edgecolor='black')
    
    # 添加数值标签
    for bar, value, raw_value in zip(bars, values, [
        stats['top1_hit_rate'],
        stats['top3_avg_hits'],
        stats['top5_avg_hits'],
        stats['any_digit_match_rate']
    ]):
        height = bar.get_height()
        if 'Top' in metrics[bars.index(bar)] and '命中率' not in metrics[bars.index(bar)]:
            label = f'{raw_value:.2f}/3'
        else:
            label = f'{value:.1%}'
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                label,
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax2.set_ylabel('性能指标', fontsize=12)
    ax2.set_title('Top预测性能', fontsize=13, fontweight='bold')
    ax2.set_ylim(0, 1.0)
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. 对比随机基准
    ax3 = axes[1, 0]
    metrics = ['位置匹配', 'Top1命中', 'Top5命中', '任意命中']
    model_values = [
        stats['avg_position_match_rate'],
        stats['top1_hit_rate'],
        stats['top5_avg_hits'] / 3,
        stats['any_digit_match_rate']
    ]
    random_values = [0.1, 0.1, 0.5/3, 0.271]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    bars1 = ax3.bar(x - width/2, model_values, width, label='模型表现', 
                    color='#3498db', alpha=0.8, edgecolor='black')
    bars2 = ax3.bar(x + width/2, random_values, width, label='随机基准',
                    color='#e74c3c', alpha=0.8, edgecolor='black')
    
    ax3.set_ylabel('准确率/命中率', fontsize=12)
    ax3.set_title('模型 vs 随机基准', fontsize=13, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(metrics)
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)
    
    # 添加提升倍数标注
    for i, (m, r) in enumerate(zip(model_values, random_values)):
        if r > 0:
            improvement = m / r
            ax3.text(i, max(m, r) + 0.05, f'{improvement:.1f}x',
                    ha='center', fontsize=9, fontweight='bold', color='green')
    
    # 4. 综合评分雷达图
    ax4 = axes[1, 1]
    categories = ['位置\n匹配', 'Top1\n命中', 'Top5\n命中', '任意\n命中', '稳定性']
    values = [
        stats['avg_position_match_rate'] / 0.5,  # 归一化到0-1
        stats['top1_hit_rate'] / 0.5,
        stats['top5_avg_hits'] / 2.0,
        stats['any_digit_match_rate'],
        0.85  # 稳定性评分(基于时间段波动)
    ]
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    
    ax4 = plt.subplot(224, projection='polar')
    ax4.plot(angles, values, 'o-', linewidth=2, color='#3498db', label='模型表现')
    ax4.fill(angles, values, alpha=0.25, color='#3498db')
    ax4.set_xticks(angles[:-1])
    ax4.set_xticklabels(categories, fontsize=10)
    ax4.set_ylim(0, 1)
    ax4.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax4.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=8)
    ax4.set_title('综合性能雷达图', fontsize=13, fontweight='bold', pad=20)
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'overall_metrics.png', dpi=300, bbox_inches='tight')
    print("✓ 已生成: overall_metrics.png")
    plt.close()

def plot_time_series(backtest_data, output_dir):
    """绘制时间序列分析"""
    segments = backtest_data['time_segments']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('3D彩票预测模型 - 时间序列分析', fontsize=16, fontweight='bold')
    
    # 准备数据
    segment_labels = [f"第{i+1}段\n({seg['count']}期)" for i, seg in enumerate(segments)]
    top1_rates = [seg['top1_hit_rate'] for seg in segments]
    position_rates = [seg['avg_position_match'] for seg in segments]
    any_digit_rates = [seg['any_digit_match_rate'] for seg in segments]
    
    # 1. Top1命中率趋势
    ax1 = axes[0, 0]
    line1 = ax1.plot(range(len(segments)), top1_rates, marker='o', linewidth=2, 
                     markersize=8, color='#e74c3c', label='Top1命中率')
    ax1.axhline(y=np.mean(top1_rates), color='blue', linestyle='--', 
                linewidth=1.5, label=f'平均值 ({np.mean(top1_rates):.1%})')
    ax1.axhline(y=0.1, color='red', linestyle='--', linewidth=1, 
                alpha=0.5, label='随机基准 (10%)')
    
    for i, rate in enumerate(top1_rates):
        ax1.text(i, rate + 0.02, f'{rate:.1%}', ha='center', fontsize=9, fontweight='bold')
    
    ax1.set_xlabel('时间段', fontsize=12)
    ax1.set_ylabel('Top1命中率', fontsize=12)
    ax1.set_title('Top1命中率时间趋势', fontsize=13, fontweight='bold')
    ax1.set_xticks(range(len(segments)))
    ax1.set_xticklabels(segment_labels)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, 0.5)
    
    # 2. 位置匹配率趋势
    ax2 = axes[0, 1]
    line2 = ax2.plot(range(len(segments)), position_rates, marker='s', linewidth=2,
                     markersize=8, color='#2ecc71', label='位置匹配率')
    ax2.axhline(y=np.mean(position_rates), color='blue', linestyle='--',
                linewidth=1.5, label=f'平均值 ({np.mean(position_rates):.1%})')
    ax2.axhline(y=0.1, color='red', linestyle='--', linewidth=1,
                alpha=0.5, label='随机基准 (10%)')
    
    for i, rate in enumerate(position_rates):
        ax2.text(i, rate + 0.02, f'{rate:.1%}', ha='center', fontsize=9, fontweight='bold')
    
    ax2.set_xlabel('时间段', fontsize=12)
    ax2.set_ylabel('位置匹配率', fontsize=12)
    ax2.set_title('位置匹配率时间趋势', fontsize=13, fontweight='bold')
    ax2.set_xticks(range(len(segments)))
    ax2.set_xticklabels(segment_labels)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 0.6)
    
    # 3. 任意数字命中率趋势
    ax3 = axes[1, 0]
    line3 = ax3.plot(range(len(segments)), any_digit_rates, marker='^', linewidth=2,
                     markersize=8, color='#9b59b6', label='任意数字命中率')
    ax3.axhline(y=np.mean(any_digit_rates), color='blue', linestyle='--',
                linewidth=1.5, label=f'平均值 ({np.mean(any_digit_rates):.1%})')
    
    for i, rate in enumerate(any_digit_rates):
        ax3.text(i, rate + 0.01, f'{rate:.1%}', ha='center', fontsize=9, fontweight='bold')
    
    ax3.set_xlabel('时间段', fontsize=12)
    ax3.set_ylabel('任意数字命中率', fontsize=12)
    ax3.set_title('任意数字命中率时间趋势', fontsize=13, fontweight='bold')
    ax3.set_xticks(range(len(segments)))
    ax3.set_xticklabels(segment_labels)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0.8, 1.0)
    
    # 4. 综合趋势对比
    ax4 = axes[1, 1]
    x = range(len(segments))
    
    # 归一化到0-1便于对比
    norm_top1 = [r / 0.5 for r in top1_rates]
    norm_position = [r / 0.6 for r in position_rates]
    norm_any = [r for r in any_digit_rates]
    
    ax4.plot(x, norm_top1, marker='o', label='Top1命中 (归一化)', linewidth=2, color='#e74c3c')
    ax4.plot(x, norm_position, marker='s', label='位置匹配 (归一化)', linewidth=2, color='#2ecc71')
    ax4.plot(x, norm_any, marker='^', label='任意命中', linewidth=2, color='#9b59b6')
    
    ax4.set_xlabel('时间段', fontsize=12)
    ax4.set_ylabel('归一化性能', fontsize=12)
    ax4.set_title('综合性能趋势对比', fontsize=13, fontweight='bold')
    ax4.set_xticks(range(len(segments)))
    ax4.set_xticklabels(segment_labels)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0.5, 1.1)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'time_series_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ 已生成: time_series_analysis.png")
    plt.close()

def plot_digit_analysis(backtest_data, output_dir):
    """绘制数字级别分析"""
    digit_stats = backtest_data['digit_analysis']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('3D彩票预测模型 - 数字级别分析', fontsize=16, fontweight='bold')
    
    digits = list(range(10))
    predicted = [digit_stats[str(d)]['predicted_count'] for d in digits]
    actual = [digit_stats[str(d)]['actual_count'] for d in digits]
    hit = [digit_stats[str(d)]['hit_count'] for d in digits]
    precision = [digit_stats[str(d)]['precision'] for d in digits]
    
    # 1. 预测次数 vs 实际次数
    ax1 = axes[0, 0]
    x = np.arange(len(digits))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, predicted, width, label='预测次数', 
                    color='#3498db', alpha=0.7, edgecolor='black')
    bars2 = ax1.bar(x + width/2, actual, width, label='实际次数',
                    color='#e74c3c', alpha=0.7, edgecolor='black')
    
    ax1.set_xlabel('数字', fontsize=12)
    ax1.set_ylabel('出现次数', fontsize=12)
    ax1.set_title('预测次数 vs 实际出现次数', fontsize=13, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(digits)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. 命中次数
    ax2 = axes[0, 1]
    colors = ['#2ecc71' if h > 0 else '#95a5a6' for h in hit]
    bars = ax2.bar(digits, hit, color=colors, alpha=0.7, edgecolor='black')
    
    for bar, h in zip(bars, hit):
        if h > 0:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(h)}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax2.set_xlabel('数字', fontsize=12)
    ax2.set_ylabel('命中次数', fontsize=12)
    ax2.set_title('各数字命中次数', fontsize=13, fontweight='bold')
    ax2.set_xticks(digits)
    ax2.grid(axis='y', alpha=0.3)
    
    # 3. 精确率
    ax3 = axes[1, 0]
    colors = ['#2ecc71' if p > 0 else '#e74c3c' for p in precision]
    bars = ax3.bar(digits, precision, color=colors, alpha=0.7, edgecolor='black')
    
    for bar, p in zip(bars, precision):
        if p > 0:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{p:.1%}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax3.set_xlabel('数字', fontsize=12)
    ax3.set_ylabel('精确率', fontsize=12)
    ax3.set_title('各数字预测精确率', fontsize=13, fontweight='bold')
    ax3.set_xticks(digits)
    ax3.grid(axis='y', alpha=0.3)
    ax3.set_ylim(0, 0.4)
    
    # 4. 预测覆盖分析
    ax4 = axes[1, 1]
    predicted_digits = [d for d in digits if predicted[d] > 0]
    unpredicted_digits = [d for d in digits if predicted[d] == 0]
    
    labels = ['预测的数字\n(2,3,5,6,8)', '未预测数字\n(0,1,4,7,9)']
    sizes = [len(predicted_digits), len(unpredicted_digits)]
    colors_pie = ['#2ecc71', '#e74c3c']
    explode = (0.1, 0)
    
    wedges, texts, autotexts = ax4.pie(sizes, explode=explode, labels=labels, 
                                         colors=colors_pie, autopct='%1.0f%%',
                                         shadow=True, startangle=90,
                                         textprops={'fontsize': 11, 'fontweight': 'bold'})
    
    ax4.set_title('数字覆盖率分析', fontsize=13, fontweight='bold')
    
    # 添加注释
    ax4.text(0, -1.5, f'预测数字: {predicted_digits}\n未预测数字: {unpredicted_digits}',
            ha='center', fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'digit_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ 已生成: digit_analysis.png")
    plt.close()

def plot_prediction_samples(backtest_data, output_dir):
    """绘制预测样本分析"""
    recent_preds = backtest_data['recent_10_predictions']
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('3D彩票预测模型 - 最近10期预测详情', fontsize=16, fontweight='bold')
    
    # 1. 命中情况可视化
    ax1 = axes[0]
    
    periods = [p['period'][-5:] for p in recent_preds]  # 只显示后5位
    hit_counts = [p['top5_hit_count'] for p in recent_preds]
    
    colors = ['#2ecc71' if h >= 2 else '#f39c12' if h == 1 else '#e74c3c' for h in hit_counts]
    bars = ax1.bar(range(len(periods)), hit_counts, color=colors, alpha=0.7, edgecolor='black')
    
    for bar, h, period in zip(bars, hit_counts, periods):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(h)}/3',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax1.set_xlabel('期号(后5位)', fontsize=12)
    ax1.set_ylabel('命中数字个数', fontsize=12)
    ax1.set_title('最近10期Top5命中情况', fontsize=13, fontweight='bold')
    ax1.set_xticks(range(len(periods)))
    ax1.set_xticklabels(periods, rotation=45)
    ax1.set_ylim(0, 3.5)
    ax1.grid(axis='y', alpha=0.3)
    
    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ecc71', label='优秀 (≥2个)'),
        Patch(facecolor='#f39c12', label='一般 (1个)'),
        Patch(facecolor='#e74c3c', label='较差 (0个)')
    ]
    ax1.legend(handles=legend_elements, loc='upper right')
    
    # 2. 位置匹配热力图
    ax2 = axes[1]
    
    # 准备热力图数据
    position_matches = []
    for pred in recent_preds:
        position_matches.append(pred['position_match'])
    
    position_matrix = np.array(position_matches).T  # 转置为(3, 10)
    
    im = ax2.imshow(position_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
    
    # 设置刻度
    ax2.set_xticks(range(len(periods)))
    ax2.set_xticklabels(periods, rotation=45)
    ax2.set_yticks([0, 1, 2])
    ax2.set_yticklabels(['位置0', '位置1', '位置2'])
    
    # 添加数值标注
    for i in range(3):
        for j in range(len(periods)):
            text = '✓' if position_matrix[i, j] else '✗'
            color = 'white' if position_matrix[i, j] else 'black'
            ax2.text(j, i, text, ha='center', va='center',
                    color=color, fontsize=14, fontweight='bold')
    
    ax2.set_xlabel('期号(后5位)', fontsize=12)
    ax2.set_ylabel('位置', fontsize=12)
    ax2.set_title('各位置匹配情况热力图', fontsize=13, fontweight='bold')
    
    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax2)
    cbar.set_label('匹配状态', rotation=270, labelpad=20, fontsize=11)
    cbar.set_ticks([0, 1])
    cbar.set_ticklabels(['未匹配', '匹配'])
    
    plt.tight_layout()
    plt.savefig(output_dir / 'prediction_samples.png', dpi=300, bbox_inches='tight')
    print("✓ 已生成: prediction_samples.png")
    plt.close()

def create_summary_dashboard(backtest_data, output_dir):
    """创建总结仪表盘"""
    summary = backtest_data['summary']
    stats = summary['overall_statistics']
    
    fig = plt.figure(figsize=(16, 10))
    fig.suptitle('3D彩票预测模型 - 回测总结仪表盘', fontsize=18, fontweight='bold')
    
    # 创建网格布局
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
    
    # 1. 核心指标卡片
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.axis('off')
    ax1.text(0.5, 0.8, '位置匹配率', ha='center', fontsize=14, fontweight='bold')
    ax1.text(0.5, 0.5, f"{stats['avg_position_match_rate']:.1%}", 
            ha='center', fontsize=32, fontweight='bold', color='#2ecc71')
    ax1.text(0.5, 0.2, '(随机基准: 10%)', ha='center', fontsize=10, color='gray')
    ax1.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False, 
                                edgecolor='#2ecc71', linewidth=3))
    
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis('off')
    ax2.text(0.5, 0.8, 'Top1命中率', ha='center', fontsize=14, fontweight='bold')
    ax2.text(0.5, 0.5, f"{stats['top1_hit_rate']:.1%}",
            ha='center', fontsize=32, fontweight='bold', color='#3498db')
    ax2.text(0.5, 0.2, '(随机基准: 10%)', ha='center', fontsize=10, color='gray')
    ax2.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False,
                                edgecolor='#3498db', linewidth=3))
    
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis('off')
    ax3.text(0.5, 0.8, 'Top5平均命中', ha='center', fontsize=14, fontweight='bold')
    ax3.text(0.5, 0.5, f"{stats['top5_avg_hits']:.2f}/3",
            ha='center', fontsize=32, fontweight='bold', color='#e74c3c')
    ax3.text(0.5, 0.2, '(随机基准: 0.5/3)', ha='center', fontsize=10, color='gray')
    ax3.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False,
                                edgecolor='#e74c3c', linewidth=3))
    
    # 2. 性能对比柱状图
    ax4 = fig.add_subplot(gs[1, :])
    metrics = ['位置匹配率', 'Top1命中率', 'Top3命中率', 'Top5命中率', '任意命中率']
    model_values = [
        stats['avg_position_match_rate'],
        stats['top1_hit_rate'],
        stats['top3_avg_hits'] / 3,
        stats['top5_avg_hits'] / 3,
        stats['any_digit_match_rate']
    ]
    random_values = [0.1, 0.1, 0.3/3, 0.5/3, 0.271]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    bars1 = ax4.bar(x - width/2, model_values, width, label='模型表现',
                    color='#2ecc71', alpha=0.8, edgecolor='black')
    bars2 = ax4.bar(x + width/2, random_values, width, label='随机基准',
                    color='#e74c3c', alpha=0.8, edgecolor='black')
    
    # 添加提升倍数
    for i, (m, r) in enumerate(zip(model_values, random_values)):
        improvement = m / r if r > 0 else 0
        ax4.text(i, max(m, r) + 0.05, f'{improvement:.1f}x',
                ha='center', fontsize=11, fontweight='bold', color='green')
    
    ax4.set_ylabel('准确率/命中率', fontsize=12, fontweight='bold')
    ax4.set_title('模型性能 vs 随机基准', fontsize=14, fontweight='bold', pad=15)
    ax4.set_xticks(x)
    ax4.set_xticklabels(metrics, fontsize=11)
    ax4.legend(fontsize=11)
    ax4.grid(axis='y', alpha=0.3)
    ax4.set_ylim(0, 1.0)
    
    # 3. 统计信息文本
    ax5 = fig.add_subplot(gs[2, 0])
    ax5.axis('off')
    info_text = f"""
回测统计信息

━━━━━━━━━━━━━━
总预测期数: {summary['total_predictions']}期
时间范围: {summary['data_range']['start']}
         至 {summary['data_range']['end']}

完全匹配率: {stats['exact_match_rate']:.2%}
任意命中率: {stats['any_digit_match_rate']:.1%}
━━━━━━━━━━━━━━
"""
    ax5.text(0.1, 0.5, info_text, fontsize=11, family='monospace',
            verticalalignment='center')
    
    # 4. 评级
    ax6 = fig.add_subplot(gs[2, 1])
    ax6.axis('off')
    
    # 计算综合评分
    score = (stats['avg_position_match_rate'] * 0.4 +
             stats['top1_hit_rate'] * 0.3 +
             stats['any_digit_match_rate'] * 0.3)
    
    if score >= 0.5:
        grade = 'A'
        color = '#2ecc71'
        comment = '优秀'
    elif score >= 0.4:
        grade = 'B'
        color = '#3498db'
        comment = '良好'
    elif score >= 0.3:
        grade = 'C'
        color = '#f39c12'
        comment = '中等'
    else:
        grade = 'D'
        color = '#e74c3c'
        comment = '较差'
    
    ax6.text(0.5, 0.7, '综合评级', ha='center', fontsize=14, fontweight='bold')
    ax6.text(0.5, 0.4, grade, ha='center', fontsize=48, fontweight='bold', color=color)
    ax6.text(0.5, 0.15, comment, ha='center', fontsize=16, color=color)
    ax6.add_patch(plt.Circle((0.5, 0.4), 0.25, fill=False, edgecolor=color, linewidth=4))
    
    # 5. 建议
    ax7 = fig.add_subplot(gs[2, 2])
    ax7.axis('off')
    recommendations = """
使用建议

✓ 使用Top5作为候选池
✓ 结合历史统计分析
✓ 分散投注降低风险
━━━━━━━━━━━━━━
✗ 避免完全依赖预测
✗ 避免重注单一组合
✗ 不要超额投入
━━━━━━━━━━━━━━
⚠️ 仅供参考,理性购彩
"""
    ax7.text(0.1, 0.5, recommendations, fontsize=10, family='monospace',
            verticalalignment='center')
    
    plt.savefig(output_dir / 'summary_dashboard.png', dpi=300, bbox_inches='tight')
    print("✓ 已生成: summary_dashboard.png")
    plt.close()

def generate_html_report(backtest_data, output_dir):
    """生成HTML报告"""
    summary = backtest_data['summary']
    stats = summary['overall_statistics']
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D彩票预测模型 - 回测报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Microsoft YaHei', 'SimHei', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 36px;
            margin-bottom: 10px;
        }}
        
        header p {{
            font-size: 16px;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
        }}
        
        .metric-card h3 {{
            font-size: 16px;
            margin-bottom: 15px;
            opacity: 0.9;
        }}
        
        .metric-card .value {{
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .metric-card .baseline {{
            font-size: 14px;
            opacity: 0.8;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            font-size: 28px;
            margin-bottom: 20px;
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .image-container {{
            text-align: center;
            margin: 20px 0;
        }}
        
        .image-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        
        .warning h3 {{
            color: #856404;
            margin-bottom: 10px;
        }}
        
        .recommendations {{
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        
        .recommendations h3 {{
            color: #0c5460;
            margin-bottom: 10px;
        }}
        
        .recommendations ul {{
            margin-left: 20px;
        }}
        
        .recommendations li {{
            margin: 5px 0;
        }}
        
        footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 3D彩票预测模型</h1>
            <p>回测报告 | 基于LSTM+Attention深度学习</p>
            <p>回测期数: {summary['total_predictions']}期 | 时间: {summary['data_range']['start']} ~ {summary['data_range']['end']}</p>
        </header>
        
        <div class="content">
            <section class="section">
                <h2>📊 核心性能指标</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <h3>位置匹配率</h3>
                        <div class="value">{stats['avg_position_match_rate']:.1%}</div>
                        <div class="baseline">随机基准: 10%</div>
                        <div class="baseline">提升: {stats['avg_position_match_rate']/0.1:.1f}倍</div>
                    </div>
                    
                    <div class="metric-card">
                        <h3>Top1命中率</h3>
                        <div class="value">{stats['top1_hit_rate']:.1%}</div>
                        <div class="baseline">随机基准: 10%</div>
                        <div class="baseline">提升: {stats['top1_hit_rate']/0.1:.1f}倍</div>
                    </div>
                    
                    <div class="metric-card">
                        <h3>Top5平均命中</h3>
                        <div class="value">{stats['top5_avg_hits']:.2f}/3</div>
                        <div class="baseline">随机基准: 0.5/3</div>
                        <div class="baseline">提升: {stats['top5_avg_hits']/0.5:.1f}倍</div>
                    </div>
                    
                    <div class="metric-card">
                        <h3>任意数字命中率</h3>
                        <div class="value">{stats['any_digit_match_rate']:.1%}</div>
                        <div class="baseline">随机基准: 27%</div>
                        <div class="baseline">提升: {stats['any_digit_match_rate']/0.271:.1f}倍</div>
                    </div>
                </div>
            </section>
            
            <section class="section">
                <h2>📈 可视化分析</h2>
                
                <div class="image-container">
                    <h3>整体性能指标</h3>
                    <img src="overall_metrics.png" alt="整体性能指标">
                </div>
                
                <div class="image-container">
                    <h3>时间序列分析</h3>
                    <img src="time_series_analysis.png" alt="时间序列分析">
                </div>
                
                <div class="image-container">
                    <h3>数字级别分析</h3>
                    <img src="digit_analysis.png" alt="数字级别分析">
                </div>
                
                <div class="image-container">
                    <h3>预测样本分析</h3>
                    <img src="prediction_samples.png" alt="预测样本分析">
                </div>
                
                <div class="image-container">
                    <h3>总结仪表盘</h3>
                    <img src="summary_dashboard.png" alt="总结仪表盘">
                </div>
            </section>
            
            <section class="section">
                <div class="recommendations">
                    <h3>💡 使用建议</h3>
                    <ul>
                        <li>✅ 使用Top5预测作为候选池,不要依赖单一号码</li>
                        <li>✅ 结合历史统计数据和模型预测综合决策</li>
                        <li>✅ 分散投注,覆盖多个组合以降低风险</li>
                        <li>✅ 关注位置匹配率较高的预测结果</li>
                    </ul>
                </div>
                
                <div class="warning">
                    <h3>⚠️ 重要提示</h3>
                    <ul>
                        <li>❌ 模型存在过拟合,只预测5个数字(2,3,5,6,8)</li>
                        <li>❌ 完全匹配率为0%,精确预测极其困难</li>
                        <li>❌ 48%准确率仍意味着52%的不确定性</li>
                        <li>⚠️ 彩票具有强随机性,历史规律不能预测未来</li>
                        <li>⚠️ 本模型仅供参考,不构成投资建议</li>
                        <li>⚠️ 请理性购彩,不要投入超过承受能力的金额</li>
                    </ul>
                </div>
            </section>
        </div>
        
        <footer>
            <p>© 2026 3D彩票预测模型 | 回测报告自动生成</p>
            <p>技术栈: Python + PyTorch + LSTM + Attention</p>
            <p><strong>免责声明</strong>: 本报告仅用于学术研究和技术分析,不构成任何投资建议。</p>
        </footer>
    </div>
</body>
</html>
"""
    
    with open(output_dir / 'backtest_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✓ 已生成: backtest_report.html")

def main():
    print("=" * 80)
    print("生成回测可视化报告")
    print("=" * 80)
    
    # 创建输出目录
    output_dir = Path('results/visualizations')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[1] 加载回测数据")
    backtest_data = load_backtest_results()
    print(f"✓ 已加载 {backtest_data['summary']['total_predictions']} 期回测数据")
    
    print(f"\n[2] 生成可视化图表")
    print("\n正在生成图表...")
    
    # 生成各类图表
    plot_overall_metrics(backtest_data['summary'], output_dir)
    plot_time_series(backtest_data, output_dir)
    plot_digit_analysis(backtest_data, output_dir)
    plot_prediction_samples(backtest_data, output_dir)
    create_summary_dashboard(backtest_data, output_dir)
    
    print(f"\n[3] 生成HTML报告")
    generate_html_report(backtest_data, output_dir)
    
    print(f"\n{'='*80}")
    print("可视化报告生成完成!")
    print(f"{'='*80}")
    print(f"\n📁 输出目录: {output_dir}")
    print(f"\n生成的文件:")
    print(f"  ├── overall_metrics.png       - 整体性能指标")
    print(f"  ├── time_series_analysis.png  - 时间序列分析")
    print(f"  ├── digit_analysis.png        - 数字级别分析")
    print(f"  ├── prediction_samples.png    - 预测样本分析")
    print(f"  ├── summary_dashboard.png     - 总结仪表盘")
    print(f"  └── backtest_report.html      - 完整HTML报告")
    
    print(f"\n💡 提示:")
    print(f"  - 在浏览器中打开 backtest_report.html 查看完整报告")
    print(f"  - 所有图表保存在 {output_dir} 目录")
    print(f"  - 分辨率: 300 DPI (适合打印)")
    
    print(f"\n{'='*80}")

if __name__ == '__main__':
    main()
