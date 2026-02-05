"""
3D彩票数据库模型
"""
from django.db import models
from django.utils import timezone


class LotteryPeriod(models.Model):
    """彩票期次数据"""
    period = models.CharField(max_length=20, unique=True, db_index=True, verbose_name='期号')
    date = models.DateField(db_index=True, verbose_name='开奖日期')
    digit1 = models.IntegerField(verbose_name='第一位')
    digit2 = models.IntegerField(verbose_name='第二位')
    digit3 = models.IntegerField(verbose_name='第三位')
    sum_value = models.IntegerField(verbose_name='和值')
    shape = models.CharField(max_length=10, verbose_name='形态')  # 组六/组三/豹子
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        ordering = ['-period']
        verbose_name = '彩票期次'
        verbose_name_plural = '彩票期次'
    
    def __str__(self):
        return f"{self.period}: [{self.digit1},{self.digit2},{self.digit3}]"
    
    @property
    def numbers(self):
        """返回号码列表"""
        return [self.digit1, self.digit2, self.digit3]
    
    @property
    def numbers_str(self):
        """返回号码字符串"""
        return f"{self.digit1}{self.digit2}{self.digit3}"


class Prediction(models.Model):
    """预测记录"""
    period = models.ForeignKey(LotteryPeriod, on_delete=models.CASCADE, related_name='predictions', verbose_name='关联期号')
    predicted_for_period = models.CharField(max_length=20, db_index=True, verbose_name='预测的期号')
    
    # 预测结果
    top5_digits = models.JSONField(verbose_name='Top5数字')
    digit_probs = models.JSONField(verbose_name='数字概率')
    confidence_score = models.FloatField(verbose_name='可信度分数')
    attention_weights = models.JSONField(null=True, blank=True, verbose_name='注意力权重')
    
    # 投注建议
    should_bet = models.BooleanField(default=False, verbose_name='建议投注')
    recommended_bets = models.JSONField(null=True, blank=True, verbose_name='推荐投注组合')
    bet_amount = models.IntegerField(default=0, verbose_name='建议投注金额')
    
    # 元数据
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='预测时间')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '预测记录'
        verbose_name_plural = '预测记录'
    
    def __str__(self):
        return f"预测{self.predicted_for_period} (可信度:{self.confidence_score:.3f})"


class BacktestResult(models.Model):
    """回测结果"""
    strategy_name = models.CharField(max_length=50, verbose_name='策略名称')
    
    # 回测配置
    start_period = models.CharField(max_length=20, verbose_name='开始期号')
    end_period = models.CharField(max_length=20, verbose_name='结束期号')
    total_periods = models.IntegerField(verbose_name='总期数')
    
    # 资金情况
    starting_capital = models.FloatField(verbose_name='起始资金')
    final_capital = models.FloatField(verbose_name='最终资金')
    total_profit = models.FloatField(verbose_name='总收益')
    roi_percentage = models.FloatField(verbose_name='ROI')
    max_drawdown = models.FloatField(verbose_name='最大回撤')
    
    # 投注统计
    bet_periods = models.IntegerField(verbose_name='投注期数')
    skip_periods = models.IntegerField(verbose_name='跳过期数')
    win_periods = models.IntegerField(verbose_name='盈利期数')
    win_rate = models.FloatField(verbose_name='胜率')
    
    # 投入产出
    total_invested = models.FloatField(verbose_name='总投入')
    total_prizes = models.FloatField(verbose_name='总奖金')
    
    # 详细数据
    period_results = models.JSONField(verbose_name='期次详细结果')
    capital_history = models.JSONField(verbose_name='资金历史')
    
    # 元数据
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '回测结果'
        verbose_name_plural = '回测结果'
    
    def __str__(self):
        return f"{self.strategy_name} (ROI:{self.roi_percentage:.2f}%)"


class DataUpdateLog(models.Model):
    """数据更新日志"""
    update_type = models.CharField(max_length=20, verbose_name='更新类型')  # crawler/manual
    periods_added = models.IntegerField(default=0, verbose_name='新增期数')
    periods_updated = models.IntegerField(default=0, verbose_name='更新期数')
    status = models.CharField(max_length=20, verbose_name='状态')  # success/failed
    message = models.TextField(blank=True, verbose_name='消息')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='更新时间')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = '数据更新日志'
        verbose_name_plural = '数据更新日志'
    
    def __str__(self):
        return f"{self.update_type} - {self.status} ({self.created_at})"
