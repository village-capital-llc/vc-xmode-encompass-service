
import paramiko
import uuid
from tenacity import retry, stop_after_attempt, wait_fixed
from loguru import logger

@retry(stop=stop_after_attempt(3), reraise=True, wait=wait_fixed(5))
def transfer_file_to_archive(secrets_dict, source_path):
    
    """
        Function: Move file from Outout folder to Archive in SFTP 
    """

    # source_path = "Output/0153447586/0153447586_e28a312e-b34f-4354-b23b-618683bf3e41.json"
    # destination_path = "Archive/67024053331/67024053331_d4594323-5684-4392-ba58-28933efac8f7.json"    
    
    
    try:
        
        SFTP_HOST = secrets_dict['SFTP_HOST']
        SFTP_PORT = secrets_dict['SFTP_PORT']
        SFTP_USERNAME = secrets_dict['SFTP_USERNAME']
        SFTP_PRIVATE_KEY = secrets_dict['SFTP_KEY']
        
        transport = paramiko.Transport((SFTP_HOST, int(SFTP_PORT)))
            
        # print(f"USERNMAE: {SFTP_USERNAME}")
        transport.connect(username=SFTP_USERNAME, password=SFTP_PRIVATE_KEY)
        
        sftp = paramiko.SFTPClient.from_transport(transport)
        logger.info("SFTP connection is stablished")
    
        json_path = source_path.split('/', 1)[-1]
        destination_path = "Archive/" + json_path
        
        guid = uuid.uuid4()
        destination_path = destination_path.replace(".", "-guid-" + str(guid)+".")            
            
        sftp.rename(source_path, destination_path)
        logger.info(f"Moved {source_path} to {destination_path} Success")
        
        transport.close()
        
    except Exception as exc:
        logger.info(f"Exception: {exc}")
        logger.info(f"Unable to move to Archive folder {source_path}")
            