from django.contrib import admin
from core.models import BrokerAccount, Signal, Order, UserActivityLog

admin.site.register(BrokerAccount)
admin.site.register(Signal)
admin.site.register(Order)
admin.site.register(UserActivityLog)
