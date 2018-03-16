#!/usr/bin/env python3

import boto3
import calendar
import click
import yaml

from clickclick.console import print_table

from .base_template import BASE_TEMPLATE

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


@cli.command('cluster')
@click.argument('command')
@click.option('--cluster-name', default='default', help='Name of the ECS cluster (default = "default")')
@click.option('--ami', help='ID of AMI to be used for the instances of the cluster')
@click.option('--instance-type', default='t2.micro', help='EC2 instance type (default = t2.micro)')
@click.option('--max-instances', default='1', help='Maximum number of EC2 instances in auto-scaling group')
def cluster(command, cluster_name, ami, instance_type, max_instances):
    """
    Manage ECS clusters.

    Possible commands: create, list, delete
    """
    ecs = boto3.client('ecs')

    if command == 'create':
        ecs.create_cluster(clusterName=cluster_name)

        cf_parameters = dict()
        cf_parameters['EcsClusterName'] = cluster_name
        cf_parameters['EcsAmiId'] = ami
        cf_parameters['EcsInstanceType'] = instance_type
        cf_parameters['AsgMaxSize'] = max_instances
        __create_cf_stack(stack_name=cluster_name, version='1', parameters=cf_parameters)

    elif command == 'list':
        __list_stacks(all=cluster_name == 'all')

    elif command == 'delete':
        __delete_cf_stack(stack_name=cluster_name, version='1')
        ecs.delete_cluster(cluster=cluster_name)


@cli.command('service')
@click.argument('command')
@click.option('--application', help='Name of the application the AWS CloudFormation stack should be created for')
@click.option('--cluster-name', default='default', help='Name of the ECS cluster (default = "default")')
@click.option('--version', help='Version of the application the AWS CloudFormation stack should be created for')
@click.option('--region', default='eu-central-1', help='AWS region to create the new stack in')
@click.option('--parameters', default='cloudcrane.yaml', help='YAML file with parameters for deployment of service to ECS')
def service(command, cluster_name, application, version, region, parameters):
    """
    Manage services in ECS cluster.

    Possible commands: deploy
    """
    if command == 'deploy':

        with open(parameters, 'rb') as f:
            cf_parameters = yaml.load(f)

        container_definitions = list()
        container_definitions.append(cf_parameters)

        ecs = boto3.client('ecs')
        ecs.register_task_definition(
            family=application,
            taskRoleArn='',
            volumes=[
            ],
            containerDefinitions=container_definitions
        )

        ecs.run_task(
            cluster=cluster_name,
            taskDefinition=application
        )


def __create_cf_stack(stack_name, version, parameters):
    """
    Create AWS CloudFormation stack for an application.
    """

    cf = boto3.client('cloudformation')

    cf_template = BASE_TEMPLATE

    cf_parameters_list = list()
    for key, value in parameters.items():
        cf_parameters_list.append({'ParameterKey': key, 'ParameterValue': value})

    cf.create_stack(
        StackName=stack_name + '-' + version,
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
                'Value': stack_name
            },
            {
                'Key': 'version',
                'Value': version
            }
        ]
    )


def __delete_cf_stack(stack_name, version):
    """
    Delete AWS CloudFormation stack for an application.
    """

    cf = boto3.client('cloudformation')

    cf.delete_stack(
        StackName=stack_name + '-' + version,
    )


def __list_stacks(all):
    """
    List active AWS CloudFormation stacks.
    """

    cf = boto3.client('cloudformation')

    if all:
        stack_status_filter = []
    else:
        stack_status_filter = [
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

    response = cf.list_stacks(StackStatusFilter=stack_status_filter)
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
