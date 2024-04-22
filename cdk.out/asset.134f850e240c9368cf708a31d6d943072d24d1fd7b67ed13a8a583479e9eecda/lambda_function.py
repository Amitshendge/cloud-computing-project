import boto3
import numpy as np
from PIL import Image
from io import BytesIO
import json
import zipfile
import os
import base64

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = os.environ['BUCKET_NAME']
    print(111)
    print(event)
    try:
        body = json.loads(base64.b64decode(event['body']))
    except:
        try:
            body = json.loads(event['body'])
        except:
            body = event['body']
    image_key = body['key']
    cropped_images_folder = 'my-cropped-images/'
    zip_folder_key = 'zipped-images/'
    temp_folder = '/tmp/'  # Lambda provides a small amount of disk space in /tmp

    # Read image from S3
    image_obj = s3_client.get_object(Bucket=bucket_name, Key=image_key)
    image = Image.open(BytesIO(image_obj['Body'].read()))

    # Crop coordinates
    crop_coordinates = body['crop_dim']
    # Crop and save images
    for idx, ((upper, lower), (left, right)) in enumerate(crop_coordinates):
        cropped_image = image.crop((left, upper, right, lower))
        buffer = BytesIO()
        cropped_image.save(buffer, format='JPEG')
        buffer.seek(0)

        # Save the cropped image to S3
        s3_client.put_object(Bucket=bucket_name, Key=f'{cropped_images_folder}cropped_image_{idx}.jpg', Body=buffer)
    
    zip_filename = 'all_images.zip'
    zip_path = os.path.join(temp_folder, zip_filename)

    # Create a zip file
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for idx, ((upper, lower), (left, right)) in enumerate(crop_coordinates):
            cropped_image = image.crop((left, upper, right, lower))
            cropped_filename = f'cropped_image_{idx}.jpg'
            cropped_path = os.path.join(temp_folder, cropped_filename)

            # Save cropped image temporarily
            cropped_image.save(cropped_path, format='JPEG')

            # Add file to zip
            zipf.write(cropped_path, cropped_filename)

            # Remove the file after adding to zip
            os.remove(cropped_path)

    # Upload the zip file to S3
    store_zip_file_name = image_key.rsplit('.', 1)[0]+'.zip'
    with open(zip_path, 'rb') as zip_file:
        s3_client.put_object(Bucket=bucket_name, Key=zip_folder_key + store_zip_file_name, Body=zip_file)

    # Clean up the zip file from /tmp
    os.remove(zip_path)

    # Generate a presigned URL for the zip file
    presigned_url = s3_client.generate_presigned_url('get_object',
                                                     Params={'Bucket': bucket_name, 'Key': zip_folder_key + store_zip_file_name},
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