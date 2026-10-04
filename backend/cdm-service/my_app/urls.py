from django.urls import path

from my_app.views.views import ChangeDataView, ExcelUploadView, HealthCheckView, ProductPollingCheckView

urlpatterns = [
    path("health-check", HealthCheckView.as_view(), name="health-check"),
    path("upload-excel", ExcelUploadView.as_view(), name="upload-excel"),
    path(
        "product-polling-check",
        ProductPollingCheckView.as_view(),
        name="product-polling-check",
    ),
    path(
        "change-data",
        ChangeDataView.as_view(),
        name="change-data-view",
    ),
]
