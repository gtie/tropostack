import tabulate
import botocore
import boto3
import time
import argparse
from datetime import datetime, timedelta, timezone

from .conf_loader import partitioned_yaml_loader


class EnvCLI():
    CONF_FUNC = partitioned_yaml_loader
    _CMD_PREFIX = 'cmd_'

    def argparser(self):
        """Generate the ArgumentParser instance to parse CLI arguments"""
        parser = argparse.ArgumentParser()
        # dynamically generate a list of commands supported by the class,
        # based on naming convention
        class_cmds = [mth[len(self._CMD_PREFIX):] for mth in dir(self)
                      if mth.startswith(self._CMD_PREFIX)
                      and callable(getattr(self, mth))
                      ]
        parser.add_argument('conf_file', type=argparse.FileType('r'))
        parser.add_argument('command',  choices=class_cmds)
        return parser

    def __init__(self, stack_cls):
        """Initialize the class and run it as a CLI command"""
        # Parse the CLI arguments
        self.args = self.argparser().parse_args()
        # Use the loader function to render a config based on the CLI config
        # Basically means "from this file handle, extract the config for BASE_NAME"
        self.conf = self.__class__.CONF_FUNC(self.args.conf_file, stack_cls.BASE_NAME,)
        # Generate a stack instance using the rendered config
        self.stack = stack_cls(self.conf)
        # Create a shortcut to the stackname
        self.stackname = self.stack.stackname
        # Run the command method invoked by the user
        method = getattr(self, self._CMD_PREFIX + self.args.command)
        method()

    def cmd_generate(self):
        """Print the generated stack out"""
        print(self.stack.compile().to_yaml())

    def _aws_stack(self, cfn, exc=True):
        """
        Wrapper around boto3.describe_stacks. Raises RuntimeError if `exc` is
        True and error is encountered. Silently returns an empty dict otherwise.
        """
        try:
            resp = cfn.describe_stacks(StackName=self.stackname)
        except botocore.exceptions.ClientError as err:
            if exc:
                raise RuntimeError('Stack "%s" not found' % name)
            else:
                return {}
        return resp['Stacks'][0]

    #Command-line functionality goes below
    def print_status_while(self, cfn, status, poll_sec=10):
        """
        Keep on polling and printing stack events while the stack is in the
        given state. Try to simulate CloudFormation experience in terminal.
        """
        #get a TZ-aware marker, going back a couple of seconds
        seen = datetime.now(timezone.utc) - timedelta(seconds=3)
        hdr = ['TIMESTAMP (UTC)', 'RESOURCE TYPE', 'RESOURCE ID', 'STATUS', 'REASON']
        tabs = '{0:<24} {1:<42} {2:<28} {3:<40} {4}'
        while True:
            try:
                ev_resp = cfn.describe_stack_events(StackName=self.stackname)
            except botocore.exceptions.ClientError as err:
                #stack might have disappeared in the meantime
                print("Stack is gone: {} ({})".format(self.stackname, err))
                return
            #Events sorted by timestamp
            s_ev = sorted(ev_resp['StackEvents'], key=lambda x: x['Timestamp'])
            new = list(ev for ev in s_ev if ev['Timestamp'] > seen)
            if new:
                seen = new[-1]['Timestamp']
            else:
                continue

            if hdr:
                print(tabs.format(*hdr))
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
        #Verify stack exists first
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
        #Verify stack exists first
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
            print(tabulate(outs, headers="keys", tablefmt="grid"))
        else:
            print('No outputs')

    def cmd_apply(self):
        """Creates the stack if it does not exists, otherwise updates it"""
        cfn = boto3.client('cloudformation', region_name=self.stack.region)
        #Verify stack exists first
        resp = self._aws_stack(cfn, exc=False)
        if resp:
            self.cmd_update(exc_on_noop=False)
        else:
            self.cmd_create()
