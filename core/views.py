from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from core.models import BrokerAccount, Signal, Order, UserActivityLog
from core.serializers import BrokerAccountSerializer, OrderSerializer
from core import services


def health_check(request):
    return JsonResponse({'status': 'ok'})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response({'error': 'username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken.'}, status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(username=username, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'username': user.username, 'token': token.key}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def obtain_token(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid username or password.'}, status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key})


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def link_broker_account(request):
    serializer = BrokerAccountSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save(user=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def receive_signal(request):
    raw_text = request.data.get('signal', '').strip()
    if not raw_text:
        return Response({'error': 'signal is required.'}, status=status.HTTP_400_BAD_REQUEST)

    parsed, error = services.parse_signal(raw_text)
    if error:
        return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

    broker = BrokerAccount.objects.filter(user=request.user, is_active=True).first()
    if not broker:
        return Response({'error': 'No active broker account found.'}, status=status.HTTP_400_BAD_REQUEST)

    signal = Signal.objects.create(
        user=request.user,
        raw_text=raw_text,
        action=parsed['action'],
        instrument=parsed['instrument'],
        entry_price=parsed['entry_price'],
        stop_loss=parsed['stop_loss'],
        take_profit=parsed['take_profit'],
    )

    order_id = services.mock_execute_trade(parsed['action'], parsed['instrument'], request.user.id)

    order = Order.objects.create(
        order_id=order_id,
        signal=signal,
        user=request.user,
        broker_account=broker,
        instrument=parsed['instrument'],
        action=parsed['action'],
        entry_price=parsed['entry_price'],
        stop_loss=parsed['stop_loss'],
        take_profit=parsed['take_profit'],
        status='pending',
    )

    UserActivityLog.objects.create(
        user=request.user,
        action='signal_received',
        details={'order_id': order_id, 'instrument': parsed['instrument'], 'action': parsed['action']},
    )

    services.start_order_simulation(order_id)

    return Response({'order_id': order_id, 'status': 'pending'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_orders(request):
    orders = Order.objects.filter(user=request.user).select_related('signal', 'broker_account').order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id):
    try:
        order = Order.objects.select_related('signal', 'broker_account').get(order_id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = OrderSerializer(order)
    return Response(serializer.data)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def analytics(request):
    orders = Order.objects.filter(user=request.user)
    total = orders.count()
    executed = orders.filter(status='executed').count()
    closed = orders.filter(status='closed').count()
    pending = orders.filter(status='pending').count()

    stats = {
        'total_orders': total,
        'pending': pending,
        'executed': executed,
        'closed': closed,
    }
    return Response(stats)
