import boto3
import json
import os

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    bucket_name = os.environ['BUCKET_NAME'] # Set this as an environment variable in your Lambda function
    object_name = event['queryStringParameters']['key']
    expiration = 3600  # or however long you want the URL to be valid

    presigned_url = s3_client.generate_presigned_post(bucket_name,
                                                     object_name,
                                                     ExpiresIn=expiration)
    return {
        'statusCode': 200,
        'body': json.dumps(presigned_url),
        'headers': {'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'},
    }
