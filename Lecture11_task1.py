import argparse
import boto3
import logging
from botocore.exceptions import ClientError
from auth import aws_client
from vpc import (
    create_vpc, add_name_tag, get_or_set_igw,
    create_route_table_without_route, create_subnet,
    associate_route_table_to_subnet, create_route_table_with_route,
    enable_auto_public_ips
)
from ec2 import (
    create_key_pair, create_security_group, add_ssh_access_sg, run_ec2
)
from rds import (
    create_db_subnet_group, create_rds_security_group, create_db_instance
)

logging.basicConfig(level=logging.INFO)

def rollback(resources):
    logging.warning("Initiating rollback...")
    ec2 = boto3.client('ec2')
    rds = boto3.client('rds')

    for resource in reversed(resources):
        try:
            r_type, r_id = resource
            if r_type == 'instance':
                ec2.terminate_instances(InstanceIds=[r_id])
                logging.info(f"Terminated EC2 instance: {r_id}")
            elif r_type == 'sg':
                ec2.delete_security_group(GroupId=r_id)
                logging.info(f"Deleted Security Group: {r_id}")
            elif r_type == 'subnet':
                ec2.delete_subnet(SubnetId=r_id)
                logging.info(f"Deleted Subnet: {r_id}")
            elif r_type == 'rtb':
                ec2.delete_route_table(RouteTableId=r_id)
                logging.info(f"Deleted Route Table: {r_id}")
            elif r_type == 'igw':
                igw_id, vpc_id = r_id
                ec2.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
                ec2.delete_internet_gateway(InternetGatewayId=igw_id)
                logging.info(f"Deleted IGW: {igw_id}")
            elif r_type == 'vpc':
                ec2.delete_vpc(VpcId=r_id)
                logging.info(f"Deleted VPC: {r_id}")
            elif r_type == 'rds_subnet_group':
                rds.delete_db_subnet_group(DBSubnetGroupName=r_id)
                logging.info(f"Deleted RDS Subnet Group: {r_id}")
            elif r_type == 'db_instance':
                rds.delete_db_instance(DBInstanceIdentifier=r_id, SkipFinalSnapshot=True)
                logging.info(f"Deleted RDS Instance: {r_id}")
        except Exception as e:
            logging.error(f"Failed to delete {resource}: {e}")

def create_bastion(args):
    ec2_client = aws_client('ec2', args.region)
    rds_client = aws_client('rds', args.region)

    resources = []

    try:
        vpc_id = create_vpc(ec2_client, args.vpc_cidr)
        resources.append(('vpc', vpc_id))
        add_name_tag(ec2_client, vpc_id, "bastion-vpc")

        igw_id = get_or_set_igw(ec2_client, vpc_id)
        resources.append(('igw', (igw_id, vpc_id)))

        private_subnets = []
        for i, cidr in enumerate(['10.0.0.0/24', '10.0.1.0/24']):
            subnet_id = create_subnet(ec2_client, vpc_id, cidr, f'private_sub_{i}', f'{args.region}a')
            resources.append(('subnet', subnet_id))
            rtb_id = create_route_table_without_route(ec2_client, vpc_id)
            resources.append(('rtb', rtb_id))
            associate_route_table_to_subnet(ec2_client, rtb_id, subnet_id)
            private_subnets.append(subnet_id)

        public_subnet = create_subnet(ec2_client, vpc_id, '10.0.2.0/24', 'public_sub_1', f'{args.region}a')
        resources.append(('subnet', public_subnet))
        pub_rtb_id = create_route_table_with_route(ec2_client, vpc_id, 'public_route', igw_id)
        resources.append(('rtb', pub_rtb_id))
        associate_route_table_to_subnet(ec2_client, pub_rtb_id, public_subnet)
        enable_auto_public_ips(ec2_client, public_subnet, 'enable')

        create_key_pair(ec2_client, args.key_name)

        ec2_sg = create_security_group(ec2_client, "bastion-ec2-sg", "Access for bastion host", vpc_id)
        resources.append(('sg', ec2_sg))
        add_ssh_access_sg(ec2_client, ec2_sg)

        instance_id = run_ec2(ec2_client, ec2_sg, public_subnet, args.instance_name)
        resources.append(('instance', instance_id))

        subnet_group_name = "bastion-subnet-group"
        create_db_subnet_group(rds_client, subnet_group_name, vpc_id, private_subnets)
        resources.append(('rds_subnet_group', subnet_group_name))

        rds_sg = create_rds_security_group(ec2_client, "bastion-rds-sg", vpc_id, ec2_sg)
        resources.append(('sg', rds_sg))

        create_db_instance(rds_client, rds_sg, subnet_group_name)
        resources.append(('db_instance', 'bastion-db-instance'))

        logging.info("Bastion setup complete")

    except Exception as e:
        logging.error(f"Error during setup: {e}")
        rollback(resources)

def main():
    parser = argparse.ArgumentParser(description="AWS Bastion Host CLI Tool")
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    parser.add_argument('--vpc-cidr', type=str, default='10.0.0.0/16')
    parser.add_argument('--region', type=str, default='us-east-1')
    parser.add_argument('--key-name', type=str, default='bastion-key')
    parser.add_argument('--instance-name', type=str, default='bastion-ec2')

    args = parser.parse_args()

    if args.create:
        create_bastion(args)
    elif args.rollback:
        logging.info("Performing manual rollback")
        rollback([
            ('db_instance', 'bastion-db-instance'),
            ('rds_subnet_group', 'bastion-subnet-group'),
            ('instance', 'i-xxxxxxxxxxxxxxxxx'),
            ('sg', 'sg-xxxxxxxxxxxxxxxxx'),
            ('vpc', 'vpc-xxxxxxxxxxxxxxxxx'),
        ])
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
