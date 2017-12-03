import collections.abc as abc
import typing as typ

import aiohttp

from .chunked_stream import ChunkedBytesStream, JsonStream
from .contextlib import AsyncContextManager

ResponseType = typ.TypeVar('ResponseType', aiohttp.ClientResponse)
StreamType = typ.TypeVar('StreamType', ChunkedBytesStream)


class StreamableResponse(typ.Generic[ResponseType, StreamType], abc.Awaitable,
                         abc.AsyncIterator, AsyncContextManager):
    """
    A Response to a method that streams blocks of data.

    .. warning::
        This iterator is designed to yield each item one time; meaning sharing
        this instance across multiple loops will cause each loop to recieve a
        subset of the data. Users needing this sort of multiplexing should
        implement it independently.

        This warning also applies to reading from the respone's content as the
        data is streamed.
    """

    def __init__(self,
                 pending_response: typ.Awaitable[ResponseType],
                 stream_class: typ.Type[StreamType] = JsonStream):
        self.pending_response = pending_response
        self.stream_class = stream_class
        self.response = None
        self.stream = None

    async def ready(self) -> None:
        """
        Waits for the response headers to be ready.

        .. warning::
            This method *does not* check the response status code or headers.
        """
        if self.response is None:
            response = await self.pending_response
            # Second check necessary in the event multiple calls to ready are
            # running at once.
            if self.response is None:
                self.response = response
                self.stream = JsonStream(response)
        # TODO: (not in this function) Check response headers.

    async def get_response(self) -> ResponseType:
        """
        Wait for the response headers to be ready and then return the response.

        This is the same response as used internally for iteration.
        """
        await self.ready()
        return self.response

    async def get_stream(self) -> StreamType:
        """
        Wait for the response headers to be ready and then return the stream.

        This is the same stream as used internally for iteration.
        """
        await self.ready()
        return self.stream

    async def complete(self):
        async with self:
            for unused in self:
                pass

    async def as_list(self, n: typ.Optional[int] = None):
        """
        Iterates over the elements in this stream and return them as a list.

        If ``n`` is ``None`` then return a list of all remaining items in the
        stream. Otherwise return a list of at most ``n`` elements; a list of
        less than ``n`` elements indicates the stream ended before reading
        the ``n`` items.

        Note that this element will not exit if this oject represents an
        infinite stream.
        """
        results = []
        stream = self.__aiter__()
        while True:
            if n is not None and len(results) >= n:
                return results
            try:
                item = await stream.__anext__()
            except StopAsyncIteration:
                return results
            results.append(item)

    async def __await__(self):
        async with self:
            return self.as_list()

    async def __aenter__(self):
        await self.ready()
        await self.response.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.ready()
        await self.response.__aexit__(exc_type, exc, tb)

    async def __anext__(self):
        await self.ready()
        return self.stream.__anext__()
