"""Eccezioni di dominio condivise dal livello dei servizi.

Vengono tradotte in codici HTTP dal livello API:
- NotFoundError   -> 404
- ForbiddenError  -> 403
- ConflictError   -> 409
- ValidationError -> 400
"""


class ServiceError(Exception):
    pass


class NotFoundError(ServiceError):
    pass


class ForbiddenError(ServiceError):
    pass


class ConflictError(ServiceError):
    pass


class ValidationError(ServiceError):
    pass
