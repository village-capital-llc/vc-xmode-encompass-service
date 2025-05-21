import os
import boto3
from datetime import datetime

def get_dynamo_db_table(table_name: str):
    """
    This function returns a DynamoDB table resource.
    """
    dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(table_name)

def get_oldest_record(table_name: str, loan_id: str) -> dict:
    """
    This function retrieves the loan status from DynamoDB.
    Args:
        table_name (str): The name of the DynamoDB table.
        loan_id (str): The loan number to retrieve.
    Returns:
        dict: The response from DynamoDB.
    """
    table = get_dynamo_db_table(table_name)

    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('loan_id').eq(loan_id),
        FilterExpression=boto3.dynamodb.conditions.Attr('status').eq('InProgress') & boto3.dynamodb.conditions.Attr('package_id').not_exists(),
        ScanIndexForward=True,  # Sort results in ascending order
        Limit=1  # Retrieve the first (oldest) item
    )

    print(f'{loan_id} get_oldest_record response : {response}')

    if 'Items' in response and len(response['Items']) > 0:
        return response['Items'][0]
    else:
        return None

def update_process_status(table_name: str, status: str, package_id: str, total_files: int, document: dict = {}) -> dict:
    """
    This function updates the loan status in DynamoDB.
    Args:
        table_name (str): The name of the DynamoDB table.
        status (str): The status to set for the loan number.
        package_id (str): The package ID to set for the loan number.
        total_files (int): The total number of files to set for the loan number.
        document (dict): The document to set for the loan number.
    """
    table = get_dynamo_db_table(table_name)

    document['package_id'] = package_id
    document['status'] = status 
    document['updated_time'] = int(datetime.now().timestamp())
    document['total_files'] = total_files

    response = table.put_item(
        Item = document,
    )

    return response