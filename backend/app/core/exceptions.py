"""Custom application exceptions and error mappings."""
from typing import Any, List, Optional


class AgentraException(Exception):
    """Base exception for all domain and service exceptions."""

    def __init__(
        self,
        code: str = "AGENTRA_ERROR",
        message: str = "An error occurred.",
        status_code: int = 400,
        details: Optional[List[Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class NotFoundException(AgentraException):
    def __init__(self, message: str = "Resource not found", code: str = "RESOURCE_NOT_FOUND", details: Optional[List[Any]] = None):
        # Support both (code, message) and (message) signatures
        if code != "RESOURCE_NOT_FOUND" and " " in code and not " " in message:
            code, message = message, code
        super().__init__(code=code, message=message, status_code=404, details=details)


class UnauthorizedException(AgentraException):
    def __init__(self, message: str = "Unauthorized", code: str = "UNAUTHORIZED", details: Optional[List[Any]] = None):
        if code != "UNAUTHORIZED" and " " in code and not " " in message:
            code, message = message, code
        super().__init__(code=code, message=message, status_code=401, details=details)


class ForbiddenException(AgentraException):
    def __init__(self, message: str = "Forbidden", code: str = "FORBIDDEN", details: Optional[List[Any]] = None):
        if code != "FORBIDDEN" and " " in code and not " " in message:
            code, message = message, code
        super().__init__(code=code, message=message, status_code=403, details=details)


class ConflictException(AgentraException):
    def __init__(self, message: str = "Resource conflict", code: str = "CONFLICT", details: Optional[List[Any]] = None):
        if code != "CONFLICT" and " " in code and not " " in message:
            code, message = message, code
        super().__init__(code=code, message=message, status_code=409, details=details)


class ValidationException(AgentraException):
    def __init__(self, message: str = "Validation failed", code: str = "VALIDATION_ERROR", details: Optional[List[Any]] = None):
        if code != "VALIDATION_ERROR" and " " in code and not " " in message:
            code, message = message, code
        super().__init__(code=code, message=message, status_code=422, details=details)


class BusinessRuleException(AgentraException):
    def __init__(self, message: str = "Business rule violated", code: str = "BUSINESS_RULE_VIOLATION", details: Optional[List[Any]] = None):
        super().__init__(code=code, message=message, status_code=400, details=details)


class ExternalServiceException(AgentraException):
    def __init__(self, message: str = "External service error", code: str = "EXTERNAL_SERVICE_ERROR", details: Optional[List[Any]] = None):
        if code != "EXTERNAL_SERVICE_ERROR" and " " in code and not " " in message:
            code, message = message, code
        super().__init__(code=code, message=message, status_code=502, details=details)
