awslocal sns create-topic --name vdd-topic
awslocal sqs create-queue --queue-name vdd-queue
awslocal sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:000000000000:vdd-topic \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-east-1:000000000000:vdd-queue
awslocal s3api create-bucket --bucket vdd-bucket