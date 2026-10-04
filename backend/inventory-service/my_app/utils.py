from rest_framework import status
from rest_framework.response import Response


def response(
    *,
    data=None,
    message='Success',
    errors=None,
    status_code=status.HTTP_200_OK,
):
    if status_code >= 400:
        body = {
            'code': status_code,
            'errorMessage': message,
        }

        if errors is not None:
            body['errors'] = errors
    else:
        body = data

    return Response(data=body, status=status_code)
