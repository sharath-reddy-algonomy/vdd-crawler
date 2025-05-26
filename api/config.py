import os

from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
REGION_NAME = 'us-east-1'
MSG_PUBLISHER = os.environ.get("MSG_PUBLISHER")
MSG_CONSUMER = os.environ.get("MSG_CONSUMER")
SQS_QUEUE_NAME = os.environ.get("S3_QUEUE_NAME")
USE_LOCALSTACK = os.environ.get("USE_LOCALSTACK")
DEFAULT_SEARCH_ENGINE_URL = os.environ.get("DEFAULT_GOOGLE_SEARCH_ENGINE_URL")
REGULATORY_DATABASE_SEARCH_ENGINE_URL=os.environ.get("REGULATORY_DATABASE_GOOGLE_SEARCH_ENGINE_URL")

# Only used when localstack is employed
LOCAL_AWS_ENDPOINT_URL=os.environ.get("ENDPOINT_URL")