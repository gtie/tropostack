from io import StringIO

import pytest

from tropostack.conf_loaders import partitioned_yaml_loader
from tropostack.exceptions import ConfigLoadError

VALID_CONFIG = '''
env: dev
region: eu
stack-foo:
  k1: v1
  k2: v2
stack-bar:
  var: bar
'''

IVALID_CONFIG_NOYAML = '!!'

IVALID_CONFIG_ROOT = '''
- foo
- bar
'''

INVALID_CONFIG_STACK = '''
env: dev
region: eu
stack-foo:
 - bar
 - baz
'''


def test_partitioned_yaml_loader_usage():
    dict_foo = partitioned_yaml_loader(StringIO(VALID_CONFIG), 'stack-foo')
    assert dict_foo == {'env': 'dev', 'region': 'eu', 'k1': 'v1', 'k2': 'v2'}
    dict_bar = partitioned_yaml_loader(StringIO(VALID_CONFIG), 'stack-bar')
    assert dict_bar == {'env': 'dev', 'region': 'eu', 'var': 'bar'}


def test_partitioned_yaml_loader_validation():
    with pytest.raises(ConfigLoadError):
        partitioned_yaml_loader(StringIO(IVALID_CONFIG_NOYAML), 'stack-foo')
    with pytest.raises(ConfigLoadError):
        partitioned_yaml_loader(StringIO(IVALID_CONFIG_ROOT), 'stack-foo')
    with pytest.raises(ConfigLoadError):
        partitioned_yaml_loader(StringIO(INVALID_CONFIG_STACK), 'stack-foo')
