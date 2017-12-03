

class ImageApiMixin(object):

    async def image_history(self, resource_id):
        return self._query_json(
            self._format_url('images/{}/history', resource_id)
        )
