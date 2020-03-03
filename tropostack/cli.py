import time
import argparse
from datetime import datetime, timedelta, timezone

import botocore
import boto3
import tabulate

from .conf_loaders import partitioned_yaml_loader

class InlineConfCLI():
    """
    TropostackCLI that doesn't take any configuration. All variables need
    to be hardcoded in the Tropostack class.
    """
    _CMD_PREFIX = 'cmd_'

    def __init__(self, stack_cls):
        """Initialize the class and te_terun it as a CLI command"""
        # Parse the CLI arguments
        self.args = self.argparser().parse_args()
        # Instantiate the Tropostack instance
        self.stack = stack_cls(conf={})
        # Save a shortcut to the stack name
        self.stackname = self.stack.stackname
        # Save the command method picked via CLI
        self.run_method = getattr(self, self._CMD_PREFIX + self.args.command)

    # CLI Management
    def argparser(self):
        """Generate the ArgumentParser instance to parse CLI arguments"""
        parser = argparse.ArgumentParser()
        # dynamically generate a list of commands supported by the class,
        # based on naming convention
        class_cmds = [mth[len(self._CMD_PREFIX):] for mth in dir(self)
                      if mth.startswith(self._CMD_PREFIX)
                      and callable(getattr(self, mth))
                      ]
        parser.add_argument('command',  choices=class_cmds)
        return parser

    def run(self):
        """
        Let the CLI command take over.
        """
        self.run_method()

    # CloudFormation helper funcs

    def _aws_stack(self, cfn, exc=True):
        """
        Wrapper around boto3.describe_stacks. Raises RuntimeError if `exc` is
        True and error is encountered. Returns an empty dict otherwise.
        """
        try:
            resp = cfn.describe_stacks(StackName=self.stackname)
        except botocore.exceptions.ClientError:
            if exc:
                raise RuntimeError('Stack "%s" not found' % self.stackname)
            else:
                return {}
        return resp['Stacks'][0]

    def _cfn_conn(self):
        """
        Wrapper around CloudFormation connection establishing.

        Takes a region from the stack instance, if available.
        """
        return boto3.client('cloudformation', region_name=self.stack.region)


    def print_status_while(self, cfn, status, poll_sec=10):
        """
        Keep on polling and printing stack events while the stack is in the
        given state. Try to simulate CloudFormation experience in terminal.
        """
        # get a TZ-aware marker, going back a couple of seconds
        seen = datetime.now(timezone.utc) - timedelta(seconds=3)
        hdr = ['TIMESTAMP (UTC)', 'RESOURCE TYPE',
               'RESOURCE ID', 'STATUS', 'REASON']
        hdr_printed = False
        tabs = '{0:<24} {1:<42} {2:<28} {3:<40} {4}'
        while True:
            try:
                ev_resp = cfn.describe_stack_events(StackName=self.stackname)
            except botocore.exceptions.ClientError as err:
                # stack might have disappeared in the meantime
                print("Stack is gone: {} ({})".format(self.stackname, err))
                return
            # Events sorted by timestamp
            s_ev = sorted(ev_resp['StackEvents'], key=lambda x: x['Timestamp'])
            new = list(ev for ev in s_ev if ev['Timestamp'] > seen)
            if new:
                seen = new[-1]['Timestamp']
            else:
                continue

            if hdr and not hdr_printed:
                print(tabs.format(*hdr))
                hdr_printed = True
            for ev in new:
                print(tabs.format(
                    ev['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    ev['ResourceType'],
                    ev['LogicalResourceId'],
                    ev['ResourceStatus'],
                    ev.get('ResourceStatusReason', '')
                ))
            if self._aws_stack(cfn, exc=False).get('StackStatus') != status:
                break
            time.sleep(poll_sec)

    # Base CloudFormation commands
    def cmd_print(self):
        """Print out the generated stack"""
        print(self.stack.compile().to_yaml())


    def cmd_validate(self):
        """Validates the generated stack against the CloudFormation API"""
        cfn = boto3.client('cloudformation', region_name=self.stack.region)
        template_body = self.stack.compile().to_yaml()
        resp = cfn.validate_template(TemplateBody=template_body)
        status = resp.get('ResponseMetadata', {}).get('HTTPStatusCode', '')
        if status == 200:
            print('Validation OK')
        else:
            raise RuntimeError('Validation failed! Response:\n%s' % resp)

    def cmd_create(self):
        """Creates the stack YAML"""
        cfn = boto3.client('cloudformation', region_name=self.stack.region)
        template_body = self.stack.compile().to_yaml()
        resp = cfn.create_stack(
            StackName=self.stackname,
            TemplateBody=template_body,
            Capabilities=self.stack.CFN_CAPS,
            Tags=self.stack.tags
        )
        status = resp.get('ResponseMetadata', {}).get('HTTPStatusCode', '')
        if status == 200:
            print('Stack creation initiated for: %s' % resp['StackId'])
            self.print_status_while(cfn, 'CREATE_IN_PROGRESS')
        else:
            raise RuntimeError('Creation failed! Response:\n%s' % resp)

    def cmd_update(self, exc_on_noop=True):
        """
        Updates the stack YAML. In case `exc_on_noop` is set to False, then the
        exception that's normally raised if there is nothing to update will be
        swallowed instead of propagated.
        """
        cfn = boto3.client('cloudformation', region_name=self.stack.region)
        # Verify stack exists first
        self._aws_stack(cfn, exc=True)
        template_body = self.stack.compile().to_yaml()

        try:
            resp = cfn.update_stack(
                StackName=self.stackname,
                TemplateBody=template_body,
                Capabilities=self.stack.CFN_CAPS,
                Tags=self.stack.tags
            )
        except botocore.exceptions.ClientError as err:
            # Porcelain! Depends on AWS response message to detect the case
            if not exc_on_noop and 'no updates' in err.args[0].lower():
                print('No updates to be performed for: %s' % self.stackname)
                return
            else:
                raise
        status = resp.get('ResponseMetadata', {}).get('HTTPStatusCode', '')
        if status == 200:
            print('Stack update initiated for:%s' % resp['StackId'])
            self.print_status_while(cfn, 'UPDATE_IN_PROGRESS')
        else:
            raise RuntimeError('Update failed! Response:\n%s' % resp)

    def cmd_delete(self):
        """Deletes the stack and the associated resources"""
        cfn = boto3.client('cloudformation', region_name=self.stack.region)
        # Verify stack exists first
        self._aws_stack(cfn, exc=True)
        resp = cfn.delete_stack(StackName=self.stackname)
        status = resp.get('ResponseMetadata', {}).get('HTTPStatusCode', '')
        if status == 200:
            print('Destroy initiated for stack: %s' % self.stackname)
            self.print_status_while(cfn, 'DELETE_IN_PROGRESS')
        else:
            raise RuntimeError('Update failed! Response:\n%s' % resp)

    def cmd_outputs(self):
        """Prints out the stack outputs"""
        cfn = boto3.client('cloudformation', region_name=self.stack.region)
        stack = self._aws_stack(cfn, exc=True)
        outs = stack.get('Outputs')
        status = stack.get('StackStatus')
        print('Stack is in status: %s' % status)
        if outs:
            print(tabulate.tabulate(outs, headers="keys"))
        else:
            print('No outputs')

    def cmd_apply(self):
        """Creates the stack if it does not exists, otherwise updates it"""
        cfn = boto3.client('cloudformation', region_name=self.stack.region)
        # Verify stack exists first
        resp = self._aws_stack(cfn, exc=False)
        if resp:
            self.cmd_update(exc_on_noop=False)
        else:
            self.cmd_create()


class InlineConfOvrdCLI(InlineConfCLI):
    """
    TropostackCLI that uses a class-level configration, but accpets overrides
    as command-line arguments.
    """

    def __init__(self, stack_cls):
        """Initialize the class and te_terun it as a CLI command"""
        # Parse the CLI arguments
        self.args = self.argparser().parse_args()
        # Use command-line values as initial config
        overrides = {}
        for arg in self.args.conf:
            kv = arg.split('=', 1)
            k = kv[0]
            v = kv[1] if len(kv) == 2 else None
            overrides[k] = v
        # Instantiate the Tropostack instance
        self.stack = stack_cls(conf=overrides)
        # Save a shortcut to the stack name
        self.stackname = self.stack.stackname
        # Save the command method picked via CLI
        self.run_method = getattr(self, self._CMD_PREFIX + self.args.command)

    # CLI Management
    def argparser(self):
        parser = super().argparser()
        #  Add a multi-value config override parameter
        parser.add_argument('--conf', action='append', default = [],
                            help='Override conf variables: --conf foo=bar')
        return parser

class EnvCLI(InlineConfCLI):
    CONF_FUNC = partitioned_yaml_loader

    def __init__(self, stack_cls):
        """Initialize the class and run it as a CLI command"""
        # Parse the CLI arguments
        self.args = self.argparser().parse_args()
        # Use the loader function to render a config based on the CLI config
        # Translates as "from this file,  extract the config for BASE_NAME"
        self.conf = self.__class__.CONF_FUNC(
            self.args.conf_file, stack_cls.BASE_NAME,)
        # Generate a stack instance using the rendered config
        self.stack = stack_cls(self.conf)
        # Create a shortcut to the stackname
        self.stackname = self.stack.stackname
        # Run the command method invoked by the user
        self.run_method = getattr(self, self._CMD_PREFIX + self.args.command)

    def argparser(self):
        """Add parameter for config file"""
        parser = super().argparser()
        parser.add_argument('conf_file', type=argparse.FileType('r'))
        return parser