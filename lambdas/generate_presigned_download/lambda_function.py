import os
import boto3
import json
import base64

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    print(event)
    bucket_name = os.environ['BUCKET_NAME']
    try:
        body = json.loads(event['queryStringParameters'])
    except:
        body = event['queryStringParameters']
    
    print(body)
    image_key = body['key']
    
    presigned_url = s3_client.generate_presigned_url('get_object',
                                                     Params={'Bucket': bucket_name, 'Key': image_key},
                                                     ExpiresIn=3600)  # URL expires in 1 hour
    print(presigned_url)
    return {
        'statusCode': 200,
        'headers': {'Access-Control-Allow-Headers': 'Content-Type',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'},
        'body': json.dumps({
                    'statusCode': 200,
                    'body': {'download_url':presigned_url}
                })
    }