from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from my_app.models.product import Product


class CategorySerializer(serializers.Serializer):
    categoryCode = serializers.CharField(source='category_code')
    categoryName = serializers.CharField(source='category_name')


class ProductUnitSerializer(serializers.Serializer):
    unitCode = serializers.CharField(source='unit_code')
    unitName = serializers.CharField(source='unit_name')
    baseUnitQty = serializers.IntegerField(source='base_unit_qty', min_value=1)
    isBaseUnit = serializers.BooleanField(source='is_base_unit')


class ProductSerializer(ModelSerializer):
    sku = serializers.CharField(
        max_length=100, required=True, allow_blank=False, allow_null=False
    )
    partnerSKU = serializers.CharField(
        source='partner_sku',
        max_length=100,
        required=False,
        allow_blank=False,
        allow_null=True,
    )
    productName = serializers.CharField(
        source='product_name',
        max_length=255,
        required=True,
        allow_blank=False,
        allow_null=False,
    )
    unitCode = serializers.CharField(
        source='unit_code',
        max_length=50,
        required=True,
        allow_blank=False,
        allow_null=False,
    )
    unitName = serializers.CharField(
        source='unit_name',
        max_length=100,
        required=True,
        allow_blank=False,
        allow_null=False,
    )
    serialType = serializers.IntegerField(
        source='serial_type',
        required=False,
        min_value=0,
        default=None,
    )
    isExpiryDate = serializers.BooleanField(source='is_expiry_date', default=False)
    categories = CategorySerializer(many=True, required=False)
    productUnits = ProductUnitSerializer(
        many=True, source='product_units', required=False
    )

    class Meta:
        model = Product
        fields = (
            'id',
            'partnerSKU',
            'sku',
            'productName',
            'unitCode',
            'unitName',
            'serialType',
            'isExpiryDate',
            'categories',
            'productUnits',
        )


from rest_framework import serializers


class ProductQuerySerializer(serializers.Serializer):
    updatedFrom = serializers.DateTimeField(required=True)
    updatedTo = serializers.DateTimeField(required=True)

    def validate(self, attrs):
        if attrs["updatedFrom"] >= attrs["updatedTo"]:
            raise serializers.ValidationError(
                {"updatedTo": "Phải lớn hơn updatedFrom."}
            )

        return attrs
