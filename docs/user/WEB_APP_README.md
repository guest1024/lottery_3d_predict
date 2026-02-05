# 3D彩票预测系统 - Web应用使用指南

## 🎯 系统概述

基于Django开发的3D彩票预测系统Web应用，提供完整的数据管理、模型预测、回测分析和投注建议功能。

### 核心功能

✅ **Tab式仪表板** - 多标签切换，简洁明了  
✅ **历史开奖查询** - 7,362期完整数据  
✅ **特征提取查看** - 可视化训练输入  
✅ **智能预测生成** - 一键生成预测  
✅ **动态投注建议** - 基于可信度的投注策略  
✅ **回测结果展示** - ROI分析和资金曲线  
✅ **数据自动更新** - 爬虫集成，无重复导入  

---

## 🚀 快速启动

### 方法1: 使用启动脚本（推荐）

```bash
cd /c1/program/lottery_3d_predict
./start_web.sh
```

### 方法2: 手动启动

```bash
cd /c1/program/lottery_3d_predict

# 如果是首次启动，先初始化数据库
python manage.py migrate
python import_data.py

# 启动服务
python manage.py runserver 0.0.0.0:8000
```

### 访问地址

浏览器打开: **http://localhost:8000/**

---

## 📊 功能详解

### 1. 仪表板（Tab式设计）

#### Tab 1: 概览
- **统计卡片**: 总期数、最新期号、预测记录、数据更新时间
- **最新开奖**: 显示最新一期的开奖号码和详情
- **最佳策略**: 推荐ROI最高的投注策略

#### Tab 2: 最新预测
- **生成预测**: 点击按钮基于最近30期生成下一期预测
- **预测结果**: 
  - 预测期号
  - Top5高概率数字
  - 可信度评分
  - 投注建议（是否建议投注 + 建议金额）
- **实时反馈**: 预测完成后自动刷新展示

#### Tab 3: 回测结果
- **策略对比表**: 
  - 策略名称（如Top 10% Dynamic）
  - 测试期数、投注期数
  - 起始/最终资金
  - ROI、胜率、最大回撤
- **点击查看详情**: 跳转到回测详情页

#### Tab 4: 投注策略
- **策略说明文档**:
  - Top 10%策略详解
  - 投注流程说明
  - 风险提示
- **帮助用户理解**: 为什么选择该策略

#### Tab 5: 数据管理
- **爬取最新数据**: 
  - 点击按钮自动爬取最新开奖数据
  - 自动去重，只添加新期号
  - 实时显示进度和结果
- **数据统计**: 
  - 数据库总期数
  - 最新期号和日期
- **更新日志**: 
  - 显示历史更新记录
  - 新增/更新期数
  - 状态和消息

---

### 2. 历史开奖

#### 功能
- **搜索**: 按期号或号码搜索
- **列表展示**: 
  - 期号、日期、开奖号码（彩球样式）
  - 形态标签（豹子/组三/组六）
  - 和值
- **分页**: 每页50条，支持首页/上一页/下一页/末页
- **操作按钮**:
  - **详情**: 查看该期完整信息
  - **特征**: 查看该期用于训练的特征提取

---

### 3. 期号详情

#### 展示内容
- **开奖信息**: 
  - 期号、日期
  - 开奖号码（大号彩球）
  - 形态、和值、奇偶比
- **前30期历史**: 
  - 该期预测时使用的输入序列
  - 表格展示，可滚动查看
- **预测记录**: 
  - 如果该期有预测，显示预测详情
  - Top5数字、可信度、投注建议

---

### 4. 特征提取（Tab式）

点击历史列表的"特征"按钮进入，分4个Tab：

#### Tab 1: 输入序列
- 前30期的完整历史数据
- 表格形式展示：序号、期号、号码、形态、和值
- 这就是模型的输入 [30, 3]

#### Tab 2: 数字频率
- 0-9每个数字在30期中的出现次数
- 网格展示，数字+彩球样式
- 说明频率特征的作用

#### Tab 3: 和值分布
- 最小值、平均值、最大值
- 统计卡片展示
- 说明和值特征的意义

#### Tab 4: 形态统计
- 豹子/组三/组六的次数和占比
- 网格展示 with emoji图标
- 说明形态定义和理论概率

---

### 5. 预测记录

#### 功能
- **筛选**: 
  - 全部
  - ✓ 建议投注
  - ✗ 不建议投注
