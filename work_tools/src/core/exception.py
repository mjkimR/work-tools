class TokenRetrievalError(Exception):
    """Raised when auth token cannot be retrieved from Chrome."""

    pass


class TokenExpiredError(Exception):
    """Raised when an API request fails due to an expired or invalid auth token.

    The user must refresh the session in the browser manually.
    """

    pass
