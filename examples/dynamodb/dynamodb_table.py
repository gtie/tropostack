#!/usr/bin/env python3
"""
Executable/library defining a Troposphere-powered: DynamoDB
"""
from troposphere import Output, Export, Sub, GetAtt
from troposphere import dynamodb

from tropostack.base import InlineConfStack
from tropostack.cli import InlineConfCLI

class DynamoDbStack(InlineConfStack):
    BASE_NAME = 'example-dynamodb'

    CONF = {
        'region': 'eu-west-1',
        'table_name': 'tropostack-sample-table',
        'table_key': 'tropostack-sample-key',
    }
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
    cli = InlineConfCLI(DynamoDbStack)
    cli.run()
