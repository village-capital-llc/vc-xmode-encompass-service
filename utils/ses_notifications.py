import boto3
import requests
import json

def send_ses_message(secrets_dict, subject, message, loan_id, loan_status=''):
    
    webhook(secrets_dict, subject, message)
    print("sending ses message")
    recipients = ["zaid.ahmad@gomoder.com", "lokesh.babu@gomoder.com"]
    
    ses_client = boto3.client("ses", region_name="us-west-2")
    CHARSET = "UTF-8"
    response = ses_client.send_email(
        Destination={
            "ToAddresses": recipients,
        },
        Message={
            "Body": {
                "Text": {
                    "Charset": CHARSET,
                    "Data": f"{message}",
                }
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": f"{subject}",
            },
        },
        Source="zaid.ahmad@gomoder.com",
    )
    
    print("Message sned successfully")
    print(f"Recipients: {recipients}")
    print(f"Subject: {subject}")
    print(f"message: {message}")


def webhook(secrets_dict, subject, message):
    
    webhook_url = secrets_dict['WEBHOOK_URL']
    
    teams_message = {
        "title": subject,
        "text": message
    }
    
    response = requests.post(webhook_url, data=json.dumps(teams_message))
    print(response.text)
    print(f'statusCode: {response.status_code}')