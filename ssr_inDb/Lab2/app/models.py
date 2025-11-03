from django.contrib.auth.models import User
from django.db import models


class Consumer(models.Model):
    STATUS_CHOICES = (
        (1, 'Действует'),
        (2, 'Удалена'),
    )

    name = models.CharField(max_length=100, verbose_name="Название")
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    image = models.ImageField(blank=True, null=True, default='default.png')
    description = models.TextField(verbose_name="Описание")

    power = models.IntegerField(verbose_name="Потребление")
    category = models.CharField(verbose_name="Категория")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Потребитель"
        verbose_name_plural = "Потребители"
        db_table = "consumers"
        ordering = ("pk",)


class Reserve(models.Model):
    STATUS_CHOICES = (
        (1, 'Введён'),
        (2, 'В работе'),
        (3, 'Завершен'),
        (4, 'Отклонен'),
        (5, 'Удален')
    )

    status = models.IntegerField(choices=STATUS_CHOICES, default=1, verbose_name="Статус")
    date_created = models.DateTimeField(verbose_name="Дата создания", auto_now_add=True)
    date_formation = models.DateTimeField(verbose_name="Дата формирования", blank=True, null=True)
    date_complete = models.DateTimeField(verbose_name="Дата завершения", blank=True, null=True)

    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Пользователь", null=True,
                              related_name='owner')
    moderator = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="Инженер", null=True,
                                  related_name='moderator')

    temperature = models.IntegerField(blank=True, null=True)
    calculated_range = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return "Запас хода №" + str(self.pk)

    class Meta:
        verbose_name = "Запас хода"
        verbose_name_plural = "Запасы хода"
        db_table = "reserves"
        ordering = ('-date_formation',)


class ConsumerReserve(models.Model):
    pk = models.CompositePrimaryKey("consumer_id", "reserve_id")
    consumer = models.ForeignKey(Consumer, on_delete=models.DO_NOTHING)
    reserve = models.ForeignKey(Reserve, on_delete=models.DO_NOTHING)
    percentage = models.IntegerField(default=0)

    def __str__(self):
        return "м-м №" + str(self.pk)

    class Meta:
        verbose_name = "м-м"
        verbose_name_plural = "м-м"
        db_table = "consumer_reserve"
        ordering = ('pk',)
