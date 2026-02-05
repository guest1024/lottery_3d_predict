"""
lottery app URL配置
"""
from django.urls import path
from . import views

app_name = 'lottery'

urlpatterns = [
    # 首页和仪表板
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # 历史开奖
    path('history/', views.history_list, name='history_list'),
    path('history/<str:period>/', views.period_detail, name='period_detail'),
    
    # 预测
    path('predictions/', views.predictions_list, name='predictions_list'),
    
    # 回测
    path('backtest/<int:pk>/', views.backtest_detail, name='backtest_detail'),
    
    # 特征提取
    path('features/<str:period>/', views.feature_extraction_view, name='feature_extraction'),
    
    # 投资策略分析
    path('investment/', views.investment_strategy_view, name='investment_strategy'),
    
    # 调度器管理
    path('scheduler/', views.scheduler_status_view, name='scheduler_status'),
    
    # 投注建议页面
    path('betting/', views.betting_recommendation_view, name='betting_recommendation'),
    
    # API接口
    path('api/crawl/', views.crawl_latest_data, name='api_crawl'),
    path('api/predict/', views.generate_prediction, name='api_predict'),
    path('api/run-task/', views.run_task_now, name='api_run_task'),
    
    # 投注建议 API
    path('api/betting/latest-recommendation/', views.get_latest_recommendation, name='api_latest_recommendation'),
    path('api/betting/recommendation-history/', views.get_recommendation_history, name='api_recommendation_history'),
]
