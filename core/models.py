import uuid
from django.db import models
from django.contrib.auth.models import User


class BrokerAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='broker_accounts')
    account_id = models.CharField(max_length=100)
    broker_name = models.CharField(max_length=100, default='MetaTrader')
    api_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.broker_name} ({self.account_id})"


class Signal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='signals')
    raw_text = models.TextField()
    action = models.CharField(max_length=10)
    instrument = models.CharField(max_length=20)
    entry_price = models.FloatField(null=True, blank=True)
    stop_loss = models.FloatField()
    take_profit = models.FloatField()
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} {self.instrument} - user {self.user_id}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('executed', 'Executed'),
        ('closed', 'Closed'),
    ]

    order_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    signal = models.OneToOneField(Signal, on_delete=models.CASCADE, related_name='order')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    broker_account = models.ForeignKey(BrokerAccount, on_delete=models.SET_NULL, null=True, related_name='orders')
    instrument = models.CharField(max_length=20)
    action = models.CharField(max_length=10)
    entry_price = models.FloatField(null=True, blank=True)
    stop_loss = models.FloatField()
    take_profit = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.status}"


class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=200)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"
