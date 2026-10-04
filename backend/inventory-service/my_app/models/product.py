from django.db import models
from my_app.models.models import BaseModel


class Product(BaseModel):
    sku = models.CharField(max_length=100, null=False, blank=False, unique=True)
    partner_sku = models.CharField(max_length=100, null=True, blank=False)
    product_name = models.CharField(max_length=255, null=False, blank=False)
    unit_code = models.CharField(max_length=50, null=False, blank=False)
    unit_name = models.CharField(max_length=100, null=False, blank=False)
    serial_type = models.IntegerField(null=False, blank=True, default=None)
    is_expiry_date = models.BooleanField(default=False)
    categories = models.JSONField(default=list, null=False, blank=True)
    product_units = models.JSONField(default=list, null=False, blank=True)

    def __str__(self):
        return self.product_name

    class Meta:
        indexes = [
            models.Index(fields=['updated_at', 'id'], name='product_update_at_id_idx'),
        ]
