#!/usr/bin/env python3

from troposphere import Output, Export, Sub, GetAtt, Join, Ref
from troposphere import s3
from troposphere import iam

from tropostack.base import InlineConfStack
from tropostack.cli import InlineConfCLI

class S3UserStack(InlineConfStack):
    """
    Tropostack defining an S3 bucket, together with an IAM user account that is
    allowed to access the bucket

    Args:
      region (str): Explicit region specification for the stack
      bucket_name (str): The name of the S3 bucket to be created.
        Can contain AWS variables such as ``${AWS::AccountId}``
      path (str): Templated IAM user path. Must start and finish with a ``/``
      username (str): Templated username, e.g. ``${AWS::StackName}-bot``
      allowed_actions (list of str): S3 API actions to be enabled for the user

    Outputs:
        BucketArn (str): The ARN of the created S3 bucket
        UserName (str): The ARN of the created S3 bucket
    """
    BASE_NAME = 's3-iam-stack'

    CONF = {
        'region': 'eu-west-1',
        'bucket_name': '${AWS::AccountId}-my-s3-iam-test-bucket',
        'path': '/bot/${AWS::StackName}/',
        'username': '${AWS::StackName}-s3bot',
        'allowed_actions': ['s3:*'],
    }

    # Since we are creating a Named IAM user account, we need extra capability
    CFN_CAPS = ['CAPABILITY_NAMED_IAM']

    @property
    def o_bucket_arn(self):
        _id = 'BucketArn'
        return Output(
            _id,
            Description='The ARN of the S3 bucket',
            Value=GetAtt(self.r_bucket,'Arn'),
            Export=Export(Sub("${AWS::StackName}-%s" % _id))
        )

    @property
    def o_username(self):
        _id = 'UserName'
        return Output(
            _id,
            Description='Username of the created bot account',
            Value=self.r_iam_user.ref(),
            Export=Export(Sub("${AWS::StackName}-%s" % _id))
        )

    @property
    def r_bucket(self):
        return s3.Bucket(
            'S3Bucket',
            BucketName=Sub(self.conf['bucket_name']),
        )

    @property
    def r_iam_user(self):
        return iam.User(
            'S3BotUser',
            Path=Sub(self.conf['path']),
            UserName=Sub(self.conf['username']),
            Policies=[
                iam.Policy(
                    'S3BotUserPolicy',
                    PolicyName=Sub("${AWS::StackName}-policy"),
                    PolicyDocument = {
                        "Statement":[{
                            "Action": ['s3:*'],
                            "Effect": "Allow",
                            "Resource": Join("",["arn:aws:s3:::", self.r_bucket.ref(), '/*'], ),
                        }]
                    }
                )
            ]
        )

if __name__ == '__main__':
    cli = InlineConfCLI(S3UserStack)
    cli.run()
