from django.db.transaction import atomic
from django.templatetags.static import static
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.serializers import ModelSerializer
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


class OrderSerializer(ModelSerializer):
    class OrderDetailsSerializer(ModelSerializer):
        product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

        class Meta:
            model = OrderDetails
            fields = ["product", "quantity"]

    products = OrderDetailsSerializer(many=True, source="order_details")

    class Meta:
        model = Orders
        fields = ["id", "first_name", "last_name", "phone_number", "address", "products"]

    def create(self, validated_data):
        products_data = validated_data.pop('order_details')
        order = Orders.objects.create(**validated_data)
        for detail_data in products_data:
            OrderDetails.objects.create(order=order, price=products_data[0]["product"].price * detail_data["quantity"], **detail_data)
        return order


@api_view(['GET', 'POST'])
def register_order(request):
    if request.method == "POST":
        with atomic():
            order_json = request.data
            serializer = OrderSerializer(data=order_json)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        for product in serializer.validated_data["order_details"]:
            product["product"] = product["product"].id
        return Response(serializer.validated_data, 201)
    elif request.method == "GET":
        order = Orders.objects.order_by('-id').first()
        serializer = OrderSerializer(order)
        return Response(serializer.data)
