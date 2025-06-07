import argparse
import boto3
from botocore.exceptions import ClientError

def create_security_group(ec2_client, sg_name, description):
    try:
        response = ec2_client.create_security_group(
            GroupName=sg_name,
            Description=description
        )
        sg_id = response['GroupId']
        print(f"Security Group Created: {sg_id}")

        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {'IpProtocol': 'tcp',
                 'FromPort': 3306,
                 'ToPort': 3306,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
            ]
        )
        print("Ingress rule added for MySQL port 3306.")
        return sg_id
    except ClientError as e:
        print(e)
        return None

def create_rds_instance(rds_client, instance_identifier, master_username, master_password, sg_id):
    try:
        response = rds_client.create_db_instance(
            DBInstanceIdentifier=instance_identifier,
            Engine='mysql',
            DBInstanceClass='db.t3.large',  
            AllocatedStorage=60,
            MasterUsername=master_username,
            MasterUserPassword=master_password,
            VpcSecurityGroupIds=[sg_id],
            PubliclyAccessible=True, 
            StorageType='gp2' 
        )
        print(f"RDS instance {instance_identifier} creation initiated.")
        return response['DBInstance']
    except ClientError as e:
        print(e)
        return None

def main():
    parser = argparse.ArgumentParser(description='Create an AWS RDS instance and Security Group.')
    parser.add_argument('--instance-identifier', required=True, help='Identifier for the RDS instance.')
    parser.add_argument('--master-username', required=True, help='Master username for the RDS instance.')
    parser.add_argument('--master-password', required=True, help='Master password for the RDS instance.')
    parser.add_argument('--security-group-name', required=True, help='Name for the new Security Group.')
    parser.add_argument('--security-group-description', default='Security group for RDS instance', help='Description for the new Security Group.')

    args = parser.parse_args()

    ec2_client = boto3.client('ec2')
    rds_client = boto3.client('rds')
    
    sg_id = create_security_group(ec2_client, args.security_group_name, args.security_group_description)

    if sg_id:
        
        rds_instance = create_rds_instance(
            rds_client,
            args.instance_identifier,
            args.master_username,
            args.master_password,
            sg_id
        )

        if rds_instance:
            print("Waiting for RDS instance to become available...")
            waiter = rds_client.get_waiter('db_instance_available')
            try:
                waiter.wait(DBInstanceIdentifier=args.instance_identifier)
                print(f"RDS instance {args.instance_identifier} is available.")
                
                instance_description = rds_client.describe_db_instances(DBInstanceIdentifier=args.instance_identifier)['DBInstances'][0]
                endpoint = instance_description['Endpoint']['Address']
                print(f"RDS Endpoint: {endpoint}")
            except ClientError as e:
                print(f"Error waiting for instance to become available: {e}")

if __name__ == '__main__':
    main()
