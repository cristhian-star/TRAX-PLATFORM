"""Local read-tool contracts. Never deserialize actor identity from tool arguments."""
import json
from datetime import date

MAX_INPUT_BYTES = 4096
MAX_OUTPUT_BYTES = 16384


class InvalidInput(ValueError):
    pass


def text_schema(limit, minimum=0):
    return {"type": "string", "minLength": minimum, "maxLength": limit}


PAGE = {"type": "integer", "minimum": 1, "maximum": 1000}
DAY = {"type": "string", "format": "date", "minLength": 10, "maxLength": 10}


def object_schema(properties, required=()):
    return {"type": "object", "additionalProperties": False,
            "properties": properties, "required": list(required)}


INPUT_SCHEMAS = {
    "help.search": object_schema({"query": text_schema(200, 1),
                                  "limit": {"type": "integer", "minimum": 1, "maximum": 3}}, ("query",)),
    "work_records.list": object_schema({"q": text_schema(160), "page": PAGE,
                                        "follow": {"type": "string", "enum": ["all", "with", "without"]}}),
    "work_records.get": object_schema({"record_id": {"type": "integer", "minimum": 1,
                                                    "maximum": 2147483647}}, ("record_id",)),
    "followups.list": object_schema({"from": DAY, "to": DAY, "page": PAGE}),
}


def validate(name, arguments):
    if type(name) is not str or name not in INPUT_SCHEMAS or type(arguments) is not dict:
        raise InvalidInput()
    try:
        size = len(json.dumps(arguments, ensure_ascii=False, allow_nan=False).encode("utf-8"))
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise InvalidInput() from None
    if size > MAX_INPUT_BYTES:
        raise InvalidInput()
    schema = INPUT_SCHEMAS[name]
    if set(arguments) - set(schema["properties"]) or set(schema["required"]) - set(arguments):
        raise InvalidInput()
    for key, value in arguments.items():
        rule = schema["properties"][key]
        if rule["type"] == "integer":
            if type(value) is not int or not rule["minimum"] <= value <= rule["maximum"]:
                raise InvalidInput()
        else:
            if type(value) is not str or not rule.get("minLength", 0) <= len(value) <= rule.get("maxLength", 200):
                raise InvalidInput()
            if "enum" in rule and value not in rule["enum"]:
                raise InvalidInput()
            if rule.get("format") == "date":
                try:
                    if date.fromisoformat(value).isoformat() != value:
                        raise ValueError()
                except ValueError:
                    raise InvalidInput() from None
    if "query" in arguments and not arguments["query"].strip():
        raise InvalidInput()
    if arguments.get("from", "0000") > arguments.get("to", "9999"):
        raise InvalidInput()
    return dict(arguments)


def bounded_text(value, chars, byte_limit=None):
    value = (value or "")[:chars]
    if byte_limit is not None:
        value = value.encode("utf-8")[:byte_limit].decode("utf-8", errors="ignore")
    return value


def required_object(properties):
    return object_schema(properties, properties)


IDENTIFIER = {"type": "integer", "minimum": 1, "maximum": 2147483647}
BOOLEAN = {"type": "boolean"}
NULLABLE_DAY = {"anyOf": [DAY, {"type": "null"}]}
SUMMARY = {"id": IDENTIFIER, "title": text_schema(160), "work_date": DAY,
           "followup_enabled": BOOLEAN, "url": text_schema(512, 1)}


def paginated(item):
    return required_object({"items": {"type": "array", "maxItems": 10, "items": item},
                            "page": PAGE, "has_next": BOOLEAN})


OUTPUT_DATA_SCHEMAS = {
    "help.search": required_object({
        "items": {"type": "array", "maxItems": 3, "items": required_object({
            "id": text_schema(80, 1), "title": text_schema(160, 1), "excerpt": text_schema(800),
            "version": text_schema(40, 1), "source": {"type": "string", "enum": ["work_records"]},
            "url": text_schema(512, 1)})},
        "corpus_version": {"type": "integer", "minimum": 1, "maximum": 1}}),
    "work_records.list": paginated(required_object(SUMMARY)),
    "work_records.get": required_object({**SUMMARY, "notes": text_schema(10000), "notes_truncated": BOOLEAN,
        "followup": required_object({"enabled": BOOLEAN, "reason": text_schema(300),
                                     "tentative_date": NULLABLE_DAY})}),
    "followups.list": paginated(required_object({"record_id": IDENTIFIER, "title": text_schema(160),
        "reason": text_schema(300), "tentative_date": DAY, "url": text_schema(512, 1)})),
}


def conforms(value, rule):
    """Small fail-closed validator for the exact output-schema subset used above."""
    if "anyOf" in rule:
        return any(conforms(value, branch) for branch in rule["anyOf"])
    kind = rule["type"]
    if kind == "null":
        return value is None
    if kind == "boolean":
        return type(value) is bool
    if kind == "integer":
        return type(value) is int and rule["minimum"] <= value <= rule["maximum"]
    if kind == "string":
        if type(value) is not str or not rule.get("minLength", 0) <= len(value) <= rule.get("maxLength", 200):
            return False
        if "enum" in rule and value not in rule["enum"]:
            return False
        if rule.get("format") == "date":
            try:
                return date.fromisoformat(value).isoformat() == value
            except ValueError:
                return False
        return True
    if kind == "array":
        return type(value) is list and len(value) <= rule["maxItems"] and all(conforms(v, rule["items"]) for v in value)
    if kind == "object":
        return (type(value) is dict and not set(value) - set(rule["properties"])
                and not set(rule["required"]) - set(value)
                and all(conforms(v, rule["properties"][k]) for k, v in value.items()))
    return False
