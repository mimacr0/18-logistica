from marshmallow import Schema, fields, ValidationError


class SchemaValidator:
    def __init__(self, schema: Schema):
        self.schema = schema

    def validate(self, data: dict):
        try:
            self.schema.load(data)
            return True, None
        except ValidationError as e:
            return False, e.messages
