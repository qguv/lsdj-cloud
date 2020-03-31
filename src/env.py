from os import environ
from sys import exit

def env2dict(**conf_map):
    d = {}
    for env_key, conf in conf_map.items():
        try:
            v = environ[env_key]
        except KeyError:
            continue

        if isinstance(conf, tuple):
            conf_key, fn, msg = conf
            try:
                v = fn(v)
            except ValueError:
                print(msg)
                exit(1)
        else:
            conf_key = conf

        d[conf_key] = v
    return d

def redis_config():
    return env2dict(
        REDIS_SOCKET='unix_socket_path',
        REDIS_HOST='host',
        REDIS_PORT=('port', int, 'REDIS_PORT must be numeric!'),
        REDIS_PASSWORD='password',
    )

def store_config():
    return env2dict(
        S3_BUCKET='s3_bucket',
        S3_URL='s3_url',
        S3_KEY_ID='s3_key_id',
        S3_SECRET='s3_secret',
    )

def inject_flask_secret(app):
    app.secret_key = environ['SECRET_KEY']
