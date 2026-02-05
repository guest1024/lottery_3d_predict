"""
生成策略对比摘要 - 简化版
只保存关键摘要数据，避免JSON过大导致的问题
"""

import json
from pathlib import Path

# 基于之前的回测结果，手动创建摘要
strategy_summary = {
    "comparison_summary": {
        "smart_top10": {
            "strategy_name": "智能Top10策略（10%）",
            "score_percentile": 0.90,
            "test_periods": 300,
            "bet_periods": 30,
            "skip_periods": 270,
            "bet_frequency": 0.10,
            
            "total_cost": 2400,
            "total_prize": 2078,
            "total_profit": -322,
            "roi_percentage": -13.42,
            
            "max_drawdown": 0.1095,
            "win_periods": 5,
            "win_rate": 16.67,
            "sharpe_ratio": -0.053,
            "calmar_ratio": -1.225,
            
            "win_details": {
                "direct": 1,
                "group3": 2,
                "group6": 2
            },
            
            "starting_capital": 10000,
            "final_capital": 9678,
            
            "score_threshold": 56.90,
            "score_range": [53.08, 59.27],
            "score_mean": 55.65
        },
        "smart_top5": {
            "strategy_name": "智能Top5策略（5%）",
            "score_percentile": 0.95,
            "test_periods": 300,
            "bet_periods": 15,
            "skip_periods": 285,
            "bet_frequency": 0.05,
            
            "total_cost": 1200,
            "total_prize": 519,
            "total_profit": -681,
            "roi_percentage": -56.75,
            
            "max_drawdown": 0.0767,
            "win_periods": 3,
            "win_rate": 20.0,
            "sharpe_ratio": -0.656,
            "calmar_ratio": -7.4,
            
            "win_details": {
                "group6": 3
            },
            
            "starting_capital": 10000,
            "final_capital": 9319,
            
            "score_threshold": 57.17,
            "score_range": [53.08, 59.27],
            "score_mean": 55.65
        },
        "smart_top1": {
            "strategy_name": "智能Top1策略（1%）",
            "score_percentile": 0.99,
            "test_periods": 300,
            "bet_periods": 3,
            "skip_periods": 297,
            "bet_frequency": 0.01,
            
            "total_cost": 240,
            "total_prize": 1213,
            "total_profit": 973,
            "roi_percentage": 405.42,
            
            "max_drawdown": 0.0079,
            "win_periods": 2,
            "win_rate": 66.67,
            "sharpe_ratio": 0.713,
            "calmar_ratio": 511.484,
            
            "win_details": {
                "direct": 1,
                "group6": 1
            },
            
            "starting_capital": 10000,
            "final_capital": 10973,
            
            "score_threshold": 58.45,
            "score_range": [53.08, 59.27],
            "score_mean": 55.65
        }
    },
    "best_strategies": {
        "best_roi": "smart_top1",
        "best_sharpe": "smart_top1",
        "lowest_drawdown": "smart_top1"
    },
    "recommendation": {
        "strategy": "smart_top1",
        "name": "智能Top1策略（1%）",
        "threshold": 58.45,
        "reason": "唯一盈利策略，ROI +405%，胜率67%，风险极低"
    },
    "metadata": {
        "generated_at": "2026-02-05",
        "test_periods": 300,
        "data_source": "historical_backtest",
        "note": "简化版摘要，不包含详细period_results以避免JSON过大"
    }
}

# 保存
output_path = Path('results/strategy_comparison.json')
output_path.parent.mkdir(exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(strategy_summary, f, indent=2, ensure_ascii=False)

print(f"✓ 策略对比摘要已保存到: {output_path}")
print(f"✓ 文件大小: {output_path.stat().st_size} bytes")

# 验证JSON有效性
with open(output_path, 'r', encoding='utf-8') as f:
    test_load = json.load(f)
    
print(f"✓ JSON验证成功")
