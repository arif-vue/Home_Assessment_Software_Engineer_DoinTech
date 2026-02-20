import uuid
import time
import logging
import threading
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)


def parse_signal(text):
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]

    if not lines:
        return None, "Signal text is empty."

    first = lines[0].split()
    if len(first) < 2:
        return None, "First line must be: ACTION INSTRUMENT [@price]"

    action = first[0].upper()
    if action not in ('BUY', 'SELL'):
        return None, f"Action must be BUY or SELL, got '{action}'."

    instrument = first[1].upper()

    entry_price = None
    if len(first) >= 3 and first[2].startswith('@'):
        try:
            entry_price = float(first[2][1:])
        except ValueError:
            return None, "Entry price is not a valid number."

    sl = None
    tp = None
    for line in lines[1:]:
        parts = line.split()
        if len(parts) == 2:
            label = parts[0].upper()
            try:
                value = float(parts[1])
            except ValueError:
                return None, f"{label} value is not a valid number."
            if label == 'SL':
                sl = value
            elif label == 'TP':
                tp = value

    if sl is None:
        return None, "SL (Stop Loss) is missing."
    if tp is None:
        return None, "TP (Take Profit) is missing."

    if action == 'BUY' and sl >= tp:
        return None, "For BUY, SL must be lower than TP."
    if action == 'SELL' and sl <= tp:
        return None, "For SELL, SL must be higher than TP."

    return {
        'action': action,
        'instrument': instrument,
        'entry_price': entry_price,
        'stop_loss': sl,
        'take_profit': tp,
    }, None


def mock_execute_trade(action, instrument, user_id):
    order_id = str(uuid.uuid4())
    logger.info(f"Executing {action} {instrument} for user {user_id}, order {order_id}")
    return order_id


def _simulate_order_executed(order_id):
    from core.models import Order
    time.sleep(5)
    try:
        order = Order.objects.get(order_id=order_id)
        order.status = 'executed'
        order.save(update_fields=['status', 'updated_at'])
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'orders',
            {
                'type': 'order_update',
                'data': {
                    'type': 'order.executed',
                    'order_id': order_id,
                    'instrument': order.instrument,
                    'entry_price': order.entry_price,
                }
            }
        )
    except Order.DoesNotExist:
        pass


def start_order_simulation(order_id):
    t = threading.Thread(target=_simulate_order_executed, args=(order_id,), daemon=True)
    t.start()
