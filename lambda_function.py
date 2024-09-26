from utils.aws_resources import get_pdf_from_storage, get_secrets, send_msg_sqs
from utils.misc import get_file_metadata, get_pdf_from_local_storage, is_valid_pdf, load_dash_efolder_mapping, find_efolder_mapping_id
from utils.exp_apis import _get_access_token as GET_ACCESS_TOKEN
from utils.exp_apis import _get_loan_guid as GET_LOAN_GUID
from utils.exp_apis import get_all_retrieve_documents, create_new_document
from utils.storage import get_pdf_from_sftp, get_pdfjson_from_sftp
from utils.sftp_file_transfer import transfer_file_to_archive
import urllib.parse
import json
import threading

def main(event, context):
    # log input event
    print(json.dumps(event))

    # get input json sftp path
    try:
        json_file_path = event['detail']['object']['key']
    except Exception as e:
        raise Exception('Invalid input json path')
    
    # Load secrets values
    secrets_dict = get_secrets()
    if secrets_dict is None:
        raise Exception('Invalid Secrets values')

    # read input json file from sftp
    json_pdf_data = None
    try:
        json_pdf_data = get_pdfjson_from_sftp(json_file_path, secrets_dict)
    except Exception as e:
        print(e)
        raise Exception(f'Unable to load json data from path: {json_file_path}')
    
    # print(json.dumps(json_pdf_data))

    json_pdf_data_details = json_pdf_data.get('details' , None)
    if json_pdf_data_details is None or len(json_pdf_data_details) == 0:
        # print(json.dumps(json_pdf_data))
        raise Exception('Invalid json data in path, missing "details" key')

    # get loan_number from sftp json file
    loan_number = json_pdf_data_details[0].get('loanNumber', None)
    print(f'loan_number = {loan_number}')
    if loan_number is None:
        raise Exception('Invalid loanNumber in sftp json data')
    
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
    
    print(f'loan_guid = {loan_guid}')
    
    # load dash_efolder_mapping as dict
    dash_efolder_mapping_dict = load_dash_efolder_mapping('dash_efolder_mapping.json')
    if dash_efolder_mapping_dict is None:
        raise Exception('Unable to load dash_efolder_mapping')
    
    # get all document from get_all_retrieve_documents econnect api
    econnect_document_list = get_all_retrieve_documents(api_server, loan_guid, access_token)
    print(f'econnect_document_list length = {len(econnect_document_list)}')
    
    # loop all files in sftp json
    total_files = len(json_pdf_data_details)
    processed_files = 0
    
    for file_detail in json_pdf_data_details:
        processed_files = processed_files + 1
        
        file_path = file_detail['docPath']
        file_name = file_detail['docName']
        loan_id = file_detail['loanNumber']
        print('-' * 50)
        print(f'processing_files : {processed_files} out of {total_files}')
        print('file_name', file_name)
        print('file_path', file_path)
        print('loan_id', loan_id)
        
        # get efolder file name from dash file name
        efolder_file_name = dash_efolder_mapping_dict.get(file_name, None)
        if efolder_file_name == "nan" or efolder_file_name == "Need to discuss with Moder further":
            efolder_file_name = None
        print(f'efolder_file_name : {efolder_file_name}')
        
        # get efolder file id
        efolder_file_id = None
        if efolder_file_name:
            efolder_file_id = find_efolder_mapping_id(econnect_document_list, efolder_file_name)
        print(f'efolder_file_id : {efolder_file_id}')
        
        # create new file id at econnect
        if efolder_file_name and efolder_file_id == None:
            print('create new document on econnect')
            efolder_file_id = create_new_document(api_server, loan_guid, access_token, efolder_file_name)
            
            if efolder_file_id != None:
                econnect_document_list.append({
                    'id': efolder_file_id,
                    'title': efolder_file_name
                })
            print(f'new efolder_file_id : {efolder_file_id}')
        
        # push message for sqs
        msg_obj = {
            'sftp_file_path': file_path,
            'title': file_name,
            'entityId': efolder_file_id,
            'efolder_file_name': efolder_file_name,
            'loan_guid': loan_guid,
            'loan_number': loan_number
        }
        
        print(json.dumps(msg_obj))
        
        try:
            sqs_msg_id = send_msg_sqs(json.dumps(msg_obj))
            print(f'sqs_msg_id = {sqs_msg_id}')
        except Exception as e:
            print(e)
            raise Exception('Unable to send message to sqs')
        
        # stop condition, used for testing code
        # if processed_files > 1:
        #     break
        
    
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