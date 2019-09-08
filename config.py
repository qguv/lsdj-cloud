# delete this line once you've configured this file
assert False, "You must first configure the app in config.py."

secret_key = r''
bucket_name = ''

# passed as kwargs to boto3.resource()
s3 = dict(
    endpoint_url='https://s3.wasabisys.com',
    aws_access_key_id=r'',
    aws_secret_access_key=r'',
)
