class StopTask(Exception):
    """Raised to explicitly stop Celery task without retry."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
