import json
import boto3
import requests
from io import BytesIO
from PIL import Image
import os


# HF_API_TOKEN = "chemi tokeni"


s3 = boto3.client('s3')

def lambda_handler(event, context):
    
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    
    response = s3.get_object(Bucket=bucket, Key=key)
    image_data = response['Body'].read()
    image = Image.open(BytesIO(image_data))
    
   
    process_with_model(image, key, "google/mobilenet_v1_0.75_192")
    process_with_model(image, key, "microsoft/resnet-50")
    process_with_model(image, key, "nvidia/mit-b0")
    process_with_model(image, key, "hustvl/yolos-tiny")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Image processing completed!')
    }

def process_with_model(image, image_key, model_name):
    try:
        
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_bytes = buffered.getvalue()
        
        
        api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        
        if "yolos" in model_name:
            
            response = requests.post(api_url, headers=headers, data=img_bytes)
        else:
           
            response = requests.post(api_url, headers=headers, json={"inputs": img_bytes})
        
        result = response.json()
        
        image_name = os.path.splitext(os.path.basename(image_key))[0]
        
        model_folder = model_name.split('/')[-1]
        output_key = f"json/{model_folder}_{image_name}.json"
        
        s3.put_object(
            Bucket='btu-2025-classerni',
            Key=output_key,
            Body=json.dumps(result)
        )
        
    except Exception as e:
        print(f"Error processing with {model_name}: {str(e)}")