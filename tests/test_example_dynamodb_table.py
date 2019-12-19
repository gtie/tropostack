from conftest import *

# Stack under test
from examples.dynamodb.dynamodb_table import DynamoDbStack as Sut

def test_stack_init():
    stack = Sut({})

def test_stack_resources():
    stack = Sut({})
    sdict = stack2dict(stack)
    resources = key_by_rsc_type(sdict['Resources'])
    assert 'AWS::DynamoDB::Table' in resources

def test_stack_outputs():
    stack = Sut({})
    sdict = stack2dict(stack)
    assert 'TableName' in sdict['Outputs']
    assert 'TableArn' in sdict['Outputs']