"""Domain exceptions."""


class NotificationError(Exception):
    """Base notification error."""
    pass


class NotificationNotFoundError(NotificationError):
    """Notification not found."""
    pass


class EmailSendError(NotificationError):
    """Failed to send email."""
    pass
