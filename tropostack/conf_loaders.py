"""
Configuration loading routines
"""
from collections.abc import Mapping

import yaml

from tropostack.exceptions import ConfigLoadError


def partitioned_yaml_loader(fhanlde, stack_basename):
    """
    This loader expects a file handle  to parse YAML from. The root of the YAML
    document must be a mapping. The top-level keys with simple (non-mapping)
    values would be returned, updated with the value of a mapping named the same
    as `stack_basename`

    Args:
        fhandle (file): A file-handle-compatible stream
        stack_basename (str): Base name of the stack to be configured

    Returns:
        dict: Flattened configuration dict pertinent to the specific stack

    Raises:
        tropostack.exceptions.ConfigLoadError: When configuraiton parsing fails

    Usage:
    >>> import StringIO
    >>> config_src = StringIO(u'''
    ...  env: dev
    ...  region: eu-west-1
    ...  stack-foo:
    ...      stackvar: baz
    ...  stack-bar:
    ...      stackvar: bar
    ... ''')
    >>> partitioned_yaml_loader(config_src, 'stack-bar') ==  \\
    ...   {'env': 'dev', 'region': 'eu-west-1', 'stackvar': 'bar'}
    True


    """
    try:
        full_conf = yaml.safe_load(fhanlde)
    except yaml.YAMLError as exc:
        raise ConfigLoadError('YAML Parsing failed: %s' % exc)
    stack_conf = {}
    if not isinstance(full_conf, Mapping):
        raise ConfigLoadError('Top-level configuration must be a mapping')
    for key, value in full_conf.items():
        if not isinstance(value, Mapping):
            # Only non-mapping values get "inherited"
            stack_conf[key] = value
    stack_tree = full_conf.get(stack_basename, {})
    if not isinstance(stack_tree, Mapping):
        raise ConfigLoadError('Stack-specific config must be a mapping')
    stack_conf.update(stack_tree)
    return stack_conf
