import json
import boto3
import pandas as pd
from io import StringIO
import my_function as testing
import os

s3 = boto3.client('s3')

def handler(event, context):
    # Define the source bucket and folder
    source_bucket_name = os.environ['BUCKET_NAME']
    prefix = 'Chinmay_rawJSON_output/'  # Make sure to include the trailing slash
    
    # Define the destination bucket and file name
    destination_bucket_name = source_bucket_name
    destination_file_name = 'Chinmay_final_csv/combined_data.csv'
    
    # List files in the source folder
    response = s3.list_objects_v2(Bucket=source_bucket_name, Prefix=prefix)
    
    # Initialize an empty DataFrame
    df_combined = pd.DataFrame()
    
    # Iterate over the files and read them into a DataFrame
    for item in response.get('Contents', []):
        if not item['Key'].endswith("_page_1.json"):
            continue
        file_key = item['Key']
        response = s3.get_object(Bucket=source_bucket_name, Key=file_key)
        file_content = response['Body'].read().decode('utf-8')
        # Load JSON content into a DataFrame
        data = {'FileName':item['Key'].split('/')[-1].replace("_page_1.json","")}
        key_val = testing.key_val(json.loads(file_content))
        data.update(key_val)
        df = pd.DataFrame([data])
        # Append this DataFrame to the combined DataFrame
        df_combined = pd.concat([df_combined, df], ignore_index=True)
    
    # Convert the combined DataFrame to CSV
    csv_buffer = StringIO()
    df_combined.to_csv(csv_buffer, index=False)
    
    # Write the CSV to the destination bucket
    s3.put_object(Bucket=destination_bucket_name, Key=destination_file_name, Body=csv_buffer.getvalue())
    
    return {
        'statusCode': 200,
        'body': json.dumps('CSV file has been created and uploaded successfully.')
    }
