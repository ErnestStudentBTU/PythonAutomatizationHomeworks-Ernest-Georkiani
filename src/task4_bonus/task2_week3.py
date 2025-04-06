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


def delete_file_from_bucket(bucket_name:str, file_name:str):
    try:
        aws_client.delete_object(Bucket=bucket_name, Key=file_name)
        print("File successfully deleted from bucket")
    except ClientError as e:
        logging.error(e)
        print("File was not deleted from bucket")

@app.command()
def manage_file(bucket_name:str, file_name:str, flag:str):


    if flag == "del":
        delete_file_from_bucket(bucket_name,file_name)
    else:
        print("Command was not recognized")

if __name__ == "__main__":
       
    app()