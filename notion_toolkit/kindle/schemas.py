from datetime import datetime
from marshmallow import Schema, fields, post_load


class ClippingSchema(Schema):
    document = fields.Dict()
    metadata = fields.Dict()
    content = fields.Str()

    @post_load
    def make_highlight(self, data, **kwargs):
        created_at = datetime.fromisoformat(data["metadata"]["timestamp"])

        return dict(
            kindle_reference_title=data["document"]["title"],
            location=data["metadata"]["location"]["begin"],
            created_at=created_at,
            uid=str(created_at.timestamp()),
            content=data["content"]
        )