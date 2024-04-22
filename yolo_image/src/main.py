import json
import boto3
from ultralytics import YOLO
import cv2
from PIL import Image
import numpy as np
import io
import time
import os

model = YOLO("yolov8m-seg.pt")

bucket_name = os.environ['BUCKET_NAME'] # Set this as an environment variable in your Lambda function

# Create an S3 client
s3 = boto3.client('s3')

def get_image_from_s3(object_key):
    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        image_data = response['Body'].read()
        
        # Open the image using Pillow
        return np.array(Image.open(io.BytesIO(image_data)))
    
    except Exception as e:
        print('Error:', str(e))

def save_cropped_images(image, predict):
    count = 0
    final_images = []
    for i, acc in zip(predict[0].boxes.xywhn,predict[0].boxes.conf):
        if acc<0.4:
            continue
        count = count + 1
        height, width = image.shape[:2]

        # Box coordinates in XYWHN format (normalized)
        x_center, y_center, w_norm, h_norm = i  # Example values, replace with yours

        # Convert normalized coordinates to pixel coordinates
        x_center, y_center = int(x_center * width), int(y_center * height)
        w, h = int(w_norm * width)+40, int(h_norm * height)+40

        # crop_img = image[(y_center - h // 2)-30:(y_center + h // 2)+10, x_center - w // 2:x_center + w // 2]
        final_images.append((((y_center - h // 2)-30,(y_center + h // 2)+10), (x_center - w // 2,x_center + w // 2)))
    return final_images

def handler(event, context):
    print(event)
    print("Hello from image/src/main.py")
    object_key = "img20221019_15225111.jpg"
    object_key = event['queryStringParameters']['key']
    t_start = time.time()
    image = get_image_from_s3(object_key)
    t_end = time.time()
    print(f"Time taken to get image from S3: {t_end-t_start:.2f} seconds")
    t_start = time.time()
    predict = model.predict(image)
    t_end = time.time()
    print(f"Time taken to predict: {t_end-t_start:.2f} seconds")
    t_start = time.time()
    cropped_images = save_cropped_images(image, predict)
    t_end = time.time()
    print(f"Time taken to crop images: {t_end-t_start:.2f} seconds")
    print(cropped_images)
    return {"output": json.dumps(cropped_images)}