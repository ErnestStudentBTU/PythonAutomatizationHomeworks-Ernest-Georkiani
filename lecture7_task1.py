import boto3
from os import getenv
import argparse

ec2_client = boto3.client(
  "ec2",
  aws_access_key_id=getenv("aws_access_key_id"),
  aws_secret_access_key=getenv("aws_secret_access_key"),
  aws_session_token=getenv("aws_session_token"),
  region_name=getenv("aws_region_name")
)

def list_vpcs():
  result = ec2_client.describe_vpcs()
  vpcs = result.get("Vpcs")
  print(vpcs)

def create_vpc():
  result = ec2_client.create_vpc(CidrBlock="10.0.0.0/16")
  vpc = result.get("Vpc")
  print(vpc)
  return result

def add_name_tag(vpc_id, name="Ernesto"):
  ec2_client.create_tags(Resources=[vpc_id],
                       Tags=[{
                         "Key": "Name",
                         "Value": name
                       }])

def create_igw():
  result = ec2_client.create_internet_gateway()
  return result.get("InternetGateway").get("InternetGatewayId")

def create_public_subnet(vpc_id, cidr="10.0.1.0/24"):
  result = ec2_client.create_subnet(CidrBlock=cidr, VpcId=vpc_id)
  return result.get("Subnet").get("SubnetId")

def create_private_subnet(vpc_id="vpc-0bde832998b4d4910", cidr="10.0.2.0/24", az='us-east-1a'):
    subnet_id = ec2_client.create_subnet(VpcId=vpc_id, CidrBlock=cidr, AvailabilityZone=az)["Subnet"]["SubnetId"]
    ec2_client.modify_subnet_attribute(SubnetId=subnet_id, MapPublicIpOnLaunch={'Value': False})
    ec2_client.associate_route_table(
        RouteTableId=ec2_client.create_route_table(VpcId=vpc_id)["RouteTable"]["RouteTableId"],
        SubnetId=subnet_id
    )
    return subnet_id

def attach_igw_to_vpc(vpc_id, igw_id):
  ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)

def main():

    parser = argparse.ArgumentParser(description="AWS VPC Management Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    
    list_parser = subparsers.add_parser('list-vpcs', help='List all VPCs')
    
    
    create_vpc_parser = subparsers.add_parser('create-vpc', help='Create a new VPC')
    create_vpc_parser.add_argument('--name', type=str, help='Name tag for the VPC', default="Ernesto")
    
    
    create_igw_parser = subparsers.add_parser('create-igw', help='Create an Internet Gateway')
    
    
    attach_igw_parser = subparsers.add_parser('attach-igw', help='Attach Internet Gateway to VPC')
    attach_igw_parser.add_argument('--vpc-id', type=str, required=True, help='VPC ID to attach to')
    attach_igw_parser.add_argument('--igw-id', type=str, required=True, help='Internet Gateway ID to attach')
    
    
    pub_sub_parser = subparsers.add_parser('create-public-subnet', help='Create a public subnet')
    pub_sub_parser.add_argument('--vpc-id', type=str, required=True, help='VPC ID for the subnet')
    pub_sub_parser.add_argument('--cidr', type=str, default="10.0.1.0/24", help='CIDR block for the subnet')
    
    
    priv_sub_parser = subparsers.add_parser('create-private-subnet', help='Create a private subnet')
    priv_sub_parser.add_argument('--vpc-id', type=str, required=True, help='VPC ID for the subnet')
    priv_sub_parser.add_argument('--cidr', type=str, default="10.0.2.0/24", help='CIDR block for the subnet')
    priv_sub_parser.add_argument('--az', type=str, default='us-east-1a', help='Availability Zone for the subnet')
    
    args = parser.parse_args()
    
    if args.command == 'list-vpcs':
        list_vpcs()
    elif args.command == 'create-vpc':
        vpc_response = create_vpc()
        vpc_id = vpc_response.get("Vpc").get("VpcId")
        add_name_tag(vpc_id, args.name)
    elif args.command == 'create-igw':
        igw_id = create_igw()
        print(f"Created Internet Gateway: {igw_id}")
    elif args.command == 'attach-igw':
        attach_igw_to_vpc(args.vpc_id, args.igw_id)
        print(f"Attached IGW {args.igw_id} to VPC {args.vpc_id}")
    elif args.command == 'create-public-subnet':
        subnet_id = create_public_subnet(args.vpc_id, args.cidr)
        print(f"Created Public Subnet: {subnet_id}")
    elif args.command == 'create-private-subnet':
        subnet_id = create_private_subnet(args.vpc_id, args.cidr, args.az)
        print(f"Created Private Subnet: {subnet_id}")
    else:
        "Error"

if __name__ == "__main__":
    main()