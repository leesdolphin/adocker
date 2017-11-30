import docker.constants
import docker.utils

from adocker.utils.contextlib import AsyncContextManager
from adocker.utils.streamed_response import StreamableResponse
from adocker.utis.aiodocker_ext import APIClient


class DockerClient(AsyncContextManager):
    @classmethod
    def from_env(cls,
                 *,
                 timeout=docker.constants.DEFAULT_TIMEOUT_SECONDS,
                 version=None,
                 ssl_version=None,
                 assert_hostname=None,
                 environment=None):
        kwargs = dict(
            timeout=timeout,
            version=version,
        )
        # TODO: port this method.
        env_args = docker.utils.kwargs_from_env(
            ssl_version=ssl_version,
            assert_hostname=assert_hostname,
            environment=environment,
        )
        if 'base_url' in env_args:
            # Rename from `base_url` to `url` for aiodocker
            kwargs['url'] = env_args.pop('base_url')
        if 'tls' in env_args:
            raise NotImplementedError('TLS configuration is not supported.')
        if len(env_args) > 0:
            raise NotImplementedError('Unsupported environment arguments.')
        return cls(
            **kwargs
        )

    def __init__(self, url, **kwargs):
        self.client = APIClient(url=url, **kwargs)

    # TODO: Handlers for images, containers ect.

    def events(self, **params) -> StreamableResponse:
        return self.client._json_stream(
            "events",
            method="GET",
            params=params,
        )

    async def __aexit__(self):
        await self._client.close()
