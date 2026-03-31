from sqlalchemy import Integer, BigInteger, String, Text, DateTime
from models import db


def sa_type_to_openapi(column):
    t = column.type
    if isinstance(t, (Integer, BigInteger)):
        return {"type": "integer"}
    if isinstance(t, DateTime):
        return {"type": "string", "format": "date-time"}
    return {"type": "string"}


def model_schema(model, only_fillable=False):
    props = {}
    required = []

    fillable = getattr(model, '__fillable__', set())

    for col in model.__table__.columns:
        if only_fillable and col.name not in fillable:
            continue

        props[col.name] = sa_type_to_openapi(col)

        if not col.nullable and col.default is None:
            required.append(col.name)

    schema = {
        "type": "object",
        "properties": props
    }

    if required:
        schema["required"] = required

    return schema


def crud_paths(model, url_prefix):
    name = model.__tablename__
    pk = model.primary_key()

    return {
        f"{url_prefix}/": {
            "get": {
                "summary": f"List {name}",
                "responses": {"200": {"description": "OK"}}
            },
            "post": {
                "summary": f"Create {name}",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": model_schema(model, only_fillable=True)
                        }
                    }
                },
                "responses": {"201": {"description": "Created"}}
            }
        },
        f"{url_prefix}/{{id}}": {
            "get": {
                "summary": f"Get {name} by ID",
                "parameters": [
                    {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                ],
                "responses": {"200": {"description": "OK"}}
            },
            "put": {
                "summary": f"Update {name}",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": model_schema(model, only_fillable=True)
                        }
                    }
                },
                "responses": {"200": {"description": "Updated"}}
            },
            "delete": {
                "summary": f"Delete {name}",
                "responses": {"200": {"description": "Deleted"}}
            }
        }
    }
