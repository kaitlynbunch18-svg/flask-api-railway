from marshmallow import Schema, fields, validate, EXCLUDE

class ProductPayloadSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    idempotency_key = fields.String(required=True, validate=validate.Length(min=1))
    sku = fields.String(required=False)
    title = fields.String(required=True, validate=validate.Length(min=3))
    description = fields.String(required=False, allow_none=True)
    metadata = fields.Dict(required=False, allow_none=True)
    images = fields.List(fields.Url(), required=False, allow_none=True)
    price = fields.Integer(required=False, allow_none=True)   # cents
    cost = fields.Integer(required=False, allow_none=True)
    source = fields.String(required=False, validate=validate.Length(max=128))
