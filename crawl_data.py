#!/usr/bin/env python3
"""
抓取真实数据脚本
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_loader.crawler import Lottery3DCrawler

def main():
    print("="*60)
    print("开始抓取3D彩票历史数据")
    print("="*60)
    
    # 创建爬虫（先抓取较少页面测试）
    crawler = Lottery3DCrawler(output_dir='./data', max_workers=5)
    
    # 抓取100页数据（约2000条记录）
    stats = crawler.crawl(start_page=1, end_page=100, save_interval=20)
    
    print("\n" + "="*60)
    print("抓取完成！")
    print("="*60)
    print(f"总页数: {stats['total_pages']}")
    print(f"成功页数: {stats['success_pages']}")
    print(f"失败页数: {stats['failed_pages']}")
    print(f"总记录数: {stats['total_records']}")
    print(f"输出文件: {stats['output_file']}")
    print("="*60)
    
    return stats['total_records'] > 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
