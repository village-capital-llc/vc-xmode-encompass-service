import requests
from requests.utils import unquote as url_decode
import json
from tenacity import retry, stop_after_attempt
from .constants import ENCOMPASS_USERNAME, ENCOMPASS_PASSWORD
from .api_store import API_STORE


api_store_obj = API_STORE()


def _get_access_token1(api_server, instance_id, api_user_client_id, api_user_client_secret):
    url = f'{api_server}/oauth2/v1/token'

    payload = f'instance_id={instance_id}&scope=lp&grant_type=client_credentials'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response = requests.post(url, headers=headers, data=payload, auth=(api_user_client_id, api_user_client_secret))

    access_token = response.text['ACCESS_TOKEN']

    return access_token


@retry(stop=stop_after_attempt(3), reraise=True)
def _get_access_token(api_server, instance_id, api_user_client_id, api_user_client_secret, encompass_username, encompass_password):
    url = f'{api_server}/oauth2/v1/token'

    payload = {
        'grant_type': 'password',
        'username': f'{encompass_username}@encompass:{instance_id}',
        'password': encompass_password,
        'client_id': api_user_client_id,
        'client_secret': api_user_client_secret
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    access_token = None
    try:
        response = requests.request("POST", url, headers=headers, data=payload)

        if response.status_code == 200:
            json_dict = json.loads(response.text)
            access_token = json_dict.get('access_token', None)
        else:
            print(response.text)
            raise Exception(f'Unable to get access_token, status_code = {response.status_code}')
    except Exception as e:
        raise e
    
    return access_token


def _get_attachment_upload_url(api_server, loan_guid, file_size, file_name, access_token):
    url = f'{api_server}/encompass/v3/loans/{loan_guid}/attachmentUploadUrl'

    payload = json.dumps({
        'file': {
            'contentType': 'application/pdf',
            'name': file_name,
            'size': file_size 
            },
        'title': file_name 
    })
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    upload_url = None
    authorization_header = None
    multichunk_required = False
    multichunk_json = None
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)
        json_dict = json.loads(response.text)

        if json_dict.get('multiChunkRequired', None):
            multichunk_required = True
            multichunk_json = json_dict
        else:
            upload_url = json_dict.get('uploadUrl', None)
            authorization_header = json_dict.get('authorizationHeader', None)
        
    except Exception as e:
        raise e
    
    return upload_url, authorization_header, multichunk_required, multichunk_json


def _upload_attachment_multichunk(multichunk_json, file_obj):
    
    chunk_start = 0
    chunk_end = 0
    call_commit_url = True
    
    authorization_header = multichunk_json['authorizationHeader']
    
    for chunks in multichunk_json['multiChunk']['chunkList']:
        chunk_end = chunk_start + chunks['size']
        chunked_byte = file_obj[chunk_start:chunk_end]
        chunk_start = chunk_end
        
        # print("chunked_byte")
        # # print(type(chunked_byte))
        # print(chunked_byte[:10])
        url = chunks['uploadUrl']
        print(f'Upload url = {url}')
        # print(f'Upload authorization_header = {authorization_header}')
    
        headers = {
            'Authorization': authorization_header,
            'Content-Type': 'application/pdf'
        }
    
        response = None
        try:
            response = requests.request("PUT", url_decode(url), headers=headers, data=chunked_byte)
        
            print(f'response statusCode {response.status_code}')
            
            if response.status_code != 200:
                call_commit_url = False
                print(f'Upload response = {response.text}')
                
        except Exception as e:
            raise e
    
    if call_commit_url:
        
        url = multichunk_json['multiChunk']['commitUrl']
        
        try:
            response = requests.request("POST", url, headers=headers)

            print('commitUrl', response.text, response.status_code)
            
        except Exception as e:
            raise e


