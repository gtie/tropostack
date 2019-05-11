import pytest

from tropostack.exceptions import InvalidStackError
from tropostack import base

DEF_CFG = {
    'region': 'pytestregion',
    'env': 'pytestenv',
    'release': 'pytestrelease'
}


class TEnvStack(base.EnvStack):
    BASE_NAME = 'sample-stack'


class TReleaseEnvStack(base.ReleaseEnvStack):
    BASE_NAME = 'sample-stack'


def test_stacks_uninstantiable():
    with pytest.raises(InvalidStackError):
        base.BaseStack(DEF_CFG)
    with pytest.raises(InvalidStackError):
        base.EnvStack(DEF_CFG)
    with pytest.raises(InvalidStackError):
        base.ReleaseEnvStack(DEF_CFG)


def test_stack_init():
    stack = TEnvStack(DEF_CFG)
    assert DEF_CFG['env'] in stack.stackname


def test_stack_compile():
    stack = TEnvStack(DEF_CFG)
    compiled = stack.compile()
    assert compiled.to_yaml()
    assert compiled.to_json()


def test_release_stack_init():
    stack = TReleaseEnvStack(DEF_CFG)
    assert DEF_CFG['env'] in stack.stackname
    assert DEF_CFG['release'] in stack.stackname
