from django.db import models
from django.utils import timezone


class GeoPy(models.Model):
    address = models.CharField(
        'адрес',
        max_length=100,
        unique=True
    )
    lat = models.DecimalField(
        'Широта',
        max_digits=8,
        decimal_places=5
    )
    lon = models.DecimalField(
        'Долгота',
        max_digits=8,
        decimal_places=5
    )
    date = models.DateTimeField(
        default=timezone.now(),
        verbose_name="Дата загрузки данных"
    )
