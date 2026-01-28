from __future__ import annotations


class DomainError(Exception):
    status_code: int = 400
    code: str = "domain_error"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class UnauthorizedError(DomainError):
    status_code: int = 401
    code: str = "unauthorized"


class ForbiddenError(DomainError):
    status_code: int = 403
    code: str = "forbidden"


class NotFoundError(DomainError):
    status_code: int = 404
    code: str = "not_found"


class ConflictError(DomainError):
    status_code: int = 409
    code: str = "conflict"


