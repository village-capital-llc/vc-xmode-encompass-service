

def transfer_file_to_archive(sftp, source_path):
    
    """
        Function: Move file from Outout folder to Archive in SFTP 
    """

    # source_path = "Output/0153447586/0153447586_e28a312e-b34f-4354-b23b-618683bf3e41.json"
    # destination_path = "Archive/67024053331/67024053331_d4594323-5684-4392-ba58-28933efac8f7.json"
    
    try:
        
        json_path = source_path.split('/', 1)[-1]
        destination_path = "Archive/" + json_path
        archive_list = sftp.listdir("Archive")
        print(f"json_path: {json_path} Archive file list: {archive_list}")
        
        if json_path in archive_list:
            print(f'File already exist in Archive folder: {destination_path} ')
            sftp.remove(destination_path)
            print(f"Existing file {destination_path} is removed")
            
        sftp.rename(source_path, destination_path)
        print(f"Moved {source_path} to {destination_path} Status: Success")
        
    except Exception as exc:
        print(f"Exception: {exc}")
        print(f"Unable to move to Archive folder: {source_path}")
            