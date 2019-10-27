import pytest
from conftest import *

# Module under test
import s3_bucket as mut
# Stack under test
from s3_bucket import S3BucketStack as Sut

#from tropostack.conf_loaders import partitioned_yaml_loader

#@pytest.fixture
#def conf(request, scope='module'):
    #fname = os.path.join(os.path.dirname(mut.__file__), 'config_dev.yaml')
    #with open(fname) as fhandle:
        #result = partitioned_yaml_loader(fhandle, Sut.BASE_NAME)
    #return result

def test_stack_init():
    stack = Sut({})
    
def test_stack_resources():
    stack = Sut({})
    sdict = stack2dict(stack)
    resources = key_by_rsc_type(sdict['Resources'])
    
    assert 'AWS::S3::Bucket' in resources
    