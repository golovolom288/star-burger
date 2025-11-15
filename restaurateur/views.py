from django import forms
import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F, Sum
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
import django.conf.global_settings
from geopy import distance
from foodcartapp.models import Product, Restaurant, Orders, RestaurantMenuItem
from geopy_bd.models import GeoPy
from star_burger.settings import YANDEX_API_KEY

coordinates = {}


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_coordinates(model):
    global coordinates
    try:
        model_coordinates = coordinates[model.address]
    except KeyError:
        model_coordinates = GeoPy.objects.get_or_create(
            address=model.address,
            defaults={
                "lat": fetch_coordinates(YANDEX_API_KEY, model.address)[0],
                "lon": fetch_coordinates(YANDEX_API_KEY, model.address)[1]
            }
        )
        coordinates[model.address] = {}
        coordinates[model.address]["lat"] = model_coordinates[0].lat
        coordinates[model.address]["lon"] = model_coordinates[0].lon
    return model_coordinates


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    restaurants = {}
    restaurantmenuitem_model = RestaurantMenuItem.objects.all()
    restaurants_model = Restaurant.objects.only("id", "address", "name").prefetch_related("menu_items")
    for order in Orders.objects.only("id", "address", "order_details").prefetch_related("order_details"):
        order_coordinates = get_coordinates(order)
        restaurants[order.id] = {}
        for restaurant in restaurants_model:
            try:
                for product in order.order_details.only("product").prefetch_related("product"):
                    restaurantmenuitem_model.get(product=product.product, restaurant=restaurant, availability=True)
            except ObjectDoesNotExist:
                continue
            restaurant_coordinates = get_coordinates(restaurant)
            if restaurant_coordinates and order_coordinates:
                restaurants[order.id][restaurant.id] = {
                    "name": restaurant.name,
                    "distance": round(
                        distance.distance((
                                coordinates[order.address]["lat"],
                                coordinates[order.address]["lon"]
                            ),
                            (
                                coordinates[restaurant.address]["lat"],
                                coordinates[restaurant.address]["lon"]
                            )).km, 2
                    )
                }
            else:
                restaurants[order.id][restaurant.id] = {
                    "name": restaurant.name,
                    "distance": "Ошибка определения координат"
                }
        restaurants[order.id] = sorted(restaurants[order.id].values(), key=lambda item: item["distance"])
    return render(request, template_name='order_items.html', context={
        'order_items': Orders.objects.prefetch_related("order_details").annotate(price=Sum(F("order_details__price"))).iterator(chunk_size=500),
        'orders_availability': restaurants
    })
