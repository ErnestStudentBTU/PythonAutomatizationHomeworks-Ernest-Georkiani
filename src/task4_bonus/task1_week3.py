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
from boto3.s3.transfer import TransferConfig

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
def upload_small_files(src:str, bucket_name:str, dest:str):
    try:
        response = aws_client.upload_file(src, bucket_name, dest)
        print("small file uploaded successfully")

    except ClientError as e:
        print("unfortunatelly,small file was not uploaded successfully")

@app.command()
def multipart_upload_boto3(file_path, bucket_name, key):

    config = TransferConfig(
        multipart_threshold=8 * 1024 * 1024,  
        multipart_chunksize=8 * 1024 * 1024,
        #max_concurrency=10,
        #use_threads=True
    )

    try:
        aws_client.upload_file(
            file_path,
            bucket_name,
            key,
            ExtraArgs={'ContentType': 'application/*'},
            Config=config
        )

        print("Uploaded")

    except ClientError as e:
        logging.error(e)
        print("Not uploaded")


@app.command()
def put_policy(bucket_name:str):
    lfc = {
            "Rules": [
            {
                "Expiration": {"Days": 120},
                "ID": "lifepolicy",
                "Filter": {"Prefix": "*"},
                "Status": "Enabled",
                }
              ]
            }
    aws_client.put_bucket_lifecycle_configuration(Bucket=bucket_name , LifecycleConfiguration=lfc)
    print("Lifecycle policy added successfully")

if __name__ == "__main__":
       
    app()