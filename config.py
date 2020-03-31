# delete this line once you've configured this file
assert False, "You must first configure the app in config.py."

# flask secret key: set to a long random string
secret_key = r''

valid_token = r'' # DEBUG
token_ttl = 3600 # seconds

# S3 bucket used to store files
bucket_name = ''

# passed as kwargs to boto3.resource()
s3 = dict(
    endpoint_url='https://s3.wasabisys.com',
    aws_access_key_id=r'',
    aws_secret_access_key=r'',
)

redis = dict(
    unix_socket_path='/run/redis/redis.sock',
    decode_responses=True,
)
