"""Define package errors."""


class AstroWeatherError(Exception):
    """Define a base error."""

    pass


class RequestError(AstroWeatherError):
    """Define an error related to invalid requests."""

    pass


class ResultError(AstroWeatherError):
    """Define an error related to the result returned from a request."""

    pass


class MetnoError(Exception):
    """Generic Metno exception."""
    

class MetnoConnectionError(MetnoError):
    """Metno connection exception."""

    
class OpenMeteoError(Exception):
    """Generic OpenMeteo exception."""


class OpenMeteoConnectionError(OpenMeteoError):
    """OpenMeteo connection exception."""
