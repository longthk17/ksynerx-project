from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from my_app.utils import response


class PaginationParamsSerializer(serializers.Serializer):
    PageIndex = serializers.IntegerField(min_value=0, default=0)
    PageSize = serializers.IntegerField(
        min_value=1,
        max_value=100,
        default=10,
    )


class ProductPagination(PageNumberPagination):
    page_size = 10
    page_query_param = "PageIndex"
    page_size_query_param = "PageSize"
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        serializer = PaginationParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        self.params = serializer.validated_data
        return super().paginate_queryset(queryset, request, view)

    def get_page_number(self, request, paginator):
        return self.params.get("PageIndex", 0) + 1

    def get_page_size(self, request):
        return self.params.get("PageSize", self.page_size)

    def get_paginated_response(self, data):
        return response(
            data={
                "pageIndex": self.page.number - 1,
                "pageSize": self.get_page_size(self.request),
                "totalCount": self.page.paginator.count,
                "totalPages": self.page.paginator.num_pages,
                "hasNextPage": self.page.has_next(),
                "hasPreviousPage": self.page.has_previous(),
                "results": data,
            },
            message="Paginated response",
        )
