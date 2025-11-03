from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .calc import calc
from .serializers import *
from .utils import get_draft_reserve, get_user, get_moderator, identity_user


@api_view(["GET"])
def search_consumers(request):
    consumer_name = request.GET.get("consumer_name", "")

    consumers = Consumer.objects.filter(status=1)
    if consumer_name:
        consumers = consumers.filter(name__icontains=consumer_name)

    serializer = ConsumersSerializer(consumers, many=True)

    return Response(serializer.data)


@api_view(["GET"])
def get_consumer_by_id(request, consumer_id):
    if not Consumer.objects.filter(pk=consumer_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    consumer = Consumer.objects.get(pk=consumer_id)
    serializer = ConsumerSerializer(consumer)

    return Response(serializer.data)


@api_view(["PUT"])
def update_consumer(request, consumer_id):
    if not Consumer.objects.filter(pk=consumer_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    consumer = Consumer.objects.get(pk=consumer_id)

    serializer = ConsumerSerializer(consumer, data=request.data, partial=True)

    if serializer.is_valid(raise_exception=True):
        serializer.save()

    return Response(serializer.data)


@api_view(["POST"])
def create_consumer(request):
    serializer = ConsumerSerializer(data=request.data, partial=False)

    serializer.is_valid(raise_exception=True)

    Consumer.objects.create(**serializer.validated_data)

    consumers = Consumer.objects.filter(status=1)
    serializer = ConsumerSerializer(consumers, many=True)

    return Response(serializer.data)


@api_view(["DELETE"])
def delete_consumer(request, consumer_id):
    if not Consumer.objects.filter(pk=consumer_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    consumer = Consumer.objects.get(pk=consumer_id)
    consumer.status = 2
    consumer.save()

    consumers = Consumer.objects.filter(status=1)
    serializer = ConsumerSerializer(consumers, many=True)

    return Response(serializer.data)


@api_view(["POST"])
def add_consumer_to_reserve(request, consumer_id):
    if not Consumer.objects.filter(pk=consumer_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    consumer = Consumer.objects.get(pk=consumer_id)

    draft_reserve = get_draft_reserve()

    if draft_reserve is None:
        draft_reserve = Reserve.objects.create()
        draft_reserve.owner = get_user()
        draft_reserve.save()

    if ConsumerReserve.objects.filter(reserve=draft_reserve, consumer=consumer).exists():
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    item = ConsumerReserve.objects.create(
        reserve=draft_reserve,
        consumer=consumer
    )
    item.save()

    serializer = ReserveSerializer(draft_reserve)
    return Response(serializer.data["consumers"])


@api_view(["POST"])
def update_consumer_image(request, consumer_id):
    if not Consumer.objects.filter(pk=consumer_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    consumer = Consumer.objects.get(pk=consumer_id)

    image = request.data.get("image")
    if image is None:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    consumer.image = image
    consumer.save()

    serializer = ConsumerSerializer(consumer)
    return Response(serializer.data)


@api_view(["GET"])
def search_reserves(request):
    status = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    reserves = Reserve.objects.exclude(status__in=[1, 5])

    if status > 0:
        reserves = reserves.filter(status=status)

    if date_formation_start and parse_datetime(date_formation_start):
        reserves = reserves.filter(date_formation__gt=parse_datetime(date_formation_start) - timedelta(days=1))

    if date_formation_end and parse_datetime(date_formation_end):
        reserves = reserves.filter(date_formation__lt=parse_datetime(date_formation_end) + timedelta(days=1))

    serializer = ReservesSerializer(reserves, many=True)

    return Response(serializer.data)


@api_view(["GET"])
def get_cart_info(request):
    resp = {
        "consumers_count": 0,
        "draft_reserve": 0
    }

    draft_reserve = get_draft_reserve()
    if draft_reserve:
        consumers = ConsumerReserve.objects.filter(reserve=draft_reserve)
        resp = {
            "consumers_count": consumers.count(),
            "draft_reserve": draft_reserve.pk
        }

    return Response(resp)


@api_view(["GET"])
def get_reserve_by_id(request, reserve_id):
    if not Reserve.objects.filter(pk=reserve_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    reserve = Reserve.objects.get(pk=reserve_id)
    serializer = ReserveSerializer(reserve, many=False)

    return Response(serializer.data)


@api_view(["PUT"])
def update_reserve(request, reserve_id):
    if not Reserve.objects.filter(pk=reserve_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    reserve = Reserve.objects.get(pk=reserve_id)
    serializer = ReserveSerializer(reserve, data=request.data, partial=True)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    return Response(serializer.data)


@api_view(["PUT"])
def update_status_user(request, reserve_id):
    if not Reserve.objects.filter(pk=reserve_id).exists():
        return Response({
            "error": "запас хода не найден"
        }, status=status.HTTP_404_NOT_FOUND)

    reserve = Reserve.objects.get(pk=reserve_id)

    if reserve.status != 1:
        return Response({
            "error": "запас хода не в том статусе"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if not reserve.temperature:
        return Response({
            "error": "поле temperature не заполнено"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    reserve.status = 2
    reserve.date_formation = timezone.now()
    reserve.save()

    serializer = ReserveSerializer(reserve)
    return Response(serializer.data)


@api_view(["PUT"])
def update_status_admin(request, reserve_id):
    if not Reserve.objects.filter(pk=reserve_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    request_status = int(request.data["status"])
    if request_status not in [3, 4]:
        return Response({
            "error": "некорректный status"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    reserve = Reserve.objects.get(pk=reserve_id)

    if reserve.status != 2:
        return Response({
            "error": "запас хода не в том статусе"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if request_status == 3:
        serializer = ReserveSerializer(reserve)
        reserve.calculated_range = calc(serializer.data)

    reserve.date_complete = timezone.now()
    reserve.status = request_status
    reserve.moderator = get_moderator()
    reserve.save()

    serializer = ReserveSerializer(reserve)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
def delete_reserve(request, reserve_id):
    if not Reserve.objects.filter(pk=reserve_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    reserve = Reserve.objects.get(pk=reserve_id)

    if reserve.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    reserve.status = 5
    reserve.save()

    serializer = ReserveSerializer(reserve, many=False)

    return Response(serializer.data)


@api_view(["DELETE"])
def delete_consumer_from_reserve(request, reserve_id, consumer_id):
    if not ConsumerReserve.objects.filter(reserve_id=reserve_id, consumer_id=consumer_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = ConsumerReserve.objects.get(reserve_id=reserve_id, consumer_id=consumer_id)
    item.delete()

    items = ConsumerReserve.objects.filter(reserve_id=reserve_id)
    data = [ConsumerItemSerializer(item.consumer, context={"percentage": item.percentage}).data for item in items]

    return Response(data, status=status.HTTP_200_OK)


@api_view(["PUT"])
def update_consumer_in_reserve(request, reserve_id, consumer_id):
    if not ConsumerReserve.objects.filter(consumer_id=consumer_id, reserve_id=reserve_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    reserve = Reserve.objects.get(pk=reserve_id)
    if reserve.status != 1:
        return Response({
            "error": "Некорректный статус запаса хода"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    item = ConsumerReserve.objects.get(consumer_id=consumer_id, reserve_id=reserve_id)

    serializer = ConsumerReserveSerializer(item, data=request.data, partial=True)

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)


@api_view(["POST"])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    user = serializer.save()

    serializer = UserSerializer(user)

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def login(request):
    serializer = UserLoginSerializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    user = authenticate(**serializer.data)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    serializer = UserSerializer(user)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
def logout(request):
    return Response(status=status.HTTP_200_OK)


@api_view(["GET"])
def user_info(request):
    user = identity_user(request)
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
def update_user(request):
    user = identity_user(request)

    serializer = UserUpdateProfileSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)