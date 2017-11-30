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
