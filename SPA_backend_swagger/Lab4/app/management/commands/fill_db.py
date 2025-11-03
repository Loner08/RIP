from django.core.management.base import BaseCommand

from app.calc import calc
from app.models import *
from app.serializers import ReserveSerializer
from app.utils import *


def add_users():
    User.objects.create_user("user", "user@user.com", "1234", first_name="user", last_name="user")
    User.objects.create_superuser("root", "root@root.com", "1234", first_name="root", last_name="root")

    for i in range(2, 10):
        User.objects.create_user(f"user{i}", f"user{i}@user.com", "1234", first_name=f"user{i}", last_name=f"user{i}")
        User.objects.create_superuser(f"root{i}", f"root{i}@root.com", "1234", first_name=f"user{i}", last_name=f"user{i}")


def add_consumers():
    Consumer.objects.create(
        name="Обогрев салона",
        description="Основная система отопления салона. Значительно снижает запас хода в сильные морозы.",
        power=3000,
        image="1.png",
        category="Обогрев"
    )

    Consumer.objects.create(
        name="Подогрев рулевого колеса",
        description="Подогрев руля – это не только элемент комфорта, но и важная составляющая безопасности в зимний период. Тёплый руль позволяет водителю сосредоточиться на управлении, исключая дискомфорт от замёрзших рук.",
        power=40,
        image="2.png",
        category="Комфорт"
    )

    Consumer.objects.create(
        name="Подогрев сидений",
        description="Подогрев сидений — это система электрических нагревательных элементов, встраиваемых в автомобильные кресла или устанавливаемых в виде чехлов, предназначенная для повышения комфорта пассажиров в холодное время года путем их обогрева",
        power=100,
        image="3.png",
        category="Комфорт"
    )

    Consumer.objects.create(
        name="Кондиционер (обогрев)",
        description="Кондиционер в режиме обогрева – это сплит-система, которая работает как тепловой насос «воздух-воздух», перенося тепло с улицы в помещение, а не производя его напрямую.",
        power=2000,
        image="4.png",
        category="Обогрев"
    )

    Consumer.objects.create(
        name="Кондиционер (охлаждение)",
        description="Кондиционер в режиме охлаждения (Cool) – это основная функция кондиционера, позволяющая снижать температуру в помещении, поглощая тепло из воздуха и вынося его наружу с помощью специального вещества – хладагента (фреона)",
        power=1500,
        image="5.png",
        category="Комфорт"
    )

    Consumer.objects.create(
        name="Подогрев аккумлятора",
        description="Подогрев аккумулятора — это использование специальных систем и устройств для поддержания оптимальной рабочей температуры аккумулятора при низких температурах",
        power=6000,
        image="6.png",
        category="Безопасность"
    )



def add_reserves():
    users = User.objects.filter(is_staff=False)
    moderators = User.objects.filter(is_staff=True)
    consumers = Consumer.objects.all()

    for _ in range(30):
        status = random.randint(2, 5)
        owner = random.choice(users)
        add_reserve(status, consumers, owner, moderators)

    # add_reserve(1, consumers, users[0], moderators)
    add_reserve(2, consumers, users[0], moderators)
    add_reserve(3, consumers, users[0], moderators)
    add_reserve(4, consumers, users[0], moderators)
    add_reserve(5, consumers, users[0], moderators)

    for _ in range(10):
        status = random.randint(2, 5)
        add_reserve(status, consumers, users[0], moderators)


def add_reserve(status, consumers, owner, moderators):
    reserve = Reserve.objects.create()
    reserve.status = status

    if status in [3, 4]:
        reserve.moderator = random.choice(moderators)
        reserve.date_complete = random_date()
        reserve.date_formation = reserve.date_complete - random_timedelta()
        reserve.date_created = reserve.date_formation - random_timedelta()
    else:
        reserve.date_formation = random_date()
        reserve.date_created = reserve.date_formation - random_timedelta()

    reserve.temperature = random.randint(-40, 0)

    reserve.owner = owner

    for consumer in random.sample(list(consumers), random.randint(1, 3)):
        item = ConsumerReserve(
            reserve=reserve,
            consumer=consumer,
            percentage=random.randint(1, 100)
        )
        item.save()

    if status == 3:
        serializer = ReserveSerializer(reserve)
        reserve.calculated_range = calc(serializer.data)

    reserve.save()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        add_users()
        add_consumers()
        add_reserves()
