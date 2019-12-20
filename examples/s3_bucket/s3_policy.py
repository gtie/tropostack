#!/usr/bin/env python3

from troposphere import Output, Export, Sub, GetAtt, Join
from troposphere import s3
import boto3.s3

from tropostack.base import InlineConfStack
from tropostack.cli import InlineConfCLI

class S3BucketStack(InlineConfStack):
    """
    Tropostack defining an S3 bucket with optional IP-based access restriction

    Args:
      allowed_cidr (str): IP CIDR range to allow access from.
        Use ``0.0.0.0/0`` to allow access from anywhere.
      bucket_name (str): The name of the S3 bucket to be created.
        Can contain AWS variables such as ``${AWS::AccountId}``

    Outputs:
        BucketArn (str): The ARN of the created S3 bucket
    """
    # Base name for all instances of that same stack
    BASE_NAME = 'example-s3-stack'

    # Since this stack is declared as InlineConf - no external configuration -
    # we add any settings as part of the class itself
    CONF = {
        'region': 'eu-west-1',
        'bucket_name': '${AWS::AccountId}-tropostack-my-test-bucket',
        'allowed_cidr': '0.0.0.0/0'
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
            BucketName=Sub(self.conf['bucket_name']),
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
                                "aws:SourceIp": self.conf['allowed_cidr']
                            }
                        }
                }]

            }
        )

class AugmentedCLI(InlineConfCLI):
    """
    Extend the default set of CLI commands to add a custom action.
    """
    # Create a custom command, but part of the Tropostack script
    def cmd_purge(self):
        """
        Delete all objects inside the S3 bucket, along with the bucket itself.
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
