"""
测试所有API接口
"""

import requests
import json
import sys

def test_api(method, url, description):
    """测试单个API"""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                status = data.get('status', 'unknown')
                print(f"✓ {description:<40} Status: {status}")
                return True, data
            except:
                print(f"✓ {description:<40} HTML页面")
                return True, None
        else:
            print(f"✗ {description:<40} HTTP {response.status_code}")
            return False, None
    except Exception as e:
        print(f"✗ {description:<40} 错误: {e}")
        return False, None

def main():
    """测试所有API"""
    base_url = "http://localhost:8000"
    
    print("="*70)
    print("API接口测试")
    print("="*70)
    
    tests = [
        # Web页面
        ('GET', '/', 'Web首页'),
        ('GET', '/dashboard/', 'Dashboard仪表板'),
        ('GET', '/history/', '历史开奖列表'),
        ('GET', '/predictions/', '预测记录列表'),
        ('GET', '/investment/', '投资策略分析'),
        
        # API接口
        ('POST', '/api/predict/', '生成预测API'),
        ('POST', '/api/crawl/', '爬取数据API'),
    ]
    
    passed = 0
    failed = 0
    
    for method, path, description in tests:
        url = base_url + path
        success, data = test_api(method, url, description)
        if success:
            passed += 1
        else:
            failed += 1
    
    print("="*70)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("="*70)
    
    if failed == 0:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 有测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())
