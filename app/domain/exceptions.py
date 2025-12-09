from abc import ABC


class DomainException(Exception, ABC):
    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message


# Repository exceptions
class RepositoryException(DomainException, ABC):
    pass


class NotFoundError(RepositoryException):
    pass


class DoubleFoundError(RepositoryException):
    pass


# Service exceptions
class ServiceException(DomainException, ABC):
    pass


class ValueException(ServiceException):
    pass


class PermissionException(ServiceException):
    pass


class MessageRouterException(DomainException):
    pass

class UserNotFoundError(MessageRouterException):
    pass
