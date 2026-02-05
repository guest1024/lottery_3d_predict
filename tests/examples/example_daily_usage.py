"""
每日使用示例
============

演示如何在Python代码中调用每日机会评估功能
"""

from daily_opportunity_check import (
    check_today_opportunity,
    check_quick,
    get_betting_plan
)


# ==================== 示例1: 详细评估 ====================
def example_1_detailed():
    """详细模式 - 获取完整评估信息"""
    print("="*70)
    print("示例1: 详细评估模式")
    print("="*70)
    
    result = check_today_opportunity(verbose=True)
    
    print("\n返回结果:")
    print(f"  评分: {result['score']:.2f}")
    print(f"  建议: {result['recommendation']}")
    print(f"  是否投注: {result['should_bet']}")
    
    if result['should_bet']:
        plan = result['betting_plan']
        print(f"\n投注计划:")
        print(f"  注数: {plan['num_bets']}")
        print(f"  成本: ¥{plan['cost']}")
        print(f"  预期胜率: {plan['expected_win_rate']*100:.1f}%")


# ==================== 示例2: 快速检查 ====================
def example_2_quick():
    """快速模式 - 只判断是否投注"""
    print("\n" + "="*70)
    print("示例2: 快速检查模式")
    print("="*70)
    
    should_bet = check_quick()
    
    if should_bet:
        print("✅ 今天建议投注！")
        
        # 获取投注计划
        plan = get_betting_plan()
        print(f"\n投注详情:")
        print(f"  投注: {plan['num_bets']}注")
        print(f"  成本: ¥{plan['cost']}")
        print(f"\n前5注:")
        for i, combo in enumerate(plan['combinations'][:5], 1):
            print(f"  {i}. {combo}")
    else:
        print("❌ 今天继续观望。")


# ==================== 示例3: 自动化脚本 ====================
def example_3_automation():
    """自动化场景 - 定时任务使用"""
    print("\n" + "="*70)
    print("示例3: 自动化脚本")
    print("="*70)
    
    # 安静模式评估
    result = check_today_opportunity(verbose=False)
    
    # 记录到日志
    with open('betting_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"\n{result['timestamp']}\n")
        f.write(f"评分: {result['score']:.2f}\n")
        f.write(f"建议: {result['recommendation']}\n")
        
        if result['should_bet']:
            f.write(f"投注: {result['betting_plan']['num_bets']}注\n")
            f.write(f"成本: ¥{result['betting_plan']['cost']}\n")
        else:
            f.write(f"差距: {abs(result['score_gap']):.2f}分\n")
    
    print("✓ 评估完成，已记录到 betting_log.txt")
    
    # 如果建议投注，发送通知（这里用打印代替）
    if result['should_bet']:
        print(f"\n🔔 投注提醒:")
        print(f"   评分: {result['score']:.2f}分")
        print(f"   投注: {result['betting_plan']['num_bets']}注")
        print(f"   成本: ¥{result['betting_plan']['cost']}")


# ==================== 示例4: 条件判断 ====================
def example_4_conditional():
    """条件判断 - 基于评分做不同操作"""
    print("\n" + "="*70)
    print("示例4: 条件判断")
    print("="*70)
    
    result = check_today_opportunity(verbose=False)
    score = result['score']
    
    if score >= 63.0:
        print(f"🌟 极高分！评分: {score:.2f}")
        print("   历史命中率: 100%")
        print("   强烈建议投注！")
    elif score >= 58.45:
        print(f"✅ 高分！评分: {score:.2f}")
        print("   历史胜率: 67%")
        print("   建议投注")
    elif score >= 57.0:
        print(f"⚠️  接近阈值。评分: {score:.2f}")
        print(f"   差距: {58.45 - score:.2f}分")
        print("   可继续观察")
    else:
        print(f"❌ 评分较低。评分: {score:.2f}")
        print("   建议观望")


# ==================== 示例5: 集成到定时任务 ====================
def example_5_cron_job():
    """
    Cron定时任务示例
    
    每天上午10点运行:
    0 10 * * * cd /c1/program/lottery_3d_predict && python daily_opportunity_check.py --quiet >> /tmp/betting.log
    
    或使用Python脚本:
    0 10 * * * cd /c1/program/lottery_3d_predict && python example_daily_usage.py
    """
    print("\n" + "="*70)
    print("示例5: 定时任务集成")
    print("="*70)
    
    import os
    from datetime import datetime
    
    # 设置日志文件
    log_file = '/tmp/daily_betting_check.log'
    
    # 评估
    result = check_today_opportunity(verbose=False)
    
    # 写入日志
    with open(log_file, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"\n{'='*60}\n")
        f.write(f"时间: {timestamp}\n")
        f.write(f"评分: {result['score']:.2f}\n")
        f.write(f"阈值: {result['threshold']:.2f}\n")
        f.write(f"建议: {result['recommendation']}\n")
        
        if result['should_bet']:
            f.write(f"💰 投注计划:\n")
            f.write(f"   注数: {result['betting_plan']['num_bets']}\n")
            f.write(f"   成本: ¥{result['betting_plan']['cost']}\n")
            f.write(f"   Top10: {result['top10_digits']}\n")
        else:
            f.write(f"   差距: {abs(result['score_gap']):.2f}分\n")
    
    print(f"✓ 日志已写入: {log_file}")
    
    # 如果建议投注，可以发送邮件/短信通知（示例）
    if result['should_bet']:
        print(f"\n📧 [模拟] 发送投注提醒...")
        print(f"   收件人: your_email@example.com")
        print(f"   主题: 3D彩票投注提醒 - 评分{result['score']:.2f}")
        print(f"   内容: 建议投注{result['betting_plan']['num_bets']}注，成本¥{result['betting_plan']['cost']}")
        
        # 实际实现可以使用:
        # import smtplib
        # send_email(...)


# ==================== 示例6: Web API集成 ====================
def example_6_web_api():
    """Flask/Django API集成示例"""
    print("\n" + "="*70)
    print("示例6: Web API集成")
    print("="*70)
    
    # 这可以用在Flask/Django的API endpoint中
    result = check_today_opportunity(verbose=False)
    
    # 返回JSON格式
    api_response = {
        'status': 'success',
        'data': {
            'timestamp': result['timestamp'],
            'score': round(result['score'], 2),
            'recommendation': result['recommendation'],
            'should_bet': result['should_bet'],
            'last_period': result['last_period'],
        }
    }
    
    if result['should_bet']:
        api_response['data']['betting_plan'] = {
            'num_bets': result['betting_plan']['num_bets'],
            'cost': result['betting_plan']['cost'],
            'expected_return': round(result['betting_plan']['cost'] * result['betting_plan']['expected_roi'], 2)
        }
    
    print("API响应:")
    import json
    print(json.dumps(api_response, indent=2, ensure_ascii=False))


# ==================== 主函数 ====================
def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("每日机会评估 - 使用示例")
    print("="*70)
    
    try:
        # 示例1: 详细评估
        example_1_detailed()
        
        # 示例2: 快速检查
        example_2_quick()
        
        # 示例3: 自动化脚本
        example_3_automation()
        
        # 示例4: 条件判断
        example_4_conditional()
        
        # 示例5: 定时任务
        example_5_cron_job()
        
        # 示例6: Web API
        example_6_web_api()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 运行所有示例
    main()
    
    # 或者只运行特定示例:
    # example_2_quick()
