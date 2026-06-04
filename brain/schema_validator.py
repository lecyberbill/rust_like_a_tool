# [WFGY] Zone: SAFE | λ: 0.1 | Action: Schema validator checking recipe arguments against registry.json specs

import json
from pathlib import Path

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

class SchemaValidator:
    """
    Validates recipes against the registry definition.
    """
    def __init__(self, registry_path: Path):
        with open(registry_path, "r", encoding="utf-8") as f:
            self.registry = json.load(f)

    def validate_step(self, primitive_name: str, args: dict) -> tuple[bool, str]:
        if primitive_name not in self.registry.get("primitives", {}):
            return False, f"Primitive '{primitive_name}' not defined in registry."

        spec = self.registry["primitives"][primitive_name]
        schema = spec.get("parameters", {})

        if HAS_JSONSCHEMA:
            try:
                jsonschema.validate(instance=args, schema=schema)
                return True, ""
            except jsonschema.ValidationError as e:
                return False, f"Validation error: {e.message}"
        else:
            required = schema.get("required", [])
            properties = schema.get("properties", {})
            
            for req in required:
                if req not in args:
                    return False, f"Missing required parameter: '{req}'"

            for key, val in args.items():
                if key not in properties:
                    return False, f"Unexpected parameter: '{key}'"
                
                expected_type = properties[key].get("type")
                if expected_type == "string" and not isinstance(val, str):
                    return False, f"Parameter '{key}' should be a string, got {type(val).__name__}"
                
                enum_vals = properties[key].get("enum")
                if enum_vals and val not in enum_vals:
                    return False, f"Parameter '{key}' has invalid value '{val}'. Must be one of {enum_vals}"

            return True, ""
