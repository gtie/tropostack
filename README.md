tropostack
==========

[![Latest PyPI version](https://img.shields.io/pypi/v/tropostack.svg)](https://pypi.python.org/pypi/tropostack)
[![Build Status](https://travis-ci.org/gtie/tropostack.svg?branch=master)](https://travis-ci.org/gtie/tropostack)

Wrapper around the excellent Troposphere library for easy creation and management of CloudFormation stacks.

Getting Started
-----

You use `tropostack` as a library to:
 - Consisteny define CloudFormation templates in Python code
 - Have a CLI around each stack definition, enabling it to live as a standalone executable
 
Here is a minimalistic example of a stack that creates a DynamoDB table with a single key:

```
#!/usr/bin/env python3
from troposphere import Output, Export, Ref, Sub, GetAtt
from troposphere import dynamodb

from tropostack.base import EnvStack
from tropostack.cli import EnvCLI

class DynamoDbStack(EnvStack):
    BASE_NAME = 'example-dynamodb'

    @property
    def o_dynamodb_table_name(self):
        _id = 'TableName'
        return Output(
            _id,
            Description='The name of the DynamoDB table',
            Value=self.r_table.ref(),
            Export=Export(Sub("${AWS::StackName}-%s" % _id))
        )

    @property
    def o_dynamodb_table_arn(self):
        _id = 'TableArn'
        return Output(
            _id,
            Description='The ARN identifier of the DynamoDB table',
            Value=GetAtt(self.r_table, 'Arn'),
            Export=Export(Sub("${AWS::StackName}-%s" % _id))
        )

    @property
    def r_table(self):
        table_name = self.conf['table_name']
        table_key = self.conf['table_key']
        return dynamodb.Table(
            'DynamoDbTable',
            TableName=table_name,
            BillingMode='PAY_PER_REQUEST',
            AttributeDefinitions=[
                dynamodb.AttributeDefinition(
                    AttributeName=table_key,
                    AttributeType='S'
                ),
            ],
            KeySchema=[
                dynamodb.KeySchema(
                    AttributeName=table_key,
                    KeyType='HASH'
                )
            ]
        )

if __name__ == '__main__':
    cli = EnvCLI(DynamoDbStack)
```

The above already gives you a CLI around your stack definition.
Assuming you put it inside an executable file called `my_dynamodb.py`, you'd be able to call it already:
```
$ ./my_dynamodb.py -h
usage: my_dynamodb.py [-h]
                    conf_file
                    {apply,create,delete,generate,outputs,update,validate}

positional arguments:
  conf_file
  {apply,create,delete,generate,outputs,update,validate}

optional arguments:
  -h, --help            show this help message and exit

```

To enable the stack definition to be reused across multiple environments (e.g. def, test, production) with differing details,
a configuration file is required (by default). A simple configuration file for the above stack would look like:
```
env: dev
region: eu-west-1

example-dynamodb:
  table_name: my-test-table
  table_key: my-id
```

Now we can fire up the CloudFormation stack that would create our DynamoDB table:
```
$ ./dynamodb_table.py config.yaml create
Stack creation initiated for: arn:aws:cloudformation:eu-west-1:472799024263:stack/example-dynamodb-dev/2e0f8430-e2a9-11e9-bd25-0aac5439e4be
TIMESTAMP (UTC)          RESOURCE TYPE                              RESOURCE ID                  STATUS                                   REASON
2019-09-29 11:06:26      AWS::CloudFormation::Stack                 example-dynamodb-dev         CREATE_IN_PROGRESS                       User Initiated
2019-09-29 11:06:28      AWS::DynamoDB::Table                       DynamoDbTable                CREATE_IN_PROGRESS                       
2019-09-29 11:06:28      AWS::DynamoDB::Table                       DynamoDbTable                CREATE_IN_PROGRESS                       Resource creation Initiated
2019-09-29 11:06:59      AWS::DynamoDB::Table                       DynamoDbTable                CREATE_COMPLETE                          
2019-09-29 11:07:00      AWS::CloudFormation::Stack                 example-dynamodb-dev         CREATE_COMPLETE                     
```

(the `apply` subcommand above is equivalent to _create or update_)

Stock commands
------------
While the CLI can be expanded for particular stacks, there are several subcommands that come out of the box:
  - `generate` - prints the resulting CloudFormation YAML to the screen 
  - `validate` - Sends the CloudFormation template to the AWS API for validation, and reports back result
  - `create` - Initiates the stack creation (should only be used if the stack does not exist yet)
  - `update` - Updates an existing stack (should only be used if the stack exists)
  - `apply` - Idempotently updates or creates a stack, based on whether it exists or not
  - `outputs` - Shows the outputs of an existing stack
  - `delete` - Deletes an existing stack


Installation
------------
`pip install tropostack`


Compatibility
-------------

Licence
-------
See LICENSE file.

Authors
-------
`tropostack` was written by `tie <tropostack /\ morp.org>`.
