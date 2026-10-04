# my_app/tasks.py
import logging

from arrow import arrow
from celery import shared_task
from django.core.files.storage import default_storage
from django.db import transaction
from django.db import transaction
import requests
from rest_framework import status

from my_app.configs import SERVICE_CONFIG

from my_app.serializers.polling import ChangeDataSerializer
from my_app.utils import (
    get_relative_datetime,
    map_product_sheets,
    read_excel_sheets,
    response,
)
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def poll_products(self):
    task_id = self.request.id

    date_from = get_relative_datetime(set_minute=0, set_second=0, shift_days=-1)
    date_to = get_relative_datetime(set_minute=0, set_second=0)

    query_params = {
        "updatedFrom": date_from.isoformat(),
        "updatedTo": date_to.isoformat(),
    }

    logger.info(
        "[%s] Polling started: from=%s to=%s",
        task_id,
        query_params["updatedFrom"],
        query_params["updatedTo"],
    )
    stage = "request_inventory"
    url = SERVICE_CONFIG.get("product_sync")
    try:
        result = requests.get(
            url,
            params=query_params,
            timeout=(5, 30),
        )
        result.raise_for_status()
        data = result.json()

        stage = "validation"

        created_instances = []
        serializer = ChangeDataSerializer(
            data=data,
            many=True,
            context={
                "created_instances": created_instances,
            },
        )
        serializer.is_valid(raise_exception=False)

        logger.info(
            "[%s] Validation passed: records=%s",
            task_id,
            len(serializer.validated_data),
        )

        stage = "database_save"

        with transaction.atomic():
            serializer.save()

        summary = {
            "processed": len(serializer.validated_data),
            "created": len(created_instances),
            "duplicates": (len(serializer.validated_data) - len(created_instances)),
        }
        logger.info(
            "[%s] Polling completed: processed=%s created=%s duplicates=%s",
            task_id,
            summary["processed"],
            summary["created"],
            summary["duplicates"],
        )

        return summary

    except Exception:
        logger.exception(
            "[%s] Polling failed: stage=%s",
            task_id,
            stage,
        )
        raise


@shared_task(bind=True)
def process_excel_file(self, file_name):
    task_id = self.request.id

    logger.info(
        "[%s] Excel processing started: file=%s",
        self.request.id,
        file_name,
    )

    try:
        with default_storage.open(file_name, "rb") as file:
            sheets = read_excel_sheets(file)

        stage = "map_sheets"

        try:
            products = map_product_sheets(sheets)
        except Exception as exc:
            raise ValidationError({"file": exc.errors}) from exc

        logger.info(
            "[%s] Excel mapped: products=%s",
            task_id,
            len(products),
        )

        stage = "validation"
        created_instances = []

        serializer = ChangeDataSerializer(
            data=products,
            many=True,
            context={
                "created_instances": created_instances,
            },
        )
        serializer.is_valid(raise_exception=True)

        stage = "database_save"

        with transaction.atomic():
            serializer.save()

        summary = {
            "processed": len(serializer.validated_data),
            "created": len(created_instances),
            "duplicates": (len(serializer.validated_data) - len(created_instances)),
        }

        logger.info(
            "[%s] Excel processing completed: %s",
            task_id,
            summary,
        )

        return summary

    except Exception:
        logger.exception(
            "[%s] Excel processing failed: stage=%s file=%s",
            task_id,
            stage,
            file_name,
        )
        raise
