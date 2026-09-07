"""Stable error types for Account 360 integration failures."""


class Account360IntegrationError(Exception):
    """Base error for failures at an owning-module integration boundary."""


class UnsupportedModuleError(Account360IntegrationError, ValueError):
    """Raised when a request targets a module outside the approved contract set."""


class IntegrationUnavailableError(Account360IntegrationError):
    """Raised when an owning source is unavailable and no authoritative data exists."""


class IntegrationTimeoutError(Account360IntegrationError):
    """Raised when an owning source does not respond within its contract window."""


class StaleDataError(Account360IntegrationError):
    """Raised when a caller explicitly requires data newer than the available projection."""
