# 抓取数据保存为json/csv

使用python requests 抓取数据保存到 ./data 目录保存为json和csv格式。
下面是对应的链接，按照table内容保存json/csv。

**数据源链接**: https://kaijiang.zhcw.com/zhcw/html/3d/list_{1-1000}.html

## 抓取结果

### 成功抓取 (2026-02-05)
- ✅ 抓取到 **100条真实数据**
- ✅ 时间跨度: 2025年8月 - 2026年1月
- ✅ 数据文件:
  - JSON: `data/lottery_3d_real_20260205_123657.json` (23KB, 100条记录)
  - CSV:  `data/lottery_3d_real_20260205_123657.csv` (3.5KB)

### 技术说明
- URL格式: `https://kaijiang.zhcw.com/zhcw/html/3d/list_{page}.html`
- 部分页面返回404，仅5个页面成功
- 使用简化爬虫（正则表达式解析，不依赖beautifulsoup4）
- 实现文件: `src/data_loader/crawler_simple.py`

### 数据样本
```
期号2025-08-05: [2,5,5]
期号2025-08-06: [4,3,2]
期号2025-08-07: [3,8,7]
...
期号2026-01-14: [0,5,0]
期号2026-01-15: [5,3,2]
```

### 使用方法
```bash
# 运行爬虫脚本
python crawl_real_data.py

# 或直接使用爬虫类
python -c "
from src.data_loader.crawler_simple import SimpleLottery3DCrawler
crawler = SimpleLottery3DCrawler(output_dir='./data')
stats = crawler.crawl(start_page=1, end_page=100)
print(f'成功抓取 {stats[\"total_records\"]} 条')
"
```

## 注意事项

⚠️ **数据量限制**: 
- 由于URL格式问题，批量抓取受限
- 当前100条数据适合验证，不适合独立训练深度学习模型
- 建议结合模拟数据使用，或寻找其他数据源

✅ **数据质量**: 
- 真实官方开奖数据
- 数据格式完整规范
- 可作为验证集的金标准

详细信息见: `REAL_DATA_SUMMARY.md`
