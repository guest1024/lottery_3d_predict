"""
简化版3D彩票历史数据爬虫
不依赖beautifulsoup4，直接使用正则表达式解析
"""
import json
import logging
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

logger = logging.getLogger(__name__)


class SimpleLottery3DCrawler:
    """简化版3D彩票数据爬虫"""
    
    BASE_URL = "http://kaijiang.zhcw.com/zhcw/inc/3d/3d_wqhg.jsp?pageNum={page}"
    
    def __init__(self, output_dir: str = "./data", max_workers: int = 5):
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
        
    def _parse_html_simple(self, html: str) -> List[Dict]:
        """
        使用正则表达式解析HTML
        
        Args:
            html: HTML文本
            
        Returns:
            数据记录列表
        """
        records = []
        
        # 匹配表格行 <tr>...</tr>
        tr_pattern = r'<tr[^>]*>(.*?)</tr>'
        trs = re.findall(tr_pattern, html, re.DOTALL)
        
        for tr in trs[2:]:  # 跳过前两行表头
            # 匹配td单元格
            td_pattern = r'<td[^>]*>(.*?)</td>'
            tds = re.findall(td_pattern, tr, re.DOTALL)
            
            if len(tds) < 3:
                continue
            
            try:
                # 期号
                period = re.sub(r'<[^>]+>', '', tds[0]).strip()
                
                # 日期
                date = re.sub(r'<[^>]+>', '', tds[1]).strip()
                
                # 开奖号码 - 在<em>标签中
                em_pattern = r'<em[^>]*>(\d)</em>'
                numbers_match = re.findall(em_pattern, tds[2])
                
                if len(numbers_match) != 3:
                    continue
                
                numbers = [int(n) for n in numbers_match]
                
                # 销售额和中奖注数（可选）
                sales = re.sub(r'<[^>]+>', '', tds[3]).strip() if len(tds) > 3 else ""
                prizes = re.sub(r'<[^>]+>', '', tds[4]).strip() if len(tds) > 4 else ""
                
                record = {
                    'period': period,
                    'date': date,
                    'numbers': numbers,
                    'digit_0': numbers[0],
                    'digit_1': numbers[1],
                    'digit_2': numbers[2],
                    'sales': sales,
                    'prizes': prizes,
                }
                records.append(record)
                
            except (ValueError, IndexError) as e:
                logger.warning(f"Parse error: {e}")
                continue
        
        return records
    
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
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                response.encoding = 'utf-8'
                
                # 使用正则解析
                records = self._parse_html_simple(response.text)
                
                if records:
                    logger.info(f"Page {page_num}: Fetched {len(records)} records")
                    return records
                else:
                    logger.warning(f"Page {page_num}: No records found")
                    return None
                
            except requests.RequestException as e:
                logger.warning(f"Page {page_num}: Attempt {attempt + 1} failed - {e}")
                if attempt < retry - 1:
                    time.sleep(2)
                else:
                    logger.error(f"Page {page_num}: All attempts failed")
                    return None
        
        return None
    
    def crawl(self, start_page: int = 1, end_page: int = 100, 
              save_interval: int = 20) -> Dict:
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
        
        print(f"\n开始抓取页面 {start_page}-{end_page}...")
        
        # 使用线程池并发抓取
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_page = {
                executor.submit(self._fetch_page, page): page 
                for page in range(start_page, end_page + 1)
            }
            
            completed = 0
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
                
                completed += 1
                if completed % 10 == 0:
                    print(f"  进度: {completed}/{end_page - start_page + 1} 页")
                
                # 定期保存
                if len(all_records) > 0 and len(all_records) % (save_interval * 20) == 0:
                    self._save_json(all_records, suffix='_partial')
        
        # 最终保存
        if all_records:
            json_file = self._save_json(all_records)
            csv_file = self._save_csv(all_records)
            logger.info(f"Data saved to: {json_file}, {csv_file}")
        
        # 统计信息
        stats = {
            'total_pages': end_page - start_page + 1,
            'success_pages': (end_page - start_page + 1) - len(failed_pages),
            'failed_pages': len(failed_pages),
            'total_records': len(all_records),
            'json_file': str(json_file) if all_records else None,
            'csv_file': str(csv_file) if all_records else None,
        }
        
        if failed_pages:
            logger.warning(f"Failed pages: {failed_pages[:10]}{'...' if len(failed_pages) > 10 else ''}")
        
        return stats
    
    def _save_json(self, records: List[Dict], suffix: str = '') -> Path:
        """保存为JSON格式"""
        sorted_records = sorted(records, key=lambda x: x['period'])
        
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"lottery_3d_real_{timestamp}{suffix}.json"
        output_file = self.output_dir / filename
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total': len(sorted_records),
                'source': 'https://kaijiang.zhcw.com/zhcw/html/3d/',
                'crawl_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'data': sorted_records,
            }, f, ensure_ascii=False, indent=2)
        
        return output_file
    
    def _save_csv(self, records: List[Dict]) -> Path:
        """保存为CSV格式"""
        import csv
        
        sorted_records = sorted(records, key=lambda x: x['period'])
        
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"lottery_3d_real_{timestamp}.csv"
        output_file = self.output_dir / filename
        
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            if sorted_records:
                fieldnames = ['period', 'date', 'digit_0', 'digit_1', 'digit_2', 
                            'number_str', 'sum', 'sales', 'prizes']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for record in sorted_records:
                    row = {
                        'period': record['period'],
                        'date': record['date'],
                        'digit_0': record['digit_0'],
                        'digit_1': record['digit_1'],
                        'digit_2': record['digit_2'],
                        'number_str': ''.join(map(str, record['numbers'])),
                        'sum': sum(record['numbers']),
                        'sales': record.get('sales', ''),
                        'prizes': record.get('prizes', ''),
                    }
                    writer.writerow(row)
        
        return output_file
