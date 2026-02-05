#!/bin/bash
#
# 快速测试新的预测 API
#

echo "======================================================================"
echo "测试新的预测 API - 投注计划功能"
echo "======================================================================"
echo ""

# 检查服务器是否运行
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "⚠️  Django 服务器未运行"
    echo "请先启动服务器: python manage.py runserver"
    echo ""
    exit 1
fi

echo "✓ Django 服务器运行中"
echo ""

# 测试1: 默认100注
echo "======================================================================"
echo "测试1: 默认投注计划（100注）"
echo "======================================================================"
echo ""

response=$(curl -s -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json")

if echo "$response" | grep -q "success"; then
    echo "✓ API 调用成功"
    echo ""
    
    # 提取关键信息
    period=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['prediction']['period'])")
    score=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['prediction']['score'])")
    should_bet=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['prediction']['should_bet'])")
    num_bets=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['prediction']['betting_plan']['num_bets'])")
    total_cost=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['prediction']['betting_plan']['total_cost'])")
    group6=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['prediction']['betting_plan']['group6_count'])")
    group3=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['prediction']['betting_plan']['group3_count'])")
    roi=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['prediction']['betting_plan']['expected_roi'])")
    
    echo "预测结果:"
    echo "  期号: $period"
    echo "  评分: $score 分"
    echo "  建议投注: $should_bet"
    echo ""
    echo "投注计划:"
    echo "  总注数: $num_bets 注"
    echo "  总成本: $total_cost 元"
    echo "  组六: $group6 注"
    echo "  组三: $group3 注"
    echo "  预期ROI: $roi %"
    echo ""
    
    # 显示前5个组合
    echo "示例组合（前5个）:"
    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
combos = data['prediction']['betting_plan']['combinations'][:5]
for i, combo in enumerate(combos, 1):
    print(f'  {i}. {combo}')
"
else
    echo "✗ API 调用失败"
    echo "$response" | python3 -m json.tool 2>&1 | head -20
fi

echo ""
echo "======================================================================"
echo "测试2: 自定义投注计划（50注）"
echo "======================================================================"
echo ""

response=$(curl -s -X POST http://localhost:8000/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{"num_bets": 50}')

if echo "$response" | grep -q "success"; then
    echo "✓ API 调用成功"
    echo ""
    
    num_bets=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['prediction']['betting_plan']['num_bets'])")
    total_cost=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['prediction']['betting_plan']['total_cost'])")
    
    echo "投注计划:"
    echo "  总注数: $num_bets 注"
    echo "  总成本: $total_cost 元"
else
    echo "✗ API 调用失败"
fi

echo ""
echo "======================================================================"
echo "测试完成"
echo "======================================================================"
echo ""
echo "💡 提示:"
echo "  - 查看完整文档: docs/developer/API_BETTING_PLAN_UPGRADE.md"
echo "  - 查看总结: PREDICT_API_UPGRADE_SUMMARY.md"
echo "  - API 端点: POST /api/predict/"
echo ""
