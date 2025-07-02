import os
import logging

from botocore.exceptions import NoCredentialsError

from api.modules.s3_module import S3Handler

logger = logging.getLogger('S3')


async def upload_files_to_s3(bucket_name: str, schedule_id: str):
    if not schedule_id:
        logger.error(f"Missing Schedule ID")
        return

    local_path = f"./tmp/{schedule_id}"
    for root, dirs, files in os.walk(local_path):
        logger.info(f"root: {root}, dirs: {len(dirs)} -> {dirs}, files: {len(files)} -> {files}")
        for filename in files:
            local_file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_file_path, local_path)
            logger.info(f"local_file_path: {local_file_path}, relative_path: {relative_path}")
            s3_key = f"{schedule_id}/{relative_path}"

            try:
                s3_handler = S3Handler()

                s3_handler.upload_file(bucket_name, local_file_path, s3_key)
                logger.info(f"Uploaded {local_file_path} to s3://{bucket_name}/{s3_key}")
            except FileNotFoundError:
                logger.error(f"Error: File not found at {local_file_path}")
            except NoCredentialsError:
                logger.error("Error: AWS credentials not found. Make sure your AWS credentials are configured.")
                return
            except Exception as e:
                logger.error(f"An error occurred while uploading {local_file_path}: {e}")
                return


if __name__ == "__main__":
    bucket_name = os.environ.get('BUCKET_NAME')
    logger.info(f"Attempting for {bucket_name}")

