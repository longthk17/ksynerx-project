from pathlib import Path
import uuid

from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import connections, transaction
from kombu.exceptions import OperationalError as BrokerError
import requests
from zipfile import BadZipFile
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException
from rest_framework import status, generics
from rest_framework.views import APIView

from my_app.apps import API_VERSION, SERVICE_NAME
from my_app.configs import SERVICE_CONFIG
from my_app.serializers.polling import ChangeDataSerializer
from my_app.utils import get_relative_datetime, response
from my_app.tasks import process_excel_file
from my_app.models.change_data import ChangeData



class HealthCheckView(APIView):
    def get(self, request):
        # Check database connection
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT 1")
                db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        # Check cache connection
        try:
            cache.set("health_check", "ok", timeout=5)
            if cache.get("health_check") == "ok":
                cache_status = "healthy"
            else:
                cache_status = "unhealthy"
        except Exception:
            cache_status = "unhealthy"

        response_data = {
            "status": (
                "healthy"
                if db_status == "healthy" and cache_status == "healthy"
                else "unhealthy"
            ),
            "database": db_status,
            "cache": cache_status,
            "serviceName": SERVICE_NAME,
            "apiVersion": API_VERSION,
        }
        return response(
            data=response_data,
            message="Health check completed",
            status_code=status.HTTP_200_OK,
        )


class ExcelUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return response(
                message="No file provided",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # openpyxl hỗ trợ .xlsx, không hỗ trợ .xls.
        if Path(uploaded_file.name).suffix.lower() != ".xlsx":
            return response(
                message="Please upload an .xlsx file.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        file_name = default_storage.save(
            f"excel_uploads/{uuid.uuid4().hex}.xlsx",
            uploaded_file,
        )
        try:
            task = process_excel_file.delay(file_name)
        except BrokerError:
            return response(
                data={"fileName": file_name},
                message="File saved, but could not be queued.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return response(
            data={
                "taskId": task.id,
                "fileName": file_name,
            },
            message="File queued for processing",
            status_code=status.HTTP_202_ACCEPTED,
        )

        try:
            workbook = load_workbook(
                uploaded_file,
                read_only=True,
                data_only=True,
            )

        except (BadZipFile, InvalidFileException, OSError, ValueError) as e:
            return response(
                message=f"Error processing Excel file: {str(e)}",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            sheets = {}

            for sheet in workbook.worksheets:
                rows = sheet.iter_rows(values_only=True)
                header_row = next(rows, None)

                if header_row is None:
                    sheets[sheet.title] = []
                    continue

                headers = [
                    str(value).strip() if value is not None else ""
                    for value in header_row
                ]

                named_headers = [header for header in headers if header]

                if len(named_headers) != len(set(named_headers)):
                    raise ValidationError(
                        {"file": f"Sheet '{sheet.title}' có tên cột trùng."}
                    )

                records = []

                for row_number, row in enumerate(rows, start=2):
                    if all(value is None for value in row):
                        continue

                    records.append(
                        {
                            "row": row_number,
                            "data": {
                                header: value
                                for header, value in zip(headers, row)
                                if header
                            },
                        }
                    )

                sheets[sheet.title] = records

        finally:
            workbook.close()

        return response(
            data={"message": "File uploaded successfully", "sheets": sheets},
            status_code=status.HTTP_200_OK,
        )


class ProductPollingCheckView(APIView):
    def get(self, request):
        date_from = get_relative_datetime(
            set_hour=0, set_minute=0, set_second=0, shift_days=-1
        )
        date_to = get_relative_datetime(
            set_day=5, set_hour=0, set_minute=0, set_second=0
        )
        query_params = {
            "updatedFrom": date_from.isoformat(),
            "updatedTo": date_to.isoformat(),
        }
        url = SERVICE_CONFIG.get("product_sync")
        try:
            result = requests.get(
                url,
                params=query_params,
                timeout=(5, 30),
            )
            result.raise_for_status()
            data = result.json()

        except requests.Timeout:
            return response(
                data=None,
                message="Inventory Service phản hồi quá thời gian chờ",
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            )

        created_instances = []
        serializer = ChangeDataSerializer(
            data=data,
            many=True,
            context={
                "created_instances": created_instances,
            },
        )
        serializer.is_valid(raise_exception=False)
        with transaction.atomic():
            serializer.save()

        # Chỉ serialize những bản ghi mới.
        result_serializer = ChangeDataSerializer(
            created_instances,
            many=True,
        )

        return response(
            data=result_serializer.data,
            message="Health check completed",
            status_code=status.HTTP_200_OK,
        )


class ChangeDataView(generics.ListAPIView):
    queryset = ChangeData.objects.order_by('updated_at')
    serializer_class = ChangeDataSerializer

    def list(self, request, *args, **kwargs):
        result = super().list(request, *args, **kwargs)
        return response(data=result.data, message="Change data retrieved successfully")