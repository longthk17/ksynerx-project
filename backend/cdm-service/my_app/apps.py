from django.apps import AppConfig


class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_app'


SERVICE_NAME = 'cdm-service'
APP_VERSION = '1.0.0'
API_VERSION = 'v1'
ROUTE_PREFIX = f'api/{API_VERSION}'
