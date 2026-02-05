"""
Django management command: 启动定时任务调度器

使用方法:
    python manage.py start_scheduler
    
功能:
    - 启动 APScheduler 定时任务调度器
    - 注册所有定时任务
    - 持续运行直到接收到停止信号
"""

import logging
import time
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '启动定时任务调度器'

    def add_arguments(self, parser):
        """添加命令行参数"""
        parser.add_argument(
            '--test',
            action='store_true',
            help='测试模式：立即运行一次每日评估任务',
        )

    def handle(self, *args, **options):
        """执行命令"""
        from lottery.scheduler import start_scheduler, run_job_now, get_scheduler_status
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('启动定时任务调度器'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        try:
            # 启动调度器
            start_scheduler()
            
            # 显示调度器状态
            status = get_scheduler_status()
            self.stdout.write(self.style.SUCCESS(f'\n✓ 调度器状态: {"运行中" if status["running"] else "已停止"}'))
            
            if status['jobs']:
                self.stdout.write(self.style.SUCCESS(f'\n已注册的任务 ({len(status["jobs"])} 个):'))
                for i, job in enumerate(status['jobs'], 1):
                    self.stdout.write(f"\n{i}. {job['name']}")
                    self.stdout.write(f"   ID: {job['id']}")
                    self.stdout.write(f"   触发器: {job['trigger']}")
                    self.stdout.write(f"   下次运行: {job['next_run_time']}")
            
            # 测试模式：立即运行一次任务
            if options['test']:
                self.stdout.write(self.style.WARNING('\n' + '=' * 70))
                self.stdout.write(self.style.WARNING('🧪 测试模式：立即运行每日评估任务'))
                self.stdout.write(self.style.WARNING('=' * 70))
                
                success = run_job_now('daily_opportunity_check')
                
                if success:
                    self.stdout.write(self.style.SUCCESS('\n✓ 测试任务执行成功'))
                else:
                    self.stdout.write(self.style.ERROR('\n✗ 测试任务执行失败'))
                
                self.stdout.write(self.style.WARNING('=' * 70))
                return
            
            # 正常模式：持续运行
            self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
            self.stdout.write(self.style.SUCCESS('✓ 调度器启动成功，按 Ctrl+C 停止'))
            self.stdout.write(self.style.SUCCESS('=' * 70 + '\n'))
            
            # 保持运行
            try:
                while True:
                    time.sleep(60)  # 每分钟检查一次
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\n\n接收到停止信号...'))
                from lottery.scheduler import stop_scheduler
                stop_scheduler()
                self.stdout.write(self.style.SUCCESS('调度器已停止'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ 启动调度器失败: {e}'))
            logger.error(f"启动调度器失败: {e}", exc_info=True)
            raise