- **列表展示**: 
  - 预测期号
  - Top5数字（彩球样式）
  - 可信度（颜色标签）
  - 投注建议
  - 建议金额
  - 预测时间
- **分页**: 每页30条

---

### 6. 回测详情

#### 展示内容
- **统计卡片**: 
  - 起始资金、最终资金、总收益、ROI
  - 颜色区分盈亏
- **回测配置**: 
  - 测试期数、投注期数、跳过期数
  - 开始/结束期号
  - 胜率、最大回撤、盈利期数
- **投入产出**: 
  - 总投入、总奖金、净收益
  - 大号显示，一目了然
- **资金曲线图**: 
  - 基于Chart.js绘制
  - X轴：期数，Y轴：资金
  - 显示资金变化趋势

---

## 🔧 技术架构

### 后端
- **框架**: Django 5.1
- **数据库**: SQLite（db.sqlite3）
- **模型**: LSTM+Attention (PyTorch)
- **数据**: 7,362期历史数据

### 前端
- **模板引擎**: Django Template
- **样式**: 纯CSS（无Bootstrap，简洁快速）
- **交互**: 原生JavaScript
- **图表**: Chart.js 3.9

### 数据模型

#### LotteryPeriod（彩票期次）
- period: 期号
- date: 日期
- digit1/2/3: 三位数字
- sum_value: 和值
- shape: 形态

#### Prediction（预测记录）
- predicted_for_period: 预测的期号
- top5_digits: Top5数字
- confidence_score: 可信度
- should_bet: 是否建议投注
- bet_amount: 建议金额

#### BacktestResult（回测结果）
- strategy_name: 策略名称
- total_periods: 总期数
- starting_capital/final_capital: 资金
- roi_percentage: ROI
- period_results: 详细结果JSON
- capital_history: 资金历史JSON

#### DataUpdateLog（更新日志）
- update_type: 更新类型
- periods_added/updated: 新增/更新期数
- status: 状态
- message: 消息

---

## 📝 使用流程

### 典型工作流程

1. **启动服务**
   ```bash
   ./start_web.sh
   ```

2. **访问仪表板**
   - 打开 http://localhost:8000/
   - 自动跳转到Dashboard

3. **更新数据**（Tab 5）
   - 点击"爬取最新数据"
   - 等待爬取完成
   - 查看更新日志

4. **生成预测**（Tab 2）
   - 点击"生成预测"
   - 查看预测结果
   - 查看Top5数字和可信度
   - 判断是否投注

5. **查看历史**
   - 导航栏 → 历史开奖
   - 搜索/浏览期号
   - 点击"特征"查看训练输入

6. **分析回测**（Tab 3）
   - 查看不同策略的ROI对比
   - 点击"详情"查看资金曲线
   - 选择最优策略

---

## 🎨 界面设计特点

### 1. Tab导航优化
- ✅ 减少页面滚动，所有功能分Tab展示
- ✅ 每个Tab内容完整，不需要来回切换
- ✅ Tab按钮固定顶部，随时切换

### 2. 简洁明了
- ✅ 扁平化设计，无多余装饰
- ✅ 卡片式布局，结构清晰
- ✅ 彩球样式显示号码，直观醒目

### 3. 颜色语义
- 🟢 绿色：成功、盈利、建议
- 🔴 红色：失败、亏损、危险
- 🟡 黄色：警告、中等、中性
- 🔵 蓝色：信息、中性、默认

### 4. 响应式交互
- ✅ 按钮hover效果
- ✅ 表格行hover高亮
- ✅ AJAX异步请求（无刷新）
- ✅ 加载状态反馈

---

## 🔌 API接口

### 1. 爬取数据
```
POST /api/crawl/
Response: {
  "status": "success",
  "message": "成功导入数据！新增X期，更新Y期",
  "added": X,
  "updated": Y,
  "total": Z
}
```

### 2. 生成预测
```
POST /api/predict/
Response: {
  "status": "success",
  "message": "成功生成{period}期预测",
  "prediction": {
    "period": "2026XXXX",
    "top5": [6,2,8,5,3],
    "confidence": 0.1891,
    "should_bet": true
  }
}
```

---

## 📂 文件结构

