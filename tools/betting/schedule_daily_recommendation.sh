#!/bin/bash
#
# 定时执行每日投注建议
#
# 使用方法:
# 1. 手动执行: bash schedule_daily_recommendation.sh
# 2. 定时任务 (crontab):
#    # 每天20:00执行
#    0 20 * * * /path/to/lottery_3d_predict/tools/betting/schedule_daily_recommendation.sh
#

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs/betting"
mkdir -p "$LOG_DIR"

# 日志文件
LOG_FILE="$LOG_DIR/daily_recommendation_$(date +%Y%m%d_%H%M%S).log"

echo "=====================================================================" | tee -a "$LOG_FILE"
echo "每日投注建议 - $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "=====================================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# 执行投注建议生成
python tools/betting/daily_recommendation.py \
    --strategy top5 \
    2>&1 | tee -a "$LOG_FILE"

# 检查执行结果
if [ $? -eq 0 ]; then
    echo "" | tee -a "$LOG_FILE"
    echo "✅ 执行成功！" | tee -a "$LOG_FILE"
else
    echo "" | tee -a "$LOG_FILE"
    echo "❌ 执行失败！" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"
echo "日志文件: $LOG_FILE" | tee -a "$LOG_FILE"
echo "=====================================================================" | tee -a "$LOG_FILE"

# 清理30天前的日志
find "$LOG_DIR" -name "daily_recommendation_*.log" -mtime +30 -delete

exit 0
