from decimal import Decimal
import hashlib
import json

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from my_app.models.change_data import ChangeData


class CategorySerializer(serializers.Serializer):
    categoryCode = serializers.CharField(source='category_code')
    categoryName = serializers.CharField(source='category_name')


class ProductUnitSerializer(serializers.Serializer):
    unitCode = serializers.CharField(source='unit_code')
    unitName = serializers.CharField(source='unit_name')
    baseUnitQty = serializers.IntegerField(source='base_unit_qty', min_value=1)
    isBaseUnit = serializers.BooleanField(source='is_base_unit')


class ChangeDataSerializer(ModelSerializer):
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
    hashValue = serializers.CharField(
        source="hash_value",
        read_only=True,
    )

    class Meta:
        model = ChangeData
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
            'hashValue',
        )

    @staticmethod
    def generate_hash(data):
        # Chỉ hash nội dung sản phẩm, không hash id hoặc metadata.
        content = {
            "sku": data["sku"],
            "partner_sku": data.get("partner_sku"),
            "product_name": data["product_name"],
            "unit_code": data["unit_code"],
            "unit_name": data["unit_name"],
            "serial_type": data.get("serial_type"),
            "is_expiry_date": data.get("is_expiry_date", False),
            "categories": data.get("categories", []),
            "product_units": data.get("product_units", []),
        }

        def normalize(value):
            if isinstance(value, Decimal):
                # 10.0 và 10.00 có cùng biểu diễn để hash.
                return "0" if value == 0 else format(value.normalize(), "f")

            if isinstance(value, dict):
                return {key: normalize(item) for key, item in value.items()}

            if isinstance(value, list):
                return [normalize(item) for item in value]

            return value

        content = normalize(content)

        # Với categories và product_units, coi thứ tự là không quan trọng.
        # Sắp xếp để đảo thứ tự item không làm thay đổi hash.
        for field in ("categories", "product_units"):
            content[field] = sorted(
                content[field],
                key=lambda item: json.dumps(
                    item,
                    sort_keys=True,
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            )

        body = json.dumps(
            content,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )

        return hashlib.sha256(body.encode("utf-8")).hexdigest()

    def validate(self, data):
        # Custom validation logic can be added here if needed
        data['hash_value'] = data.get('hash_value') or self.generate_hash(data)
        return data

    def create(self, validated_data):
        data = dict(validated_data)
        hash_value = data.pop("hash_value")

        instance, created = ChangeData.objects.get_or_create(
            hash_value=hash_value,
            defaults=data,
        )

        if created:
            self.context["created_instances"].append(instance)

        return instance
