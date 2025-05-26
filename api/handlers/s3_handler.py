import os

from botocore.exceptions import NoCredentialsError

from api.modules.s3_module import S3Handler


async def upload_files_to_s3(bucket_name: str, schedule_id: str):
    if not schedule_id:
        print(f"Schedule ID cannot be empty!")
        return

    local_path = f"./tmp/{schedule_id}"
    for root, dirs, files in os.walk(local_path):
        print(f"root: {root}, dirs: {len(dirs)} -> {dirs}, files: {len(files)} -> {files}")
        for filename in files:
            local_file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_file_path, local_path)
            print(f"local_file_path: {local_file_path}, relative_path: {relative_path}")
            s3_key = f"{schedule_id}/{relative_path}"

            try:
                s3_handler = S3Handler()

                s3_handler.upload_file(bucket_name, local_file_path, s3_key)
                print(f"Uploaded {local_file_path} to s3://{bucket_name}/{s3_key}")
            except FileNotFoundError:
                print(f"Error: File not found at {local_file_path}")
            except NoCredentialsError:
                print("Error: AWS credentials not found. Make sure your AWS credentials are configured.")
                return
            except Exception as e:
                print(f"An error occurred while uploading {local_file_path}: {e}")
                return


def trial_run_to_s3(bucket: str):
    s3_handler = S3Handler()

    buckets = s3_handler.list_buckets()
    print("My buckets:", buckets)

    if bucket not in buckets:
        print(f"Could not find input bucket '{bucket}' in AWS, check and try again!")
        return

    new_folder = 'processed_data'
    s3_handler.create_folder(bucket, new_folder)

    file_to_upload = 'report.csv'
    s3_object_key_upload = f'{new_folder}/{file_to_upload}'

    with open(file_to_upload, 'w') as f:
        f.write("data1,data2\nvalue1,value2")
    s3_handler.upload_file(bucket, file_to_upload, s3_object_key_upload)

    print(f"Contents of '{bucket}/{new_folder}':", s3_handler.list_objects(bucket, prefix=new_folder))

    file_to_download = 'downloaded_report.csv'
    s3_handler.download_file(bucket, s3_object_key_upload, file_to_download)

    os.remove(file_to_upload)


if __name__ == "__main__":
    bucket_name = os.environ.get('BUCKET_NAME')
    print(f"Attempting for {bucket_name}")
    trial_run_to_s3(bucket_name)
