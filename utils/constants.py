import os
# from dotenv import load_dotenv


# load_dotenv()


S3_INPUT_BUCKET_NAME = os.getenv('S3_INPUT_BUCKET_NAME')
AWS_REGION_NAME = os.getenv('AWS_REGION_NAME', 'us-west-2')
AWS_SECRET_NAME = os.getenv('AWS_SECRET_NAME', 'prod/vc_xmode_encompass_service')
ENCOMPASS_USERNAME = os.getenv('ENCOMPASS_USERNAME')
ENCOMPASS_PASSWORD = os.getenv('ENCOMPASS_PASSWORD')
ENCOMPASS_API_SERVER = os.getenv('ENCOMPASS_API_SERVER')
ENCOMPASS_INSTANCE_ID = os.getenv('ENCOMPASS_INSTANCE_ID')
ENCOMPASS_API_USER_CLIENT_ID = os.getenv('ENCOMPASS_API_USER_CLIENT_ID')
ENCOMPASS_API_USER_CLIENT_SECRET = os.getenv('ENCOMPASS_API_USER_CLIENT_SECRET')
AWS_SQS_QUEUE = os.getenv('AWS_SQS_QUEUE', 'vc_xmode_encompass_queue_prod')