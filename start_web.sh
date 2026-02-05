#!/bin/bash
# 3D彩票预测系统Web服务启动脚本

echo "================================"
echo "3D彩票预测系统 Web服务"
echo "================================"
echo ""

# 检查数据库
if [ ! -f "db.sqlite3" ]; then
    echo "首次启动，初始化数据库..."
    /usr/local/miniconda3/bin/python manage.py migrate
    /usr/local/miniconda3/bin/python import_data.py
fi

echo "启动Web服务..."
echo ""
echo "访问地址: http://localhost:8000/"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

/usr/local/miniconda3/bin/python manage.py runserver 0.0.0.0:8000
