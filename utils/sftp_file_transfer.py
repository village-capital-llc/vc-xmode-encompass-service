

def transfer_file_to_archive(sftp, source_path):
    
    """
        Function: Move file from Outout folder to Archive in SFTP 
    """

    # source_path = "Output/0153447586/0153447586_e28a312e-b34f-4354-b23b-618683bf3e41.json"
    # destination_path = "Archive/67024053331/67024053331_d4594323-5684-4392-ba58-28933efac8f7.json"
    
    try:
        
        destination_path = "Archive/" + source_path.split('/', 1)[-1]
        sftp.rename(source_path, destination_path)
        print(f"Moved {source_path} to {destination_path} Status: Success")
        
    except Exception as exc:
        print(f"Exception: {exc}")
        print(f"Unable to move to Archive folder: {source_path}")
            