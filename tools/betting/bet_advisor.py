#!/usr/bin/env python3
"""
命令行投注建议工具

快速查看今日投注建议，输出简洁直观：
- 是否建议购买
- 如果建议购买，给出具体投注组合
- 成本和预期收益
"""

import os
import sys
import django
from datetime import datetime

# Django setup
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottery_web.settings')
django.setup()

from lottery.models import Prediction


def print_header():
    """打印标题"""
    print("\n" + "=" * 70)
    print("🎯  3D彩票投注建议工具")
    print("=" * 70)
    print(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")


def print_recommendation(pred):
    """打印投注建议"""
    is_bet = pred.recommendation == 'bet'
    
    # 基本信息
    print(f"📅 预测期号: {pred.predicted_for_period}")
    print(f"⏰ 生成时间: {pred.created_at.strftime('%Y-%m-%d %H:%M')}")
    print(f"📊 置信度评分: {pred.confidence_score:.2f}")
    
    if pred.percentile_rank:
        print(f"📈 百分位排名: {pred.percentile_rank:.1f}%")
    
    print(f"🎲 策略: {pred.strategy.upper()}")
    print()
    
    # 建议状态
    if is_bet:
        print("=" * 70)
        print("✅  建议投注")
        print("=" * 70)
        print(f"💡 理由: {pred.recommendation_reason}")
        print()
        
        # 投注统计
        if pred.bet_count > 0:
            print(f"💰 投注统计:")
            print(f"   总注数: {pred.bet_count} 注")
            print(f"   总成本: {pred.total_cost} 元")
            print()
        
        # Top5数字
        if pred.top5_digits and pred.digit_probs:
            print("🔢 Top5 预测数字（概率）:")
            for i, digit in enumerate(pred.top5_digits):
                prob = pred.digit_probs[digit] * 100
                print(f"   {i+1}. 数字 {digit}  →  {prob:.1f}%")
            print()
        
        # 投注组合
        if pred.betting_combinations:
            print("🎰 推荐投注组合 (前10组):")
            print("-" * 70)
            print(f"{'序号':<6} {'组合':<15} {'类型':<10} {'注数':<8} {'成本':<10} {'奖金'}")
            print("-" * 70)
            
            for idx, combo in enumerate(pred.betting_combinations[:10], 1):
                numbers_str = '-'.join(map(str, combo['numbers']))
                combo_type = '组选6' if combo['type'] == 'group6' else '组选3'
                print(f"{idx:<6} {numbers_str:<15} {combo_type:<10} "
                      f"{combo['bet_count']:<8} {combo['cost']:<10} {combo['expected_prize']}")
            
            if len(pred.betting_combinations) > 10:
                print(f"\n   ... 还有 {len(pred.betting_combinations) - 10} 个组合")
            
            print("-" * 70)
            print()
            
            # 快速复制格式
            print("📋 快速复制（前5组）:")
            for idx, combo in enumerate(pred.betting_combinations[:5], 1):
                numbers = combo['numbers']
                bet_count = combo['bet_count']
                # 生成所有排列组合
                if combo['type'] == 'group6':
                    # 组选6：三个不同数字
                    print(f"   {idx}. 组选6: {numbers[0]}{numbers[1]}{numbers[2]} × {bet_count}注")
                else:
                    # 组选3：两个相同
                    print(f"   {idx}. 组选3: {numbers[0]}{numbers[1]}{numbers[2]} × {bet_count}注")
            print()
        
    else:
        print("=" * 70)
        print("⚠️  不建议投注")
        print("=" * 70)
        print(f"💡 理由: {pred.recommendation_reason}")
        print()
        
        # 仍然显示Top5数字供参考
        if pred.top5_digits and pred.digit_probs:
            print("🔢 Top5 预测数字（仅供参考）:")
            for i, digit in enumerate(pred.top5_digits):
                prob = pred.digit_probs[digit] * 100
                print(f"   {i+1}. 数字 {digit}  →  {prob:.1f}%")
            print()
    
    print("=" * 70)
    print()


def main():
    """主函数"""
    print_header()
    
    try:
        # 获取最新预测
        latest_pred = Prediction.objects.order_by('-created_at').first()
        
        if not latest_pred:
            print("❌ 错误: 暂无预测数据")
            print()
            print("💡 请先运行以下命令生成预测:")
            print("   python tools/betting/daily_recommendation.py --strategy top5")
            print()
            return 1
        
        # 打印建议
        print_recommendation(latest_pred)
        
        # 底部提示
        if latest_pred.recommendation == 'bet':
            print("⚠️  风险提示:")
            print("   1. 彩票本质是负期望值游戏，请理性投注")
            print("   2. 建议每日投注上限不超过200元")
            print("   3. 连续5期不中建议暂停")
            print("   4. 本工具仅供参考，不构成投资建议")
            print()
        
        return 0
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
