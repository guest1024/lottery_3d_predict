from django.contrib import admin
from .models import LotteryPeriod, Prediction, BacktestResult, DataUpdateLog


@admin.register(LotteryPeriod)
class LotteryPeriodAdmin(admin.ModelAdmin):
    list_display = ['period', 'date', 'digit1', 'digit2', 'digit3', 'shape', 'sum_value', 'created_at']
    list_filter = ['shape', 'date']
    search_fields = ['period']
    ordering = ['-period']


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['predicted_for_period', 'confidence_score', 'should_bet', 'bet_amount', 'created_at']
    list_filter = ['should_bet', 'created_at']
    search_fields = ['predicted_for_period']
    ordering = ['-created_at']


@admin.register(BacktestResult)
class BacktestResultAdmin(admin.ModelAdmin):
    list_display = ['strategy_name', 'total_periods', 'roi_percentage', 'win_rate', 'created_at']
    list_filter = ['strategy_name', 'created_at']
    ordering = ['-created_at']


@admin.register(DataUpdateLog)
class DataUpdateLogAdmin(admin.ModelAdmin):
    list_display = ['update_type', 'periods_added', 'periods_updated', 'status', 'created_at']
    list_filter = ['update_type', 'status', 'created_at']
    ordering = ['-created_at']
