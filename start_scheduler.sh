#!/bin/bash
#
# 定时任务调度器启动脚本
#
# 使用方法:
#   ./start_scheduler.sh            # 前台运行
#   ./start_scheduler.sh --daemon   # 后台运行
#   ./start_scheduler.sh --test     # 测试模式
#   ./start_scheduler.sh --stop     # 停止后台进程
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/scheduler.log"
PID_FILE="$LOG_DIR/scheduler.pid"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 显示帮助信息
show_help() {
    echo "定时任务调度器启动脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  (无参数)     前台运行调度器"
    echo "  --daemon     后台运行调度器"
    echo "  --test       测试模式（立即运行一次评估任务）"
    echo "  --stop       停止后台运行的调度器"
    echo "  --status     查看调度器状态"
    echo "  --help       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                 # 前台运行"
    echo "  $0 --daemon        # 后台运行"
    echo "  $0 --test          # 测试运行"
    echo "  $0 --stop          # 停止服务"
    echo ""
}

# 检查调度器是否运行
check_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # 运行中
        else
            rm -f "$PID_FILE"
            return 1  # 未运行
        fi
    else
        return 1  # 未运行
    fi
}

# 停止调度器
stop_scheduler() {
    echo "正在停止调度器..."
    
    if check_running; then
        PID=$(cat "$PID_FILE")
        echo "发现运行中的调度器进程 (PID: $PID)"
        
        # 发送 SIGTERM 信号
        kill "$PID" 2>/dev/null
        
        # 等待进程退出（最多10秒）
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                echo "✓ 调度器已停止"
                rm -f "$PID_FILE"
                return 0
            fi
            sleep 1
        done
        
        # 如果还没停止，强制杀死
        echo "进程未响应，强制终止..."
        kill -9 "$PID" 2>/dev/null
        rm -f "$PID_FILE"
        echo "✓ 调度器已强制停止"
    else
        echo "调度器未运行"
    fi
}

# 查看状态
show_status() {
    echo "======================================================================="
    echo "调度器状态"
    echo "======================================================================="
    
    if check_running; then
        PID=$(cat "$PID_FILE")
        echo "状态: ✓ 运行中"
        echo "进程ID: $PID"
        echo "日志文件: $LOG_FILE"
        echo ""
        echo "最近的日志:"
        echo "-----------------------------------------------------------------------"
        tail -n 20 "$LOG_FILE" 2>/dev/null || echo "无日志文件"
    else
        echo "状态: ✗ 未运行"
    fi
    
    echo "======================================================================="
}

# 前台运行
run_foreground() {
    echo "======================================================================="
    echo "启动定时任务调度器 (前台模式)"
    echo "======================================================================="
    echo "按 Ctrl+C 停止"
    echo ""
    
    python manage.py start_scheduler
}

# 后台运行
run_daemon() {
    if check_running; then
        PID=$(cat "$PID_FILE")
        echo "✗ 调度器已在运行中 (PID: $PID)"
        echo "如需重启，请先执行: $0 --stop"
        exit 1
    fi
    
    echo "======================================================================="
    echo "启动定时任务调度器 (后台模式)"
    echo "======================================================================="
    
    # 后台运行并保存PID
    nohup python manage.py start_scheduler > "$LOG_FILE" 2>&1 &
    PID=$!
    echo "$PID" > "$PID_FILE"
    
    # 等待1秒检查是否成功启动
    sleep 1
    
    if check_running; then
        echo "✓ 调度器已启动"
        echo "  进程ID: $PID"
        echo "  日志文件: $LOG_FILE"
        echo ""
        echo "查看日志: tail -f $LOG_FILE"
        echo "停止服务: $0 --stop"
        echo "查看状态: $0 --status"
    else
        echo "✗ 调度器启动失败"
        echo "请查看日志: cat $LOG_FILE"
        exit 1
    fi
    
    echo "======================================================================="
}

# 测试模式
run_test() {
    echo "======================================================================="
    echo "测试模式: 立即运行一次评估任务"
    echo "======================================================================="
    echo ""
    
    python manage.py start_scheduler --test
    
    echo ""
    echo "======================================================================="
    echo "测试完成"
    echo "======================================================================="
}

# 主逻辑
case "${1:-}" in
    --daemon)
        run_daemon
        ;;
    --test)
        run_test
        ;;
    --stop)
        stop_scheduler
        ;;
    --status)
        show_status
        ;;
    --help|-h)
        show_help
        ;;
    "")
        run_foreground
        ;;
    *)
        echo "错误: 未知选项 '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac
