"""
抓取所有3D彩票历史数据 - 共378页
"""
import sys
sys.path.insert(0, '/c1/program/lottery_3d_predict')

from src.data_loader.crawler_simple import SimpleLottery3DCrawler

def main():
    print("=" * 60)
    print("抓取所有3D彩票历史数据")
    print("数据源: http://kaijiang.zhcw.com/zhcw/inc/3d/3d_wqhg.jsp")
    print("=" * 60)
    
    # 创建爬虫实例
    crawler = SimpleLottery3DCrawler(
        output_dir='./data',
        max_workers=15  # 增加并发数
    )
    
    # 抓取全部378页数据
    print("\n开始抓取全部 378 页数据...")
    stats = crawler.crawl(start_page=1, end_page=378, save_interval=50)
    
    # 打印统计信息
    print("\n" + "=" * 60)
    print("抓取完成！统计信息:")
    print("=" * 60)
    print(f"总页数: {stats['total_pages']}")
    print(f"成功页数: {stats['success_pages']}")
    print(f"失败页数: {stats['failed_pages']}")
    print(f"总记录数: {stats['total_records']}")
    print(f"预期记录数: 7542")
    print(f"覆盖率: {stats['total_records']/7542*100:.1f}%")
    print(f"JSON文件: {stats['json_file']}")
    print(f"CSV文件: {stats['csv_file']}")
    print("=" * 60)

if __name__ == '__main__':
    main()
