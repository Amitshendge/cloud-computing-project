import json
import boto3
import fitz  # PyMuPDF
from io import BytesIO,StringIO
import textract_functions as text_f
import csv
from datetime import datetime
import os
import uuid
from urllib.parse import unquote

def handler(event, context):
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
            
            img_file = text_f.get_s3_object(s3_client, bucket_name, output_key)
            textract_response = text_f.textract_analyze_image(img_file)
            output_key3 = f"Chinmay_rawJSON_output/{pdf_name}/{pdf_name}_page_{page_number + 1}.json"
            s3_client.put_object(Body=json.dumps(textract_response), Bucket=bucket_name, Key=output_key3)
    
            new_csv_data = text_f.extract_table_data(textract_response)
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
        'body': json.dumps('PDF to Image conversion completed')
    }