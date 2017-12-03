class DockerException(Exception):

    """
    Serves as a base exception for all exceptions in this library.

    .. todo::
        Ensure this is actually the case given we call into both ``aiodocker``
        and ``docker``
    """


class ChunkedStreamingError(RuntimeError):

    """
    Raised when the end of a stream is not valid.
    """


class DeprecatedInVersion1(DeprecationWarning):

    """
    An attribute or function that to to be removed before reaching version 1.
    """


class AioDockerDeprecationWarning(DeprecatedInVersion1):

    """
    An attribute or function that is kept for ``aiodocker`` compatibility.

    These will eventually be removed to ensure a consistent API
    """
