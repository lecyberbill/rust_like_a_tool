"""Regenere la documentation des primitives depuis registry.json."""
import json
from pathlib import Path

with open('brain/registry.json', encoding='utf-8') as f:
    reg = json.load(f)

prims = reg['primitives']
out = Path('docs/primitives')
out.mkdir(parents=True, exist_ok=True)

idx = ['# Primitives WFGY-Core V3', '', f'{len(prims)} primitives.', '']

for name in sorted(prims.keys()):
    s = prims[name]
    desc = s.get('description', '')
    params = s.get('parameters', {}).get('properties', {})
    required = s.get('parameters', {}).get('required', [])
    lines = [f'# {name}', '', f'_{desc}_', '']
    if params:
        lines.append('## Parametres'); lines.append('')
        lines.append('| Parametre | Type | Requis | Defaut | Description |')
        lines.append('|-----------|------|--------|--------|-------------|')
        for pn, ps in params.items():
            enum = ps.get('enum')
            extra = ' (' + ', '.join(enum) + ')' if enum else ''
            lines.append(f'| {pn} | {ps.get("type", "string")} | {"**Oui**" if pn in required else "Non"} | {ps.get("default", "\u2014")} | {ps.get("description", "")}{extra} |')
    lines.append('')
    safe = name.replace('.', '_')
    (out / f'{safe}.md').write_text('\n'.join(lines), encoding='utf-8')
    idx.append(f'- [{name}](primitives/{safe}.md) — {desc[:80]}')

Path('PRIMITIVE_REFERENCE.md').write_text('\n'.join(idx), encoding='utf-8')
print(f'Genere: {len(prims)} fichiers dans docs/primitives/')