```
lottery_3d_predict/
├── lottery_web/           # Django项目配置
│   ├── settings.py       # 配置文件
│   └── urls.py           # 主URL路由
│
├── lottery/              # 应用目录
│   ├── models.py         # 数据模型 ⭐
│   ├── views.py          # 视图函数 ⭐
│   ├── urls.py           # URL路由
│   ├── admin.py          # 后台管理
│   └── templates/        # 模板目录 ⭐
│       └── lottery/
│           ├── base.html              # 基础模板
│           ├── dashboard.html         # 仪表板（Tab式）⭐
│           ├── history_list.html      # 历史列表
│           ├── period_detail.html     # 期号详情
│           ├── feature_extraction.html # 特征提取（Tab式）⭐
│           ├── predictions_list.html  # 预测列表
│           └── backtest_detail.html   # 回测详情
│
├── static/               # 静态文件
├── media/                # 媒体文件
├── db.sqlite3            # SQLite数据库 ⭐
│
├── manage.py             # Django管理脚本
├── import_data.py        # 数据导入脚本 ⭐
├── start_web.sh          # 启动脚本 ⭐
└── WEB_APP_README.md     # 本文档 ⭐
```

---

## 💡 使用技巧

### 1. 数据更新
- 建议每周更新一次数据
- 点击"爬取最新数据"后等待3-5秒
- 成功后会自动刷新页面

### 2. 预测使用
- 可信度 ≥ 0.189 建议考虑投注
- 可信度 < 0.188 建议跳过
- 查看Top5数字了解模型倾向

### 3. 特征查看
- 点击任意期号的"特征"按钮
- 了解模型看到的输入是什么
- 帮助理解预测逻辑

### 4. 回测分析
- 对比不同策略的ROI
- 关注最大回撤（风险指标）
- 查看资金曲线了解稳定性

---

## ⚠️ 注意事项

### 1. 服务端口
- 默认端口：8000
- 如需修改：`python manage.py runserver 0.0.0.0:PORT`

### 2. 数据库备份
```bash
# 备份数据库
cp db.sqlite3 db.sqlite3.backup

# 恢复数据库
cp db.sqlite3.backup db.sqlite3
```

### 3. 清空数据重新导入
```bash
# 删除数据库
rm db.sqlite3

# 重新初始化
python manage.py migrate
python import_data.py
```

### 4. 模型文件位置
- 模型路径：`models/checkpoints/best_model.pth`
- 数据路径：`data/lottery_3d_real_20260205_125506.json`
- 确保文件存在，否则预测功能无法使用

---

## 🛠️ 故障排查

### 问题1: 启动失败
```bash
# 检查Python环境
which python
# 应该是 /usr/local/miniconda3/bin/python

# 检查依赖
pip list | grep -i django
```

### 问题2: 页面无法访问
```bash
# 检查服务是否运行
ps aux | grep runserver

# 检查端口占用
netstat -tuln | grep 8000
```

### 问题3: 爬虫失败
- 检查网络连接
- 查看错误日志（数据管理Tab → 更新日志）
- 爬虫模块：`crawl_real_data.py`

### 问题4: 预测失败
- 检查模型文件是否存在
- 检查历史数据是否足30期
- 查看浏览器控制台错误

---

## 📈 性能优化

### 1. 数据库索引
- period、date字段已建立索引
- 查询速度优化

### 2. 分页加载
- 历史列表：50条/页
- 预测记录：30条/页
- 减少单次加载时间

### 3. 静态资源
- Chart.js使用CDN
- 减少服务器负担

---

## 🔐 安全建议

### 生产环境部署
1. **修改SECRET_KEY**
   ```python
   # lottery_web/settings.py
   SECRET_KEY = '生成一个新的密钥'
   ```

2. **关闭DEBUG**
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['yourdomain.com']
   ```

3. **使用HTTPS**
4. **配置防火墙**
5. **定期备份数据库**

---

## 📞 技术支持

### 问题反馈
- 查看日志：Terminal输出
- 浏览器控制台：F12 → Console
- Django Debug页面（DEBUG=True时）

### 扩展开发
- 添加新模型：修改`lottery/models.py`
- 添加新视图：修改`lottery/views.py`
- 添加新页面：创建模板文件
- 修改样式：编辑`base.html`中的CSS

---

## 🎉 总结

这是一个**功能完整、界面简洁、操作便捷**的3D彩票预测系统Web应用：

✅ **Tab式设计** - 减少滚动，提高效率  
✅ **一键操作** - 爬取数据、生成预测  
✅ **可视化展示** - 图表、彩球、卡片  
✅ **完整功能** - 历史、预测、回测、特征  
✅ **无重复导入** - 智能去重  
✅ **SQLite集成** - 统一数据管理  

**立即启动，体验完整的彩票预测工作流！** 🚀
