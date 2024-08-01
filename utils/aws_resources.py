import boto3
import io
import json
from .constants import S3_INPUT_BUCKET_NAME, AWS_REGION_NAME, AWS_SECRET_NAME, ENCOMPASS_API_SERVER, ENCOMPASS_INSTANCE_ID, ENCOMPASS_API_USER_CLIENT_ID, ENCOMPASS_API_USER_CLIENT_SECRET, AWS_SQS_QUEUE


def get_pdf_from_storage(file_path, S3_INPUT_BUCKET_NAME):

    fileObj = None
    file_obj_io = None
    size = None

    try:
        s3 = boto3.resource('s3', region_name=AWS_REGION_NAME)
        s3_client = boto3.client('s3', region_name=AWS_REGION_NAME)

        obj = s3.Object(S3_INPUT_BUCKET_NAME, file_path)
        data = io.BytesIO()
        obj.download_fileobj(data)
        fileObj = data.getvalue()
        file_obj_io = data
        
        response = s3_client.head_object(Bucket=S3_INPUT_BUCKET_NAME, Key=file_path)
        size = response['ContentLength']

    except Exception as e:
        print(e)
        fileObj = None
        size = None

    return fileObj, file_obj_io, size


def _get_secrets_from_env():
    text_secret_data = {}
    text_secret_data['ENCOMPASS_API_SERVER'] = ENCOMPASS_API_SERVER
    text_secret_data['ENCOMPASS_INSTANCE_ID'] = ENCOMPASS_INSTANCE_ID
    text_secret_data['ENCOMPASS_API_USER_CLIENT_ID'] = ENCOMPASS_API_USER_CLIENT_ID
    text_secret_data['ENCOMPASS_API_USER_CLIENT_SECRET'] = ENCOMPASS_API_USER_CLIENT_SECRET

    return text_secret_data


def get_secrets():

    text_secret_data = None
    secret_name = AWS_SECRET_NAME
    region_name = AWS_REGION_NAME

    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name,
        )

        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )

        if 'SecretString' in get_secret_value_response:
            text_secret_data = get_secret_value_response['SecretString']
        else:
            # binary_secret_data = get_secret_value_response['SecretBinary']
            text_secret_data = None
    except Exception as e:
        print(f'AWS boto3 exception: {e}')
        text_secret_data = _get_secrets_from_env()

    text_secret_dict = json.loads(text_secret_data)
    
    return text_secret_dict


# print(AWS_SQS_QUEUE)
sqs = boto3.resource('sqs')
queue = sqs.get_queue_by_name(QueueName=AWS_SQS_QUEUE)

def send_msg_sqs(msg_json):
    response = queue.send_message(MessageBody=msg_json)

    return response.get('MessageId')
