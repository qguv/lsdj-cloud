from subprocess import run
from tempfile import TemporaryDirectory
from pathlib import Path

binpath = './deps/linux-amd64/bin/'
export = binpath + 'lsdsng-export'

def split(sav_path: str) -> TemporaryDirectory:
    d = TemporaryDirectory()
    run([export, '-uo', d.name, sav_path], check=True)

    # remove the unsaved track from working memory
    for working_memory in Path(d.name).glob('*.WM.lsdsng'):
        working_memory.unlink()

    return d

def peek(sav_path):
    res = run([export, '-up', sav_path], check=True, capture_output=True).stdout.decode()
    print(res)
    for song in res.strip().split('\n')[1:]:
        try:
            no = int(song[0:4].strip())
        except ValueError:
            no = None

        name = song[4:13].strip()

        try:
            ver = int(song[13:15].strip(), base=16)
        except ValueError:
            ver = None

        fmt = song[15:18].strip()

        if ver is not None:
            yield (no, name, ver)
