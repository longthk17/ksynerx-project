from rest_framework import generics, serializers

from my_app.models.product import Product
from my_app.paginations.pagination import ProductPagination
from my_app.serializers.product import ProductQuerySerializer, ProductSerializer
from my_app.utils import response
from django_filters.rest_framework import DjangoFilterBackend

from my_app.filters.product import ProductFilter


class ProductView(generics.ListCreateAPIView):
    queryset = Product.objects.order_by('id')
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter

    # def get_serializer_class(self):
    #     if self.request.method == 'POST':
    #         return ProductCreateSerializer(many=True)
    #     return ProductListSerializer(many=True)

    def list(self, request, *args, **kwargs):
        result = super().list(request, *args, **kwargs)
        return response(data=result.data, message="Products retrieved successfully")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        skus = [item['sku'] for item in serializer.validated_data]
        print(serializer.validated_data)
        print(serializer)
        if len(skus) != len(set(skus)):
            return response(
                data=None,
                message="Duplicate SKUs found in the request data",
                status_code=400,
            )

        from django.db import transaction

        with transaction.atomic():
            serializer.save()

        return response(
            data=serializer.data,
            message="Product created successfully",
            status_code=201,
        )


class ProductQueryView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        query_serializer = ProductQuerySerializer(
            data=self.request.query_params,
        )
        query_serializer.is_valid(raise_exception=True)

        params = query_serializer.validated_data

        return Product.objects.filter(
            updated_at__gte=params["updatedFrom"],
            updated_at__lt=params["updatedTo"],
        ).order_by("updated_at", "id")

    def list(self, request, *args, **kwargs):
        result = super().list(request, *args, **kwargs)
        return response(data=result.data, message="Products retrieved successfully")
