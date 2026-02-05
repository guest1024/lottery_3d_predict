#!/usr/bin/env python3
"""
抓取真实3D彩票历史数据
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from data_loader.crawler_simple import SimpleLottery3DCrawler
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    print("="*60)
    print("抓取真实3D彩票历史数据")
    print("数据源: https://kaijiang.zhcw.com/zhcw/html/3d/")
    print("="*60)
    
    # 创建爬虫
    crawler = SimpleLottery3DCrawler(
        output_dir='./data',
        max_workers=5  # 并发5个线程
    )
    
    # 先测试抓取1页
    print("\n测试抓取第1页...")
    test_stats = crawler.crawl(start_page=1, end_page=1)
    
    if test_stats['total_records'] > 0:
        print(f"\n✓ 测试成功！抓取到 {test_stats['total_records']} 条记录")
        print(f"✓ JSON文件: {test_stats['json_file']}")
        print(f"✓ CSV文件: {test_stats['csv_file']}")
        
        # 询问是否继续抓取更多
        print("\n" + "="*60)
        response = input("测试成功！是否继续抓取100页？(y/n): ").strip().lower()
        
        if response == 'y':
            print("\n开始抓取100页数据...")
            stats = crawler.crawl(start_page=1, end_page=100, save_interval=10)
            
            print("\n" + "="*60)
            print("抓取完成！")
            print("="*60)
            print(f"总页数: {stats['total_pages']}")
            print(f"成功页数: {stats['success_pages']}")
            print(f"失败页数: {stats['failed_pages']}")
            print(f"总记录数: {stats['total_records']}")
            print(f"\n输出文件:")
            print(f"  JSON: {stats['json_file']}")
            print(f"  CSV:  {stats['csv_file']}")
            print("="*60)
            
            return stats['total_records'] > 1000
        else:
            print("\n取消抓取。可以使用测试数据进行后续操作。")
            return True
    else:
        print("\n✗ 测试失败！请检查网络连接或网站是否可访问。")
        return False


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
