from collections import defaultdict
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import F, Sum, Prefetch

STATUS_CHOICES = [
    ("Не обработан","Не обработан"),
    ("Принят", "Принят"),
    ("Передан ресторану", "Передан ресторану"),
    ("Готовится", "Готовится"),
    ("Передан курьеру", "Передан курьеру"),
    ("Отдан заказчику", "Отдан заказчику"),
]

PAY_METHOD_CHOICES = [
    ("Наличностью", "Наличностью"),
    ("Электронно", "Электронно")
]


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50,
        db_index=True
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name

class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=500,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"

class OrderItemsQuerySet(models.QuerySet):
    def get_price(self):
        return self.annotate(
            price=Sum(F("order_details__price"))
        )
    def get_available_restaurants(self):
        menu_items = RestaurantMenuItem.objects.filter(availability=True).select_related('restaurant', 'product')
        restaurant_products = defaultdict(set)
        available_restaurants = defaultdict(set)
        for item in menu_items:
            restaurant_products[item.restaurant].add(item.product)
        for order in self:
            order_products = set()
            for detail in order.order_details.all():
                order_products.add(detail.product)
            for restaurant, products in restaurant_products.items():
                if order_products.issubset(products):
                    available_restaurants[order.id].add(restaurant)
        return available_restaurants

class Orders(models.Model):
    first_name = models.CharField(
        verbose_name="Имя",
        max_length=50
    )
    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=50
    )
    phone_number = PhoneNumberField(
        verbose_name="Номер телефона",
        db_index=True,
    )
    address = models.CharField(
        verbose_name="Адрес доставки",
        max_length=50
    )
    status = models.CharField(
        choices=STATUS_CHOICES,
        default="Не обработан",
        verbose_name="Статус заказа",
        db_index = True,
    )
    comment = models.TextField(
        blank=True,
        default="",
        verbose_name="Комментарий к заказу"
    )
    registration_time = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата регистрации заказа",
        db_index=True,
    )
    call_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата звонка клиенту",
        db_index=True,
    )
    delivery_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата доставки клиенту",
        db_index=True,
    )
    pay_method = models.CharField(
        choices=PAY_METHOD_CHOICES,
        verbose_name="Метод оплаты",
        db_index=True,
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name='Ресторан выполняющий заказ',
        null=True,
        blank=True
    )
    objects = OrderItemsQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказы'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.address}"


class OrderDetails(models.Model):
    product = models.ForeignKey(
        Product,
        verbose_name='Заказанный продукт',
        related_name='order_details',
        on_delete=models.CASCADE
    )

    quantity = models.IntegerField(
        verbose_name="Количество продукта",
        validators=[MinValueValidator(0)],
    )

    order = models.ForeignKey(
        Orders,
        verbose_name='Заказ',
        related_name='order_details',
        on_delete=models.CASCADE
    )

    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = 'детали заказа'
        verbose_name_plural = 'детали заказа'

    def __str__(self):
        return f"Заказ: {self.order.id} - {self.product}"


