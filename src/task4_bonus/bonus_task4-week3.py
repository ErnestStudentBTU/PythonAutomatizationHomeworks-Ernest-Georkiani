import typer
import argparse
import boto3, os, sys
from collections import defaultdict
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
def move_files(bucket):
    ext_count = defaultdict(int)

    for obj in aws_client.list_objects_v2(Bucket=bucket).get('Contents', []):
        ext = os.path.splitext(obj['Key'])[1][1:]
        if ext:
            aws_client.copy_object(Bucket=bucket, CopySource={'Bucket': bucket, 'Key': obj['Key']}, Key=f"{ext}/{obj['Key']}")
            aws_client.delete_object(Bucket=bucket, Key=obj['Key'])
            ext_count[ext] += 1

    print('\n'.join(f"{ext} - {count}" for ext, count in ext_count.items()))

if __name__ == "__main__":
       
    app()