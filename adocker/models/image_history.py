import typing as typ

from .resource import attribute_value, Model
from ..utils.utils import as_aware_datetime

class ImageParent(Model):

    created = attribute_value('Created', type=int)
    created_date = attribute_value('Created', type=datetime.datetime, convert=as_aware_datetime)
    created_by = attribute_value('CreatedBy', type=str)
    tags = attribute_value('Tags', default=tuple(), type=typ.Sequence[str], convert=tuple)
    size = attribute_value('Size', type=int)
    comment = attribute_value('Comment', type=str)

    async def image(self) -> "adocker.images.Image":
        return self.collection.get(self.id)
