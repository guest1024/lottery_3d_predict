#!/usr/bin/env python3
"""
详细测试预测API - 验证是否返回完整的组选投注方案
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置 Django 环境
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottery_web.settings')
django.setup()

from lottery.views import generate_prediction
from django.test import RequestFactory
from django.http import JsonResponse


def test_predict_api():
    """测试预测API返回完整投注方案"""
    print("=" * 70)
    print("测试预测 API - 验证组选投注方案")
    print("=" * 70)
    
    # 创建模拟请求
    factory = RequestFactory()
    request_data = json.dumps({'num_bets': 100})
    request = factory.post('/api/predict/', 
                          data=request_data,
                          content_type='application/json')
    
    # 调用API
    print("\n[1] 调用 API...")
    response = generate_prediction(request)
    
    # 解析响应
    if isinstance(response, JsonResponse):
        response_data = json.loads(response.content)
    else:
        print("✗ 响应格式错误")
        return False
    
    print(f"✓ API 返回状态: {response_data.get('status')}")
    
    if response_data.get('status') != 'success':
        print(f"✗ API 调用失败: {response_data.get('message')}")
        if 'traceback' in response_data:
            print(response_data['traceback'])
        return False
    
    # 验证响应结构
    print("\n[2] 验证响应结构...")
    prediction = response_data.get('prediction', {})
    
    required_fields = ['period', 'score', 'threshold', 'should_bet', 
                      'top10_digits', 'betting_plan']
    
    for field in required_fields:
        if field not in prediction:
            print(f"✗ 缺少字段: {field}")
            return False
        print(f"✓ 包含字段: {field}")
    
    # 验证投注计划
    print("\n[3] 验证投注计划...")
    betting_plan = prediction.get('betting_plan', {})
    
    if not betting_plan:
        print("✗ 投注计划为空!")
        return False
    
    # 检查投注计划字段
    required_plan_fields = ['num_bets', 'total_cost', 'combinations', 
                           'group6_count', 'group3_count', 'expected_roi']
    
    for field in required_plan_fields:
        if field not in betting_plan:
            print(f"✗ 投注计划缺少字段: {field}")
            return False
        print(f"✓ 包含字段: {field} = {betting_plan[field] if field != 'combinations' else f'{len(betting_plan[field])}个组合'}")
    
    # 验证组合内容
    print("\n[4] 验证组选组合...")
    combinations = betting_plan.get('combinations', [])
    
    if not combinations:
        print("✗ 组合列表为空!")
        return False
    
    print(f"✓ 总组合数: {len(combinations)}")
    print(f"✓ 组六数量: {betting_plan['group6_count']}")
    print(f"✓ 组三数量: {betting_plan['group3_count']}")
    print(f"✓ 总成本: {betting_plan['total_cost']} 元")
    print(f"✓ 预期ROI: {betting_plan['expected_roi']}%")
    
    # 显示前10个组合
    print("\n[5] 组合示例 (前10个):")
    print("-" * 70)
    for i, combo in enumerate(combinations[:10], 1):
        # 判断是组六还是组三
        if len(set(combo)) == 3:
            combo_type = "组六"
        else:
            combo_type = "组三"
        print(f"  {i:2d}. {combo} - {combo_type}")
    
    # 验证组合有效性
    print("\n[6] 验证组合有效性...")
    group6_count = 0
    group3_count = 0
    invalid_count = 0
    
    for combo in combinations:
        if len(combo) != 3:
            invalid_count += 1
            continue
        
        unique_digits = len(set(combo))
        if unique_digits == 3:
            group6_count += 1
        elif unique_digits == 2:
            group3_count += 1
        else:
            invalid_count += 1
    
    print(f"✓ 有效组六: {group6_count}")
    print(f"✓ 有效组三: {group3_count}")
    
    if invalid_count > 0:
        print(f"✗ 无效组合: {invalid_count}")
        return False
    else:
        print(f"✓ 无效组合: 0")
    
    # 验证数字范围
    print("\n[7] 验证数字范围...")
    all_digits = [d for combo in combinations for d in combo]
    invalid_digits = [d for d in all_digits if d < 0 or d > 9]
    
    if invalid_digits:
        print(f"✗ 发现超出范围的数字: {set(invalid_digits)}")
        return False
    else:
        print(f"✓ 所有数字在 0-9 范围内")
    
    # 完整信息总结
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    print(f"期号: {prediction['period']}")
    print(f"评分: {prediction['score']} 分")
    print(f"阈值: {prediction['threshold']} 分")
    print(f"投注建议: {prediction.get('recommendation', 'N/A')}")
    print(f"是否应投注: {'是' if prediction['should_bet'] else '否'}")
    print(f"\n投注计划:")
    print(f"  总注数: {betting_plan['num_bets']} 注")
    print(f"  组六: {betting_plan['group6_count']} 注")
    print(f"  组三: {betting_plan['group3_count']} 注")
    print(f"  总成本: {betting_plan['total_cost']} 元")
    print(f"  预期ROI: {betting_plan['expected_roi']}%")
    print(f"\nTop10 推荐数字: {prediction['top10_digits']}")
    print("=" * 70)
    print("✓ 所有测试通过! API 返回了完整的组选投注方案")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    try:
        success = test_predict_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
