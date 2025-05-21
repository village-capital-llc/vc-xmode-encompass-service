from loguru import logger
from utils.aws_resources import get_pdf_from_storage, get_secrets, send_msg_sqs
from utils.misc import get_file_metadata, get_pdf_from_local_storage, load_dash_efolder_mapping, find_efolder_mapping_id
from utils.exp_apis import _get_access_token as GET_ACCESS_TOKEN
from utils.exp_apis import _get_loan_guid as GET_LOAN_GUID
from utils.exp_apis import get_all_retrieve_documents, create_new_document
from utils.storage import get_pdf_from_sftp, get_pdfjson_from_sftp
from utils.sftp_file_transfer import transfer_file_to_archive
from utils.ses_notifications import send_ses_message
from utils.db_helper import get_oldest_record, update_process_status
import urllib.parse
import json
import threading

def main(event, context):
    # log input event

    # get input json sftp path
    logger.info(f"event {event}")
    try:
        json_file_path = event['detail']['object']['key']
    except Exception as e:
        raise Exception('Invalid input json path')
    
    # Load secrets values
    secrets_dict = get_secrets()  
    AUDIT_LOG_TABLE_NAME = secrets_dict['AUDIT_LOG_TABLE_NAME']

    # read input json file from sftp        
    json_pdf_data = get_pdfjson_from_sftp(json_file_path, secrets_dict)

    json_pdf_data_details = json_pdf_data.get('details' , None)
    if json_pdf_data_details is None or len(json_pdf_data_details) == 0:
        # print(json.dumps(json_pdf_data))
        raise Exception('Invalid json data in path, missing "details" key')

    # get loan_number from sftp json file
    loan_number = json_pdf_data_details[0].get('loanNumber', None)
    
    if loan_number is None:
        raise Exception('Invalid loanNumber in sftp json data')
    
    subject = f"Loan {loan_number} – Submitted to Setup "
    message = f"Loan Package {loan_number} been reviewed in DASH and has been submitted to Setup."
    
    send_ses_message(secrets_dict, subject, message, loan_number)

    # get secret values from secrets_dict
    api_server = secrets_dict['ENCOMPASS_API_SERVER']
    instance_id = secrets_dict['ENCOMPASS_INSTANCE_ID']
    api_user_client_id = secrets_dict['ENCOMPASS_API_USER_CLIENT_ID']
    api_user_client_secret = secrets_dict['ENCOMPASS_API_USER_CLIENT_SECRET']
    encompass_username = secrets_dict['ENCOMPASS_USERNAME']
    encompass_password = secrets_dict['ENCOMPASS_PASSWORD']
    
    # get access_token using e-connect api
    access_token = None
    try:
        access_token = GET_ACCESS_TOKEN(api_server, instance_id, api_user_client_id, api_user_client_secret, encompass_username, encompass_password)
    except Exception as e:
        print(e)
        raise Exception('Unable to fetch access_token from e-connect api')
        
    
    # get loan_guid using e-connect api
    loan_guid = None
    try:
        loan_guid = GET_LOAN_GUID(api_server, loan_number, access_token)
    except Exception as e:
        print(e)
        raise Exception(f'Unable to fetch loan_guid from e-connect api for loan_number = {loan_number}')
    

    
    # load dash_efolder_mapping as dict
    dash_efolder_mapping_dict = load_dash_efolder_mapping('dash_efolder_mapping.json')    
    
    # get all document from get_all_retrieve_documents econnect api
    econnect_document_list = get_all_retrieve_documents(api_server, loan_guid, access_token)
    logger.info(f'econnect_document_list length = {len(econnect_document_list)}')
    
    # loop all files in sftp json
    total_files = len(json_pdf_data_details)
    processed_files = 0
    package_id = json_pdf_data_details[0].get('packageId', None)

    # Store record into DDB
    try:
        loan_status_record = get_oldest_record(AUDIT_LOG_TABLE_NAME, loan_number)
        if loan_status_record:
            logger.info(f'{loan_number} loan_status_record : {loan_status_record}')
            # update process status
            update_process_status(AUDIT_LOG_TABLE_NAME, 'ProcessedByIDP', package_id, total_files, loan_status_record)
            logger.info(f'Updated loan status in dynamo db for loan_number = {loan_number} and package_id = {package_id}')
    except Exception as e:
        logger.info(e)
        logger.exception(e)
        logger.info(f'Unable to fetch loan status from dynamo db for loan_number = {loan_number}')
    
    for file_detail in json_pdf_data_details:
        processed_files = processed_files + 1
        
        file_path = file_detail['docPath']
        file_name = file_detail['docName']
        loan_id = file_detail['loanNumber']
        
        logger.info(f'processing_files : {processed_files} out of {total_files}')
        logger.info(f'{loan_id} {file_path} {file_name}')
        
        # get efolder file name from dash file name
        efolder_file_name = dash_efolder_mapping_dict.get(file_name, None)
        efolder_file_name_list = []

        logger.info(f"loan {loan_id} file_name {file_name} efolder_file_name {efolder_file_name} ")
        
        if efolder_file_name and "*" in efolder_file_name:
            efolder_file_name_list = efolder_file_name.split('*')
        else:
            efolder_file_name_list.append(efolder_file_name)
        logger.info(f'efolder_file_name_list {efolder_file_name_list}')
        
        for index, efolder_file_name_desc in enumerate(efolder_file_name_list):

            efolder_file_name, *description = efolder_file_name_desc.split('~') if efolder_file_name_desc else [None]

            logger.info(f"{efolder_file_name} {description}")
            # get efolder file id
            efolder_file_id = None
            if efolder_file_name:
                efolder_file_id = find_efolder_mapping_id(econnect_document_list, efolder_file_name)
            logger.info(f'efolder_file_id {efolder_file_id}')
            
            # create new file id at econnect
            if efolder_file_name and efolder_file_id == None:
                
                efolder_file_id = create_new_document(api_server, loan_guid, access_token, efolder_file_name)
                
                if efolder_file_id != None:
                    econnect_document_list.append({
                        'id': efolder_file_id,
                        'title': efolder_file_name
                    })
                logger.info(f'new efolder_file_id {efolder_file_id}')
            
            final_pdf = 0
            if index == len(efolder_file_name_list)-1:
                final_pdf = 1
            # push message for sqs
            msg_obj = {
                'sftp_file_path': file_path,
                'title': file_name,
                'entityId': efolder_file_id,
                'efolder_file_name': efolder_file_name,
                'description': description[0] if description else "" ,
                'loan_guid': loan_guid,
                'loan_number': loan_number,
                'final_pdf':final_pdf
            }
                        
            sqs_msg_id = send_msg_sqs(json.dumps(msg_obj))
            logger.info(f'sqs_msg_id {sqs_msg_id} {json.dumps(msg_obj)}')            
    
    #Move json file to Archive
    transfer_file_to_archive(secrets_dict, json_file_path)
    
    return {
        'statusCode': 200,
        'body': 'OK'
    }
    

def lambda_handler(event, context):
    try:
        return main(event, context)
        
    except Exception as e:
        print('Exception', e)
        return {
            'statusCode': 400,
            'body': str(e)
        }