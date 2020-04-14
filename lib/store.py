from .memo import memo

import boto3
from werkzeug.utils import secure_filename
from werkzeug import exceptions

from time import time
from tempfile import NamedTemporaryFile


def _new_filename() -> str:
    return f"{str(time()).replace('.', '_')}.sram"


def _check_secure_filename(filenames: str or list([str])):
    if isinstance(filenames, str):
        _check_secure_filename([filenames])
        return filenames

    for filename in filenames:
        if filename != secure_filename(filename):
            raise exceptions.BadRequest(f"File {filename} is not secure!")
    return filenames


def _with_trailing_slash(path):
    if path.endswith('/'):
        return path
    else:
        return path + '/'


class Store:
    def __init__(self, s3_bucket, s3_url, s3_key_id, s3_secret):
        config = dict(
            endpoint_url=s3_url,
            aws_access_key_id=s3_key_id,
            aws_secret_access_key=s3_secret,
        )

        self.s3 = boto3.resource('s3', **config)
        self.client = boto3.client('s3', **config)
        self.bucket = self.s3.Bucket(s3_bucket)

    @staticmethod
    def stash(mf: 'binary-opened file') -> NamedTemporaryFile:  # noqa: F722
        '''Temporarily stash file stream on disk.'''
        tf = NamedTemporaryFile()
        mf.save(tf.name)
        return tf

    @memo
    def items(self, path) -> dict(name="boto3.S3.ObjectSummary"):
        path = _with_trailing_slash(path)
        trim = len(path)
        return {
            obj.key[trim:]: obj
            for obj in self.bucket.objects.filter(Prefix=path)
        }

    def assert_exists(self, path, filenames: str or [str]) -> bool:
        if isinstance(filenames, str):
            filenames = [filenames]

        dir = self.items(path)
        for filename in filenames:
            if filename not in dir:
                raise exceptions.NotFound(f"{path} file {filename} not found")

    def new_files(self, path, filenames: [str]) -> [str]:
        dir = self.items(path)
        for filename in filenames:
            if filename not in dir:
                yield filename

    def put(self, path: str, local_path: str, name=None) -> str:
        '''Upload file stream to S3.'''
        if name is None:
            name = _new_filename()
        else:
            # make sure it doesn't already exist
            if not any(self.new_files(path, [name])):
                raise exceptions.Conflict(f"{path} file {name} already exists")

        self.bucket.upload_file(
            local_path,
            _with_trailing_slash(path) + _check_secure_filename(name),
        )
        return name

    def get_link(self, path, filename: str) -> 'binary buffer':  # noqa: F722
        params = dict(
            Bucket=self.bucket.name,
            Key=_with_trailing_slash(path) + _check_secure_filename(filename),
        )
        return self.client.generate_presigned_url(
            'get_object',
            Params=params,
            ExpiresIn=60,
        )

    def delete(self, path, filenames=None):
        if filenames is None:
            filenames = ['']
        elif isinstance(filenames, str):
            filenames = [filenames]

        path = _with_trailing_slash(path)
        self.assert_exists(path, _check_secure_filename(filenames))
        response = self.bucket.delete_objects(
            Delete=dict(
                Objects=[dict(Key=path + filename) for filename in filenames],
            ),
        )
        print(response)

    def usage(self, path='') -> int:
        return sum(obj.size for obj in self.items(path).values())
