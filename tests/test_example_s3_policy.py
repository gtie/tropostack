from conftest import *

# Stack under test
from s3_policy import S3BucketStack as Sut

def test_stack_init():
    stack = Sut({})

def test_stack_resources():
    stack = Sut({})
    sdict = stack2dict(stack)
    resources = key_by_rsc_type(sdict['Resources'])

    assert 'AWS::S3::Bucket' in resources

def test_stack_outputs():
    stack = Sut({})
    sdict = stack2dict(stack)
    assert 'BucketArn' in sdict['Outputs']