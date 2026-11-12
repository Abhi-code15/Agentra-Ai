"""Custom application exceptions and error mappings."""
from typing import Any, List, Optional


class AgentraException(Exception):
    """Base exception for all domain and service exceptions."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[List[Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class NotFoundException(AgentraException):
    def __init__(self, code: str, message: str, details: Optional[List[Any]] = None):
        super().__init__(code=code, message=message, status_code=404, details=details)


class UnauthorizedException(AgentraException):
    def __init__(self, code: str, message: str, details: Optional[List[Any]] = None):
        super().__init__(code=code, message=message, status_code=401, details=details)


class ForbiddenException(AgentraException):
    def __init__(self, code: str, message: str, details: Optional[List[Any]] = None):
        super().__init__(code=code, message=message, status_code=403, details=details)


class ConflictException(AgentraException):
    def __init__(self, code: str, message: str, details: Optional[List[Any]] = None):
        super().__init__(code=code, message=message, status_code=409, details=details)


class ValidationException(AgentraException):
    def __init__(self, code: str, message: str, details: Optional[List[Any]] = None):
        super().__init__(code=code, message=message, status_code=422, details=details)


class ExternalServiceException(AgentraException):
    def __init__(self, code: str, message: str, details: Optional[List[Any]] = None):
        super().__init__(code=code, message=message, status_code=502, details=details)
