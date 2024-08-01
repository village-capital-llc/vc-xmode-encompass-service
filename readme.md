# VC Xmode - Backend

## Prerequisites

- Python version: 3.12
- `pip install -r requirements.txt`
- AWS keys
- Encompass keys

## Run application

### Local

Add `.env` file at root directory of the project

`python lambda_function.py`

## Files

- `lambda_function.py`: Root exectution file
- `utils.constants.py`: Contains various constants values
- `utils.aws_resources.py`: Contains boto3 connectivity to AWS resources
- `utils.exp_apis.py`: Contains api requests to expanse apis
- `utils.sftp_file_transfer.py`: Contains code to tranfer file from outout folder to archive
- `utils.misc.py`: Contains miscellaneous methods, like getting metadata from file name 
