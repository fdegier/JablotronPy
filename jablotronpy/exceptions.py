class BadRequestException(Exception):
    """Exception raised when request fails with 400 status code."""

    pass


class UnauthorizedException(Exception):
    """Exception raised when request fails with 401 status code."""

    pass


class SessionExpiredException(Exception):
    """Exception raised when request fails with 408 status code."""

    pass


class JablotronApiException(Exception):
    """Exception raised when request fails with unexpected status code."""

    pass


class InvalidSessionIdException(Exception):
    """Exception raised when login response does not contain a valid session id."""

    pass


class NoPinCodeException(Exception):
    """Exception raised when user does not provide pin code and default pin code is also not defined."""

    pass


class IncorrectPinCodeException(Exception):
    """Exception raised when provided or default pin code is not valid."""

    pass


class ControlActionException(Exception):
    """Exception raised when control action fails with unexpected error code."""

    pass
