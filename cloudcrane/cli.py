#!/usr/bin/env python3

import boto3
import calendar
import click
import yaml

from clickclick.console import print_table

STYLES = {
    'DELETE_COMPLETE': {'fg': 'red'},
    'DELETE_FAILED': {'fg': 'red'},
    'ROLLBACK_COMPLETE': {'fg': 'red'},
    'CREATE_COMPLETE': {'fg': 'green'},
    'CREATE_FAILED': {'fg': 'red'},
    'CREATE_IN_PROGRESS': {'fg': 'yellow', 'bold': True},
    'DELETE_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'ROLLBACK_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'ROLLBACK_FAILED': {'fg': 'red'},
    'UPDATE_COMPLETE': {'fg': 'green'},
    'UPDATE_ROLLBACK_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'UPDATE_IN_PROGRESS': {'fg': 'yellow', 'bold': True},
    'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS': {'fg': 'red', 'bold': True},
    'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS': {'fg': 'yellow', 'bold': True},
    'UPDATE_FAILED': {'fg': 'red'},
    'UPDATE_ROLLBACK_COMPLETE': {'fg': 'red'},
}

TITLES = {}

@click.group(chain=True)
def cli():
    """
    Cloudcrane's command group.
    """


@cli.command()
@click.option('--application', help='Name of the application the AWS CloudFormation stack should be created for')
@click.option('--version', help='Version of the application the AWS CloudFormation stack should be created for')
@click.option('--region', default='eu-central-1', help='AWS region to create the new stack in')
@click.option('--template', help='AWS CloudFormation template')
@click.option('--parameters', help='YAML file with parameters for AWS CloudFormation template')
def create(application, version, region, template, parameters):
    """
    Create AWS CloudFormation stack for an application.
    """

    cf = boto3.client('cloudformation')

    with open(template, 'r') as f:
        cf_template = f.read()

    with open(parameters, 'rb') as f:
        cf_parameters = yaml.load(f)

    cf_parameters_list = list()
    for key, value in cf_parameters.items():
        cf_parameters_list.append({'ParameterKey': key, 'ParameterValue': value})

    cf.create_stack(
        StackName=application + '-' + version,
        TemplateBody=cf_template,
        Parameters=cf_parameters_list,
        DisableRollback=False,
        NotificationARNs=[],
        Capabilities=[
            'CAPABILITY_IAM',
            ],
        Tags=[
            {
                'Key': 'name',
                'Value': application
            },
            {
                'Key': 'version',
                'Value': version
            }
        ]
    )


@cli.command()
@click.option('--application', help='Name of the application the AWS CloudFormation stack should be created for')
@click.option('--version', help='Version of the application the AWS CloudFormation stack should be created for')
@click.option('--region', default='eu-central-1', help='AWS region to create the new stack in')
def delete(application, version, region):
    """
    Delete AWS CloudFormation stack for an application.
    """

    cf = boto3.client('cloudformation')

    cf.delete_stack(
        StackName=application + '-' + version,
    )


@cli.command('list')
def list_stacks():
    """
    List active AWS CloudFormation stacks.
    """

    cf = boto3.client('cloudformation')

    response = cf.list_stacks(
        StackStatusFilter=[
            'CREATE_IN_PROGRESS',
            'CREATE_FAILED',
            'CREATE_COMPLETE',
            'ROLLBACK_IN_PROGRESS',
            'ROLLBACK_FAILED',
            'ROLLBACK_COMPLETE',
            'DELETE_IN_PROGRESS',
            'DELETE_FAILED',
            # 'DELETE_COMPLETE',
            'UPDATE_IN_PROGRESS',
            'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
            'UPDATE_COMPLETE',
            'UPDATE_ROLLBACK_IN_PROGRESS',
            'UPDATE_ROLLBACK_FAILED',
            'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS',
            'UPDATE_ROLLBACK_COMPLETE',
            'REVIEW_IN_PROGRESS'
            ]
    )
    rows = []

    for stack in response['StackSummaries']:
        rows.append({'stack_name': stack['StackName'],
                     'status': stack['StackStatus'],
                     'creation_time': calendar.timegm(stack['CreationTime'].timetuple()),
                     'description': stack['TemplateDescription']})

    rows.sort(key=lambda x: x['stack_name'])

    columns = ['stack_name', 'status', 'creation_time', 'description']
    print_table(columns, rows, styles=STYLES, titles=TITLES)


def main():
    cli()


if __name__ == "__main__":
    main()
