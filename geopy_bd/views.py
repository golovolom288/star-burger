import requests
from geopy import distance
from foodcartapp.models import Restaurant
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

def get_distance(orders):
    addresses = []
    distances = {}
    addresses.extend(orders.values_list("address", flat=True))
    addresses.extend(Restaurant.objects.values_list("address", flat=True))
    addresses = list(set(addresses))
    geopy_bd = GeoPy.objects.filter(address__in=addresses)
    addresses_with_coordinates = {
        geopy.address: (geopy.lat, geopy.lon)
        for geopy in geopy_bd
    }
    for address in addresses_with_coordinates:
        addresses.remove(address)
    for address in addresses:
        coordinates = fetch_coordinates(YANDEX_API_KEY, address)
        if coordinates:
            GeoPy.objects.create(address=address, lat=coordinates[0], lon=coordinates[1])
    for order in orders:
        try:
            distances[order.id] = {}
            for restaurant in orders.get_available_restaurants()[order.id]:
                try:
                    distances[order.id][restaurant.id] = {
                        "name": restaurant.name,
                        "distance": round(distance.distance(addresses_with_coordinates[order.address],
                                                            addresses_with_coordinates[restaurant.address]).km, 2)
                    }
                except KeyError:
                    distances[order.id] = None
            sorted(distances[order.id].values(), key=lambda item: item["distance"])
        except AttributeError:
            pass
    return distances
