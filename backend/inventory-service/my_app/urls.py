from django.urls import path

from my_app.views.health_view import HealthCheckView
from my_app.views.product import ProductQueryView, ProductView

urlpatterns = [
    path("health-check", HealthCheckView.as_view(), name="health-check"),
    path("product", ProductView.as_view(), name="product-list-create"),
    path("product-query-all", ProductQueryView.as_view(), name="product-query"),
]
