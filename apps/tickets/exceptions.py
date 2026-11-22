from rest_framework.response import Response
from rest_framework.views import exception_handler


class ServiceError(Exception):
    """Error de negocio con status HTTP asociado (lo lanzan los services, sin conocer HTTP)."""

    status_code = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class InvalidTransition(ServiceError):
    status_code = 409


class NotAllowed(ServiceError):
    status_code = 403


class BusinessValidationError(ServiceError):
    status_code = 400


class RateLimited(ServiceError):
    status_code = 429


def api_exception_handler(exc, context):
    if isinstance(exc, ServiceError):
        return Response({"detail": exc.detail}, status=exc.status_code)
    return exception_handler(exc, context)
