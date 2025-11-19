from django.shortcuts import render
import requests

from geopy_bd.models import GeoPy
from star_burger.settings import YANDEX_API_KEY


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    if response.ok:
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    else:
        print("Ссылка на яндекс геокод не работает")
        return
    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_coordinates(model, coordinates):
    try:
        model_coordinates = coordinates[model.address]
    except KeyError:
        try:
            model_coordinates = GeoPy.objects.get(address=model.address)
        except GeoPy.DoesNotExist:
            api_coordinates = fetch_coordinates(YANDEX_API_KEY, model.address)
            model_coordinates = GeoPy.objects.create(
                address=model.address,
                lat=api_coordinates[0],
                lon=api_coordinates[1]
            )
        coordinates[model.address] = {}
        coordinates[model.address]["lat"] = model_coordinates.lat
        coordinates[model.address]["lon"] = model_coordinates.lon
    return model_coordinates, coordinates
