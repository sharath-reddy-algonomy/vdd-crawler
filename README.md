# vdd-data-crawler
Vendor Due Diligence Data Crawler

The crawler is meant to perform a google search for the vendor received as input with the below configurations:
1. Number of pages to crawl
2. Crawlers to use (GOOGLE, NEWS, REGULATORY_DATABASES, OFFICIAL_WEBSITE)
3. Directors - List of directors; only used by GOOGLE crawler
4. Website - official website of the vendor; only used by the OFFICIAL_WEBSITE crawler

Workflow: google search -> extract URLs -> Crawl each link and download content.

Crawler uses different Google Custom Search Engines(CSE) to perform different types of crawls. 
Search engines are configurable using the environment variables.
GOOGLE: Meant for generic google search. Control over which sites to exclude will be in the search engine itself (CSE)
NEWS: Meant for searching news sites. Sites to crawl are customizable through CSE
REGULATORY_DATABASES: Meant for searching regulatory databases. Sites to crawl are customizable through CSE
OFFICIAL_WEBSITE: Crawls vendor's official website; website URL is expected as input for this crawler to work.
Notes:

1. Crawler has limited control over the content crawled; crawls whatever content google search returns.
2. Crawler takes its time, be patient.
3. Once complete, crawler creates a `manifest.json` against each crawl type folder with information about the file names used, URL whose content is extracted, and status indicating if the download was successful or not.
4. Crawler employs a rotating proxy. Proxy URL, username and passwords are configurable using environment variables.
5. Proxies can only increase the effectiveness of the crawl to some extent, it doesn't guarantee 100% downloads. 
6. Report any issues found on this repository using the "Issues" feature of github.

## PRE-REQUISITE

Python version 3.10 or above

### VIRTUAL ENV

Create Python Virtual Environment

`$ python -m venv vdd_venv`

`$ source vdd_venv/bin/activate`

### Install Dependencies

`$ pip install -r requirements.txt`

### .env file
Have an .env file created under root directory (i.e. /vdd-data-crawler) with following entries.
Below values are for local development environment. Change out the values when pointing to actual AWS instance.
```commandline
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
BUCKET_NAME=vdd-bucket
MSG_PUBLISHER=arn:aws:sns:us-east-1:000000000000:vdd-topic
MSG_CONSUMER=arn:aws:sqs:us-east-1:000000000000:vdd-queue
S3_QUEUE_NAME=vdd-queue
DEFAULT_GOOGLE_SEARCH_ENGINE_URL=https://cse.google.com/cse?cx=30ed94f37199f4ea8
REGULATORY_DATABASE_GOOGLE_SEARCH_ENGINE_URL=https://cse.google.com/cse?cx=d665f5ed70d3243dc
NEWS_SEARCH_ENGINE_URL=https://cse.google.com/cse?cx=30ed94f37199f4ea8
ENDPOINT_URL=http://host.docker.internal:4566
```
### Local Sandbox Setup
1. Install Localstack to simulate AWS (follow instructions here https://docs.localstack.cloud/getting-started/installation/)
2. Install Localstack Desktop (follow instructions here https://docs.localstack.cloud/getting-started/installation/#localstack-desktop)
3. Install Localstack AWS CLI (follow instructions here https://docs.localstack.cloud/user-guide/integrations/aws-cli/#localstack-aws-cli-awslocal)
4. Use LOCALSTACK - export localstack parameter via terminal 
```commandline
export USE_LOCALSTACK=True
```
5. Run Localstack 
```commandline
localstack start
```
6. Create local topic
```commandline
awslocal sns create-topic --name vdd-topic
```
7. Create local queue
```commandline
awslocal sqs create-queue --queue-name vdd-queue
```
8. Subscribe local queue to local topic
```commandline
awslocal sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:000000000000:vdd-topic \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-east-1:000000000000:vdd-queue
```
9. Create local S3 bucket
```commandline
awslocal s3api create-bucket --bucket vdd-bucket
```

### Build and Run crawler app locally
1. Create a docker network for VDD. Note that this command needs to be run only once and not everytime you build docker image.
```commandline
docker network create vdd-network -d bridge
```
2. Build docker image
```commandline
docker build --file Dockerfile-0 -t vdd-crawler .
```
3. Run docker for API (will start a FASTApi server)
```commandline
docker run --env-file .env.example --network vdd-network vdd-crawler:latest api
```
4. In another terminal run `listener`
```commandline
docker run --env-file .env.example --network vdd-network vdd-crawler:latest listener
```
5. In any browser open URL `http://localhost:8080/docs`. This should load Swagger UI.
6. Try out the `/crawler/due-diligence` API with relevant request body.
7. Once you hit the `Execute` button in Swagger, you should see that the listener will start crawling for the vendor specified.

### AWS Setup
```commandline
S3 Buckets:
There should be a bucket named 'vdd-bucket' and the user should have necessry permissions to read/write into S3 buckets

Another bucket is created for setting up notification to SNS on getting new files into the bucket.

SNS Topic:
A topic is created named 'vdd-topic' to get notified by S3 on new objects dropped into the bucket. 

SQS Queue:
A queue named 'vdd-queue' for subscribing to the topic and to be listened from the code for processing messages from S3 and scheduling events from API requests.

Policies:
A test user with below permissions 
3 policies added S3 SNS and SQS operations
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Statement1",
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "arn:aws:s3:::vdd-crawler/*"
        },
        {
            "Sid": "Statement2",
            "Effect": "Allow",
            "Action": "s3:ListAllMyBuckets",
            "Resource": "*"
        }
    ]
}

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sns:Publish"
            ],
            "Resource": "arn:aws:sns:<region>:<account>:vdd-*"
        }
    ]
}

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueUrl"
            ],
            "Resource": "arn:aws:sqs:<region>:<account>:vdd-*"
        }
    ]
}

The above policies should be attached to the user whose 
AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY is mentioned in the .env file
```
