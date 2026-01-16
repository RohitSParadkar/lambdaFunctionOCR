import boto3
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_FOLDER = os.getenv('S3_FOLDER')

def upload_and_manage_files(manual_source_path):
    base_path = Path(manual_source_path)
    success_dir = base_path / "uploaded"
    failure_dir = base_path / "unuploaded"

    success_dir.mkdir(exist_ok=True)
    failure_dir.mkdir(exist_ok=True)

    s3_client = boto3.client('s3')
    
    # Get list of files (excluding the subfolders we just created)
    files_to_process = [f for f in base_path.iterdir() if f.is_file()]
    
    print(f"--- Found {len(files_to_process)} files in {manual_source_path} ---")

    for file_path in files_to_process:
        file_name = file_path.name
        # The key becomes 'data/yourfile.pdf'
        s3_key = f"{S3_FOLDER}{file_name}"
        
        try:
            print(f"Uploading: {file_name} -> s3://{BUCKET_NAME}/{s3_key}")
            s3_client.upload_file(str(file_path), BUCKET_NAME, s3_key)
            
            shutil.move(str(file_path), str(success_dir / file_name))
            print(f"  ✅ Done!")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            shutil.move(str(file_path), str(failure_dir / file_name))

if __name__ == "__main__":
    # 1. Update this to your ACTUAL local folder path
    my_source = r"D:\Project\lambadaFunction\Folder_Structure\Automatic_Preprocess" 
    
    print("Script started...")
    if os.path.exists(my_source):
        upload_and_manage_files(my_source)
    else:
        print(f"❌ ERROR: The local folder '{my_source}' was not found.")
    print("Script finished.")