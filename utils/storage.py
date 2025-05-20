import paramiko
import json
import os
from tenacity import retry, stop_after_attempt, wait_fixed
from loguru import logger


def get_pdf_from_sftp(file_path, secrets_dict):
    file_content = None
    file_size = 0

    SFTP_HOST = secrets_dict['SFTP_HOST']
    SFTP_PORT = secrets_dict['SFTP_PORT']
    SFTP_USERNAME = secrets_dict['SFTP_USERNAME']
    SFTP_PRIVATE_KEY = secrets_dict['SFTP_KEY']
    
    transport = paramiko.Transport((SFTP_HOST, int(SFTP_PORT)))
        
    # print(f"USERNMAE: {SFTP_USERNAME}")
    transport.connect(username=SFTP_USERNAME, password=SFTP_PRIVATE_KEY)
    
    sftp = paramiko.SFTPClient.from_transport(transport)
    print("SFTP connection is stablished")
    
    f_obj = None
    with sftp.open(file_path, 'r') as f:
        file_content = f.read()
        f_obj = f
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

    transport.close()
    
    return file_content, file_size, f_obj
    

@retry(stop=stop_after_attempt(3), reraise=True, wait=wait_fixed(5))    
def get_pdfjson_from_sftp(output_path, secrets_dict):
    SFTP_HOST = secrets_dict['SFTP_HOST']
    SFTP_PORT = secrets_dict['SFTP_PORT']
    SFTP_USERNAME = secrets_dict['SFTP_USERNAME']
    SFTP_PRIVATE_KEY = secrets_dict['SFTP_KEY']
    
    try:

        transport = paramiko.Transport((SFTP_HOST, int(SFTP_PORT)))
        
        # print(f"USERNMAE: {SFTP_USERNAME}")
        transport.connect(username=SFTP_USERNAME, password=SFTP_PRIVATE_KEY)
        
        sftp = paramiko.SFTPClient.from_transport(transport)
        logger.info("SFTP connection is stablished output path {output_path}")
        json_data = None

        with sftp.open(f'{output_path}', 'r') as f:
            file_content = f.read()
            # print(file_content)
            json_data = json.loads(file_content.decode('utf-8'))
            
            logger.info(f'sftp json_data {json.dumps(json_data)}')
            
    except Exception as e:
        logger.info(e)
        raise Exception('Unable to load json file from sftp path')

    transport.close()
    
    if json_data is None:
        raise Exception(f'Invalid json data in output_path: {output_path}')
    
    return json_data