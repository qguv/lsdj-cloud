import boto3
from flask import g
from werkzeug.utils import secure_filename
from werkzeug import exceptions

from time import time
from io import BytesIO
from functools import wraps
from tempfile import NamedTemporaryFile

def _new_filename() -> str:
    return f"{str(time()).replace('.', '_')}.sram"

def _check_secure_filename(filename):
    if filename != secure_filename(filename):
        raise exceptions.BadRequest(f"File {filename} is not secure!")
    return filename

def _with_trailing_slash(path):
    if path.endswith('/'):
        return path
    else:
        return path + '/'

def stash(mf: 'binary-opened file') -> NamedTemporaryFile:
    '''Temporarily stash file stream on disk.'''
    tf = NamedTemporaryFile()
    mf.save(tf)
    return tf

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

@memo
def items(path) -> dict(key="boto3.S3.ObjectSummary"):
    path = _with_trailing_slash(path)
    trim = len(path)
    return {obj.key[trim:]: obj for obj in g.bucket.objects.filter(Prefix=path)}

def assert_exists(path, filename: str) -> bool:
    if filename not in items(path):
        raise exceptions.NotFound(f"{path} file {filename} not found")

def assert_unused(path, filename: str) -> bool:
    if filename in items(path):
        raise exceptions.Conflict(f"{path} file {filename} already exists")

def put(path: str, local_path: str, name=None) -> str:
    '''Upload file stream to S3.'''
    if name is None:
        name = _new_filename()
    else:
        # make sure it doesn't already exist
        assert_unused(path, name)

    g.bucket.upload_file(local_path, _with_trailing_slash(path) + _check_secure_filename(name))
    return name

def get_link(path, filename: str) -> 'binary buffer':
    params = dict(
        Bucket=g.bucket.name,
        Key=_with_trailing_slash(path) + _check_secure_filename(filename),
    )
    return g.client.generate_presigned_url('get_object', Params=params, ExpiresIn=60)

def delete(path, filename: str):
    assert_exists(path, _check_secure_filename(filename))
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

def usage(path='') -> int:
    return sum(obj.size for obj in items(path).values())
