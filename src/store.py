from time import time
from pathlib import Path

_root = Path('./sram')

def _new_filename() -> (str, Path):
    name = f"{str(time()).replace('.', '_')}.sram"
    return (name, _root / name)

def put(f: 'werkzeug.FileStorage') -> str:
    name, path = _new_filename()
    f.save(str(path))
    return name

def get(filename: str) -> 'file':
    return (_root / filename).open('r')

def index() -> [Path]:
    return (f.name for f in _root.glob('*.sram'))
