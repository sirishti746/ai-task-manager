class AIServiceError(Exception):
    """The AI provider failed or returned something unusable.
    The API layer turns this into a 502 Bad Gateway."""


class AIConfigurationError(AIServiceError):
    """The AI feature is not configured (for example, no API key).
    The API layer turns this into a 503 Service Unavailable.
    It is a subclass of AIServiceError, so catch it FIRST."""