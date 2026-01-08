"""Exceptions for Jablotron API integration."""


class BadRequestException(Exception):
    """Exception raised when request fails with 400 status code."""


class UnauthorizedException(Exception):
    """Exception raised when request fails with 401 status code."""


class SessionExpiredException(Exception):
    """Exception raised when request fails with 408 status code."""


class JablotronApiException(Exception):
    """Exception raised when request fails with unexpected status code."""


class InvalidSessionIdException(Exception):
    """Exception raised when login response does not contain a valid session id."""


class NoPinCodeException(Exception):
    """Exception raised when user does not provide pin code and default pin code is also not defined."""


class IncorrectPinCodeException(Exception):
    """Exception raised when provided or default pin code is not valid."""


class ControlActionException(Exception):
    """Exception raised when control action fails with unexpected error code."""
