#!/bin/bash
# Lotto3D-Core 快速开始脚本

echo "========================================"
echo "Lotto3D-Core 快速开始"
echo "========================================"

# 检查Python版本
echo ""
echo "1. 检查环境..."
python --version

# 安装依赖
echo ""
echo "2. 安装依赖..."
pip install -q -r requirements.txt

# 运行测试
echo ""
echo "3. 运行系统测试..."
python test_simple.py

# 显示帮助
echo ""
echo "4. 可用命令:"
echo "  python src/cli.py --help          # 查看所有命令"
echo "  python src/cli.py info            # 查看系统信息"
echo "  python src/cli.py crawl --pages 10    # 抓取数据（测试）"
echo "  python src/cli.py extract --numbers 1,2,3  # 提取特征"
echo ""
echo "详细文档请参阅:"
echo "  - README.md"
echo "  - docs/user_guide/quick_start.md"
echo "  - PROJECT_SUMMARY.md"
echo ""
echo "========================================"
echo "✓ 系统就绪！"
echo "========================================"
