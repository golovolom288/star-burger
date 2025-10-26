import json
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

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
    try:
        if not order_json["products"]:
            return Response({
                "error": f"products: Это поле не может быть пустым"
            },
                status=status.HTTP_400_BAD_REQUEST
            )
    except (KeyError, IndexError):
        return Response({
            "error": f"products: Это поле не может быть пустым"
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
            "error": f"products: Ожидался list со значениями, но был получен 'str'. 'products': '{order_json['products']}'"
        },
            status=status.HTTP_400_BAD_REQUEST
        )
