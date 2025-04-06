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
def check_bucket_versioning(bucket_name, flag: str = "vers-check"):
    response = aws_client.get_bucket_versioning(Bucket=bucket_name)
    versioning_status = response.get('Status', 'Not Enabled')
    if versioning_status == 'Enabled':
        typer.echo("Versioning is active.")
    elif versioning_status == 'Suspended':
        typer.echo("Versioning is suspended.")
    else:
        typer.echo("Versioning is not enabled for this bucket.")


@app.command()
def get_file_versions(bucket_name, file_name, flag: str = "get-vers"):
    
    versions = aws_client.list_object_versions(Bucket=bucket_name, Prefix=file_name)

    version_info = []
    for version in versions['Versions']:
            version_id = version['VersionId']
            last_modified = version['LastModified']
            typer.echo(f"Version ID: {version_id}, Last Modified: {last_modified}")
    
    return version_info



@app.command()
def upload_previous_version_as_new(bucket_name, file_name, flag: str = "upload-prev-vers"):

    versions = aws_client.list_object_versions(Bucket=bucket_name, Prefix=file_name)
    
    if len(versions.get('Versions', [])) < 2:
        return "No previous version available."
    
    previous_version = versions['Versions'][1] 

    aws_client.download_file(bucket_name, file_name, 'temp_file')

    aws_client.upload_file('temp_file', bucket_name, file_name)
    return f"Previous version uploaded as new version for file {file_name}"



if __name__ == "__main__":
       
    app()