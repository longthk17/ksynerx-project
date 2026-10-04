import django_filters
from django.db.models import Q

from my_app.models.product import Product


class ProductFilter(django_filters.FilterSet):
    Keyword = django_filters.CharFilter(method="filter_keyword")
    PartnerSKUs = django_filters.CharFilter(method="filter_partner_skus")
    SKUs = django_filters.CharFilter(method="filter_skus")

    def filter_keyword(self, queryset, name, value):
        value = value.strip()

        if not value:
            return queryset

        return queryset.filter(
            Q(sku__icontains=value) | Q(product_name__icontains=value)
        )

    def filter_partner_skus(self, queryset, name, value):
        values = self.split_values(value)

        if not values:
            return queryset

        return queryset.filter(partner_sku__in=values)

    def filter_skus(self, queryset, name, value):
        values = self.split_values(value)

        if not values:
            return queryset

        return queryset.filter(sku__in=values)

    @staticmethod
    def split_values(value):
        return [item.strip() for item in value.split(",") if item.strip()]

    class Meta:
        model = Product
        fields = []
