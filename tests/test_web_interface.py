"""
测试Web界面是否正常工作
"""

import requests
import sys

def test_url(url, expected_title):
    """测试URL是否正常"""
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            if expected_title in response.text:
                print(f"✓ {url} - OK")
                return True
            else:
                print(f"✗ {url} - 页面加载成功但标题不匹配")
                return False
        else:
            print(f"✗ {url} - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ {url} - 错误: {e}")
        return False

def main():
    """测试所有关键页面"""
    base_url = "http://localhost:8000"
    
    tests = [
        ("/", "3D彩票预测系统"),
        ("/dashboard/", "仪表板"),
        ("/history/", "历史开奖记录"),
        ("/predictions/", "预测记录"),
        ("/investment/", "投资策略分析"),
    ]
    
    print("="*60)
    print("Web界面测试")
    print("="*60)
    
    all_passed = True
    for path, title in tests:
        url = base_url + path
        if not test_url(url, title):
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("✓ 所有测试通过")
        return 0
    else:
        print("✗ 有测试失败")
        return 1

if __name__ == '__main__':
    sys.exit(main())
