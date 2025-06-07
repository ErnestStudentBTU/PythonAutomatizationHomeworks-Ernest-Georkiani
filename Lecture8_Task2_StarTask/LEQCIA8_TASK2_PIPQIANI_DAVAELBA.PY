import boto3
import json
import os
import tempfile
from huggingface_hub import InferenceClient
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ImageProcessingResults')

def lambda_handler(event, context):
    try:
        content_type = event['headers']['Content-Type']
        body = event['body']
        
        image_data = body['image']
        model_id = body['model']
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name
        
        client = InferenceClient()
        
        if 'detr' in model_id:
            predictions = client.object_detection(temp_file_path)
        else:
            predictions = client.image_classification(temp_file_path, model=model_id)
        
        s3_bucket = os.environ['S3_BUCKET_NAME']
        s3_key = f"uploads/{context.aws_request_id}.jpg"
        s3.upload_file(temp_file_path, s3_bucket, s3_key)
        
        image_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': s3_bucket, 'Key': s3_key},
            ExpiresIn=3600
        )
        
        item = {
            'requestId': context.aws_request_id,
            'modelId': model_id,
            'predictions': json.dumps(predictions),
            'imageUrl': f"s3://{s3_bucket}/{s3_key}",
            'timestamp': datetime.now().isoformat()
        }
        table.put_item(Item=item)
        
        os.unlink(temp_file_path)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'predictions': predictions,
                'imageUrl': image_url
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }