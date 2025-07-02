import os
import logging

import boto3
from botocore.exceptions import ClientError
from api.config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION_NAME, USE_LOCALSTACK, LOCAL_AWS_ENDPOINT_URL
)

logger = logging.getLogger(__name__)


class S3Handler:
    def __init__(self):
        """
        Initializes the S3Handler with AWS credentials and region.
        """
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            raise RuntimeError(f"Cannot proceed with S3 due to required ID and/or KEY missing!!")

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=REGION_NAME,
            endpoint_url=f"{LOCAL_AWS_ENDPOINT_URL}" if USE_LOCALSTACK else None,
        )

    def list_buckets(self):
        """
        Lists all S3 buckets.
        """
        try:
            response = self.s3_client.list_buckets()
            return [bucket['Name'] for bucket in response['Buckets']]
        except ClientError as e:
            logger.error(f"Error listing buckets: {e}")
            return None

    def create_folder(self, bucket_name, folder_name):
        """
        Creates a folder (object with a trailing '/') in the specified S3 bucket.
        """
        try:
            self.s3_client.put_object(Bucket=bucket_name, Key=f"{folder_name}/")
            logger.info(f"Folder '{folder_name}' created successfully in bucket '{bucket_name}'.")
            return True
        except ClientError as e:
            logger.error(f"Error creating folder '{folder_name}' in bucket '{bucket_name}': {e}")
            return False

    def upload_file(self, bucket_name, file_path, object_key):
        """
        Uploads a file to the specified S3 bucket.

        Args:
            bucket_name (str): The name of the S3 bucket.
            file_path (str): The local path to the file to upload.
            object_key (str): The key (name) of the object in the S3 bucket.
        """
        try:
            self.s3_client.upload_file(file_path, bucket_name, object_key)
            logger.info(f"File '{file_path}' uploaded to '{object_key}' in bucket '{bucket_name}'.")
            return True
        except ClientError as e:
            logger.error(f"Error uploading file '{file_path}' to '{object_key}' in bucket '{bucket_name}': {e}")
            return False

    def download_file(self, bucket_name, object_key, local_file_path):
        """
        Downloads a file from the specified S3 bucket.

        Args:
            bucket_name (str): The name of the S3 bucket.
            object_key (str): The key (name) of the object in the S3 bucket.
            local_file_path (str): The local path to save the downloaded file.
        """
        try:
            self.s3_client.download_file(bucket_name, object_key, local_file_path)
            logger.info(f"File '{object_key}' downloaded from bucket '{bucket_name}' to '{local_file_path}'.")
            return True
        except ClientError as e:
            logger.error(f"Error downloading file '{object_key}' from bucket '{bucket_name}': {e}")
            return False

    def list_objects(self, bucket_name, prefix=''):
        """
        Lists objects in the specified S3 bucket with an optional prefix.
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            else:
                return []
        except ClientError as e:
            logger.error(f"Error listing objects in bucket '{bucket_name}' with prefix '{prefix}': {e}")
            return None

    def delete_object(self, bucket_name, object_key):
        """
        Deletes an object from the specified S3 bucket.
        """
        try:
            self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            logger.info(f"Object '{object_key}' deleted from bucket '{bucket_name}'.")
            return True
        except ClientError as e:
            logger.error(f"Error deleting object '{object_key}' from bucket '{bucket_name}': {e}")
            return False
