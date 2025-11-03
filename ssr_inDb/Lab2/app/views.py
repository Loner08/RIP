from django.contrib.auth.models import User
from django.db import connection
from django.shortcuts import render, redirect
from django.utils import timezone

from app.models import Consumer, Reserve, ConsumerReserve


def index(request):
    consumer_name = request.GET.get("consumer_name", "")
    consumers = Consumer.objects.filter(status=1)

    if consumer_name:
        consumers = consumers.filter(name__icontains=consumer_name)

    context = {
        "consumer_name": consumer_name,
        "consumers": consumers
    }

    draft_reserve = get_draft_reserve()
    if draft_reserve:
        context["consumers_count"] = len(draft_reserve.consumerreserve_set.all())
        context["draft_reserve"] = draft_reserve

    return render(request, "consumers_page.html", context)


def consumer_page(request, consumer_id):
    context = {
        "consumer": Consumer.objects.get(id=consumer_id)
    }

    return render(request, "consumer_page.html", context)


def reserve_page(request, reserve_id):
    if not Reserve.objects.filter(pk=reserve_id).exists():
        return render(request, "404.html")

    reserve = Reserve.objects.get(id=reserve_id)
    if reserve.status == 5:
        return render(request, "404.html")

    context = {
        "reserve": reserve,
        "items": reserve.consumerreserve_set.all()
    }

    return render(request, "reserve_page.html", context)


def add_consumer_to_draft_reserve(request, consumer_id):
    consumer_name = request.POST.get("consumer_name")
    redirect_url = f"/?consumer_name={consumer_name}" if consumer_name else "/"

    draft_reserve = get_draft_reserve()
    if draft_reserve is None:
        draft_reserve = Reserve.objects.create()
        draft_reserve.owner = get_current_user()
        draft_reserve.date_created = timezone.now()
        draft_reserve.save()

    consumer = Consumer.objects.get(pk=consumer_id)
    if ConsumerReserve.objects.filter(reserve=draft_reserve, consumer=consumer).exists():
        return redirect(redirect_url)

    item = ConsumerReserve(
        reserve=draft_reserve,
        consumer=consumer
    )
    item.save()

    return redirect(redirect_url)


def delete_reserve(request, reserve_id):
    if not Reserve.objects.filter(pk=reserve_id).exists():
        return redirect("/")

    with connection.cursor() as cursor:
        cursor.execute("UPDATE reserves SET status=5 WHERE id = %s", [reserve_id])

    return redirect("/")


def get_draft_reserve():
    return Reserve.objects.filter(status=1).first()


def get_current_user():
    return User.objects.filter(is_superuser=False).first()
