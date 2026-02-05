"""
定时任务调度器模块

功能：
1. 每天自动运行机会评估
2. 定期爬取最新数据
3. 定期清理过期日志
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

# 配置日志
logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = BackgroundScheduler()


def daily_opportunity_check():
    """
    每日机会评估任务
    
    运行时间：每天早上 9:00
    功能：评估当前投资机会，记录评分和建议
    """
    try:
        logger.info("=" * 70)
        logger.info(f"开始每日机会评估 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        
        # 导入评估函数
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from tools.strategies.daily_opportunity_check import check_today_opportunity
        
        # 执行评估
        result = check_today_opportunity()
        
        # 记录结果
        logger.info(f"\n评估结果:")
        logger.info(f"  评分: {result['score']:.2f}分")
        logger.info(f"  阈值: {result['threshold']:.2f}分")
        logger.info(f"  差距: {abs(result['score_gap']):.2f}分")
        logger.info(f"  建议: {result['recommendation']}")
        logger.info(f"  是否投注: {'✅ 是' if result['should_bet'] else '❌ 否'}")
        
        if result['should_bet']:
            betting_plan = result.get('betting_plan', {})
            logger.info(f"\n🎯 投注计划:")
            logger.info(f"  投注注数: {betting_plan.get('num_bets', 'N/A')}注")
            logger.info(f"  投注金额: {betting_plan.get('cost', 'N/A')}元")
            logger.info(f"  预期胜率: {betting_plan.get('expected_win_rate', 0)*100:.1f}%")
            logger.info(f"  预期ROI: {betting_plan.get('expected_roi', 0)*100:.1f}%")
        
        logger.info("=" * 70)
        logger.info("每日机会评估完成")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"每日机会评估失败: {e}", exc_info=True)


def weekly_data_crawl():
    """
    每周数据爬取任务
    
    运行时间：每周一早上 8:00
    功能：爬取最新开奖数据，更新数据库
    """
    try:
        logger.info("=" * 70)
        logger.info(f"开始每周数据爬取 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        
        # 导入爬虫
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from tools.crawlers.crawl_real_data import SimpleLottery3DCrawler
        
        # 执行爬取
        crawler = SimpleLottery3DCrawler()
        results = crawler.crawl_recent_data(days=7)
        
        logger.info(f"爬取结果: 获取 {len(results)} 条数据")
        
        # 导入并保存到数据库
        from lottery.models import LotteryResult
        
        added = 0
        updated = 0
        for result in results:
            _, created = LotteryResult.objects.update_or_create(
                period=result['period'],
                defaults={
                    'num1': result['num1'],
                    'num2': result['num2'],
                    'num3': result['num3'],
                    'date': result['date'],
                }
            )
            if created:
                added += 1
            else:
                updated += 1
        
        logger.info(f"数据导入完成: 新增 {added} 条，更新 {updated} 条")
        logger.info("=" * 70)
        logger.info("每周数据爬取完成")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"每周数据爬取失败: {e}", exc_info=True)


def cleanup_old_job_executions(max_age=604_800):
    """
    清理过期的任务执行记录
    
    运行时间：每天凌晨 2:00
    功能：删除7天前的任务执行记录
    
    Args:
        max_age: 最大保留时间（秒），默认7天
    """
    try:
        logger.info(f"开始清理过期任务记录 (>7天)")
        util.delete_old_job_executions(max_age)
        logger.info("清理完成")
    except Exception as e:
        logger.error(f"清理任务记录失败: {e}", exc_info=True)


def start_scheduler():
    """
    启动定时任务调度器
    
    注册所有定时任务并启动调度器
    """
    if scheduler.running:
        logger.info("调度器已在运行中")
        return
    
    try:
        # 添加任务存储
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        # 任务1: 每天早上 9:00 运行机会评估
        scheduler.add_job(
            daily_opportunity_check,
            trigger=CronTrigger(hour=9, minute=0),  # 每天 9:00
            id="daily_opportunity_check",
            max_instances=1,
            replace_existing=True,
            name="每日机会评估",
        )
        logger.info("✓ 已注册任务: 每日机会评估 (每天 9:00)")
        
        # 任务2: 每周一早上 8:00 爬取数据
        scheduler.add_job(
            weekly_data_crawl,
            trigger=CronTrigger(day_of_week='mon', hour=8, minute=0),  # 每周一 8:00
            id="weekly_data_crawl",
            max_instances=1,
            replace_existing=True,
            name="每周数据爬取",
        )
        logger.info("✓ 已注册任务: 每周数据爬取 (每周一 8:00)")
        
        # 任务3: 每天凌晨 2:00 清理过期记录
        scheduler.add_job(
            cleanup_old_job_executions,
            trigger=CronTrigger(hour=2, minute=0),  # 每天 2:00
            id="cleanup_old_job_executions",
            max_instances=1,
            replace_existing=True,
            name="清理过期任务记录",
        )
        logger.info("✓ 已注册任务: 清理过期记录 (每天 2:00)")
        
        # 启动调度器
        scheduler.start()
        logger.info("=" * 70)
        logger.info("🚀 定时任务调度器已启动")
        logger.info("=" * 70)
        logger.info("\n已注册的定时任务:")
        logger.info("1. 每日机会评估     - 每天 9:00")
        logger.info("2. 每周数据爬取     - 每周一 8:00")
        logger.info("3. 清理过期记录     - 每天 2:00")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"启动调度器失败: {e}", exc_info=True)
        raise


def stop_scheduler():
    """
    停止定时任务调度器
    """
    if not scheduler.running:
        logger.info("调度器未运行")
        return
    
    try:
        scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已停止")
    except Exception as e:
        logger.error(f"停止调度器失败: {e}", exc_info=True)


def get_scheduler_status():
    """
    获取调度器状态
    
    Returns:
        dict: 包含调度器状态和任务列表的字典
    """
    status = {
        'running': scheduler.running,
        'jobs': []
    }
    
    if scheduler.running:
        for job in scheduler.get_jobs():
            status['jobs'].append({
                'id': job.id,
                'name': job.name,
                'next_run_time': str(job.next_run_time) if job.next_run_time else None,
                'trigger': str(job.trigger),
            })
    
    return status


def run_job_now(job_id):
    """
    立即运行指定任务（用于测试）
    
    Args:
        job_id: 任务ID
    """
    try:
        job = scheduler.get_job(job_id)
        if job:
            logger.info(f"立即运行任务: {job.name}")
            job.func()
            logger.info(f"任务执行完成: {job.name}")
            return True
        else:
            logger.error(f"未找到任务: {job_id}")
            return False
    except Exception as e:
        logger.error(f"运行任务失败: {e}", exc_info=True)
        return False
