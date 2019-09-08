import boto3
from flask import g
from werkzeug.utils import secure_filename
from werkzeug import exceptions

from time import time
from io import BytesIO
from functools import wraps

def _new_filename() -> str:
    return f"{str(time()).replace('.', '_')}.sram"

def _check_secure_filename(filename):
    if filename != secure_filename(filename):
        raise exceptions.BadRequest(f"File {filename} is not secure!")

def _with_trailing_slash(path):
    if path.endswith('/'):
        return path
    else:
        return path + '/'

def memo(f):
    @wraps(f)
    def wrapping(*args, **kwargs):
        assert not kwargs, "functions accepting kwargs can't be memo'd yet!" # TODO

        if 'memo' not in g:
            g.memo = dict(stats=dict())

        f_memo = g.memo[f] = g.memo.get(f, dict())
        f_stats = g.memo['stats'][f] = g.memo['stats'].get(f, dict(hit=0, miss=0))

        try:
            v = f_memo[args]
            f_stats['hit'] += 1

        except KeyError:
            v = f(*args)
            f_memo[args] = v
            f_stats['miss'] += 1

        print(f"DEBUG\n{f.__name__}: {f_stats}\n")
        return v

    return wrapping

def put(path: str, f: 'binary-opened file') -> str:
    name = _new_filename()
    g.bucket.upload_fileobj(f, _with_trailing_slash(path) + name)
    return name

def get_link(path, filename: str) -> 'binary buffer':
    _check_secure_filename(filename)
    params = dict(
        Bucket=g.bucket.name,
        Key=_with_trailing_slash(path) + filename,
    )
    return g.client.generate_presigned_url('get_object', Params=params, ExpiresIn=60)

@memo
def exists(path, filename: str) -> bool:
    _check_secure_filename(filename)
    query = dict(Prefix=_with_trailing_slash(path) + filename)
    result = g.bucket.objects.filter(**query).limit(1)
    return any(True for _ in result)

def delete(path, filename: str):
    _check_secure_filename(filename)
    if not exists(path, filename):
        raise exceptions.NotFound(f"{path} file {filename} not found")

    response = g.bucket.delete_objects(
        Delete=dict(
            Objects=[
                dict(
                    Key=_with_trailing_slash(path) + filename,
                ),
            ],
        ),
    )
    print(response)

@memo
def _iter(path) -> list(["boto3.S3.ObjectSummary"]):
    return list(g.bucket.objects.filter(Prefix=_with_trailing_slash(path)))

def iter(path) -> list(["filename"]):
    trim = len(_with_trailing_slash(path))
    return [obj.key[trim:] for obj in _iter(path)]

def usage(path='') -> int:
    return sum(obj.size for obj in _iter(path))
