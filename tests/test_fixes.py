#!/usr/bin/env python
"""
测试Bug修复
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lottery_web.settings')
django.setup()

from lottery.models import LotteryPeriod
from lottery.views import feature_extraction_view
from django.test import RequestFactory


def test_feature_extraction():
    """测试特征提取视图"""
    print("测试1: 特征提取视图")
    print("-" * 50)
    
    # 获取最新期号
    latest = LotteryPeriod.objects.first()
    if not latest:
        print("❌ 错误: 数据库中没有数据")
        return False
    
    print(f"✓ 最新期号: {latest.period}")
    print(f"✓ 开奖号码: [{latest.digit1}, {latest.digit2}, {latest.digit3}]")
    
    # 模拟请求
    factory = RequestFactory()
    request = factory.get(f'/features/{latest.period}/')
    
    try:
        response = feature_extraction_view(request, latest.period)
        
        if response.status_code == 200:
            print("✓ 视图返回成功 (200)")
            
            # 检查context
            context = response.context_data
            if 'shape_freq' in context:
                print("✓ shape_freq存在于context中")
                
                shape_freq = context['shape_freq']
                print(f"✓ shape_freq类型: {type(shape_freq)}")
                
                for shape, data in shape_freq.items():
                    if isinstance(data, dict) and 'count' in data and 'percentage' in data:
                        print(f"✓ {shape}: {data['count']}次 ({data['percentage']}%)")
                    else:
                        print(f"❌ {shape}数据格式错误: {data}")
                        return False
                
                print("\n✅ 测试1通过: 特征提取视图正常工作\n")
                return True
            else:
                print("❌ 错误: shape_freq不在context中")
                return False
        else:
            print(f"❌ 错误: 视图返回状态码 {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crawl_button():
    """测试拉取按钮配置"""
    print("\n测试2: 拉取最新数据按钮配置")
    print("-" * 50)
    
    # 检查模板文件
    templates = {
        'base.html': 'lottery/templates/lottery/base.html',
        'history_list.html': 'lottery/templates/lottery/history_list.html'
    }
    
    all_ok = True
    
    for name, path in templates.items():
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查是否包含quickCrawl函数
            if 'quickCrawl' in content:
                print(f"✓ {name}: 包含quickCrawl函数")
            else:
                print(f"❌ {name}: 缺少quickCrawl函数")
                all_ok = False
            
            # 检查是否包含按钮
            if '拉取最新数据' in content:
                print(f"✓ {name}: 包含拉取按钮")
            else:
                print(f"❌ {name}: 缺少拉取按钮")
                all_ok = False
        else:
            print(f"❌ {name}: 文件不存在")
            all_ok = False
    
    if all_ok:
        print("\n✅ 测试2通过: 拉取按钮配置正确\n")
    else:
        print("\n❌ 测试2失败: 拉取按钮配置有问题\n")
    
    return all_ok


def test_database():
    """测试数据库"""
    print("\n测试3: 数据库状态")
    print("-" * 50)
    
    total = LotteryPeriod.objects.count()
    print(f"✓ 数据库总期数: {total}")
    
    if total > 0:
        latest = LotteryPeriod.objects.first()
        print(f"✓ 最新期号: {latest.period}")
        print(f"✓ 开奖日期: {latest.date}")
        print(f"✓ 开奖号码: [{latest.digit1}, {latest.digit2}, {latest.digit3}]")
        print(f"✓ 形态: {latest.shape}")
        print(f"✓ 和值: {latest.sum_value}")
        
        print("\n✅ 测试3通过: 数据库正常\n")
        return True
    else:
        print("❌ 错误: 数据库为空")
        return False


def main():
    print("="*50)
    print("Bug修复测试")
    print("="*50)
    print()
    
    results = []
    
    # 测试1: 特征提取
    results.append(("特征提取视图", test_feature_extraction()))
    
    # 测试2: 拉取按钮
    results.append(("拉取数据按钮", test_crawl_button()))
    
    # 测试3: 数据库
    results.append(("数据库状态", test_database()))
    
    # 总结
    print("="*50)
    print("测试总结")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print()
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统正常运行。")
        return 0
    else:
        print(f"\n⚠️  {total - passed}个测试失败，请检查。")
        return 1


if __name__ == '__main__':
    sys.exit(main())
