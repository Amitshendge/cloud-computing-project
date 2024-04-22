import json
import boto3
import fitz
from io import BytesIO,StringIO
import csv
from datetime import datetime
import os
import uuid
from urllib.parse import unquote
import json
import re
from collections import defaultdict

def textract_analyze_image(img_file):
    textract = boto3.client('textract')
    return textract.analyze_document(
            Document={'Bytes': img_file},
            FeatureTypes=['FORMS'])

def get_s3_object(s3_client, bucket_name, key, isBytes=True):
    img_file_obj = s3_client.get_object(Bucket=bucket_name, Key=key)
    return img_file_obj['Body'].read() if isBytes else BytesIO(img_file_obj['Body'].read())
    
def put_s3_object(s3_client, bucket_name, output_key, body):
    return s3_client.put_object(Body=body, Bucket=bucket_name, Key=output_key)

def extract_table_data(response):
    blocks = response['Blocks']

    # get key and value maps
    key_map = {}
    value_map = {}
    block_map = {}
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block
    
    
    def get_kv_relationship(key_map, value_map, block_map):
        kvs = defaultdict(list)
        for block_id, key_block in key_map.items():
            value_block = find_value_block(key_block, value_map)
            key = get_text(key_block, block_map)
            val = get_text(value_block, block_map)
            kvs[key].append(val)
        return kvs
    
    
    def find_value_block(key_block, value_map):
        for relationship in key_block['Relationships']:
            if relationship['Type'] == 'VALUE':
                for value_id in relationship['Ids']:
                    value_block = value_map[value_id]
        return value_block
    
    
    def get_text(result, blocks_map):
        text = ''
        if 'Relationships' in result:
            for relationship in result['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        word = blocks_map[child_id]
                        if word['BlockType'] == 'WORD':
                            text += word['Text'] + ' '
                        if word['BlockType'] == 'SELECTION_ELEMENT':
                            if word['SelectionStatus'] == 'SELECTED':
                                text += 'X '
    
        return text
    
    
    def print_kvs(kvs):
        for key, value in kvs.items():
            print(key, ":", value)
    
    
    def search_value(kvs, search_key):
        for key, value in kvs.items():
            if re.search(search_key, key, re.IGNORECASE):
                return value
    
    
    
    
    
    kvs = get_kv_relationship(key_map, value_map, block_map)
    # print("\n\n== FOUND KEY : VALUE pairs ===\n")
    
    # required_key = ['Invoice #','APPROVED','Date','Cost','Invoice Date','EA Project #','DBA -','Expense']
    # def list_comp(my_lst):
    #     if len(my_lst) >0:
    #         return my_lst[0]
    #     else:
    #         return ""
    
    # final_dict = {}
    # for key, value in kvs.items():
    #     key2 = key.replace(':','').strip()
    #     if key2 in required_key:
    #         final_dict[key2] = list_comp(kvs[key])
    return kvs

def handler(event, context):
    print(event)
    s3_client = boto3.client('s3')
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        pdf_key = record['s3']['object']['key']
        pdf_key = unquote(pdf_key).replace('+',' ')
        
        # bucket_name = 'amit-storage-bucket'
        # pdf_key = 'Chinmay_pdf/EA Invoice 159618_Approved.pdf'
    
        pdf_name = pdf_key.split('/')[-1]
    
        # Download PDF file from S3
        pdf_file_obj = s3_client.get_object(Bucket=bucket_name, Key=pdf_key)
        pdf_file = BytesIO(pdf_file_obj['Body'].read())
        
        # Open the PDF file
        pdf_document = fitz.open(stream=pdf_file, filetype="pdf")
        
        # Define the desired DPI
        desired_dpi = 300
        zoom_factor = desired_dpi / 72  # PDFs default to 72 DPI
        mat = fitz.Matrix(zoom_factor, zoom_factor)  # Create a Matrix with the zoom factor
        my_data = {}
        # Iterate over PDF pages and export each as image
        for page_number in range(len(pdf_document)):
            page = pdf_document.loadPage(page_number)
            
            # Use the Matrix to get a higher DPI pixmap
            pix = page.getPixmap(matrix=mat)
        
            output_image = BytesIO()
            temp_image_path = f"/tmp/page_{page_number + 1}.jpg"
            pix.writeImage(temp_image_path, "jpeg")
        
            # Read the temp image file into BytesIO object and upload it to S3
            with open(temp_image_path, 'rb') as image_file:
                output_image = BytesIO(image_file.read())
                output_key = f"Chinmay_pdf_output/{pdf_name}/{pdf_name}_page_{page_number + 1}.jpg"
                output_image.seek(0)
                s3_client.put_object(Body=output_image, Bucket=bucket_name, Key=output_key)
                print(f"Saved page {page_number + 1} as {output_key}")
                
            # Optionally, remove the temp image file
            os.remove(temp_image_path)
            
            img_file = get_s3_object(s3_client, bucket_name, output_key)
            textract_response = textract_analyze_image(img_file)
            output_key3 = f"Chinmay_rawJSON_output/{pdf_name}/{pdf_name}_page_{page_number + 1}.json"
            s3_client.put_object(Body=json.dumps(textract_response), Bucket=bucket_name, Key=output_key3)
    
            new_csv_data = extract_table_data(textract_response)
            my_data.update(new_csv_data)
            
    
        required_key = ['Invoice #','APPROVED','Date','Cost','Invoice Date','EA Project #','DBA -','Expense']
        def list_comp(my_lst):
            if len(my_lst) >0:
                return my_lst[0]
            else:
                return ""
        output_key2 = f"Chinmay_json_output/{pdf_name}.json"
        final_dict = {'File_name':pdf_name}
        for key, value in my_data.items():
            key2 = key.replace(':','').strip()
            if key2 in required_key:
                final_dict[key2] = list_comp(my_data[key]).strip()
        s3_client.put_object(Bucket=bucket_name, Key=output_key2, Body=json.dumps(final_dict))
        # Close the PDF document
        pdf_document.close()

    return {
        'statusCode': 200,
        'body': 'AAAA'
    }