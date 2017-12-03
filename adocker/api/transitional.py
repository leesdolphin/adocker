import warnings

from ..errors import AioDockerDeprecationWarning


class AioDockerTransitionalDeprecationMixin(object):
    @property
    def docker_host(self) -> str:
        """
        This property is deprecated. Please use ``.base_url``.
        """
        warnings.warn(
            "Accessing `.docker_host` is deprecated. Use `.base_url`",
            AioDockerDeprecationWarning)
        return self.base_url

    @docker_host.setter
    def docker_host(self, value: str):
        """
        This property is deprecated. Please use ``.base_url``.
        """
        warnings.warn("Setting `.docker_host` is deprecated. Use `.base_url`",
                      AioDockerDeprecationWarning)
        self.base_url = value

    @property
    def api_version(self) -> str:
        """
        The API version used during requests.

        This is *not* the Docker Engine version. Please use :func:`version` to
        retrieve that.

        .. note::
            This value must not start with a ``'v'``. Doing so will raise a
            deprecation warning.
        """
        return self._api_version

    @api_version.setter
    def api_version(self, version: str):
        if version[0] == 'v':
            warnings.warn(
                'Setting `.api_version` a "v..." string is deprecated.'
                ' Remove the "v" prefix.',
                AioDockerDeprecationWarning)
            version = version[1:]
        self._api_version = version
