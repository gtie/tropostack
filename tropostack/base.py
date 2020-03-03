from collections.abc import Iterable

from troposphere import Template
import boto3

from tropostack.exceptions import InvalidStackError


class BaseStack():
    CFN_CAPS = []
    BASE_NAME = None

    # Methods prefixed with below prefix return Troposphere/CFN Resources
    _RSC_PREFIX = 'r_'
    # Methods prefixed with below prefix return Troposphere/CFN Outputs
    _OUT_PREFIX = 'o_'

    def __init__(self, conf):
        self.conf = conf
        # The only absolutely required configuration of each stack is its region
        self.region = conf.get('region')
        self.validate()

    def validate(self):
        # No class is valid without a name
        if not self.BASE_NAME:
            raise InvalidStackError("Stack is missing BASE_NAME attribute")
        # While it is sometimes possible to proceed without a region for some
        # stacks, AWS partitions such as China require one, so it is best to
        # consistenly require it
        if not getattr(self, 'region'):
            raise InvalidStackError("Stack configuration is missing: region")

    def ami_by_location(self, location):
        """
        Find AMI according to the given location
        """
        if self.region == 'pytest' or not self.region or not location:
            # Short-circuit if we're running a test or do not have data
            return 'ami-notfound'
        client = boto3.client('ec2', region_name=self.region)
        response = client.describe_images(Filters=[
            {'Name': 'manifest-location', 'Values': [location]},
        ])
        if len(response['Images']) == 0:
            raise RuntimeError('No AMIs found with location: %s' % location)
        if len(response['Images']) > 1:
            raise RuntimeError('Multiple AMIs found: %s' % response['Images'])
        return response['Images'][0]['ImageId']


    @property
    def stackname(self):
        """Name composition is up to the derived classes"""
        raise NotImplementedError

    def compile(self, template=None):
        """
        Generate a Troposphere Template object by attaching the results of all
        methods/properties following the `_RSC_PREFIX`/`_OUT_PREFIX` convention
        as either Resources or Outputs.
        """
        # Support for attaching resources to externally-passed template,
        # allowing for creating "composite" stacks, where resources are built
        # on top of existing stack objects
        if template is None:
            template = Template()

        # Auto-detect and add resources/outputs based on prefix + introspection
        for attr in dir(self):
            add_fn = None
            # Handle Resource addition
            if attr.startswith(self._RSC_PREFIX):
                add_fn = template.add_resource
            # Handle Outputs addition
            elif attr.startswith(self._OUT_PREFIX):
                add_fn = template.add_output
            # Ignore if the property is not of interest
            if not add_fn:
                continue

            value = getattr(self, attr)
            # Handle iterable vs non-iterable resource/outputs
            if isinstance(value, Iterable):
                [add_fn(elem) for elem in value]
            else:
                add_fn(value)
        return template

    @property
    def tags(self):
        """Generate the stack-wide tags for CloudFormation"""
        return [
            {'Key': 'Name', 'Value': self.stackname},
            {'Key': 'BaseName', 'Value': self.BASE_NAME},
        ]

class InlineConfStack(BaseStack):
    CONF = {}
    def __init__(self, conf):
        # Override the class CONF with any passed-in config dict
        super().__init__(conf={** self.CONF, ** conf})

    @property
    def stackname(self):
        """Name can be parametrized on the passed conf"""
        return self.BASE_NAME.format(**self.conf)

class EnvStack(BaseStack):

    def __init__(self, conf):
        self.env = conf.get('env')
        super().__init__(conf=conf)

    @property
    def stackname(self):
        return '{}-{}'.format(self.BASE_NAME, self.env)

    def validate(self):
        if not self.env:
            raise InvalidStackError("Stack configiration is missing: env")
        super().validate()

    @property
    def tags(self):
        parent_tags = super().tags
        return parent_tags + [{'Key': 'Env', 'Value': self.env}]



class ReleaseEnvStack(EnvStack):
    def __init__(self, conf):
        self.release = conf.get('release')
        super().__init__(conf)

    def validate(self):
        super().validate()
        if not self.release:
            raise InvalidStackError("Stack configiration is missing: release")
        super().validate()

    @property
    def stackname(self):
        return '{}-{}-{}'.format(self.BASE_NAME, self.env, self.release)

    @property
    def tags(self):
        parent_tags = super().tags
        return parent_tags + [{'Key': 'Release', 'Value': self.release}]