import typer
import argparse
import boto3
import magic
import io
import logging
from botocore.exceptions import ClientError
from os import getenv
from dotenv import load_dotenv
import json

load_dotenv()

app = typer.Typer()

def init_client():

    try:
        client = boto3.client("s3",
                aws_access_key_id=getenv("aws_access_key_id"),
                aws_secret_access_key=getenv("aws_secret_access_key"),
                aws_session_token=getenv("aws_session_token"),
                region_name=getenv("aws_region_name")
                )
    
        client.list_buckets()

        return client
    
    except ClientError as e:
        logging.error(e)
    except:
        print("Undefined error")

aws_client = init_client()

@app.command()
def list_buckets():

    try:
       
       buckets = aws_client.list_buckets()
       if buckets:
           for bucket in buckets["Buckets"]:
               print(f'{bucket["Name"]}')

    except ClientError as e:
        logging.error(e)

@app.command()
def create_bucket(bucket_name:str, region="us-west-2"):
    try:
        location = {"LocationConstraint": region}
        aws_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=location)
        print("Bucket successfully created!")
    except ClientError as e:
        logging.error(e)

@app.command()
def delete_bucket(bucket_name):
    try:
        aws_client.delete_bucket(Bucket=bucket_name)
    except ClientError as e:
        logging.error(e)

@app.command()
def bucket_exists(bucket_name):
    try:
        aws_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' exists")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"Bucket '{bucket_name}' does not exist")
        else:
            print(f"Error checking bucket existence: {e}")
        return False

@app.command()
def set_object_access_policy(bucket_name, file_name):
    try:
        response = aws_client.put_object_acl(ACL="public-read", Bucket=bucket_name, Key=file_name)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        if status_code == 200:
            print("Yes, bucket exists and ACL granted")
        else:
            print("Bucket does not exists or other error occured")
    except ClientError as e:
        logging.error(e)
    
def generate_public_read_policy(bucket_name):
    policy = {
        "Version":
        "2012-10-17",
        "Statement": [{
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{bucket_name}/*",
        }],
    }

    return json.dumps(policy)

@app.command()
def create_bucket_policy(bucket_name):
     aws_client.delete_public_access_block(Bucket=bucket_name)
     aws_client.put_bucket_policy(Bucket=bucket_name, Policy=generate_public_read_policy(bucket_name))
     print("Bucket succesfully have policy now")

@app.command()
def read_bucket_policy(bucket_name):
    try:
        policy = aws_client.get_bucket_policy(Bucket=bucket_name)
        policy_str = policy["Policy"]
        print(policy_str)
    except ClientError as e:
        print(e)

@app.command()
def download_file_and_upload_to_s3(bucket_name:str, url:str, file_name:str, keep_local=False):
    
    from urllib.request import urlopen
    import io

    mime = magic.Magic(mime=True)

    with urlopen(url) as response:

        content = response.read()

        mime_type = mime.from_buffer(content)

        valid_mime_types = ['image/bmp', 'image/jpeg', 'image/png', 'image/webp', 'video/mp4']

        if mime_type not in valid_mime_types:
            print(f"Unsupported file type: {mime_type}. Supported types: .bmp, .jpg, .jpeg, .png, .webp, .mp4")

        try:
            aws_client.upload_fileobj(
                Fileobj=io.BytesIO(content),
                Bucket=bucket_name,
                ExtraArgs={'ContentType': mime_type},
                Key=file_name)
            print("Object(image) uploaded successfully!")
        except Exception as e:
            print(e)

    if keep_local:
        with open(file_name, mode='wb') as file:
            file.write(content)

    return f"https://s3-us-west-2.amazonaws.com/btu-classroom-11/file_example_JPG_100kB.jpg"


if __name__ == "__main__":
       
    app()