class LinkedInError(Exception):
    """Base error returned by the LinkedIn integration."""


class LinkedInTemporaryError(LinkedInError):
    def __init__(self, message: str, retry_after_seconds: int | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class LinkedInPermanentError(LinkedInError):
    pass
