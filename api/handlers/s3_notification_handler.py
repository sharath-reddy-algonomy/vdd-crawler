import sys
import asyncio
import boto3
import json
import time

sys.path.append("/app")

from api.config import REGION_NAME, SQS_QUEUE_NAME, MSG_PUBLISHER
from api.crawlers.crawler_default import google_search_and_download, perform_due_diligence


def schedule_run(topic_arn, message, subject=None):
    sns_client = boto3.client('sns', region_name=REGION_NAME)

    try:
        if subject:
            response = sns_client.publish(
                TopicArn=topic_arn,
                Message=message,
                Subject=subject
            )
        else:
            response = sns_client.publish(
                TopicArn=topic_arn,
                Message=message
            )
        print(f"Message sent to topic {topic_arn}")
        print(f"Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Error sending message to topic {topic_arn}: {e}")


async def listen_to_s3_notifications():
    """
    Listens for S3 event notifications from an SQS queue.
    """
    sqs = boto3.client('sqs', region_name=REGION_NAME)

    try:
        queue_url = sqs.get_queue_url(QueueName=SQS_QUEUE_NAME)['QueueUrl']
        print(f"Listening for S3 notifications on SQS queue: {queue_url}")

        while True:
            # Receive messages from the SQS queue
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,  # Adjust as needed (1-10)
                WaitTimeSeconds=20  # Long polling for efficiency (0-20)
            )

            messages = response.get('Messages', [])

            for message in messages:
                try:
                    body = json.loads(message['Body'])
                    # If the notification came via SNS, the S3 event is in the 'Message' body
                    if 'Sns' in body and 'Message' in body['Sns']:
                        s3_event = json.loads(body['Sns']['Message'])
                    else:
                        s3_event = body  # Direct S3 notification to SQS

                    print("Received S3 event:")
                    print(json.dumps(s3_event, indent=2))

                    subject = s3_event.get("Subject", "")
                    if "Scheduling" in subject:
                        s3_msg = json.loads(s3_event.get("Message", {}))
                        msg_id = s3_msg.get("schedule_id", "")
                        vendor_name = s3_msg.get("vendor_name", "")
                        pages = s3_msg.get("pages", "")
                        print(f"Message ID {msg_id}")
                        if msg_id and vendor_name:
                            print(f"Schedule Code should be implemented for {msg_id}")
                            await perform_due_diligence(actor_name=vendor_name, schedule_id=msg_id, pages=pages)
                        else:
                            print(f"Could not find required info (vendor, schedule id) from the message")
                    elif subject == "Amazon S3 Notification":
                        print(f"S3 file upload implementation should be done here")

                        if 'Records' in s3_event:
                            for record in s3_event['Records']:
                                bucket_name = record['s3']['bucket']['name']
                                object_key = record['s3']['object']['key']
                                event_type = record['eventName']
                                print(f"  Event Type: {event_type}")
                                print(f"  Bucket: {bucket_name}")
                                print(f"  Object Key: {object_key}")

                    # Delete the message from the queue to prevent reprocessing
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    print("Message deleted from the queue.")

                except json.JSONDecodeError:
                    print(f"Error decoding message body: {message['Body']}")
                except Exception as e:
                    print(f"An error occurred while processing the message: {e}")

            time.sleep(3)

    except sqs.exceptions.QueueDoesNotExist:
        print(f"Error: SQS queue '{SQS_QUEUE_NAME}' does not exist in region '{REGION_NAME}'.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(listen_to_s3_notifications())
