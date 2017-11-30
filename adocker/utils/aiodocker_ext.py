import aiodocker

from adocker.utils.streamed_response import StreamableResponse


class APIClient(aiodocker.Docker):

    def _json_stream(self, url, **kwargs) -> StreamableResponse:

        # `timeout` has to be set to 0, otherwise after 5 minutes the client
        # will close the connection
        # http://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientSession.request
        kwargs.update(timeout=0)
        return StreamableResponse(self._query(
            url,
            **kwargs
        ))
