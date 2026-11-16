"""Exceptions for Jablotron API integration."""


class BadRequestException(Exception):
    """Exception raised when request fails with 400 status code."""


class UnauthorizedException(Exception):
    """Exception raised when request fails with 401 status code."""


class SessionExpiredException(Exception):
    """Exception raised when request fails with 408 status code."""


class JablotronApiException(Exception):
    """Exception raised when request fails with unexpected status code."""


class BadGatewayException(JablotronApiException):
    """Exception raised when request fails with 502 or 504 status code.

    The Jablotron Cloud gateway gave up waiting for the backend, so the requested action may still be applied.
    """


class TooManyRequestsException(JablotronApiException):
    """Exception raised when request fails with 429 status code."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        """Initialize exception with optional retry delay.

        :param message: error message
        :param retry_after: number of seconds to wait before retrying, if provided by the API
        """

        super().__init__(message)
        self.retry_after = retry_after


class InvalidSessionIdException(Exception):
    """Exception raised when login response does not contain a valid session id."""


class NoPinCodeException(Exception):
    """Exception raised when user does not provide pin code and default pin code is also not defined."""


class IncorrectPinCodeException(Exception):
    """Exception raised when provided or default pin code is not valid."""


class ControlActionException(Exception):
    """Exception raised when control action fails with unexpected error code."""
