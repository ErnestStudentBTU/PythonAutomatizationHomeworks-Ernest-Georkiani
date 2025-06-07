import argparse
import boto3
from botocore.exceptions import ClientError

def create_vpc(ec2_client, cidr_block):
    
    try:
        response = ec2_client.create_vpc(CidrBlock=cidr_block)
        vpc_id = response['Vpc']['VpcId']
        print(f"VPC Created: {vpc_id}")
        return vpc_id
    except ClientError as e:
        print(f"Error creating VPC: {e}")
        return None

def create_subnet(ec2_client, vpc_id, cidr_block, availability_zone, is_public=False):
    
    try:
        response = ec2_client.create_subnet(
            VpcId=vpc_id,
            CidrBlock=cidr_block,
            AvailabilityZone=availability_zone
        )
        subnet_id = response['Subnet']['SubnetId']
        print(f"Subnet Created: {subnet_id}")
        if is_public:
            ec2_client.modify_subnet_attribute(
                SubnetId=subnet_id,
                MapPublicIpOnLaunch={'Value': True}
            )
            print(f"Subnet {subnet_id} set to auto-assign public IPs.")
        return subnet_id
    except ClientError as e:
        print(f"Error creating subnet: {e}")
        return None

def create_internet_gateway(ec2_client, vpc_id):
    
    try:
        response = ec2_client.create_internet_gateway()
        igw_id = response['InternetGateway']['InternetGatewayId']
        print(f"Internet Gateway Created: {igw_id}")
        ec2_client.attach_internet_gateway(
            InternetGatewayId=igw_id,
            VpcId=vpc_id
        )
        print(f"Internet Gateway {igw_id} attached to VPC {vpc_id}.")
        return igw_id
    except ClientError as e:
        print(f"Error creating or attaching Internet Gateway: {e}")
        return None

def create_public_route_table(ec2_client, vpc_id, igw_id):
    
    try:
        response = ec2_client.create_route_table(VpcId=vpc_id)
        route_table_id = response['RouteTable']['RouteTableId']
        print(f"Public Route Table Created: {route_table_id}")
        ec2_client.create_route(
            RouteTableId=route_table_id,
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=igw_id
        )
        print("Route to Internet Gateway added to public route table.")
        return route_table_id
    except ClientError as e:
        print(f"Error creating public route table or route: {e}")
        return None

def associate_route_table_with_subnet(ec2_client, route_table_id, subnet_id):
    
    try:
        ec2_client.associate_route_table(
            RouteTableId=route_table_id,
            SubnetId=subnet_id
        )
        print(f"Route table {route_table_id} associated with subnet {subnet_id}.")
    except ClientError as e:
        print(f"Error associating route table with subnet: {e}")

def main():
    parser = argparse.ArgumentParser(description='Create an AWS VPC with specified public and private subnets.')
    parser.add_argument('--vpc-cidr', required=True, help='CIDR block for the VPC (e.g., 10.0.0.0/16).')
    parser.add_argument('--num-public-subnets', type=int, default=1, help='Number of public subnets to create (max 200 total).')
    parser.add_argument('--num-private-subnets', type=int, default=1, help='Number of private subnets to create (max 200 total).')

    args = parser.parse_args()

    total_subnets = args.num_public_subnets + args.num_private_subnets
    if total_subnets > 200:
        print("Error: Total number of subnets cannot exceed 200.")
        return

    ec2_client = boto3.client('ec2')

    
    try:
        response = ec2_client.describe_availability_zones(State='available')
        availability_zones = [az['ZoneName'] for az in response['AvailabilityZones']]
        if not availability_zones:
            print("Error: No available Availability Zones found.")
            return
    except ClientError as e:
        print(f"Error describing Availability Zones: {e}")
        return

    
    vpc_id = create_vpc(ec2_client, args.vpc_cidr)
    if not vpc_id:
        return

    
    igw_id = create_internet_gateway(ec2_client, vpc_id)
    if not igw_id:
        
        return

    
    public_route_table_id = create_public_route_table(ec2_client, vpc_id, igw_id)
    if not public_route_table_id:
        
        return

    vpc_cidr_parts = args.vpc_cidr.split('/')
    base_cidr = vpc_cidr_parts[0]
    base_ip_parts = list(map(int, base_cidr.split('.')))
    cidr_prefix = int(vpc_cidr_parts[1])

    if cidr_prefix > 23: 
         print("Error: VPC CIDR block must be at least /23 to accommodate /24 subnets.")
         
         return

    subnet_cidr_prefix = 24

    public_subnet_ids = []
    for i in range(args.num_public_subnets):
        if i >= len(availability_zones):
            print(f"Warning: Not enough Availability Zones for all public subnets. Creating {len(availability_zones)} public subnets.")
            break
        subnet_cidr = f"{base_ip_parts[0]}.{base_ip_parts[1]}.{base_ip_parts[2] + i}.0/{subnet_cidr_prefix}"
        subnet_id = create_subnet(ec2_client, vpc_id, subnet_cidr, availability_zones[i], is_public=True)
        if subnet_id:
            public_subnet_ids.append(subnet_id)
            associate_route_table_with_subnet(ec2_client, public_route_table_id, subnet_id)

    
    private_subnet_ids = []
    for i in range(args.num_private_subnets):
        if i + args.num_public_subnets >= len(availability_zones):
             print(f"Warning: Not enough Availability Zones for all private subnets. Creating {len(availability_zones) - args.num_public_subnets} private subnets.")
             break
        subnet_cidr = f"{base_ip_parts[0]}.{base_ip_parts[1]}.{base_ip_parts[2] + args.num_public_subnets + i}.0/{subnet_cidr_prefix}"
        subnet_id = create_subnet(ec2_client, vpc_id, subnet_cidr, availability_zones[args.num_public_subnets + i], is_public=False)
        if subnet_id:
            private_subnet_ids.append(subnet_id)

    print("\nVPC creation process completed (simplified).")
    print(f"VPC ID: {vpc_id}")
    print(f"Public Subnet IDs: {public_subnet_ids}")
    print(f"Private Subnet IDs: {private_subnet_ids}")

if __name__ == '__main__':
    main()