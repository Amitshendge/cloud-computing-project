from io import BytesIO,StringIO
import boto3
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