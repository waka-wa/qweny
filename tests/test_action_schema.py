"""Unit tests for action schema validation."""

import json
from jsonschema import validate, ValidationError


ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "click": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 2,
            "maxItems": 2,
        },
        "modifiers": {
            "type": "object",
            "properties": {
                "shift": {"type": "boolean"},
            },
            "required": ["shift"],
        },
        "reason": {"type": "string"},
    },
    "required": ["click", "modifiers", "reason"],
}


def test_valid_action():
    action = {"click": [123, 456], "modifiers": {"shift": False}, "reason": "test"}
    # Should not raise
    validate(instance=action, schema=ACTION_SCHEMA)


def test_invalid_action_missing_field():
    action = {"click": [1, 2], "modifiers": {"shift": False}}
    try:
        validate(instance=action, schema=ACTION_SCHEMA)
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_invalid_action_wrong_type():
    action = {"click": ["x", "y"], "modifiers": {"shift": False}, "reason": "bad"}
    try:
        validate(instance=action, schema=ACTION_SCHEMA)
        assert False, "Expected ValidationError"
    except ValidationError:
        pass