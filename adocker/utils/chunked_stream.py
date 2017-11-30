import collections.abc
import json
import typing as typ

import aiohttp
import docker.utils.json_stream as stream_utils

from .contextlib import AsyncContextManager
from ..errors import ChunkedStreamingError

T = typ.TypeVar('T')
SplitterReturn = typ.Optional[typ.Tuple[T, typ.Text]]


async def split_buffer(
        stream: typ.AsyncIterable[bytes],
        splitter: typ.Optional[typ.Callable[[typ.Text],
                                            SplitterReturn]] = None,
        decoder: typ.Callable[[typ.Text], T] = lambda a: a,
        encoding: typ.Optional[typ.AnyStr] = 'utf-8') -> typ.AsyncIterable[T]:
    """
    Given an async generator which yields byte-strings and a splitter
    function, will convert the data to a string using ``encoding``; then
    splits the data using ``splitter``, and then yielding the result of
    calling ``decoder`` with the split data.

    .. note::
        ``splitter`` and ``decoder`` should be synchronous functions.
    """
    splitter = splitter or stream_utils.line_splitter
    buffered = ''
    async for data in stream:
        buffered += data
        while True:
            buffer_split = splitter(buffered)
            if buffer_split is None:
                break
            item, buffered = buffer_split
            yield item
    if buffered:
        try:
            yield decoder(buffered)
        except Exception as e:
            raise ChunkedStreamingError() from e


class ChunkedBytesStream(collections.abc.AsyncIterator, AsyncContextManager):
    def __init__(self, response: aiohttp.ClientResponse):
        self.response = response

    async def __aenter__(self):
        await self.response.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.response.__aexit__(exc_type, exc, tb)
        async for unused in self:  # noqa: F841 - Unused variable
            pass

    async def __anext__(self):
        if self.response.at_eof():
            await self.response.close()
            raise StopAsyncIteration
        try:
            chunk_complete = False
            buffer = b''
            while not chunk_complete:
                data, chunk_complete = await self.response.content.readchunk()
                buffer += data
        except aiohttp.ClientPayloadError as e:
            raise ChunkedStreamingError() from e
        return buffer

    async def complete(self):
        items = []
        with self:
            async for item in self:
                items.append(item)
        return items


class ChunkedStream(ChunkedBytesStream):
    async def __anext__(self):
        return bytes.decode(
            await super().__anext__(),
            # Charset can sometimes be none in which case default to utf-8.
            encoding=self.response.charset or 'utf-8',
            errors='replace')


class SplitStream(ChunkedStream):
    """
    An asynchronous iterator over subsets of the stream.
    """

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._buffer = ''

    def splitter(self, buffer: typ.Text) -> typ.Optional[SplitterReturn]:
        """
        Convert a portion of the buffer into the final object and return it.

        .. returns::
            A 2-tuple of the parsed object, and the unused buffer.
        """
        if buffer:
            return buffer[:-2], buffer[-2:]
        else:
            return None

    def decoder(self, buffer: typ.Text) -> T:
        """
        Convert the last portion of the buffer into the final object.

        This will only be called once the :class:`ChunkedStream` indicates the
        end of the stream *and* :meth:`splitter` returns ``None`` *and* there
        is data still in the buffer(i.e. ``len(buffer) > 0``)
        """
        return buffer

    async def __anext__(self):
        end_of_stream = False
        while True:
            buffer_split = self.splitter(self._buffer)
            if buffer_split is not None:
                item, new_buffer = buffer_split
                self._buffer = new_buffer
                return item
            elif buffer_split is None and end_of_stream:
                if self._buffer:
                    self._buffer, tmp_buf = '', self._buffer
                    try:
                        return self.decoder(tmp_buf)
                    except Exception as e:
                        raise ChunkedStreamingError() from e
                raise StopAsyncIteration
            try:
                self._buffer += await super().__anext__()
            except StopAsyncIteration:
                end_of_stream = True


class JsonStream(SplitStream):
    def __init__(self,
                 *a,
                 decoder_cls: typ.Type[json.JSONDecoder] = json.JSONDecoder,
                 **k):
        super().__init__(*a, **k)
        self._decoder = decoder_cls()

    def splitter(
            self, buffer: typ.Text
    ) -> typ.Optional[typ.Tuple[typ.Dict[str, typ.Any], typ.Text]]:
        """
        Decode the partial JSON object and return it.
        """
        buffer = buffer.strip()
        try:
            obj, index = self._decoder.raw_decode(buffer)
            rest = buffer[json.decoder.WHITESPACE.match(buffer, index).end():]
            return obj, rest
        except ValueError:
            return None

    def decoder(self, buffer: typ.Text) -> typ.Dict[str, typ.Any]:
        return self._decoder.decode(buffer)
