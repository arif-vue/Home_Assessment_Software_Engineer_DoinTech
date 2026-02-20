from rest_framework import serializers
from core.models import BrokerAccount, Order


class BrokerAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrokerAccount
        fields = ['id', 'account_id', 'broker_name', 'api_key', 'is_active', 'created_at']
        extra_kwargs = {
            'api_key': {'write_only': True},
        }


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'order_id', 'instrument', 'action', 'entry_price', 'stop_loss', 'take_profit', 'status', 'created_at', 'updated_at']
