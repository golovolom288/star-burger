import json
from types import NoneType

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import phonenumbers
from .models import Product, Orders, OrderDetails


@api_view(['GET'])
def banners_list_api(request):
    # FIXME move data to db?
    return Response([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ])


@api_view(['GET'])
def product_list_api(request):
    products = Product.objects.select_related('category').available()
    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return Response(dumped_products)


@api_view(['POST'])
def register_order(request):
    order_json = request.data
    error_fields = []
    bd_fields = ["products", "firstname", "lastname", "phonenumber", "address"]
    print(type(None))
    for field_number in range(1, len(order_json)):
        if not isinstance(order_json[bd_fields[field_number]], str):
            if not isinstance(order_json[bd_fields[field_number]], type(None)):
                return Response({
                    "error": f"{bd_fields[field_number]}: Ожидался str, но был получен {type(order_json[bd_fields[field_number]])}. '{bd_fields[field_number]}': '{order_json['products']}'"
                },
                    status=status.HTTP_400_BAD_REQUEST
                )
    for field in bd_fields:
        try:
            if not order_json[f"{field}"]:
                error_fields.append(field)
        except KeyError:
            error_fields.append(field)
    if error_fields:
        return Response({
            "error": f"{', '.join(error_fields)}: Это поле не может быть пустым"
        },
            status=status.HTTP_400_BAD_REQUEST
        )
    if not phonenumbers.is_valid_number(phonenumbers.parse(order_json["phonenumber"])):
        return Response({
            "error": "phonenumber: Некорректный номер телефона"
        },
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        [Product.objects.get(id=product["product"]) for product in order_json["products"]]
    except ObjectDoesNotExist:
        return Response({
            "error": "products: Некорректный id продукта"
        },
            status=status.HTTP_400_BAD_REQUEST
        )
    if isinstance(order_json["products"], list):
        order = Orders.objects.create(
            first_name=order_json["firstname"],
            last_name=order_json["lastname"],
            phone_number=order_json["phonenumber"],
            address=order_json["address"],
        )
        for ordered_product in order_json["products"]:
            OrderDetails.objects.create(
                product=Product.objects.get(id=ordered_product["product"]),
                quantity=ordered_product["quantity"],
                order=order
            )
        return Response(order_json)
    else:
        return Response({
            "error": f"products: Ожидался list со значениями, но был получен {type(order_json['products'])}. 'products': '{order_json['products']}'"
        },
            status=status.HTTP_400_BAD_REQUEST
        )
