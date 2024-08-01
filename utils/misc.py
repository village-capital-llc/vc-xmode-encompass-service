import os
import pypdf
import json


def get_file_metadata(file_path):
    filename_list = file_path.split('_')

    loan_id = None
    file_name = None

    if len(filename_list) > 1:
        loan_id = filename_list[0]
        file_name = filename_list[1].replace('.pdf', '')

    return loan_id, file_name


def get_pdf_from_local_storage(file_path):
    file_content = None
    file_size = 0

    with open(file_path, mode='rb') as file: 
        file_content = file.read()

    try:
        file_size = os.path.getsize(file_path)
    except Exception as e:
        print(e)

    return file_content, file_size


def is_valid_pdf(file_obj):
    bool_is_encrypted = False
    try:
        bool_is_encrypted = pypdf.PdfReader(file_obj).is_encrypted
    except Exception as e:
        print(e)
        
    return bool_is_encrypted
    
    
def load_dash_efolder_mapping(file_path):
    json_dict = None
    
    with open(file_path) as f:
        json_dict = json.load(f)
        
    return json_dict   
        
        
def find_efolder_mapping_id(econnect_document_list, efolder_file_name):
    document_id = None
    efolder_file_name = efolder_file_name.strip().lower()
    
    for doc_dict in econnect_document_list:
        if efolder_file_name == doc_dict['title'].strip().lower():
            document_id = doc_dict['id']
            break
        
    return document_id
    