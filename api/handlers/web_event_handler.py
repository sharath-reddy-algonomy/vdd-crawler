import sys
import boto3
import json
import asyncio

sys.path.append("/app")

from api.config import REGION_NAME, MSG_PUBLISHER, USE_LOCALSTACK, SQS_QUEUE_NAME, LOCAL_AWS_ENDPOINT_URL
from api.crawlers.crawler_orchestrator import perform_due_diligence_v2

sqs = boto3.client(
    "sqs",
    region_name=REGION_NAME,
    endpoint_url=f"{LOCAL_AWS_ENDPOINT_URL}" if USE_LOCALSTACK else None,
)

queue_url = sqs.get_queue_url(QueueName=SQS_QUEUE_NAME)['QueueUrl']


def schedule_run(message, subject=None):
    print(f"Using LocalStack {USE_LOCALSTACK}", flush=True)
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
        print(f"Message sent to topic {MSG_PUBLISHER}", flush=True)
        print(f"Message ID: {response['MessageId']}", flush=True)
    except Exception as e:
        print(f"Error sending message to topic {MSG_PUBLISHER}: {e}", flush=True)


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


        print(f"Received message with ID {message_id} for vendor: {vendor_name}", flush=True)
        print(f"Schedule ID: {schedule_id}", flush=True)
        print(f"Pages to process: {pages}", flush=True)
        print(f"Directors for {vendor_name}: {directors}", flush=True)
        print(f"Website URL of {vendor_name}: {website_url}", flush=True)
        print(f"Crawlers chosen: {crawlers}", flush=True)

        await perform_due_diligence_v2(payload)
        print(f"Completed processing message with ID {message_id}.", flush=True)

    except Exception as e:
        print(f"Failed to process message: {e}", flush=True)


async def poll_messages():
    print("Polling for messages...", flush=True)

    try:
        while True:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=10  # Long polling
            )

            messages = response.get("Messages", [])
            if not messages:
                continue

            tasks = []
            to_delete = []
            for message in messages:
                print("Received message:", message["MessageId"], flush=True)
                tasks.append(process_message(message["Body"], message["MessageId"]))
                to_delete.append(message["ReceiptHandle"])
            await asyncio.gather(*tasks)

            for receipt_handle in to_delete:
                sqs.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=receipt_handle
                )
    except Exception as e:
        print(f"Polling error: {e}", flush=True)
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(poll_messages())
