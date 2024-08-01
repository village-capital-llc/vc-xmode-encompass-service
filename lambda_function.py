from utils.aws_resources import get_pdf_from_storage, get_secrets, send_msg_sqs
from utils.misc import get_file_metadata, get_pdf_from_local_storage, is_valid_pdf, load_dash_efolder_mapping, find_efolder_mapping_id
from utils.exp_apis import _get_access_token as GET_ACCESS_TOKEN
from utils.exp_apis import _get_loan_guid as GET_LOAN_GUID
from utils.exp_apis import get_all_retrieve_documents, create_new_document
from utils.storage import get_pdf_from_sftp, get_pdfjson_from_sftp
import urllib.parse
import json
import threading


'''
def main1(event, context):
    file_path = None
    local_file = False
    
    print(json.dumps(event))
    
    try:
        # file_path = urllib.parse.unquote_plus(event['detail']['object']['key'], encoding='utf-8')
        file_path = event['detail']['object']['key']
    except Exception as e:
        raise e
    
    # Load secrets values
    secrets_dict = get_secrets()
    if secrets_dict is None:
        raise Exception('Invalid Secrets values')

    json_pdf_data = None
    try:
        json_pdf_data = get_pdfjson_from_sftp(file_path, secrets_dict)
    except Exception as e:
        raise e
    
    # print(json.dumps(json_pdf_data))

    json_pdf_data_details = json_pdf_data.get('details' , None)
    if json_pdf_data_details is None:
        # print(json.dumps(json_pdf_data))
        raise Exception('Invalid json data in output path, missing "details" key')
    
    total_files = len(json_pdf_data_details)
    processed_files = 1
    
    for file_detail in json_pdf_data_details:
        
        file_path = file_detail['docPath']
        file_name = file_detail['docName']
        loan_id = file_detail['loanNumber']
        # loan_id = '795f0156-2724-443f-a4ae-3b9c32bc5238'
        print('file_name', file_name)
        print('file_path', file_path)
        print('loan_id', loan_id)
        print('processed_files', processed_files)
        
        # Get metadata from file name
        # loan_id, file_name = get_file_metadata(file_path)
        # if loan_id is None or file_name is None:
        #     raise Exception(f'Invalid Loan Id or File Name. FilePath = {file_path}')
    
        # print(f'loan_id = {loan_id}')
        # print(f'file_name = {file_name}')
    
        # Download file object from storage
        pdf_file_obj, file_obj_io, file_size = None, None, None
    
        try:
            pdf_file_obj, file_size, file_obj_io = get_pdf_from_sftp(file_path, secrets_dict)
        except Exception as e:
            print(e)
            raise Exception(f'Unable to load input pdf file : {file_path}')
        
        # quit()
        
        # if local_file:
        #     print('Loading file from local storage')
    
        #     pdf_file_obj, file_size = get_pdf_from_local_storage(file_path)
        #     if pdf_file_obj is None:
        #         raise Exception(f'Invalid File data')
        # else:
        #     print('Loading file from s3 storage')
    
        #     pdf_file_obj, file_obj_io, file_size = get_pdf_from_storage(file_path, secrets_dict['S3_INPUT_BUCKET_NAME'])
        #     if pdf_file_obj is None:
        #         raise Exception(f'Unable to load pdf file from s3')
    
        # print(f'file_size = {file_size}')
        
        bool_is_invalid_pdf = is_valid_pdf(file_obj_io)
    
        if bool_is_invalid_pdf:
            raise Exception(f'Unable to load pdf, either its password protected or corrupt')
    
        # Upload file to server via api calls
        api_server = secrets_dict['ENCOMPASS_API_SERVER']
        instance_id = secrets_dict['ENCOMPASS_INSTANCE_ID']
        api_user_client_id = secrets_dict['ENCOMPASS_API_USER_CLIENT_ID']
        api_user_client_secret = secrets_dict['ENCOMPASS_API_USER_CLIENT_SECRET']
        encompass_username = secrets_dict['ENCOMPASS_USERNAME']
        encompass_password = secrets_dict['ENCOMPASS_PASSWORD']
        loan_guid = loan_id
        file_obj = pdf_file_obj
    
        try:
            t = threading.Thread(target=upload_attachment, args=(api_server, instance_id, api_user_client_id, api_user_client_secret, loan_guid, file_size, file_name, file_obj, encompass_username, encompass_password, file_obj_io,))
            t.start()
            # upload_attachment(api_server, instance_id, api_user_client_id, api_user_client_secret, loan_guid, file_size, file_name, file_obj, encompass_username, encompass_password, file_obj_io)
        except Exception as e:
            raise Exception(e)
            
        processed_files = processed_files + 1

    return {
        'statusCode': 200,
        'body': 'OK'
    }
'''

def main(event, context):
    # log input event
    print(json.dumps(event))

    # get input json sftp path
    try:
        file_path = event['detail']['object']['key']
    except Exception as e:
        raise Exception('Invalid input json path')
    
    # Load secrets values
    secrets_dict = get_secrets()
    if secrets_dict is None:
        raise Exception('Invalid Secrets values')

    # read input json file from sftp
    json_pdf_data = None
    try:
        json_pdf_data = get_pdfjson_from_sftp(file_path, secrets_dict)
    except Exception as e:
        print(e)
        raise Exception(f'Unable to load json data from path: {file_path}')
    
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


# if __name__ == "__main__":
#     event = {
#         "Records": [
#             {
#                 "s3": {
#                     "bucket": {
#                         "name": "vc-xmode-encompass-bucket"
#                     },
#                     "object": {
#                         "key": "795f0156-2724-443f-a4ae-3b9c32bc5238_dummypdf.pdf",
#                         "size": 13264
#                     }
#                 }
#             }
#         ]
#     }

#     context = {}
    
#     lambda_handler(event, context, True)
