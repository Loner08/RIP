import uuid
from datetime import timedelta

from django.contrib.auth import authenticate
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .calc import calc
from .permissions import IsModerator, IsAuthenticated, IsBuyer
from .redis import session_storage
from .serializers import *
from .utils import get_session, get_draft_reserve, identity_user


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'consumer_name',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        )
    ]
)
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


@swagger_auto_schema(method='put', request_body=ConsumerSerializer)
@api_view(["PUT"])
@permission_classes([IsModerator])
def update_consumer(request, consumer_id):
    if not Consumer.objects.filter(pk=consumer_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    consumer = Consumer.objects.get(pk=consumer_id)

    serializer = ConsumerSerializer(consumer, data=request.data, partial=True)

    if serializer.is_valid(raise_exception=True):
        serializer.save()

    return Response(serializer.data)


@swagger_auto_schema(method='POST', request_body=ConsumerAddSerializer)
@api_view(["POST"])
@permission_classes([IsModerator])
def create_consumer(request):
    serializer = ConsumerSerializer(data=request.data, partial=False)

    serializer.is_valid(raise_exception=True)

    Consumer.objects.create(**serializer.validated_data)

    consumers = Consumer.objects.filter(status=1)
    serializer = ConsumerSerializer(consumers, many=True)

    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsModerator])
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
@permission_classes([IsBuyer])
def add_consumer_to_reserve(request, consumer_id):
    if not Consumer.objects.filter(pk=consumer_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    consumer = Consumer.objects.get(pk=consumer_id)

    draft_reserve = get_draft_reserve(request)

    if draft_reserve is None:
        draft_reserve = Reserve.objects.create()
        draft_reserve.owner = identity_user(request)
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


@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('image', openapi.IN_FORM, type=openapi.TYPE_FILE),
    ]
)
@api_view(["POST"])
@permission_classes([IsModerator])
@parser_classes((MultiPartParser,))
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


@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter(
            'status',
            openapi.IN_QUERY,
            type=openapi.TYPE_NUMBER
        ),
        openapi.Parameter(
            'date_formation_start',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'date_formation_end',
            openapi.IN_QUERY,
            type=openapi.TYPE_STRING
        )
    ]
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_reserves(request):
    status = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    reserves = Reserve.objects.exclude(status__in=[1, 5])

    user = identity_user(request)
    if not user.is_superuser:
        reserves = reserves.filter(owner=user)

    if status > 0:
        reserves = reserves.filter(status=status)

    if date_formation_start and parse_datetime(date_formation_start):
        reserves = reserves.filter(date_formation__gt=parse_datetime(date_formation_start) - timedelta(days=1))

    if date_formation_end and parse_datetime(date_formation_end):
        reserves = reserves.filter(date_formation__lt=parse_datetime(date_formation_end) + timedelta(days=1))

    serializer = ReservesSerializer(reserves, many=True)

    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsBuyer])
def get_cart_info(request):
    resp = {
        "consumers_count": 0,
        "draft_reserve": 0
    }

    draft_reserve = get_draft_reserve(request)
    if draft_reserve:
        consumers = ConsumerReserve.objects.filter(reserve=draft_reserve)
        resp = {
            "consumers_count": consumers.count(),
            "draft_reserve": draft_reserve.pk
        }

    return Response(resp)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_reserve_by_id(request, reserve_id):
    if not Reserve.objects.filter(pk=reserve_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    reserve = Reserve.objects.get(pk=reserve_id)

    user = identity_user(request)
    if not user.is_superuser and reserve.owner != user:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = ReserveSerializer(reserve, many=False)
    return Response(serializer.data)


@swagger_auto_schema(method='put', request_body=ReserveSerializer)
@api_view(["PUT"])
@permission_classes([IsBuyer])
def update_reserve(request, reserve_id):
    user = identity_user(request)
    if not Reserve.objects.filter(pk=reserve_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    reserve = Reserve.objects.get(pk=reserve_id)
    serializer = ReserveSerializer(reserve, data=request.data, partial=True)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()

    return Response(serializer.data)


@api_view(["PUT"])
@permission_classes([IsBuyer])
def update_status_user(request, reserve_id):
    user = identity_user(request)
    if not Reserve.objects.filter(pk=reserve_id, owner=user).exists():
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


@swagger_auto_schema(
    method='put',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'status': openapi.Schema(type=openapi.TYPE_NUMBER),
        }
    )
)
@api_view(["PUT"])
@permission_classes([IsModerator])
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
    reserve.moderator = identity_user(request)
    reserve.save()

    serializer = ReserveSerializer(reserve)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsBuyer])
def delete_reserve(request, reserve_id):
    user = identity_user(request)
    if not Reserve.objects.filter(pk=reserve_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    reserve = Reserve.objects.get(pk=reserve_id)

    if reserve.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    reserve.status = 5
    reserve.save()

    serializer = ReserveSerializer(reserve, many=False)

    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([IsBuyer])
def delete_consumer_from_reserve(request, reserve_id, consumer_id):
    user = identity_user(request)
    if not Reserve.objects.filter(pk=reserve_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    if not ConsumerReserve.objects.filter(reserve_id=reserve_id, consumer_id=consumer_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    item = ConsumerReserve.objects.get(reserve_id=reserve_id, consumer_id=consumer_id)
    item.delete()

    items = ConsumerReserve.objects.filter(reserve_id=reserve_id)
    data = [ConsumerItemSerializer(item.consumer, context={"percentage": item.percentage}).data for item in items]

    return Response(data, status=status.HTTP_200_OK)


@swagger_auto_schema(method='PUT', request_body=ConsumerReserveSerializer)
@api_view(["PUT"])
@permission_classes([IsBuyer])
def update_consumer_in_reserve(request, reserve_id, consumer_id):
    user = identity_user(request)
    if not Reserve.objects.filter(pk=reserve_id, owner=user).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

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


@swagger_auto_schema(method='post', request_body=UserRegisterSerializer)
@api_view(["POST"])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    user = serializer.save()

    session_id = str(uuid.uuid4())
    session_storage.set(session_id, user.id)

    serializer = UserSerializer(user)
    response = Response(serializer.data, status=status.HTTP_201_CREATED)
    response.set_cookie("session_id", session_id, samesite="lax")

    return response


@swagger_auto_schema(method='post', request_body=UserLoginSerializer)
@api_view(["POST"])
def login(request):
    serializer = UserLoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(**serializer.data)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    session_id = str(uuid.uuid4())
    session_storage.set(session_id, user.id)

    serializer = UserSerializer(user)
    response = Response(serializer.data, status=status.HTTP_200_OK)
    response.set_cookie("session_id", session_id, samesite="lax")

    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    session = get_session(request)
    session_storage.delete(session)

    response = Response(status=status.HTTP_200_OK)
    response.delete_cookie('session_id')

    return response


@api_view(["GET"])
def user_info(request):
    user = identity_user(request)
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(method='PUT', request_body=UserUpdateProfileSerializer)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user(request):
    user = identity_user(request)

    serializer = UserUpdateProfileSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data)
