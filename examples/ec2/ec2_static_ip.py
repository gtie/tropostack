#!/usr/bin/env python3

from troposphere import ec2
from troposphere import Output, Export, Sub, GetAtt, Ref

from tropostack.base import InlineConfStack
from tropostack.cli import InlineConfCLI

class EC2Stack(InlineConfStack):
    """
    Single-instance EC2 stack, which assigns a static IP address to the
    instance. Also features a security group, dedicated to the instance/stack.
    Uses a human-friendly AMI path specification rather than AMI ID.

    Args:
      region (str): Region where the stack/instance would be deployed
      instance_type (str): EC2 instance type
      ami_location (str): Qualified path to the AMI (i.e. Source in the UI).
        Example: ``amazon/amzn2-ami-hvm-2.0.20191116.0-x86_64-ebs``
      vpc_id (str): VPC that the instance would be a part of
      subnet_id (str): ID of the subnet where the instance would be deployed
      ssh_key_name (str): SSH Keypair name to be associated with the instance
      private_ip (str): Static IP address of the instance. Must be available
        under the respective Subnet
      access (list of 3-tuples): List of 3 tuples to allow Ingress from,
        formatted as (Protocol, Port, Network Range). Sample value:
        ``[('tcp', 22, '0.0.0.0/0'), ]``
    """

    BASE_NAME = 'ec2-instance'
    CONF = {
        'region': 'eu-west-1',
        'instance_type': 't3.nano',
        'access': [('tcp', 22, '0.0.0.0/0'), ],
        'vpc_id': 'REPLACE-ME',
        'subnet_id': 'REPLACE-ME',
        'ssh_key_name': 'REPLACE-ME',
        'private_ip': 'REPLACE-ME',
        'ami_location': '',
    }

    @property
    def r_ec2_secgroup(self):
        return ec2.SecurityGroup(
            "Ec2SecurityGroup",
            VpcId=self.conf['vpc_id'],
            GroupDescription="Access to the instance ports",
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    IpProtocol=proto,
                    FromPort=port,
                    ToPort=port,
                    CidrIp=cidr,
                ) for (proto, port, cidr) in self.conf['access']
            ],
        )

    @property
    def r_ec2(self):
        return ec2.Instance(
            "Ec2Instance",
            ImageId=self.ami_by_location(self.conf['ami_location']),
            InstanceType=self.conf['instance_type'],
            KeyName=self.conf['ssh_key_name'],
            SecurityGroupIds=[self.r_ec2_secgroup.ref()],
            PrivateIpAddress=self.conf['private_ip'],
            SubnetId = self.conf['subnet_id']
        )

if __name__ == '__main__':
    # Wrap the stack in a CLI and run it
    cli = InlineConfCLI(EC2Stack)
    cli.run()