@retry(stop=stop_after_attempt(3), reraise=True)
def upload_attachment(api_server, instance_id, api_user_client_id, api_user_client_secret, loan_guid, file_size, file_name, file_obj, encompass_username, encompass_password, file_obj_io):
    access_token = api_store_obj.get_access_token()
    
    if not access_token:
        print('Fetch access_token')
        try:
            access_token = _get_access_token(api_server, instance_id, api_user_client_id, api_user_client_secret, encompass_username, encompass_password)
            api_store_obj.set_access_token(access_token)
        except Exception as e:
            raise e
    
    # print(f'access_token = {access_token}')

    loan_guid_ori = api_store_obj.get_loan_guid()
    if not loan_guid_ori:
        print('Fetch loan_guid_ori')
        try:
            loan_guid_ori = _get_loan_guid(api_server, loan_guid, access_token)
            api_store_obj.set_loan_guid(loan_guid_ori)
        except Exception as e:
            raise e
        
    if loan_guid_ori == None:
        raise Exception(f'Unable to fetch loan guid for loan number = {loan_guid}')

    url, authorization_header, multichunk_required, multichunk_json = None, None, None, None
    try:
        url, authorization_header, multichunk_required, multichunk_json = _get_attachment_upload_url(api_server, loan_guid_ori, file_size, file_name, access_token)
        
        print('multichunk_required', multichunk_required)
        if multichunk_required:
            try:
                _upload_attachment_multichunk(multichunk_json, file_obj)
                return 0
            except Exception as e:
                raise e
        else:
            if url is None or authorization_header is None:
                raise Exception('Unable to get upload url or header')
    except Exception as e:
        raise e
    
    print(f'Upload url = {url}')
    # print(f'Upload authorization_header = {authorization_header}')

    payload = file_obj
    headers = {
        'Authorization': authorization_header,
        'Content-Type': 'application/pdf'
    }

    response = None
    try:
        response = requests.request("PUT", url_decode(url), headers=headers, data=payload)
    except Exception as e:
        raise e

    print(f'Upload response = {response}')


@retry(stop=stop_after_attempt(3), reraise=True)
def _get_loan_guid(api_server, loan_id, access_token):
    
    url = f'{api_server}/encompass/v3/loanPipeline'
    
    payload = json.dumps(
        {
            "filter": {
                "canonicalName": "Loan.LoanNumber",
                "value": loan_id,
                "matchType": "exact"
            },
            "orgType": "Internal",
            "loanOwnership": "AllLoans"
        }
    )
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print(f"_get_loan_guid from loan id url: {url} payload: {payload} access_token: {access_token}")
    
    load_guid = None
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        json_dict = json.loads(response.text)
        print(f"json_dict: {json_dict}")
        
        if len(json_dict) and json_dict[0].get("loanId", None):
            load_guid = json_dict[0]["loanId"]
        else:
            print('response _get_loan_guid')
            print(response.text)
    except Exception as e:
        print(e)
        raise Exception('Unable to fetch loan guid from econnect')
    
    return load_guid
    

@retry(stop=stop_after_attempt(3), reraise=True)
def get_all_retrieve_documents(api_server, loan_guid, access_token):
    
    url = f'{api_server}/encompass/v3/loans/{loan_guid}/documents?includeRemoved=false&requireActiveAttachments=false'
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    json_dict = None
    try:
        response = requests.request("GET", url, headers=headers)
        json_dict = json.loads(response.text)
    except Exception as e:
        print(e)
        raise Exception('Unable to retrieve_documents from econnect')
    
    return json_dict
    
    
@retry(stop=stop_after_attempt(3), reraise=True)
def create_new_document(api_server, loan_guid, access_token, doc_title):
    
    url = f'{api_server}/encompass/v3/loans/{loan_guid}/documents?action=add&view=entity'
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    payload = json.dumps([
      {
        "title": doc_title,
        "description": ""
      }
    ])

    document_id = None
    try:
        response = requests.request("PATCH", url, headers=headers, data=payload)
        json_dict = json.loads(response.text)
        document_id = json_dict[0]['id']
    except Exception as e:
        print(e)
        raise Exception('Unable to create_new_document in econnect')
    
    return document_id