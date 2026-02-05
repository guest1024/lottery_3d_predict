"""
3D彩票历史数据爬虫模块

从中国福利彩票官网抓取3D彩票历史开奖数据
"""
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

logger = logging.getLogger(__name__)


class Lottery3DCrawler:
    """3D彩票数据爬虫"""
    
    BASE_URL = "https://kaijiang.zhcw.com/zhcw/html/3d/list_{page}.html"
    
    def __init__(self, output_dir: str = "./data", max_workers: int = 10):
        """
        初始化爬虫
        
        Args:
            output_dir: 数据输出目录
            max_workers: 最大并发线程数
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
    def _fetch_page(self, page_num: int, retry: int = 3) -> Optional[List[Dict]]:
        """
        抓取单页数据
        
        Args:
            page_num: 页码
            retry: 重试次数
            
        Returns:
            该页所有期号的数据列表
        """
        url = self.BASE_URL.format(page=page_num)
        
        for attempt in range(retry):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'lxml')
                table = soup.find('table')
                
                if not table:
                    logger.warning(f"Page {page_num}: No table found")
                    return None
                
                # 提取表格数据
                records = []
                rows = table.find_all('tr')[2:]  # 跳过表头
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) < 5:
                        continue
                    
                    try:
                        period = cols[0].text.strip()
                        date = cols[1].text.strip()
                        
                        # 提取开奖号码（三个数字）
                        number_cells = cols[2].find_all('em')
                        if len(number_cells) != 3:
                            continue
                            
                        numbers = [int(cell.text.strip()) for cell in number_cells]
                        
                        # 提取销售额和中奖注数（如果有）
                        sales = cols[3].text.strip() if len(cols) > 3 else ""
                        prizes = cols[4].text.strip() if len(cols) > 4 else ""
                        
                        record = {
                            'period': period,
                            'date': date,
                            'numbers': numbers,
                            'digit_0': numbers[0],  # 百位
                            'digit_1': numbers[1],  # 十位
                            'digit_2': numbers[2],  # 个位
                            'sales': sales,
                            'prizes': prizes,
                        }
                        records.append(record)
                        
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Page {page_num}: Parse error - {e}")
                        continue
                
                logger.info(f"Page {page_num}: Fetched {len(records)} records")
                return records
                
            except requests.RequestException as e:
                logger.warning(f"Page {page_num}: Attempt {attempt + 1} failed - {e}")
                if attempt < retry - 1:
                    time.sleep(1)
                else:
                    logger.error(f"Page {page_num}: All attempts failed")
                    return None
                    
        return None
    
    def crawl(self, start_page: int = 1, end_page: int = 1000, 
              save_interval: int = 100) -> Dict:
        """
        批量抓取数据
        
        Args:
            start_page: 起始页码
            end_page: 结束页码
            save_interval: 每隔多少页保存一次
            
        Returns:
            抓取统计信息
        """
        all_records = []
        failed_pages = []
        
        # 使用Rich显示进度条
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ) as progress:
            
            task = progress.add_task(
                f"[cyan]Crawling pages {start_page}-{end_page}...", 
                total=end_page - start_page + 1
            )
            
            # 使用线程池并发抓取
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_page = {
                    executor.submit(self._fetch_page, page): page 
                    for page in range(start_page, end_page + 1)
                }
                
                for future in as_completed(future_to_page):
                    page = future_to_page[future]
                    try:
                        records = future.result()
                        if records:
                            all_records.extend(records)
                        else:
                            failed_pages.append(page)
                    except Exception as e:
                        logger.error(f"Page {page}: Unexpected error - {e}")
                        failed_pages.append(page)
                    
                    progress.advance(task)
                    
                    # 定期保存
                    if len(all_records) % (save_interval * 20) == 0 and len(all_records) > 0:
                        self._save_data(all_records, suffix='_partial')
        
        # 最终保存
        if all_records:
            output_file = self._save_data(all_records)
            logger.info(f"Data saved to: {output_file}")
        
        # 统计信息
        stats = {
            'total_pages': end_page - start_page + 1,
            'success_pages': (end_page - start_page + 1) - len(failed_pages),
            'failed_pages': len(failed_pages),
            'total_records': len(all_records),
            'output_file': str(output_file) if all_records else None,
        }
        
        if failed_pages:
            logger.warning(f"Failed pages: {failed_pages[:10]}{'...' if len(failed_pages) > 10 else ''}")
        
        return stats
    
    def _save_data(self, records: List[Dict], suffix: str = '') -> Path:
        """
        保存数据到JSON文件
        
        Args:
            records: 数据记录列表
            suffix: 文件名后缀
            
        Returns:
            保存的文件路径
        """
        # 按期号排序
        sorted_records = sorted(records, key=lambda x: x['period'])
        
        # 生成文件名
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"lottery_3d_data_{timestamp}{suffix}.json"
        output_file = self.output_dir / filename
        
        # 保存JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total': len(sorted_records),
                'data': sorted_records,
            }, f, ensure_ascii=False, indent=2)
        
        return output_file
    
    def load_latest_data(self) -> Optional[List[Dict]]:
        """
        加载最新的数据文件
        
        Returns:
            数据记录列表
        """
        json_files = list(self.output_dir.glob("lottery_3d_data_*.json"))
        if not json_files:
            logger.warning("No data files found")
            return None
        
        # 获取最新文件
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {data['total']} records from {latest_file.name}")
        return data['data']
