from conftest import *

# Stack under test
from examples.ec2.ec2_static_ip import EC2Stack as Sut

def test_stack_init():
    stack = Sut({})

def test_stack_resources():
    stack = Sut({})
    sdict = stack2dict(stack)
    resources = key_by_rsc_type(sdict['Resources'])
    assert 'AWS::EC2::Instance' in resources
    assert 'AWS::EC2::SecurityGroup' in resources
