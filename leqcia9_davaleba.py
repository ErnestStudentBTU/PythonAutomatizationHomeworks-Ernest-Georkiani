import argparse
import boto3
import os
import requests

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org')
        response.raise_for_status() 
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error getting public IP: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Create AWS VPC resources and launch an EC2 instance.")
    parser.add_argument("--vpc_id", required=True, help="The ID of the VPC to use.")
    parser.add_argument("--subnet_id", required=True, help="The ID of the subnet to use.")

    args = parser.parse_args()

    vpc_id = args.vpc_id
    subnet_id = args.subnet_id

    ec2 = boto3.client('ec2')

    try:
        security_group_response = ec2.create_security_group(
            Description='Security group for EC2 instance',
            GroupName='my-instance-security-group',
            VpcId=vpc_id
        )
        security_group_id = security_group_response['GroupId']
        print(f"Created security group with ID: {security_group_id}")
    except Exception as e:
        print(f"Error creating security group: {e}")
        return

    public_ip = get_public_ip()
    if not public_ip:
        print("Could not get public IP, SSH access may not work.")
        ssh_cidr = '0.0.0.0/0' 
    else:
        ssh_cidr = f"{public_ip}/32" 

    try:
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {'IpProtocol': 'tcp',
                 'FromPort': 80,
                 'ToPort': 80,
                 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                {'IpProtocol': 'tcp',
                 'FromPort': 22,
                 'ToPort': 22,
                 'IpRanges': [{'CidrIp': ssh_cidr}]}
            ]
        )
        print("Configured inbound rules for HTTP and SSH.")
    except Exception as e:
        print(f"Error configuring inbound rules: {e}")
       
        ec2.delete_security_group(GroupId=security_group_id)
        print(f"Deleted security group {security_group_id} due to error.")
        return

    key_pair_name = 'my-instance-key-pair'
    try:
        key_pair_response = ec2.create_key_pair(KeyName=key_pair_name)
        private_key = key_pair_response['KeyMaterial']
       
        with open(f'{key_pair_name}.pem', 'w') as f:
            f.write(private_key)
        os.chmod(f'{key_pair_name}.pem', 0o400) 
        print(f"Created key pair '{key_pair_name}' and saved the private key to '{key_pair_name}.pem'")
    except Exception as e:
        print(f"Error creating key pair: {e}")
        
        ec2.delete_security_group(GroupId=security_group_id)
        print(f"Deleted security group {security_group_id} due to error.")
        return

    ami_id = 'ami-0abcdef1234567890'  

    try:
        instance_response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            NetworkInterfaces=[
                {
                    'DeviceIndex': 0,
                    'SubnetId': subnet_id,
                    'Groups': [security_group_id],
                    'AssociatePublicIpAddress': True  
                }
            ],
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/sda1',  
                    'Ebs': {
                        'VolumeSize': 10,
                        'VolumeType': 'gp2'
                    }
                }
            ],
            KeyName=key_pair_name
        )
        instance_id = instance_response['Instances'][0]['InstanceId']
        print(f"Launched EC2 instance with ID: {instance_id}")

        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        print(f"Instance {instance_id} is now running.")

        instance_description = ec2.describe_instances(InstanceIds=[instance_id])
        public_ip_address = instance_description['Reservations'][0]['Instances'][0].get('PublicIpAddress')

        if public_ip_address:
            print(f"Instance public IP address: {public_ip_address}")
            print("Please verify SSH access to the instance using the downloaded key pair.")
        else:
            print("Instance did not receive a public IP address.")

    except Exception as e:
        print(f"Error launching EC2 instance: {e}")
    
        ec2.delete_security_group(GroupId=security_group_id)
        ec2.delete_key_pair(KeyName=key_pair_name)
        
        if 'instance_id' in locals():
             ec2.terminate_instances(InstanceIds=[instance_id])
             print(f"Terminated instance {instance_id} due to error.")
        print(f"Cleaned up resources due to error.")


if __name__ == "__main__":
    main()
