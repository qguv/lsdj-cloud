from os import environ
from sys import exit


def _str(k):
    try:
        yield environ[k]
    except KeyError:
        raise ValueError(f"environment variable {k} must be present")


def _maybe_str(k):
    yield environ.get(k)


def _truthy_str(k, msg=None):
    v = environ[k]
    if v:
        yield v
    else:
        raise ValueError(f"environment varible {k} must be set")


def _int(k):
    try:
        yield int(next(_str(k)))
    except ValueError:
        raise ValueError(f"environment variable {k} must be an integer")


def _maybe_int(k):
    try:
        yield int(environ[k])
    except KeyError:
        yield None
    except ValueError:
        raise ValueError(f"environment variable {k} must be an integer")


def env2dict(**conf_map):
    d = {}
    doomed = False
    for k, gen in conf_map.items():
        try:
            d[k] = next(gen)
        except ValueError as e:
            doomed = True
            print(str(e))
            continue

    if doomed:
        exit(1)
    else:
        return d


def redis_config():
    return env2dict(
        unix_socket_path=_maybe_str('REDIS_SOCKET'),
        host=_maybe_str('REDIS_HOST'),
        port=_maybe_int('REDIS_PORT'),
        password=_maybe_str('REDIS_PASSWORD'),
    )


def store_config():
    return env2dict(
        s3_bucket=_maybe_str('S3_BUCKET'),
        s3_url=_maybe_str('S3_URL'),
        s3_key_id=_maybe_str('S3_KEY_ID'),
        s3_secret=_maybe_str('S3_SECRET'),
    )


def auth_config():
    return env2dict(
        token_ttl=_int('TOKEN_TTL'),
    )


def flask_config():
    return env2dict(
        SECRET_KEY=_str('SECRET_KEY'),
        SQLALCHEMY_DATABASE_URI=_str('DATABASE_URI'),
    )
