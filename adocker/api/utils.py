import functools
import urllib.parse

PATH_QUOTE = functools.partial(urllib.parse.quote_plus, safe="/:")


class ApiUtilitiesMixin(object):

    def _format_url(self, pathfmt, *args: str, versioned_api: bool=True) -> str:
        """
        Generate a URL by formatting ``pathfmt`` with URL-safe ``args``

        Returns a versioned URL if ``versioned_api`` is ``True``.
        """
        # Coppied from docker-py
        for idx, arg in enumerate(args):
            if not isinstance(arg, str):
                raise ValueError(
                    'Expected a string but found {0} ({1}) at {2} '
                    'instead'.format(arg, type(arg), idx)
                )

        args = map(PATH_QUOTE, args)
        if versioned_api:
            return '{0}/v{1}{2}'.format(
                self.base_url, self.api_version, pathfmt.format(*args)
            )
        else:
            return '{0}{1}'.format(self.base_url, pathfmt.format(*args))
