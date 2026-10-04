import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    result = exception_handler(exc, context)

    if result is not None:
        # Giữ nguyên status và headers của DRF.
        result.data = {
            "code": getattr(exc, "default_code", "request_error"),
            "errorMessage": result.data,
        }
        return result

    # Lỗi ngoài dự kiến: ghi chi tiết vào log.
    logger.error(
        "Unhandled API exception",
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return Response(
        {
            "code": "internal_server_error",
            "errorMessage": "An unexpected error occurred.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
