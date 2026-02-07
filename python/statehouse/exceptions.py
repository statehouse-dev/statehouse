"""
Exceptions for Statehouse SDK
"""


class StatehouseError(Exception):
    """Base exception for Statehouse errors"""

    pass


class TransactionError(StatehouseError):
    """Transaction-related errors"""

    pass


class NotFoundError(StatehouseError):
    """Resource not found"""

    pass


class ConnectionError(StatehouseError):
    """Connection to daemon failed"""

    pass
