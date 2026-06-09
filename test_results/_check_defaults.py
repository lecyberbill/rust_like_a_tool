import json
r = json.load(open("brain/registry.json"))
for p, v in r.get("primitives", {}).items():
    props = v.get("parameters", {}).get("properties", {})
    defaults = {k: v["default"] for k, v in props.items() if "default" in v}
    if defaults:
        print(f"{p}: defaults={defaults}")
