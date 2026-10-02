"""Domain errors raised by the shop services.

Views translate these into user facing messages; they must never be swallowed
by a blanket ``except Exception``.
"""


class ShopServiceError(Exception):
    """Base class for every recoverable shop error."""


class InvalidQuantityError(ShopServiceError):
    """The submitted quantity is missing or not a positive integer."""


class ProductUnavailableError(ShopServiceError):
    """The product cannot be ordered (unavailable or out of stock)."""


class OutOfStockError(ShopServiceError):
    """The requested quantity exceeds the remaining stock."""


class InsufficientStockError(ShopServiceError):
    """Stock changed between adding to the cart and checking out."""
