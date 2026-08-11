"""Validate all YAML candidates against ontology schemas."""
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print('pyyaml required: pip install pyyaml')
    sys.exit(1)


def validate_candidates():
    candidates_dir = Path(__file__).parent.parent / 'candidates'
    errors = []
    for f in sorted(candidates_dir.glob('*.yaml')):
        if 'destroyer_report' in f.name:
            continue
        with open(f) as fh:
            data = yaml.safe_load(fh)
        if not data:
            errors.append(f'{f.name}: empty file')
            continue
        required = ['id', 'name', 'status']
        for key in required:
            if key not in data:
                errors.append(f'{f.name}: missing {key}')
    if errors:
        for e in errors:
            print(f'ERROR: {e}')
        sys.exit(1)
    print('All candidates valid.')


if __name__ == '__main__':
    validate_candidates()