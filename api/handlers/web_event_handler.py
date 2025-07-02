import sys
import boto3
import json
import asyncio
import logging

sys.path.append("/app")

from api.config import REGION_NAME, MSG_PUBLISHER, USE_LOCALSTACK, SQS_QUEUE_NAME, LOCAL_AWS_ENDPOINT_URL
from api.crawlers.crawler_orchestrator import perform_due_diligence_v2
from api.logger_config import setup_logging

logger = logging.getLogger('listener')

sqs = boto3.client(
    "sqs",
    region_name=REGION_NAME,
    endpoint_url=f"{LOCAL_AWS_ENDPOINT_URL}" if USE_LOCALSTACK else None,
)

queue_url = sqs.get_queue_url(QueueName=SQS_QUEUE_NAME)['QueueUrl']


def schedule_run(message, subject=None):
    logger.debug(f"Using LocalStack {USE_LOCALSTACK}")
    sns_client = boto3.client(
        'sns',
        region_name=REGION_NAME,
        endpoint_url=f"{LOCAL_AWS_ENDPOINT_URL}" if USE_LOCALSTACK else None,
    )

    try:
        if subject:
            response = sns_client.publish(
                TopicArn=MSG_PUBLISHER,
                Message=message,
                Subject=subject
            )
        else:
            response = sns_client.publish(
                TopicArn=MSG_PUBLISHER,
                Message=message
            )
        logger.info(f"Message sent to topic {MSG_PUBLISHER}")
        logger.debug(f"Message ID: {response['MessageId']}")
    except Exception as e:
        logger.error(f"Error sending message to topic {MSG_PUBLISHER}: {e}")


async def process_message(message_body, message_id):
    try:
        # SNS wraps your payload inside another JSON structure under "Message"
        outer = json.loads(message_body)
        payload = json.loads(outer["Message"])

        vendor_name = payload["vendor_name"]
        schedule_id = payload["schedule_id"]
        pages = payload["pages"]
        directors = payload["directors"]
        website_url = payload["website_url"]
        crawlers = payload["crawlers"]

        logger.debug(f"Received message with ID {message_id} for vendor: {vendor_name}")
        logger.info(f"Schedule ID: {schedule_id}")
        logger.info(f"Pages to process: {pages}")
        logger.info(f"Directors for {vendor_name}: {directors}")
        logger.info(f"Website URL of {vendor_name}: {website_url}")
        logger.info(f"Crawlers chosen: {crawlers}")

        await perform_due_diligence_v2(payload)
        logger.info(f"Completed processing message with ID {message_id}.")

    except Exception as e:
        logger.error(f"Failed to process message: {e}")


async def poll_messages():
    logger.info("Polling for messages...")

    try:
        while True:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10  # Long polling
            )

            messages = response.get("Messages", [])
            if not messages:
                continue

            tasks = []
            to_delete = []
            for message in messages:
                logger.info(f"Received message: {message['MessageId']}")
                tasks.append(process_message(message["Body"], message["MessageId"]))
                to_delete.append(message["ReceiptHandle"])
            await asyncio.gather(*tasks)

            for receipt_handle in to_delete:
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
    except Exception as e:
        logger.error(f"Polling error: {e}")
        await asyncio.sleep(5)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(poll_messages())
