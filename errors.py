class AppError(Exception):
    """Base application exception."""
    pass


class ValidationError(AppError):
    """Raised when user input violates validation rules."""
    pass


class RuleError(AppError):
    """Raised when business logic or workflow constraints are violated."""
    pass


class StorageError(AppError):
    """Raised when file I/O or data integrity issues occur."""
    pass
