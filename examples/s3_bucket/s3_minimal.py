#!/usr/bin/env python3

from troposphere import s3
from troposphere import Output, Export, Sub, GetAtt

from tropostack.base import InlineConfStack
from tropostack.cli import InlineConfCLI


class MyS3BucketStack(InlineConfStack):
    # Name of the stack
    BASE_NAME = 'my-s3-bucket-stack'

    # Define configuration values for the stack
    CONF = {
        # Region is always explicitly required
        'region': 'eu-west-1',
        # Prefix the bucket name with the account ID
        'bucket_name': Sub('${AWS::AccountId}-my-first-tropostack-bucket')
    }

    # Stack Resources are defined as class properties prefixed with 'r_'
    @property
    def r_bucket(self):
        return s3.Bucket(
            'MyBucketResource',
            BucketName=self.conf['bucket_name']
        )

    # Stack Outputs are defined as class properties prefixed with 'o_'
    @property
    def o_bucket_arn(self):
        _id = 'BucketArn'
        return Output(
            _id,
            Description='The ARN of the S3 bucket',
            Value=GetAtt(self.r_bucket, 'Arn'),
            # We're exporting the output as <StackName>-<OutputId>
            # Other stacks can read the output relying on the same convention
            Export=Export(Sub("${AWS::StackName}-%s" % _id))
        )


if __name__ == '__main__':
    cli = InlineConfCLI(MyS3BucketStack)
    cli.run()
