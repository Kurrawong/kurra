class FusekiError(Exception):
    """An error that occurred while interacting with Fuseki."""

    def __init__(self, message_context: str, message: str, status_code: int) -> None:
        self.message = f"{status_code} {message_context}. {message}"
        super().__init__(self.message)
