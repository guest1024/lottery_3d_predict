"""
自动抓取3D彩票历史数据 - 无需交互
"""
import sys
sys.path.insert(0, '/c1/program/lottery_3d_predict')

from src.data_loader.crawler_simple import SimpleLottery3DCrawler

def main():
    print("=" * 60)
    print("自动抓取真实3D彩票历史数据")
    print("数据源: https://kaijiang.zhcw.com/zhcw/html/3d/")
    print("=" * 60)
    
    # 创建爬虫实例
    crawler = SimpleLottery3DCrawler(
        output_dir='./data',
        max_workers=10  # 增加并发数
    )
    
    # 直接抓取200页数据
    print("\n开始抓取 1-200 页数据...")
    stats = crawler.crawl(start_page=1, end_page=200, save_interval=20)
    
    # 打印统计信息
    print("\n" + "=" * 60)
    print("抓取完成！统计信息:")
    print("=" * 60)
    print(f"总页数: {stats['total_pages']}")
    print(f"成功页数: {stats['success_pages']}")
    print(f"失败页数: {stats['failed_pages']}")
    print(f"总记录数: {stats['total_records']}")
    print(f"JSON文件: {stats['json_file']}")
    print(f"CSV文件: {stats['csv_file']}")
    print("=" * 60)

if __name__ == '__main__':
    main()
