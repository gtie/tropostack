from conftest import *

# Stack under test
from examples.s3_bucket.s3_user import S3UserStack as Sut

def test_stack_init():
    stack = Sut({})

def test_stack_resources():
    stack = Sut({})
    sdict = stack2dict(stack)
    resources = key_by_rsc_type(sdict['Resources'])

    assert 'AWS::S3::Bucket' in resources
    assert 'AWS::IAM::User' in resources

def test_stack_outputs():
    stack = Sut({})
    sdict = stack2dict(stack)
    assert 'BucketArn' in sdict['Outputs']
    assert 'UserName' in sdict['Outputs']