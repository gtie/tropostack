#!/usr/bin/env python3
"""
Sample Tropostack script for defining an S3 bucket with IP-based access control
"""
from troposphere import Output, Export, Sub, GetAtt, Join
from troposphere import s3
import boto3.s3

from tropostack.base import InlineConfStack
from tropostack.cli import InlineConfCLI

class S3BucketStack(InlineConfStack):
    """
    """
    # Base name for all instances of that same stack
    BASE_NAME = 'example-s3-stack'
    
    # Since this stack is declared as InlineConf - no external configuration -
    # we add any settings as part of the class itself
    CONF = {
        'region': 'eu-west-1',
        'bucket_name': 'tropostack-my-test-bucket',
        'allowed_cidrs': '0.0.0.0/0'
    }

    # This is an Output element in the stack, as denoted by leading 'o_'
    @property
    def o_bucket_arn(self):
        _id = 'BucketArn'
        return Output(
            _id,
            Description='The ARN of the S3 bucket',
            Value=GetAtt(self.r_bucket,'Arn'),
            # We're exporting the output as <StackName>-<OutputName>
            # Other stacks can consume the output value using the same naming
            Export=Export(Sub("${AWS::StackName}-%s" % _id))
        )

    # Below are the Resource elements in the stack, specified by a leading 'r_'
    @property
    def r_bucket(self):
        # Create an S3 Bucket
        return s3.Bucket(
            'S3Bucket',
            # Bucket name comes from configuraion file
            BucketName=self.conf['bucket_name'],
        )

    @property
    def r_bucket_policy(self):
        # Append a policy to the S3 bucket
        return s3.BucketPolicy(
            'S3BucketPolicy',
            # We're addressing the bucket directly as a property of the instance
            Bucket = self.r_bucket.BucketName,
            PolicyDocument = {
                "Statement":[{
                    "Action":["s3:GetObject"],
                        "Effect":"Allow",
                        # We obtain a list of permitted CIDRs from the configuration
                        "Resource": Join("",["arn:aws:s3:::", self.r_bucket.ref(), '/*'], ),
                        "Principal":"*",
                        "Condition":{
                            "IpAddress": {
                                "aws:SourceIp": self.conf['allowed_cidrs']
                            }
                        }
                }]

            }
        )

class AugmentedCLI(InlineConfCLI):
    """
    Extend the default set of CLI commands with a custom one.
    """
    # Create a custom command, but part of the Tropostack script
    def cmd_purge(self):
        """
        Delete all objects inside the S3 bucket.
        """
        # Retrieve the name directly from the generated stack
        bucket_name = self.stack.r_bucket.BucketName
        bucket = boto3.resource('s3').Bucket(bucket_name)
       
        try:
            print('Deleting all objects in bucket: {}'.format(bucket_name))
            bucket.objects.all().delete()
            print('Deleting bucket itself')
            bucket.delete()
        except Exception as err:
            print('Failed purging bucket {}: {}'.format(bucket_name, err))
            raise
        print('Done.')

if __name__ == '__main__':
    cli = AugmentedCLI(S3BucketStack)
    cli.run()
